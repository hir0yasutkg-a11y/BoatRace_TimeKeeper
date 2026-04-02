import requests
from bs4 import BeautifulSoup
import time
from sqlalchemy.orm import Session
from database import Race, Entry, Exhibition
from models import Racer, ExhibitionInfo
import lxml
import re

BASE_URL = "https://www.boatrace.jp/owpc/pc/race"

# 全24場のシステム分類とベースURLの設定
VENUES_CONFIG = {
    # Group 1: Cyber系 (ASP)
    "01": {"type": "cyber", "url": "https://www.kiryu-kyotei.com/sp/index.php"},
    "03": {"type": "cyber", "url": "https://www.edogawa-kyotei.co.jp/asp/edogawa/sp/kyogi"},
    "04": {"type": "cyber", "url": "https://www.heiwajima.gr.jp/asp/heiwajima/sp/kyogi"},
    "05": {"type": "cyber", "url": "https://www.tamagawa.co.jp/asp/tamagawa/sp/kyogi"},
    "06": {"type": "cyber", "url": "https://www.hamanako-kyotei.com/asp/hamanako/sp/kyogi"},
    "14": {"type": "cyber", "url": "https://www.n14.jp/sp"}, # 鳴門
    "15": {"type": "cyber", "url": "https://www.marugameboat.jp/asp/kyogi/15/pc"}, # 丸亀はPC版が取得しやすい
    "18": {"type": "cyber", "url": "https://www.boatrace-tokuyama.jp/sp"},
    "21": {"type": "cyber", "url": "https://www.boatrace-ashiya.com/sp"},

    # Group 2: K-Data/Synergy系 (PHP)
    "02": {"type": "kdata", "url": "https://www.boatrace-toda.jp/sp"},
    "07": {"type": "kdata", "url": "https://www.boatrace-gamagori.jp/sp"},
    "08": {"type": "kdata", "url": "https://www.boatrace-tokoname.jp/sp"},
    "09": {"type": "kdata", "url": "https://www.boatrace-tsu.jp/sp"},
    "10": {"type": "kdata", "url": "https://www.boatrace-mikuni.jp/sp"},
    "11": {"type": "kdata", "url": "https://www.boatrace-biwako.jp/sp"},
    "12": {"type": "kdata", "url": "https://www.boatrace-suminoe.jp/sp"},
    "16": {"type": "kdata", "url": "https://www.kojimaboat.jp/sp"},
    "17": {"type": "kdata", "url": "https://www.boatrace-miyajima.com/sp"},
    "19": {"type": "kdata", "url": "https://www.shimonoseki.gr.jp/sp"},
    "20": {"type": "kdata", "url": "https://www.wakamatsu-kyotei.com/sp"},
    "23": {"type": "kdata", "url": "https://www.boatrace-karatsu.jp/sp"},
    "24": {"type": "kdata", "url": "https://www.omuraboat.jp/sp"},

    # Group 3: Custom/Modules系
    "13": {"type": "module", "url": "https://www.boatrace-amagasaki.jp/modules/race"}
}

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
        if not text: return default
        # 数字とドット以外を除去
        m = re.search(r'(\d+\.\d+)', text)
        if m: return float(m.group(1))
        # fallback
        num_text = "".join(filter(lambda x: x.isdigit() or x == '.', text.strip()))
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

