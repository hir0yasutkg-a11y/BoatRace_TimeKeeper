import sys
import os
sys.path.append(os.getcwd())
from database import SessionLocal, RacerCourseStats
import datetime

def inject_racer_stats():
    db = SessionLocal()
    today = datetime.datetime.now().strftime("%Y%m%d")
    
    # ブラウザエージェントが収集した実地データ
    data_map = {
      "5245": {"name": "倉富 大誠", "stats": {
          "1": {"3_rentai": 58.3, "st": 0.18, "rank": 4.0},
          "2": {"3_rentai": 42.9, "st": 0.19, "rank": 3.7},
          "3": {"3_rentai": 56.2, "st": 0.18, "rank": 3.4},
          "4": {"3_rentai": 41.7, "st": 0.15, "rank": 3.3},
          "5": {"3_rentai": 65.0, "st": 0.15, "rank": 2.7},
          "6": {"3_rentai": 30.0, "st": 0.19, "rank": 4.2}
      }},
      "4578": {"name": "藤山 雅弘", "stats": {
          "1": {"3_rentai": 94.7, "st": 0.13, "rank": 2.5},
          "2": {"3_rentai": 87.0, "st": 0.15, "rank": 3.0},
          "3": {"3_rentai": 63.2, "st": 0.13, "rank": 2.9},
          "4": {"3_rentai": 53.8, "st": 0.15, "rank": 2.8},
          "5": {"3_rentai": 73.7, "st": 0.16, "rank": 2.7},
          "6": {"3_rentai": 22.2, "st": 0.17, "rank": 4.1}
      }},
      "4735": {"name": "角山 雄哉", "stats": {
          "1": {"3_rentai": 75.0, "st": 0.15, "rank": 2.9},
          "2": {"3_rentai": 35.0, "st": 0.19, "rank": 3.5},
          "3": {"3_rentai": 43.5, "st": 0.11, "rank": 1.8},
          "4": {"3_rentai": 65.0, "st": 0.14, "rank": 2.8},
          "5": {"3_rentai": 23.1, "st": 0.16, "rank": 3.3},
          "6": {"3_rentai": 10.5, "st": 0.18, "rank": 3.1}
      }},
      "3988": {"name": "古川 誠之", "stats": {
          "1": {"3_rentai": 92.0, "st": 0.15, "rank": 2.8},
          "2": {"3_rentai": 77.3, "st": 0.16, "rank": 3.3},
          "3": {"3_rentai": 65.2, "st": 0.16, "rank": 2.8},
          "4": {"3_rentai": 56.0, "st": 0.15, "rank": 3.2},
          "5": {"3_rentai": 60.0, "st": 0.13, "rank": 2.7},
          "6": {"3_rentai": 9.1, "st": 0.18, "rank": 4.3}
      }},
      "3880": {"name": "浅見 宗孝", "stats": {
          "1": {"3_rentai": 68.4, "st": 0.15, "rank": 3.5},
          "2": {"3_rentai": 46.2, "st": 0.19, "rank": 3.6},
          "3": {"3_rentai": 33.3, "st": 0.21, "rank": 4.1},
          "4": {"3_rentai": 58.3, "st": 0.19, "rank": 4.0},
          "5": {"3_rentai": 22.2, "st": 0.18, "rank": 4.3},
          "6": {"3_rentai": 11.1, "st": 0.15, "rank": 3.3}
      }},
      "3319": {"name": "山崎 義明", "stats": {
          "1": {"3_rentai": 41.7, "st": 0.20, "rank": 4.3},
          "2": {"3_rentai": 41.7, "st": 0.18, "rank": 4.1},
          "3": {"3_rentai": 75.0, "st": 0.17, "rank": 3.8},
          "4": {"3_rentai": 47.4, "st": 0.14, "rank": 2.7},
          "5": {"3_rentai": 46.2, "st": 0.16, "rank": 2.8},
          "6": {"3_rentai": 40.0, "st": 0.17, "rank": 4.7}
      }}
    }

    print("--- 注入開始: コース別詳細統計 ---")
    for racer_id, info in data_map.items():
        print(f"Racer {racer_id} ({info['name']}) ...")
        for course_num, s in info["stats"].items():
            sid = f"{racer_id}_{course_num}"
            stats = db.query(RacerCourseStats).filter(RacerCourseStats.id == sid).first()
            if not stats:
                stats = RacerCourseStats(
                    id=sid, racer_id=racer_id, course=int(course_num),
                    entry_count=100, # 仮
                    win_rate=0.0, place2_rate=0.0, 
                    place3_rate=s["3_rentai"],
                    avg_st=s["st"], avg_st_rank=s["rank"],
                    last_updated=today
                )
                db.add(stats)
            else:
                stats.place3_rate = s["3_rentai"]
                stats.avg_st = s["st"]
                stats.avg_st_rank = s["rank"]
                stats.last_updated = today
    
    db.commit()
    print("--- 注入完了 ---")
    db.close()

if __name__ == "__main__":
    inject_racer_stats()
