import requests
from bs4 import BeautifulSoup

def debug_raceindex_sp():
    jcd = "01"
    hd = "20260405"
    url = f"https://www.boatrace.jp/owsp/sp/race/raceindex?jcd={jcd}&hd={hd}"
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1"}
    
    print(f"--- Debug RaceIndex SP RAW Fetch for {jcd} ---")
    res = requests.get(url, headers=headers, timeout=20)
    print(f"Status: {res.status_code}")
    html = res.text
    
    if "raceType" in html:
        print("Found 'raceType' in HTML!")
        idx = html.find("raceType")
        print("--- Context around 'raceType' ---")
        print(html[idx-100:idx+800])
    else:
        print("'raceType' NOT FOUND in RAW HTML.")
        print("--- Start of HTML ---")
        print(html[:2000])

if __name__ == "__main__":
    debug_raceindex_sp()
