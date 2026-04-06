import sys
import os
# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper import fetch_ashiya_data
import json

def test_ashiya():
    # Test Ashiya Race 1 for today (2026/03/31)
    rno = 1
    hd = "20260331"
    print(f"Testing Ashiya Scraper: Race {rno}, Date {hd}")
    
    result = fetch_ashiya_data(rno, hd)
    
    print("\n--- Scraping Results ---")
    if result["exhibitions"]:
        print(json.dumps(result["exhibitions"], indent=2, ensure_ascii=False))
    else:
        print("No exhibition data found. (The race might be over or data not yet available)")

if __name__ == "__main__":
    test_ashiya()
