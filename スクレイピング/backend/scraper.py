import requests
from bs4 import BeautifulSoup
import time
from sqlalchemy.orm import Session
from database import Race, Entry, Exhibition
from models import Racer, ExhibitionInfo

BASE_URL = "https://www.boatrace.jp/owpc/pc/race"

def fetch_html(url: str):
    time.sleep(1) # スクレイピングマナー: 1秒待機
    headers = {"User-Agent": "BoatRaceAnalyzer/1.0"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        # 404などエラー時は公式からの提供終了/対象外と判断
        res.raise_for_status() 
        # BOATRACE公式は基本UTF-8だがメタタグに従う
        res.encoding = res.apparent_encoding 
        return res.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_float_safe(text: str, default: float = 0.0) -> float:
    try:
        return float(text.strip())
    except (ValueError, TypeError):
        return default

def scrape_and_store_race_info(db: Session, hd: str, jcd: str, rno: int):
    race_id = f"{hd}_{jcd}_{rno}"
    existing_race = db.query(Race).filter(Race.id == race_id).first()
    
    racelist_url = f"{BASE_URL}/racelist?rno={rno}&jcd={jcd}&hd={hd}"
    beforeinfo_url = f"{BASE_URL}/beforeinfo?rno={rno}&jcd={jcd}&hd={hd}"

    # キャッシュチェック：すでにRaceや情報のDBがあれば公式へは行かない
    if existing_race and existing_race.status == "Completed":
        return True

    html_list = fetch_html(racelist_url)
    html_before = fetch_html(beforeinfo_url)

    if not existing_race:
        race = Race(id=race_id, hd=hd, jcd=jcd, rno=rno, status="Pending")
        db.add(race)
        db.commit()

    # ---------------------------
    # ① 出走表（Entry）の解析
    # ---------------------------
    if html_list:
        soup_list = BeautifulSoup(html_list, 'lxml')
        tbodys = soup_list.select('tbody.is-fs12')
        
        # BOAT RACEサイトは6つのtbody（1〜6枠）を持つ
        for waku_index, tbody in enumerate(tbodys):
            w = waku_index + 1
            entry_id = f"{race_id}_{w}"
            
            # DBに既にあればスキップ
            if db.query(Entry).filter(Entry.id == entry_id).first():
                continue

            try:
                trs = tbody.select('tr')
                if not trs: continue
                # メインの行
                main_tr = trs[0]
                tds = main_tr.select('td')
                
                # TD2内に名前クラスがある
                name_el = tbody.select_one('.is-fs18')
                name = name_el.text.replace('\u3000', ' ').strip() if name_el else f"選手{w}"
                
                # TD3内に平均ST
                st_text = tds[3].text.strip().split('\n')[-1].strip()
                st_average = parse_float_safe(st_text, 0.15)
                
                # TD4内に全国勝率
                rate_text = tds[4].text.strip().split('\n')[0].strip()
                rate_global = parse_float_safe(rate_text, 5.0)

                entry = Entry(
                    id=entry_id,
                    race_id=race_id,
                    waku=w,
                    name=name,
                    rate_global=rate_global,
                    st_average=st_average
                )
                db.add(entry)
            except Exception as e:
                print(f"Error parsing Entry for waku {w}: {e}")

    # ---------------------------
    # ② 直前情報（Exhibition）の解析
    # ---------------------------
    if html_before:
        soup_before = BeautifulSoup(html_before, 'lxml')
        tbodys = soup_before.select('tbody.is-fs12')
        
        for waku_index, tbody in enumerate(tbodys):
            if waku_index >= 6: break # 念のため
            w = waku_index + 1
            exh_id = f"{race_id}_{w}"
            
            if db.query(Exhibition).filter(Exhibition.id == exh_id).first():
                continue

            try:
                trs = tbody.select('tr')
                if not trs: continue
                
                # beforeinfoの通常構造: 展示タイムはTDの4番目か5番目
                tds = trs[0].select('td')
                
                # 直前情報テーブルは、体重、調整、展示タイム等が並ぶ。
                # 通常：Waku(0), ボート(1), モーター(2), ... , 展示タイム（4 or 5）
                # 'is-fs14' クラス等から探すなど工夫が必要だが、ここではインデックス保護して抽出
                exh_time_str = "6.80"
                for td in tds:
                    if "." in td.text and len(td.text.strip()) == 4:
                        # 展示タイムらしきものを探す（簡易的）
                        exh_time_str = td.text.strip()
                
                exh_time = parse_float_safe(exh_time_str, 6.80)
                
                exh = Exhibition(
                    id=exh_id,
                    race_id=race_id,
                    waku=w,
                    exhibition_time=exh_time,
                    lap_time=None,
                    turn_time=None,
                    straight_time=None
                )
                db.add(exh)
            except Exception as e:
                print(f"Error parsing Exhibition for waku {w}: {e}")

    # フラグ更新
    if existing_race:
        existing_race.status = "Completed"
    db.commit()
    return True

def get_race_data_from_db(db: Session, hd: str, jcd: str, rno: int):
    race_id = f"{hd}_{jcd}_{rno}"
    entries = db.query(Entry).filter(Entry.race_id == race_id).all()
    exhibitions = db.query(Exhibition).filter(Exhibition.race_id == race_id).all()
    
    if not entries:
        return []

    racers = []
    for e in entries:
        exh = next((ex for ex in exhibitions if ex.waku == e.waku), None)
        racers.append(Racer(
            waku=e.waku,
            name=e.name,
            rate_global=e.rate_global,
            st_average=e.st_average,
            exhibition_time=exh.exhibition_time if exh and exh.exhibition_time else 6.80,
            lap_time=exh.lap_time if exh else None,
            turn_time=exh.turn_time if exh else None,
            straight_time=exh.straight_time if exh else None
        ))
    return racers
