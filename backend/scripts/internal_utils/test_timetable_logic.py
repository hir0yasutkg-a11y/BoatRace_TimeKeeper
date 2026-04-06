import scraper
from database import SessionLocal

def test_timetable():
    jcd = "01" # 桐生
    hd = "20260405" # 本日
    
    print(f"--- Timetable Recon for Venue {jcd} on {hd} ---")
    tt = scraper.fetch_venue_timetable(jcd, hd)
    
    if tt:
        print(f"Success! Found {len(tt)} races.")
        for rno in sorted(tt.keys()):
            print(f"  R{rno:02d}: {tt[rno]}")
    else:
        print("Failed to fetch timetable.")

if __name__ == "__main__":
    test_timetable()