def fetch_cyber_data(jcd: str, rno: int, hd: str):
    """
    Cyber系システム(ASP)の会場からデータを取得
    """
    config = VENUES_CONFIG.get(jcd)
    if not config: return {"exhibitions": []}
    
    base_url = config["url"]
    results = {"exhibitions": []}
    headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"}
    
    # 選手コメント
    if "index.php" in base_url or jcd in ["01", "14", "18", "21"]:
        param = "yosou-syussou"
        if jcd in ["18", "21"]: param = "raceinfo-racer_comment"
        comment_url = f"{base_url}/index.php?page={param}&race={rno}"
        if jcd in ["18", "21"]: comment_url = f"{base_url}/index.php?page={param}&rno={rno}"
    elif jcd == "15": # 丸亀
        comment_url = f"https://www.marugameboat.jp/asp/kyogi/15/pc/yoso05{rno:02}.htm"
    else:
        comment_url = f"{base_url}/06comment.asp?r={rno}"
        
    comments_map = {}
    try:
        res = requests.get(comment_url, headers=headers, timeout=5)
        if res.status_code == 200:
            res.encoding = "shift_jis" if jcd == "15" else res.apparent_encoding
            soup = BeautifulSoup(res.text, 'lxml')
            table = soup.select_one('table.table1') or soup.find('table')
            if table:
                for row in table.find_all('tr'):
                    tds = row.find_all('td')
                    if len(tds) >= 3:
                        w_text = tds[0].get_text(strip=True)
                        if w_text.isdigit():
                            idx = 2 if len(tds) >= 3 else 1
                            comments_map[int(w_text)] = tds[idx].get_text(strip=True)
    except: pass

    # 展示データ
    if "index.php" in base_url or jcd in ["01", "14", "18", "21"]:
        exh_param = "yosou-chokuzen"
        if jcd == "18": exh_param = "raceinfo-original_exhibition"
        elif jcd == "21": exh_param = "raceinfo-exhibition"
        exh_url = f"{base_url}/index.php?page={exh_param}&race={rno}"
        if jcd in ["18", "21"]: exh_url = f"{base_url}/index.php?page={exh_param}&rno={rno}"
    elif jcd == "15":
        exh_url = f"https://www.marugameboat.jp/asp/kyogi/15/pc/yoso05{rno:02}.htm"
    else:
        exh_url = f"{base_url}/06original.asp?r={rno}"

    try:
        res = requests.get(exh_url, headers=headers, timeout=5)
        if res.status_code == 200:
            res.encoding = "shift_jis" if jcd == "15" else res.apparent_encoding
            soup = BeautifulSoup(res.text, 'lxml')
            table = soup.select_one('table.table1') or soup.find('table')
            if table:
                for row in table.find_all('tr'):
                    tds = row.find_all('td')
                    if len(tds) >= 4:
                        w_text = tds[0].get_text(strip=True)
                        if w_text.isdigit():
                            w = int(w_text)
                            results["exhibitions"].append({
                                "waku": w,
                                "time": parse_float_safe(tds[2].text) if len(tds) >= 3 else 0.0,
                                "lap": parse_float_safe(tds[-3].text) if len(tds) >= 6 else 0.0,
                                "turn": parse_float_safe(tds[-2].text) if len(tds) >= 6 else 0.0,
                                "straight": parse_float_safe(tds[-1].text) if len(tds) >= 6 else 0.0,
                                "comment": comments_map.get(w)
                            })
    except: pass
    return results

def fetch_kdata_data(jcd: str, rno: int, hd: str):
    config = VENUES_CONFIG.get(jcd)
    base_url = config["url"]
    results = {"exhibitions": []}
    headers = {"User-Agent": "Mozilla/5.0"}
    
    comments_map = {}
    try:
        url = f"{base_url}/index.php?page=kyogi-comment&rno={rno}"
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'lxml')
            rows = soup.select('table.table1 tr')
            for row in rows:
                tds = row.find_all('td')
                if len(tds) >= 2:
                    w_text = tds[0].get_text(strip=True)
                    if w_text.isdigit():
                        comments_map[int(w_text)] = tds[-1].get_text(strip=True)
    except: pass

    try:
        url = f"{base_url}/index.php?page=kyogi-original&rno={rno}"
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'lxml')
            rows = soup.select('table.table1 tr')
            for row in rows:
                tds = row.find_all('td')
                if len(tds) >= 5:
                    w_index = 0
                    if not tds[w_index].text.strip().isdigit(): continue
                    w = int(tds[w_index].text.strip())
                    results["exhibitions"].append({
                        "waku": w,
                        "time": parse_float_safe(tds[1].text),
                        "lap": parse_float_safe(tds[2].text),
                        "turn": parse_float_safe(tds[3].text),
                        "straight": parse_float_safe(tds[4].text),
                        "comment": comments_map.get(w)
                    })
    except: pass
    return results

