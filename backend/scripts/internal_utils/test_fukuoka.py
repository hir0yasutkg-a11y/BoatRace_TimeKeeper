import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.scraper import fetch_fukuoka_data
from backend.database import SessionLocal
from backend.scraper import scrape_and_store_race_info

def test_fukuoka():
    # Fukuoka (22) Race 1 for today (20260401)
    hd = "20260401"
    jcd = "22"
    rno = 1
    
    print(f"--- Testing Fukuoka (JCD {jcd}) {rno}R Scraping for {hd} ---")
    
    # 1. 独立関数のテスト
    results = fetch_fukuoka_data(rno, hd)
    print(f"Scraped {len(results['exhibitions'])} racers from SP site:")
    for exh in results["exhibitions"]:
        print(f"Waku {exh['waku']}: {exh['comment'][:20] if exh['comment'] else 'None'}... | Lap: {exh['lap']}, Turn: {exh['turn']}, Straight: {exh['straight']}")

    # 2. 統合プロセスのテスト
    db = SessionLocal()
    try:
        scrape_and_store_race_info(hd, jcd, rno, db)
        print("\nStored in DB successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    test_fukuoka()
