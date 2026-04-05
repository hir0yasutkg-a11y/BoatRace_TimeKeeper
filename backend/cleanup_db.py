from database import SessionLocal, Race, Entry, Exhibition
import sys

db = SessionLocal()
target_date = "20260403"

try:
    # 今日のレースを検索
    races = db.query(Race).filter(Race.hd == target_date).all()
    if not races:
        print(f"No data found for {target_date}")
        sys.exit(0)

    for r in races:
        print(f"Cleaning up Race: {r.id}")
        # 関連する Entry と Exhibition を削除
        db.query(Entry).filter(Entry.race_id == r.id).delete()
        db.query(Exhibition).filter(Exhibition.race_id == r.id).delete()
        # レース情報本体を削除
        db.delete(r)

    db.commit()
    print(f"Successfully cleaned up {len(races)} races for {target_date}")
except Exception as e:
    db.rollback()
    print(f"Error during cleanup: {e}")
finally:
    db.close()
