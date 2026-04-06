import requests
from bs4 import BeautifulSoup

url = "https://www.boatrace.jp/owpc/pc/race/racelist?rno=10&jcd=15&hd=20260331"
res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
# Try automatic detection
print(f"Apparent encoding: {res.apparent_encoding}")
res.encoding = res.apparent_encoding

soup = BeautifulSoup(res.text, 'lxml')
# Look for the first racer row
racer_tbody = soup.select_one('div.contentsFrame tbody')
if racer_tbody:
    print("--- First TBODY HTML ---")
    print(racer_tbody.prettify()[:1000])
else:
    print("No tbody found in contentsFrame")
