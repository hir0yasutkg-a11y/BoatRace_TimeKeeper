import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import traceback

with open("scrape_output.txt", "w", encoding="utf-8") as out:
    def log(msg):
        out.write(msg + "\n")
        out.flush()
        
    try:
        url = "https://www.boatrace.jp/owpc/pc/race/index"
        log("Fetching races for today...")
        res = requests.get(url)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')

        links = soup.find_all('a', href=re.compile(r'/owpc/pc/race/racelist'))
        if not links:
            log("No valid racelist links found for today.")
        else:
            href = links[0]['href']
            log(f"Sample racelist link: {href}")
            
            m = re.search(r'rno=(\d+)&jcd=(\d+)&hd=(\d+)', href)
            if m:
                rno, jcd, hd = m.groups()
                log(f"Target: hd={hd}, jcd={jcd}, rno={rno}")
                
                # Fetch beforeinfo
                before_url = f"https://www.boatrace.jp/owpc/pc/race/beforeinfo?rno={rno}&jcd={jcd}&hd={hd}"
                bres = requests.get(before_url)
                bres.encoding = 'utf-8'
                bsoup = BeautifulSoup(bres.text, 'html.parser')
                log(f"\nFetched beforeinfo URL: {before_url}")
                
                tbodys = bsoup.select('tbody.is-fs12')
                if tbodys:
                    trs = tbodys[0].select('tr')
                    for index, tr in enumerate(trs):
                        tds = tr.select('td')
                        texts = [td.text.strip().replace('\n', ' ') for td in tds]
                        log(f"TR {index}: {texts}")
                else:
                    log("No tbody.is-fs12 found in beforeinfo.")
                    
                # Check for "1周", "直線", "comments"
                # Often "オリジナル展示データ" is in a specific table.
                tables = bsoup.find_all('table')
                for i, table in enumerate(tables):
                    log(f"\n--- TABLE {i} ---")
                    headers = [th.text.strip().replace('\n', '') for th in table.find_all('th')[:15]]
                    log("Headers: " + str(headers))
                    trs = table.find_all('tr')[:3]
                    for tr in trs:
                         tds = [t.text.strip().replace('\n', '') for t in tr.find_all(['th','td'])]
                         log("Row: " + str(tds))
                         
                # Also fetch racelist to hunt for comments
                rlist_url = f"https://www.boatrace.jp/owpc/pc/race/racelist?rno={rno}&jcd={jcd}&hd={hd}"
                rres = requests.get(rlist_url)
                rres.encoding = 'utf-8'
                rsoup = BeautifulSoup(rres.text, 'html.parser')
                
                log("\n--- Racelist Tables ---")
                tables = rsoup.find_all('table')
                for i, table in enumerate(tables):
                    headers = [th.text.strip().replace('\n', '') for th in table.find_all('th')[:15]]
                    if "短評" in headers or "コメント" in str(headers):
                        log(f"Found table with Comment/Short review: Headers: {headers}")

    except Exception as e:
        log("ERROR: " + str(traceback.format_exc()))
