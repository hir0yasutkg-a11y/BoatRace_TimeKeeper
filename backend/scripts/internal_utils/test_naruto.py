import sys
import os
import requests
from bs4 import BeautifulSoup

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.scraper import fetch_naruto_data

def test_naruto():
    print("=== Testing Naruto Scraper ===")
    rno = 1
    hd = "20260401"
    
    print(f"Fetching data for Race {rno} on {hd}...")
    try:
        res = fetch_naruto_data(rno, hd)
        print(f"Result: {res}")
        
        # 非開催時の挙動確認
        if not res["exhibitions"]:
            print("Status: Success (No data found, expected for non-racing day)")
        else:
            print("Status: Success (Data found!)")
            for exh in res["exhibitions"]:
                print(f"Waku {exh['waku']}: Lap={exh['lap']}, Turn={exh['turn']}, Straight={exh['straight']}, Comment={exh['comment']}")
                
    except Exception as e:
        print(f"Status: Failed with error: {e}")

if __name__ == "__main__":
    test_naruto()
