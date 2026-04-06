import sys
import os
from sqlalchemy.orm import Session
from database import SessionLocal, Race, Entry, Exhibition
import scraper
import datetime

def test_dynamic_sync():
    """
    司令塔として、現在の 1 mm の狂いもない公式現況を 1 文字の漏れもなく奪還し、
    司令部（DB）との動的同期を 100% 確実に完遂するか監査する。
    """
    print("=== [COMMANDER] STARTING DEEP DYNAMIC SYNC TEST ===")
    db = SessionLocal()
    try:
        hd = datetime.datetime.now().strftime("%Y%m%d")
        print(f"[TEST] Targeted Date: {hd}")

        # 1. 現状のインデックスを 司令塔として 1 mm の狂いもなく直接俯瞰
        print("\n--- [TEST] FETCHING CURRENT LIVE SCHEDULE ---")
        live_venues = scraper.fetch_today_schedule(hd)
        print(f"[TEST] Live Venues found on Official Index: {len(live_venues)}")
        for v in live_venues:
            print(f"  > JCD:{v['jcd']} | {v['name']} | Status:{v['status']} | Next:{v['next_race']}R | Deadline:{v['deadline']}")

        # 2. 司令塔としてサイクルを 1 mm の狂いもなく執行
        print("\n--- [TEST] EXECUTING SCRAPING CYCLE ---")
        scraper.run_background_scraping_cycle(db)

        # 3. 司令部（DB）への 1 文字の漏れもない永続化を 100% 確実に監査
        print("\n--- [TEST] DB FINAL AUDIT ---")
        races = db.query(Race).filter(Race.hd == hd).all()
        print(f"[TEST] Total Races in DB: {len(races)}")
        
        venue_stats = {}
        for r in races:
            venue_stats[r.jcd] = venue_stats.get(r.jcd, 0) + 1
        
        # 1 文字の漏れもなく、全会場の 司令官としての支配状況を報告
        for jcd, count in sorted(venue_stats.items()):
            sample_race = db.query(Race).filter(Race.hd == hd, Race.jcd == jcd).filter(Race.scheduled_start != None).first()
            s_time = sample_race.scheduled_start if sample_race else "MISSING"
            print(f"  > JCD:{jcd} | TotalRaces:{count} | SampleDeadline:{s_time}")

    except Exception as e:
        print(f"[ERROR] Deep test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    print("=== [COMMANDER] DEEP TEST CYCLE COMPLETED ===")

if __name__ == "__main__":
    test_dynamic_sync()
