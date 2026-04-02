import sys
import os
sys.path.append(os.getcwd())
import scraper
from sqlalchemy import create_mock_engine
from sqlalchemy.orm import sessionmaker

def test_config():
    print(f"Total venues in config: {len(scraper.VENUES_CONFIG)}")
    for jcd, cfg in scraper.VENUES_CONFIG.items():
        print(f"JCD {jcd}: {cfg['type']} - {cfg['url']}")

def test_routing():
    # Test if routing exists for all 24 venues
    all_jcds = [f"{i:02}" for i in range(1, 25)]
    # 22 is Fukuoka (special)
    for jcd in all_jcds:
        if jcd == "22":
            print(f"JCD {jcd}: Handled by fetch_fukuoka_data")
        elif jcd in scraper.VENUES_CONFIG:
            print(f"JCD {jcd}: Handled by {scraper.VENUES_CONFIG[jcd]['type']}")
        else:
            print(f"JCD {jcd}: MISSING!")

if __name__ == "__main__":
    test_config()
    print("-" * 20)
    test_routing()
