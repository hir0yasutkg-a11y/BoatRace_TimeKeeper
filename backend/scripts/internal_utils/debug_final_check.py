from database import SessionLocal, Entry
from scraper import fetch_html
from bs4 import BeautifulSoup
import re

db = SessionLocal()
url = 'https://www.boatrace.jp/owpc/pc/race/racelist?rno=1&jcd=01&hd=20260405'
html = fetch_html(url)
soup = BeautifulSoup(html, 'lxml')

target_table = None
for tbl in soup.find_all('table'):
    if 'ボートレーサー' in tbl.get_text():
        target_table = tbl
        break

if not target_table:
    print("NO TABLE FOUND.")
else:
    racer_tbodys = [tb for tb in target_table.find_all('tbody') if '全国' not in tb.get_text() and tb.select('tr')][:6]
    for i, tb in enumerate(racer_tbodys):
        tr0 = tb.select('tr')[0]
        tds = tr0.find_all('td', recursive=False)
        
        # 名前抽出 (Index 2)
        name_cell = tds[2].get_text('|', strip=True)
        # 勝率抽出 (Index 4, 5)
        rate_g_cell = tds[4].get_text('|', strip=True)
        rate_l_cell = tds[5].get_text('|', strip=True)
        
        print(f"--- Waku {i+1} RAW ---")
        print(f"Name Cell: {name_cell[:50]}...")
        print(f"RateG Cell: {rate_g_cell}")
        print(f"RateL Cell: {rate_l_cell}")
        
        # DB check
        e = db.query(Entry).filter(Entry.race_id == '20260405_01_1', Entry.waku == i+1).first()
        if e:
            print(f"DB Entry: Name={e.name}, RateG={e.rate_global}, RateL={e.rate_local}")
        else:
            print(f"DB Entry: NOT FOUND for waku {i+1}")
