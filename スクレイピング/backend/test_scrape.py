import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

url = "https://www.boatrace.jp/owpc/pc/race/index"
print("Fetching races for today...")
res = requests.get(url)
res.encoding = 'utf-8'
soup = BeautifulSoup(res.text, 'lxml')

links = soup.find_all('a', href=re.compile(r'/owpc/pc/race/racelist'))
if not links:
    print("No valid racelist links found for today.")
else:
    # Get the first valid race link
    href = links[0]['href']
    print(f"Sample racelist link: {href}")
    
    # Extract hd, jcd, rno
    m = re.search(r'rno=(\d+)&jcd=(\d+)&hd=(\d+)', href)
    if m:
        rno, jcd, hd = m.groups()
        print(f"Target: hd={hd}, jcd={jcd}, rno={rno}")
        
        # Now fetch beforeinfo
        before_url = f"https://www.boatrace.jp/owpc/pc/race/beforeinfo?rno={rno}&jcd={jcd}&hd={hd}"
        bres = requests.get(before_url)
        bres.encoding = 'utf-8'
        bsoup = BeautifulSoup(bres.text, 'lxml')
        print(f"\nFetched beforeinfo URL: {before_url}")
        
        tbodys = bsoup.select('tbody.is-fs12')
        if tbodys:
            trs = tbodys[0].select('tr')
            for index, tr in enumerate(trs):
                tds = tr.select('td')
                texts = [td.text.strip().replace('\n', ' ') for td in tds]
                print(f"TR {index}: {texts}")
        else:
            print("No tbody.is-fs12 found in beforeinfo.")
            
        print("\nSearching for any elements containing '展示', '1周', 'まわり足', '直線', 'コメント'...")
        for text in ['1周', 'まわり足', '直線', 'コメント', '短評']:
            els = bsoup.find_all(string=re.compile(text))
            for el in els:
                print(f"Found '{text}': {el.parent.name} -> {el.strip().replace(chr(10), '')}")
                
        # To find comments, it might be in racelist? Let's check racelist.
        rlist_url = f"https://www.boatrace.jp/owpc/pc/race/racelist?rno={rno}&jcd={jcd}&hd={hd}"
        rres = requests.get(rlist_url)
        rres.encoding = 'utf-8'
        rsoup = BeautifulSoup(rres.text, 'lxml')
        print(f"\nFetched racelist URL: {rlist_url}")
        for text in ['コメント', '短評']:
            els = rsoup.find_all(string=re.compile(text))
            for el in els:
                print(f"Found '{text}': {el.parent.name} -> {el.strip().replace(chr(10), '')}")
