import sys
import os
sys.path.append(os.getcwd())
from database import SessionLocal, MotorStats, Entry
from scraper import scrape_and_store_race_info, get_motor_stats
import json

def test_motor_accumulation():
    db = SessionLocal()
    # テスト対象: 2026/04/04 平和島 (04) 1R
    hd, jcd, rno = "20260404", "04", 1
    
    print("--- 1回目のスクレイピング (初回蓄積) ---")
    scrape_and_store_race_info(hd, jcd, rno, db)
    
    # 第1枠のモーター番号を取得
    entry = db.query(Entry).filter(Entry.race_id == f"{hd}_{jcd}_{rno}", Entry.waku == 1).first()
    m_no = entry.motor_no
    print(f"1号艇のモーター番号: {m_no}")
    
    stats_1 = db.query(MotorStats).filter(MotorStats.jcd == jcd, MotorStats.motor_no == m_no, MotorStats.date == hd).first()
    print(f"初回平均展示: {stats_1.avg_exhibition}, サンプル数: {stats_1.record_count}")
    
    print("\n--- 2回目のスクレイピング (累積テスト) ---")
    scrape_and_store_race_info(hd, jcd, rno, db)
    
    stats_2 = db.query(MotorStats).filter(MotorStats.jcd == jcd, MotorStats.motor_no == m_no, MotorStats.date == hd).first()
    print(f"累積後平均展示: {stats_2.avg_exhibition}, サンプル数: {stats_2.record_count}")
    
    print("\n--- API向け統計取得テスト ---")
    history = get_motor_stats(db, jcd, m_no)
    print(f"API返却用データ: {history.json()}")
    
    db.close()

if __name__ == "__main__":
    test_motor_accumulation()
