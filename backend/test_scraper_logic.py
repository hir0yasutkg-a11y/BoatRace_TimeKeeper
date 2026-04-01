import sys
import os
# Add current dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper import fetch_marugame_data, fetch_html, parse_float_safe, scrape_and_store_race_info
from bs4 import BeautifulSoup
import re

def test_marugame():
    print("--- Testing Marugame 10R ---")
    results = fetch_marugame_data(10, "20260331")
    if not results["exhibitions"]:
        print("FAILED: No Marugame data found.")
    else:
        for exh in results["exhibitions"]:
            print(f"Waku {exh['waku']}: Display={exh['time']} | Lap={exh['lap']} | Turn={exh['turn']} | Str={exh['straight']}")
            print(f"  Comment: {exh['comment']}")

def test_boatrace_jp():
    print("\n--- Testing boatrace.jp 10R (Racelist) ---")
    url = "https://www.boatrace.jp/owpc/pc/race/racelist?rno=10&jcd=15&hd=20260331"
    html = fetch_html(url)
    if not html:
        print("FAILED: Could not fetch boatrace.jp")
        return

    soup = BeautifulSoup(html, 'lxml')
    btbodys = soup.select('tbody.is-fs12')
    for i, tbody in enumerate(btbodys):
        if i >= 6: break
        w = i + 1
        name = "Unknown"
        name_el = tbody.select_one('div.is-fs18 a')
        if name_el:
            name_text = name_el.get_text(separator=" ", strip=True)
            name = name_text.replace('\u3000', ' ').strip()
            name = re.sub(r'\s+', ' ', name)
        
        tds = tbody.select('td')
        rate_val, st_val = 0.0, 0.15
        if len(tds) >= 5:
            # Average ST: 4th td (index 3), 3rd p
            st_p = tds[3].select('p')
            if len(st_p) >= 3: st_val = parse_float_safe(st_p[2].text)
            
            # National Rate: 5th td (index 4), 1st p
            rate_p = tds[4].select('p')
            if len(rate_p) >= 1: rate_val = parse_float_safe(rate_p[0].text)
            
        print(f"Waku {w}: {name} | Rate: {rate_val} | ST: {st_val}")

if __name__ == "__main__":
    test_marugame()
    test_boatrace_jp()
