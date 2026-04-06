import requests
from bs4 import BeautifulSoup

def debug_raceindex():
    jcd = "01"
    hd = "20260405"
    url = f"https://www.boatrace.jp/owpc/pc/race/raceindex?jcd={jcd}&hd={hd}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"}
    
    print(f"--- Debug RaceIndex RAW Fetch for {jcd} ---")
    res = requests.get(url, headers=headers, timeout=20)
    print(f"Status: {res.status_code}")
    html = res.text
    
    if "is-w1100" in html:
        print("Found 'is-w1100' in HTML!")
        idx = html.find("is-w1100")
        print("--- Context around 'is-w1100' ---")
        print(html[idx-100:idx+1000])
    else:
        print("'is-w1100' NOT FOUND in RAW HTML.")
        print("--- Start of HTML ---")
        print(html[:2000])

if __name__ == "__main__":
    debug_raceindex()
