import scraper
from database import SessionLocal, engine, Base
import json

def test():
    print("Testing Marugame Scraper for 20260403 R12...")
    db = SessionLocal()
    # 20260403 Marugame (15) R12
    hd = "20260403"
    jcd = "15"
    rno = 12
    
    success = scraper.scrape_and_store_race_info(hd, jcd, rno, db)
    print(f"Scrape Success: {success}")
    
    racers = scraper.get_race_data_from_db(db, hd, jcd, rno)
    if racers:
        for r in racers:
            print(f"Waku {r.waku}: {r.name}, Exh: {r.exhibition_time}, Lap: {r.lap_time}, Turn: {r.turn_time}, Straight: {r.straight_time}")
            c_text = str(r.comment) if r.comment else "NO COMMENT"
            print(f"Comment: {c_text[:50]}...")
    else:
        print("No racers found in DB.")
    db.close()

if __name__ == "__main__":
    test()
