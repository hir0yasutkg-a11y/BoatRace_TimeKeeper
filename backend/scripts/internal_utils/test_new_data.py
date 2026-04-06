import sys
import os
sys.path.append(os.getcwd())
from database import SessionLocal, Race, Entry
from scraper import scrape_and_store_race_info
import json

def test_scrape_logic():
    db = SessionLocal()
    # 2026/04/04 平和島 (04) 第1レース (1)
    hd, jcd, rno = "20260404", "04", 1
    
    print(f"--- テスト開始: {hd} 平和島 {rno}R ---")
    success = scrape_and_store_race_info(hd, jcd, rno, db)
    
    if success:
        # DBから取得して確認
        entries = db.query(Entry).filter(Entry.race_id == f"{hd}_{jcd}_{rno}").all()
        results = []
        for e in entries:
            results.append({
                "waku": e.waku,
                "name": e.name,
                "racer_id": e.racer_id,
                "motor_no": e.motor_no,
                "boat_no": e.boat_no,
                "comment": e.racer_comment[:20] + "..." if e.racer_comment else "None"
            })
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print("Scraping failed.")
    db.close()

if __name__ == "__main__":
    test_scrape_logic()
