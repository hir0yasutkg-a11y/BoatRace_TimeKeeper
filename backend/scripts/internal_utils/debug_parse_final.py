import requests
from bs4 import BeautifulSoup
import re

hd = '20260405'
jcd = '01'
rno = 1
url = f"https://www.boatrace.jp/owpc/pc/race/racelist?rno={rno}&jcd={jcd}&hd={hd}"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}
resp = requests.get(url, headers=headers, timeout=20)
soup = BeautifulSoup(resp.content, 'lxml')

target_table = None
for tbl in soup.find_all('table'):
    if "ボートレーサー" in tbl.get_text():
        target_table = tbl
        break

if not target_table:
    print("NO TARGET TABLE FOUND.")
else:
    # 各選手は tbody の中か、tr の集まり
    btbodys = target_table.find_all('tbody')
    # ヘッダー tbody とレーサー tbody が分かれている場合がある
    # 実際にはデータがある tbody は 6 つ
    racer_tbodys = [tb for tb in btbodys if tb.select('tr') and len(tb.select('tr')) >= 1]
    
    # 最初の tbody はヘッダーの場合があるのでスキップが必要か確認
    if racer_tbodys and "全国" in racer_tbodys[0].get_text():
        # ヘッダーが含まれているので 1 つ目から 6 つがレーサー
        racer_tbodys = racer_tbodys[1:7]
    elif len(racer_tbodys) > 6:
        racer_tbodys = racer_tbodys[:6]

    for i, tbody in enumerate(racer_tbodys):
        tr0 = tbody.select('tr')[0]
        cols = tr0.find_all('td', recursive=False)
        print(f"\n--- Racer {i+1} ---")
        for j, col in enumerate(cols):
            print(f"Col[{j}]: {col.get_text('|', strip=True)}")
        
        try:
             # 全国 (2), 当地 (3), モーター (4), ボート (5)
            rate_g = cols[2].get_text('|', strip=True).split('|')[0]
            rate_l = cols[3].get_text('|', strip=True).split('|')[0]
            m_no = cols[4].get_text('|', strip=True).split('|')[0]
            b_no = cols[5].get_text('|', strip=True).split('|')[0]
            print(f"Result: GWin:{rate_g}, LWin:{rate_l}, MNo:{m_no}, BNo:{b_no}")
        except Exception as e:
            print(f"Error at racer {i+1}: {e}")
