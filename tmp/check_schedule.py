import sys
import os
sys.path.append(os.getcwd())
from backend.scraper import fetch_today_schedule
if __name__ == "__main__":
    venues = fetch_today_schedule("20260401")
    for v in venues:
        print(f"JCD {v['jcd']}: {v['name']}")
