import requests
from bs4 import BeautifulSoup
import re

hd = '20260405'
jcd = '01'
rno = 1
url = f"https://www.boatrace.jp/owpc/pc/race/racelist?rno={rno}&jcd={jcd}&hd={hd}"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
}
print(f"Fetching: {url}")
resp = requests.get(url, headers=headers, timeout=20)
print(f"Status: {resp.status_code}, Length: {len(resp.content)}")

soup = BeautifulSoup(resp.content, 'lxml')

btbodys = soup.select('table.is-st-table1 tbody')
if not btbodys:
    btbodys = soup.select('table.is-st_racelist tbody')
    if btbodys: print("Used fallback selector.")
    else: print("NO TBODY FOUND AT ALL.")

for i, tbody in enumerate(btbodys[:6]):
    tr0 = tbody.select('tr')[0]
    cols = tr0.find_all('td', recursive=False)
    print(f"\n--- Waku {i+1} ---")
    for j, col in enumerate(cols):
        print(f"Col[{j}]: {col.get_text('|', strip=True)}")
    
    try:
        if len(cols) >= 8:
            g_parts = cols[4].get_text('|', strip=True).split('|')
            print(f"G Win Rate: {g_parts[0]} (raw: {g_parts})")
            l_parts = cols[5].get_text('|', strip=True).split('|')
            print(f"L Win Rate: {l_parts[0]} (raw: {l_parts})")
            m_parts = cols[6].get_text('|', strip=True).split('|')
            print(f"Motor No: {m_parts[0]}, Rate2: {m_parts[1] if len(m_parts)>1 else 'None'}")
    except Exception as e:
        print(f"Error at waku {i+1}: {e}")
