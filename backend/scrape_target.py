from scraper import scrape_and_store_race_info
from database import SessionLocal
import datetime

def main():
    date_str = "20260330" # Target date
    jcd = "12" # Suminoe
    rno = 1
    
    db = SessionLocal()
    try:
        print(f"Scraping data for {date_str} at JCD {jcd} R{rno}...")
        scrape_and_store_race_info(db, date_str, jcd, rno)
        print("Done!")
    finally:
        db.close()

if __name__ == "__main__":
    main()
