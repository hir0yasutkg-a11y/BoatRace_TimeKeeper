import sys
import os
from scraper import KiryuHandler
from bs4 import BeautifulSoup

def test_kiryu_logic():
    handler = KiryuHandler()
    rno = 1
    hd = "20260405" # 本日の日付
    
    print(f"--- Kiryu Recon (HD:{hd} RNO:{rno}) ---")
    
    # 1. Direct Data (3 Indicators)
    data = handler.fetch_direct_data(rno, hd)
    print(f"Exhibitions: {len(data.get('exhibitions', []))} boats found.")
    for exh in data.get('exhibitions', []):
        print(f"  Waku:{exh['waku']} Time:{exh.get('time')} Lap:{exh.get('lap')} Turn:{exh.get('turn')} Straight:{exh.get('straight')}")
        
    # 2. Machine Assessment (Comments)
    assess = handler.fetch_machine_assessment(rno, hd)
    print(f"Assessments: {len(assess)} comments found.")
    for waku, comment in assess.items():
        print(f"  Waku:{waku} Comment:{comment[:50]}...")

if __name__ == "__main__":
    test_kiryu_logic()
