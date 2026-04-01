
import sys
import os
sys.path.append(os.getcwd())
from backend.scraper import fetch_marugame_data

def test():
    results = fetch_marugame_data(10, '20260331')
    print("--- Scraping Results for Marugame 10R ---")
    if not results["exhibitions"]:
        print("No data found.")
        return
    for exh in results["exhibitions"]:
        print(f"Waku {exh['waku']}: {exh['comment']}")

if __name__ == "__main__":
    test()
