import sqlite3
from sqlalchemy.orm import Session
from database import SessionLocal
from scraper import MiyajimaHandler

def test_miyajima():
    handler = MiyajimaHandler()
    hd = "20260405"
    rno = 1
    
    print(f"--- Miyajima Recon (HD:{hd} RNO:{rno}) ---")
    
    # 1. Raw Response Check
    html = handler._fetch_reload_html(rno, hd)
    print(f"--- Raw HTML (First 5000 chars) ---")
    print(html[:5000] if html else "None")
    
    # 2. Direct Data (3 Indicators)
    data = handler.fetch_direct_data(rno, hd)
    print(f"Exhibitions: {len(data.get('exhibitions', []))} boats found.")
    for exh in data.get('exhibitions', []):
        print(f" Waku:{exh['waku']} Time:{exh['time']} Lap:{exh['lap']} Turn:{exh['turn']} Straight:{exh['straight']}")
    
    # 2. Machine Assessment (Reporter Comments)
    assess = handler.fetch_machine_assessment(rno, hd)
    print(f"Assessments: {len(assess)} comments found.")
    for waku, comm in assess.items():
        print(f" Waku:{waku} Comment:{comm[:50]}...")

if __name__ == "__main__":
    test_miyajima()
