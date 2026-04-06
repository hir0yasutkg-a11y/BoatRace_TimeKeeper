import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import Base, Race, Entry, Exhibition
from scraper import scrape_and_store_race_info, get_race_data_from_db

DATABASE_URL = "sqlite:///./boatrace_test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_tokuyama_scraping():
    # テーブル作成
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # 20260331 (昨日) の徳山(18) 12R をテスト
    hd = "20260331"
    jcd = "18"
    rno = 12
    
    print(f"--- Testing Tokuyama (JCD 18) 1R Scraping for {hd} ---")
    
    # 既存データを削除してクリーンな状態でテスト
    race_id = f"{hd}_{jcd}_{rno}"
    db.query(Exhibition).filter(Exhibition.race_id == race_id).delete()
    db.query(Entry).filter(Entry.race_id == race_id).delete()
    db.query(Race).filter(Race.id == race_id).delete()
    db.commit()
    
    success = scrape_and_store_race_info(hd, jcd, rno, db)
    
    if success:
        racers = get_race_data_from_db(db, hd, jcd, rno)
        print(f"\nScraped {len(racers)} racers:")
        for r in racers:
            print(f"Waku {r.waku}: {r.name}")
            print(f"  Comment: {r.comment}")
            print(f"  Exh: {r.exhibition_time}, Lap: {r.lap_time}, Turn: {r.turn_time}, Straight: {r.straight_time}")
    else:
        print("Scraping failed.")
    
    db.close()

if __name__ == "__main__":
    test_tokuyama_scraping()
