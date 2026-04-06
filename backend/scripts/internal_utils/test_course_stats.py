import sys
import os
sys.path.append(os.getcwd())
from database import SessionLocal, RacerCourseStats
from scraper import get_course_stats_from_db
import json

def test_racer_course_stats():
    db = SessionLocal()
    # テスト対象: 選手登録番号 3590 (峰 竜太 選手)
    racer_id = "3590"
    
    print(f"--- 選手コース統計テスト: {racer_id} ---")
    
    # DBから取得 (蓄積がなければスクレイピングされる)
    stats = get_course_stats_from_db(db, racer_id)
    
    if stats:
        print(f"取得成功: {len(stats)}コース分のデータ")
        # 1コース(イン)の逃げ率などを表示してみる
        in_stats = stats[0] # Course 1
        print(f"【1コース】 出走数: {in_stats.entry_count}, 1着率: {in_stats.win_rate}%, 平均ST: {in_stats.avg_st}")
        
        # 6コース(大外)の3連対率などを表示
        out_stats = stats[5] # Course 6
        print(f"【6コース】 3連対率: {out_stats.place3_rate}%, 差し回数: {out_stats.kimarite_sashi}")
        
        # 全データの一部を表示 (JSON)
        print("\nJSON Data (Course 1-2):")
        print(json.dumps([s.dict() for s in stats[:2]], indent=2, ensure_ascii=False))
    else:
        print("統計データの取得に失敗しました。")
        
    db.close()

if __name__ == "__main__":
    test_racer_course_stats()
