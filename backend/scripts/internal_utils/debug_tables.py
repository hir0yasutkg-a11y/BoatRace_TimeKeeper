import requests
from bs4 import BeautifulSoup

hd = '20260405'
jcd = '01'
rno = 1
url = f"https://www.boatrace.jp/owpc/pc/race/racelist?rno={rno}&jcd={jcd}&hd={hd}"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}
resp = requests.get(url, headers=headers, timeout=20)
soup = BeautifulSoup(resp.content, 'lxml')

print(f"Total tables found: {len(soup.find_all('table'))}")
for i, table in enumerate(soup.find_all('table')):
    print(f"Table {i}: class={table.get('class')}")
    # 初めの tr の中身を 1 mm 的に覗き見る
    tr = table.find('tr')
    if tr:
        print(f"  First TR content: {tr.get_text('|', strip=True)[:100]}...")
