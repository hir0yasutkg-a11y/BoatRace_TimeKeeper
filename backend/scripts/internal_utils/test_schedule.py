import scraper
import json

def test():
    print("Testing fetch_today_schedule...")
    date = "20260404"
    venues = scraper.fetch_today_schedule(date)
    print(f"Result: {json.dumps(venues, indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    test()