def fetch_module_data(jcd: str, rno: int, hd: str):
    return fetch_kdata_data(jcd, rno, hd)

def fetch_fukuoka_data(rno: int, hd: str):
    # 福岡(22)は独自
    base_url = "https://www.boatrace-fukuoka.com/sp/index.php"
    results = {"exhibitions": []}
    headers = {"User-Agent": "Mozilla/5.0"}
    
    comments_map = {}
    try:
        res = requests.get(f"{base_url}?page=yosou-syussou&race={rno}", headers=headers, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'lxml')
            box = soup.select_one('div.box.box-yosou-syussou-4')
            if box:
                for row in box.select('table tr')[1:]:
                    tds = row.find_all('td')
                    if len(tds) >= 4:
                        w = int(tds[0].get_text(strip=True))
                        comments_map[w] = tds[3].get_text(strip=True)
    except: pass

    try:
        res = requests.get(f"{base_url}?page=yosou-cyokuzen&race={rno}", headers=headers, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'lxml')
            box = soup.select_one('div.box.box-chokuzen-1')
            if box:
                for row in box.select('table tr'):
                    tds = row.find_all('td')
                    if len(tds) >= 4:
                        w_text = tds[0].get_text(strip=True)
                        if w_text.isdigit():
                            w = int(w_text)
                            results["exhibitions"].append({
                                "waku": w,
                                "time": 0.0,
                                "lap": parse_float_safe(tds[1].text),
                                "turn": parse_float_safe(tds[2].text),
                                "straight": parse_float_safe(tds[3].text),
                                "comment": comments_map.get(w)
                            })
    except: pass
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

    # 会場別エンジン
    if jcd == "22":
        f_data = fetch_fukuoka_data(rno, hd)
        exh_list = f_data["exhibitions"]
    else:
        config = VENUES_CONFIG.get(jcd)
        if config:
            if config["type"] == "cyber":
                exh_list = fetch_cyber_data(jcd, rno, hd)["exhibitions"]
            elif config["type"] == "kdata":
                exh_list = fetch_kdata_data(jcd, rno, hd)["exhibitions"]
            elif config["type"] == "module":
                exh_list = fetch_module_data(jcd, rno, hd)["exhibitions"]

    # 公式出走表
    url_entries = f"{BASE_URL}/racelist?rno={rno}&jcd={jcd}&hd={hd}"
    html_entries = fetch_html(url_entries)
    if html_entries:
        soup = BeautifulSoup(html_entries, 'lxml')
        btbodys = soup.select('tbody.is-fs12')
        for i, tbody in enumerate(btbodys):
            if i >= 6: break
            w = i + 1
            name_el = tbody.select_one('div.is-fs18.is-fBold a')
            name = re.sub(r'\s+', '', name_el.text) if name_el else "Unknown"
            
            text_block = tbody.get_text(separator="|")
            st_val = 0.15
            rate_val = 0.0
            st_match = re.findall(r'0\.\d{2}', text_block)
            if st_match: st_val = parse_float_safe(st_match[0])
            rate_match = re.findall(r'\d\.\d{2}', text_block)
            for r in rate_match:
                val = parse_float_safe(r)
                if val > 1.0:
                    rate_val = val
                    break
            direct_entries.append({"waku": w, "name": name, "rate": rate_val, "st": st_val})

    # DB保存 (Entry)
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

    # 公式展示タイム(フォールバック用)
    if not any(x.get("time") for x in exh_list):
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
                found = next((x for x in exh_list if x["waku"] == w), None)
                if found: found["time"] = time_val
                else: exh_list.append({"waku": w, "time": time_val})

    # DB保存 (Exhibition)
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
