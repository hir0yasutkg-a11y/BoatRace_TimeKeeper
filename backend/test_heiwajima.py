import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper import fetch_heiwajima_data, fetch_html
from bs4 import BeautifulSoup

def test_heiwajima():
    print("Testing Heiwajima Scraper...")
    rno = 1
    hd = "20260403" # Tomorrow
    
    # Test Data
    print(f"Fetching data for Race {rno} on {hd}...")
    data = fetch_heiwajima_data(rno, hd)
    
    if data["exhibitions"]:
        print(f"Success! Found {len(data['exhibitions'])} racers.")
        for ex in data["exhibitions"]:
            print(f"Waku {ex['waku']}: Straight={ex['straight']}, Turn={ex['turn']}, Lap={ex['lap']}, Comment={ex['comment']}")
    else:
        print("No data found. (Common if the site is not updated yet for tomorrow)")
        # Check connectivity
        url = f"https://www.heiwajima.gr.jp/asp/heiwajima/sp/kyogi/06shusso.asp?r={rno}"
        html = fetch_html(url)
        if html:
            print("URL is reachable.")
            soup = BeautifulSoup(html, 'lxml')
            if "出走表" in soup.text:
                print("Race list page detected.")
            else:
                print("Page content detected but doesn't look like a race list.")
        else:
            print("URL connection failed.")

if __name__ == "__main__":
    test_heiwajima()
