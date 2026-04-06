from database import SessionLocal, Race, Entry, Exhibition, SeriesResult
from scraper import scrape_and_store_race_info
import json

db = SessionLocal()
hd = "20260404"
jcd = "01" # 桐生
rno = 1    # 1R

print(f"--- [VICTORY TEST] Kiryu (01) Scraper for {hd} {rno}R ---")
scrape_and_store_race_info(hd, jcd, rno, db)

# 結果の確認
race_id = f"{hd}_{jcd}_{rno}"
entry = db.query(Entry).filter(Entry.race_id == race_id, Entry.waku == 1).first()
if entry:
    print(f"Waku 1 Racer: {entry.name} (Comment: {entry.racer_comment})")

exh = db.query(Exhibition).filter(Exhibition.race_id == race_id, Exhibition.waku == 1).first()
if exh:
    print(f"Exhibition Data: Exh={exh.exhibition_time}, Lap={exh.lap_time}, Turn={exh.turn_time}, Straight={exh.straight_time}")

# 節間成績の確認
s_res = db.query(SeriesResult).filter(SeriesResult.jcd == jcd, SeriesResult.racer_id == entry.racer_id).all() if entry else []
print(f"Found {len(s_res)} series results for Racer {entry.name if entry else 'N/A'}")
for r in s_res:
    print(f"  - {r.date} {r.rno}R: Course={r.course}, Rank={r.rank}, ST={r.st}")

db.close()
