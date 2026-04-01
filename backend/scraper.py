import requests
from bs4 import BeautifulSoup
import time
from sqlalchemy.orm import Session
from database import Race, Entry, Exhibition
from models import Racer, ExhibitionInfo
import lxml
import re

BASE_URL = "https://www.boatrace.jp/owpc/pc/race"

def fetch_html(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        print(f"[SCRAPER] Fetching URL: {url}")
        res = requests.get(url, headers=headers, timeout=20)
        if res.status_code == 200:
            if "boatrace.jp" in url:
                res.encoding = "utf-8"
            elif "marugameboat.jp" in url:
                res.encoding = "shift_jis"
            else:
                res.encoding = res.apparent_encoding
            return res.text
    except Exception as e:
        print(f"[SCRAPER] Error fetching {url}: {e}")
    return None

def parse_float_safe(text: str, default: float = 0.0) -> float:
    try:
        # 数字とドット以外を除去
        m = re.search(r'(\d+\.\d+)', text)
        if m: return float(m.group(1))
        # fallback
        num_text = "".join(filter(lambda x: x.isdigit() or x == '.', text))
        return float(num_text) if num_text else default
    except:
        return default

def fetch_today_schedule(hd: str):
    url = f"{BASE_URL}/index?hd={hd}"
    html = fetch_html(url)
    if not html: return []
    
    soup = BeautifulSoup(html, 'lxml')
    venues = []
    links = soup.find_all('a', href=re.compile(r'raceindex\?jcd=\d+&hd=' + hd))
    seen_jcds = set()
    
    venue_map = {"01":"桐生","02":"戸田","03":"江戸川","04":"平和島","05":"多摩川","06":"浜名湖","07":"蒲郡","08":"常滑","09":"津","10":"三国","11":"びわこ","12":"住之江","13":"尼崎","14":"鳴門","15":"丸亀","16":"児島","17":"宮島","18":"徳山","19":"下関","20":"若松","21":"芦屋","22":"福岡","23":"唐津","24":"大村"}

    for link in links:
        m = re.search(r'jcd=(\d+)', link['href'])
        if m:
            jcd = m.group(1)
            if jcd in seen_jcds: continue
            seen_jcds.add(jcd)
            name = venue_map.get(jcd, link.text.strip())
            venues.append({"jcd": jcd, "name": name, "status": "開催中"})
    
    if not venues:
        jcds = re.findall(r'jcd=(\d+)&hd=' + hd, html)
        for jcd in sorted(list(set(jcds))):
            venues.append({"jcd": jcd, "name": venue_map.get(jcd, f"場{jcd}"), "status": "開催中"})

    return venues

def fetch_marugame_data(rno: int, hd: str):
    """
    丸亀競艇の独自サイトから展示・コメントを取得。
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    base_url = "https://www.marugameboat.jp/asp/kyogi/15/pc"
    results = {"exhibitions": []}
    
    yoso_url = f"{base_url}/yoso05{rno:02}.htm"
    try:
        res = requests.get(yoso_url, headers=headers, timeout=5)
        if res.status_code == 200:
            res.encoding = res.apparent_encoding # 自動判別 (丸亀は通常 Shift_JIS)
            soup = BeautifulSoup(res.text, 'lxml')
            
            # オリジナル展示データの抽出
            # ヘッダー列に「一周」「まわり足」「直線」が含まれるテーブルを探す
            target_table = None
            for table in soup.find_all('table'):
                header_text = table.get_text()
                if "一周" in header_text and "まわり足" in header_text and "直線" in header_text:
                    target_table = table
                    break
            
            temp_exh = {}
            if target_table:
                for row in target_table.find_all('tr'):
                    tds = row.find_all('td')
                    if len(tds) >= 8:
                        w_text = tds[0].get_text(strip=True)
                        if w_text.isdigit():
                            w = int(w_text)
                            temp_exh[w] = {
                                "waku": w,
                                "time": parse_float_safe(tds[4].text),
                                "lap": parse_float_safe(tds[5].text),
                                "turn": parse_float_safe(tds[6].text),
                                "straight": parse_float_safe(tds[7].text),
                                "comment": None
                            }
            
            # 選手コメントの抽出 (#yoso03_04 内のテーブルを優先)
            comment_div = soup.find('div', id='yoso03_04')
            target_comment_table = None
            if comment_div:
                target_comment_table = comment_div.find('table')
            
            if not target_comment_table:
                # フォールバック: テキストベースで探す
                for table in soup.find_all('table'):
                    header_text = table.text
                    if "コメント" in header_text and ("当日" in header_text or "前日" in header_text):
                        target_comment_table = table
                        break
            
            if target_comment_table:
                for row in target_comment_table.find_all('tr'):
                    tds = row.find_all('td')
                    if len(tds) >= 3:
                        # 枠番の特定
                        w_text = tds[0].get_text(strip=True)
                        w = None
                        if w_text.isdigit():
                            w = int(w_text)
                        
                        if not w:
                            # 以前のロジック (badge_w1 等) も念のため
                            w_badge = tds[0].find('span', class_=re.compile(r'badge_w\d'))
                            if w_badge:
                                m = re.search(r'badge_w(\d)', str(w_badge))
                                if m: w = int(m.group(1))
                        
                        if w and w in temp_exh:
                            # コメント抽出 (td.col3 にあるはずだが、tds[2] でアクセス)
                            comment_td = tds[2]
                            # 当日コメント (come01) を優先
                            today_p = comment_td.find('p', class_='come01')
                            if not today_p:
                                # come01がなくても、最初のpタグを試す
                                ps = comment_td.find_all('p')
                                for p in ps:
                                    if '前日' not in p.text:
                                        today_p = p
                                        break
                                if not today_p and ps: today_p = ps[0]
                            
                            if today_p:
                                # "当日" や "記者の目" などのラベルを除去
                                text_content = []
                                for node in today_p.children:
                                    if node.name is None: # Text node
                                        text_content.append(node.strip())
                                    elif node.name != 'span': # 不明なタグの中身は取るがspan(ラベル)は除外
                                        text_content.append(node.get_text(strip=True))
                                
                                comment = " ".join([t for t in text_content if t])
                                if not comment: # 念のため全部取り
                                    comment = today_p.get_text(separator=" ").replace("当日", "").replace("記者の目", "").strip()
                                
                                temp_exh[w]["comment"] = comment
            
            results["exhibitions"] = list(temp_exh.values())
            if results["exhibitions"]:
                print(f"[SCRAPER] Marugame details found (including comments) for {len(results['exhibitions'])} racers.")
    except Exception as e:
        print(f"[SCRAPER] Error fetching Marugame data: {e}")
            
    return results

def fetch_common_sp_data(jcd: str, rno: int, hd: str):
    """
    芦屋(21)、徳山(18)など共通のSPサイトシステムを採用している会場から展示・コメントを取得。
    """
    venue_domain_map = {
        "18": "https://www.boatrace-tokuyama.jp",
        "21": "https://www.boatrace-ashiya.com"
    }
    
    base_domain = venue_domain_map.get(jcd)
    if not base_domain: 
        return {"exhibitions": []}
        
    base_url = f"{base_domain}/sp/index.php"
    results = {"exhibitions": []}
    headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"}
    
    # 1. 選手コメントの取得
    comment_url = f"{base_url}?page=raceinfo-racer_comment&rno={rno}"
    comments_map = {}
    try:
        res = requests.get(comment_url, headers=headers, timeout=5)
        if res.status_code == 200:
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, 'lxml')
            # 共通システムでは #table1 または table.table1 を使用
            table = soup.select_one('#table1') or soup.select_one('.table1')
            if table:
                for row in table.find_all('tr')[1:]: # ヘッダー飛ばし
                    tds = row.find_all('td')
                    if len(tds) >= 3:
                        w_text = tds[0].get_text(strip=True)
                        if w_text.isdigit():
                            w = int(w_text)
                            # 21:芦屋は3列目, 18:徳山も3列目(当日コメント)
                            comments_map[w] = tds[2].get_text(strip=True)
    except Exception as e:
        print(f"[SCRAPER] Error fetching SP comments for JCD {jcd}: {e}")

    # 2. オリジナル展示データの取得
    exh_param = "raceinfo-original_exhibition" if jcd == "18" else "raceinfo-exhibition"
    exh_url = f"{base_url}?page={exh_param}&rno={rno}"
    try:
        res = requests.get(exh_url, headers=headers, timeout=5)
        if res.status_code == 200:
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, 'lxml')
            table = soup.select_one('#table1') or soup.select_one('.table1')
            if table:
                for row in table.find_all('tr'):
                    tds = row.find_all('td')
                    if len(tds) >= 6:
                        w_text = tds[0].get_text(strip=True)
                        if w_text.isdigit():
                            w = int(w_text)
                            results["exhibitions"].append({
                                "waku": w,
                                "time": parse_float_safe(tds[2].text),
                                "straight": parse_float_safe(tds[3].text),
                                "turn": parse_float_safe(tds[4].text),
                                "lap": parse_float_safe(tds[5].text),
                                "comment": comments_map.get(w)
                            })
    except Exception as e:
        print(f"[SCRAPER] Error fetching SP exhibition for JCD {jcd}: {e}")
            
    return results

def fetch_ashiya_data(rno: int, hd: str):
    return fetch_common_sp_data("21", rno, hd)

def fetch_tokuyama_data(rno: int, hd: str):
    return fetch_common_sp_data("18", rno, hd)

def fetch_fukuoka_data(rno: int, hd: str):
    """
    福岡(22)のSPサイトから展示・コメントを取得。
    """
    base_url = "https://www.boatrace-fukuoka.com/sp/index.php"
    results = {"exhibitions": []}
    headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"}
    
    # 1. 選手コメント
    comment_url = f"{base_url}?page=yosou-syussou&race={rno}"
    comments_map = {}
    try:
        res = requests.get(comment_url, headers=headers, timeout=5)
        if res.status_code == 200:
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, 'lxml')
            box = soup.select_one('div.box.box-yosou-syussou-4')
            if box:
                table = box.select_one('table')
                if table:
                    for row in table.find_all('tr')[1:]:
                        tds = row.find_all('td')
                        if len(tds) >= 4:
                            w_text = tds[0].get_text(strip=True)
                            if w_text.isdigit():
                                comments_map[int(w_text)] = tds[3].get_text(strip=True)
    except Exception as e:
        print(f"[SCRAPER] Error fetching Fukuoka comments: {e}")

    # 2. 展示データ
    exh_url = f"{base_url}?page=yosou-cyokuzen&race={rno}"
    try:
        res = requests.get(exh_url, headers=headers, timeout=5)
        if res.status_code == 200:
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, 'lxml')
            box = soup.select_one('div.box.box-chokuzen-1')
            if box:
                table = box.select_one('table')
                if table:
                    for row in table.find_all('tr'):
                        tds = row.find_all('td')
                        if len(tds) >= 4:
                            w_text = tds[0].get_text(strip=True)
                            if w_text.isdigit():
                                w = int(w_text)
                                results["exhibitions"].append({
                                    "waku": w,
                                    "time": 0.0, # 公式から取る
                                    "straight": parse_float_safe(tds[3].text),
                                    "turn": parse_float_safe(tds[2].text),
                                    "lap": parse_float_safe(tds[1].text),
                                    "comment": comments_map.get(w)
                                })
    except Exception as e:
        print(f"[SCRAPER] Error fetching Fukuoka exhibition: {e}")
            
    return results

def fetch_naruto_data(rno: int, hd: str):
    """
    鳴門(14)のSPサイトから展示・コメントを取得。
    """
    base_url = "https://www.n14.jp/sp/index.php"
    results = {"exhibitions": []}
    headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"}
    
    # 1. 選手コメント
    comment_url = f"{base_url}?page=yosou-syussou&race={rno}"
    comments_map = {}
    try:
        res = requests.get(comment_url, headers=headers, timeout=5)
        if res.status_code == 200:
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, 'lxml')
            # 鳴門の選手コメントは .box-yosou-syussou-3
            box = soup.select_one('div.box.box-yosou-syussou-3')
            if box:
                table = box.select_one('table')
                if table:
                    for row in table.find_all('tr')[1:]:
                        tds = row.find_all('td')
                        if len(tds) >= 4:
                            w_text = tds[0].get_text(strip=True)
                            if w_text.isdigit():
                                comments_map[int(w_text)] = tds[3].get_text(strip=True)
    except Exception as e:
        print(f"[SCRAPER] Error fetching Naruto comments: {e}")

    # 2. 展示データ
    exh_url = f"{base_url}?page=yosou-chokuzen&race={rno}"
    try:
        res = requests.get(exh_url, headers=headers, timeout=5)
        if res.status_code == 200:
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, 'lxml')
            # 鳴門のオリジナル展示データは .box-yosou-chokuzen-3
            box = soup.select_one('div.box.box-yosou-chokuzen-3')
            if box:
                table = box.select_one('table')
                if table:
                    for row in table.find_all('tr'):
                        tds = row.find_all('td')
                        if len(tds) >= 4:
                            w_text = tds[0].get_text(strip=True)
                            if w_text.isdigit():
                                w = int(w_text)
                                results["exhibitions"].append({
                                    "waku": w,
                                    "time": 0.0, # 公式から取得
                                    "straight": parse_float_safe(tds[3].text),
                                    "turn": parse_float_safe(tds[2].text),
                                    "lap": parse_float_safe(tds[1].text),
                                    "comment": comments_map.get(w)
                                })
    except Exception as e:
        print(f"[SCRAPER] Error fetching Naruto exhibition: {e}")
            
    return results

def fetch_kiryu_data(rno: int, hd: str):
    """
    桐生(01)のSPサイトから展示・コメントを取得。
    """
    base_url = "https://www.kiryu-kyotei.com/sp/index.php"
    results = {"exhibitions": []}
    headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"}
    
    # 1. 選手コメント
    comment_url = f"{base_url}?page=yosou-syussou&race={rno}"
    comments_map = {}
    try:
        res = requests.get(comment_url, headers=headers, timeout=5)
        if res.status_code == 200:
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, 'lxml')
            # 桐生の選手コメントは .box-yosou-syussou-2
            box = soup.select_one('div.box.box-yosou-syussou-2')
            if box:
                table = box.select_one('table')
                if table:
                    for row in table.find_all('tr'):
                        tds = row.find_all('td')
                        if len(tds) >= 3:
                            w_text = tds[0].get_text(strip=True)
                            if w_text.isdigit():
                                comments_map[int(w_text)] = tds[2].get_text(strip=True)
    except Exception as e:
        print(f"[SCRAPER] Error fetching Kiryu comments: {e}")

    # 2. 展示データ
    exh_url = f"{base_url}?page=yosou-chokuzen&race={rno}"
    try:
        res = requests.get(exh_url, headers=headers, timeout=5)
        if res.status_code == 200:
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, 'lxml')
            # 桐生のオリジナル展示データは .box-yosou-chokuzen-1
            box = soup.select_one('div.box.box-yosou-chokuzen-1')
            if box:
                table = box.select_one('table')
                if table:
                    for row in table.find_all('tr'):
                        tds = row.find_all('td')
                        if len(tds) >= 6:
                            w_text = tds[0].get_text(strip=True)
                            if w_text.isdigit():
                                w = int(w_text)
                                results["exhibitions"].append({
                                    "waku": w,
                                    "time": parse_float_safe(tds[2].text),
                                    "straight": parse_float_safe(tds[5].text),
                                    "turn": parse_float_safe(tds[4].text),
                                    "lap": parse_float_safe(tds[3].text),
                                    "comment": comments_map.get(w)
                                })
    except Exception as e:
        print(f"[SCRAPER] Error fetching Kiryu exhibition: {e}")
            
    return results

def scrape_and_store_race_info(hd: str, jcd: str, rno: int, db: Session):
    race_id = f"{hd}_{jcd}_{rno}"
    race = db.query(Race).filter(Race.id == race_id).first()
    if not race:
        race = Race(id=race_id, hd=hd, jcd=jcd, rno=rno, status="Processing")
        db.add(race)
        db.commit()

    print(f"[SCRAPER] Starting scraping for {race_id}")
    exh_list = []
    direct_entries = []

    if jcd == '15':
        m_data = fetch_marugame_data(rno, hd)
        if m_data["exhibitions"]:
            exh_list = m_data["exhibitions"]
    elif jcd == '18':
        t_data = fetch_tokuyama_data(rno, hd)
        if t_data["exhibitions"]:
            exh_list = t_data["exhibitions"]
    elif jcd == '21':
        a_data = fetch_ashiya_data(rno, hd)
        if a_data["exhibitions"]:
            exh_list = a_data["exhibitions"]
    elif jcd == '22':
        f_data = fetch_fukuoka_data(rno, hd)
        if f_data["exhibitions"]:
            exh_list = f_data["exhibitions"]
    elif jcd == '14':
        n_data = fetch_naruto_data(rno, hd)
        if n_data["exhibitions"]:
            exh_list = n_data["exhibitions"]
    elif jcd == '01':
        k_data = fetch_kiryu_data(rno, hd)
        if k_data["exhibitions"]:
            exh_list = k_data["exhibitions"]

    # 公式出走表
    url_entries = f"{BASE_URL}/racelist?rno={rno}&jcd={jcd}&hd={hd}"
    html_entries = fetch_html(url_entries)
    if html_entries:
        soup = BeautifulSoup(html_entries, 'lxml')
        btbodys = soup.select('tbody.is-fs12')
        for i, tbody in enumerate(btbodys):
            if i >= 6: break
            w = i + 1
            name = "Unknown"
            name_el = tbody.select_one('div.is-fs18 a')
            if name_el:
                name_text = name_el.get_text(separator=" ", strip=True)
                name = name_text.replace('\u3000', ' ').strip()
                name = re.sub(r'\s+', ' ', name)
            
            # 氏名取得
            name_el = tbody.select_one('div.is-fs18.is-fBold a')
            name = "Unknown"
            if name_el:
                name = re.sub(r'\s+', '', name_el.text)
            
            # 数値データの抽出 (正規表現で対応)
            # 全テキストを連結して、必要な数値を抜き出す
            text_block = tbody.get_text(separator="|")
            st_val = 0.15
            rate_val = 0.0
            
            # 平均STを探す (例: 0.15)
            # F数/L数の後にくる 0.\d+ 形式を探す
            st_match = re.findall(r'0\.\d{2}', text_block)
            if st_match:
                # 通常、1つ目が平均ST
                st_val = parse_float_safe(st_match[0])
            
            # 全国勝率を探す (例: 6.08)
            # 勝率は通常 1.00〜9.99 程度
            # レイアウト上、名前の後の大きな数字ブロックにある
            rate_match = re.findall(r'\d\.\d{2}', text_block)
            if len(rate_match) >= 1:
                # 既にSTとして使われたもの以外で、最初の 0.XX 以外の数値を探す
                for r in rate_match:
                    val = parse_float_safe(r)
                    if val > 1.0: # 勝率はおよそ1.0以上
                        rate_val = val
                        break
            
            direct_entries.append({"waku": w, "name": name, "rate": rate_val, "st": st_val})

    # DB保存
    for item in direct_entries:
        entry_id = f"{race_id}_{item['waku']}"
        entry = db.query(Entry).filter(Entry.id == entry_id).first()
        comment = next((x["comment"] for x in exh_list if x["waku"] == item["waku"]), None)
        if not entry:
            entry = Entry(id=entry_id, race_id=race_id, waku=item['waku'], name=item['name'], rate_global=item['rate'], st_average=item['st'], racer_comment=comment)
            db.add(entry)
        else:
            entry.name, entry.rate_global, entry.st_average = item['name'], item['rate'], item['st']
            if comment: entry.racer_comment = comment

    if not exh_list:
        before_url = f"{BASE_URL}/beforeinfo?rno={rno}&jcd={jcd}&hd={hd}"
        html_before = fetch_html(before_url)
        if html_before:
            soup_before = BeautifulSoup(html_before, 'lxml')
            bt_before = soup_before.select('tbody.is-fs12')
            for i, tbody in enumerate(bt_before):
                if i >= 6: break
                w = i + 1
                td_time = tbody.select_one('td.is-vk_center')
                time_val = parse_float_safe(td_time.text) if td_time else 6.80
                exh_list.append({"waku": w, "time": time_val})

    if exh_list:
        valid_times = [x["time"] for x in exh_list if x.get("time", 0) > 0]
        sorted_times = sorted(list(set(valid_times))) if valid_times else []
        for item in exh_list:
            exh_id = f"{race_id}_{item['waku']}"
            exh = db.query(Exhibition).filter(Exhibition.id == exh_id).first()
            rank = sorted_times.index(item["time"]) + 1 if item.get("time") in sorted_times else None
            if not exh:
                exh = Exhibition(id=exh_id, race_id=race_id, waku=item['waku'], exhibition_time=item.get('time', 6.80), exhibition_rank=rank, lap_time=item.get('lap'), turn_time=item.get('turn'), straight_time=item.get('straight'))
                db.add(exh)
            else:
                exh.exhibition_time, exh.exhibition_rank = item.get('time', 6.80), rank
                if item.get('lap'): exh.lap_time = item.get('lap')
                if item.get('turn'): exh.turn_time = item.get('turn')
                if item.get('straight'): exh.straight_time = item.get('straight')
    
    race.status = "Completed"
    db.commit()
    return True

def get_race_data_from_db(db: Session, hd: str, jcd: str, rno: int):
    race_id = f"{hd}_{jcd}_{rno}"
    entries = db.query(Entry).filter(Entry.race_id == race_id).order_by(Entry.waku).all()
    exhibitions = db.query(Exhibition).filter(Exhibition.race_id == race_id).all()
    if not entries: return []
    racers = []
    for e in entries:
        exh = next((ex for ex in exhibitions if ex.waku == e.waku), None)
        racers.append(Racer(waku=e.waku, name=e.name, rate_global=e.rate_global, st_average=e.st_average, comment=e.racer_comment, exhibition_time=exh.exhibition_time if exh else 6.80, exhibition_rank=exh.exhibition_rank if exh else None, lap_time=exh.lap_time if exh else None, turn_time=exh.turn_time if exh else None, straight_time=exh.straight_time if exh else None))
    return racers

def get_mock_racers():
    return [Racer(waku=i+1, name=n, rate_global=r, st_average=s, exhibition_time=e, exhibition_rank=rk, comment=c) for i, (n, r, s, e, rk, c) in enumerate([("峰 竜太", 9.55, 0.12, 6.65, 1, "絶好調です！"), ("毒島 誠", 8.70, 0.10, 6.70, 2, "伸びは普通かな。"), ("馬場 貴也", 8.45, 0.14, 6.72, 3, "まわり足は悪くない。"), ("桐生 順平", 8.10, 0.15, 6.75, 4, "コメントなし"), ("石野 貴之", 7.90, 0.13, 6.78, 5, "調整中です。"), ("菊地 孝平", 7.80, 0.09, 6.80, 6, "スタート勝負！")])]

def get_mock_predictions():
    return [{"waku": w, "score": s, "rank_prediction": r} for w, s, r in [(1, 95, 1), (2, 88, 2), (3, 82, 3), (6, 75, 4)]]
