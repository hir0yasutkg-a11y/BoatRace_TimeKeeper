from scraper import KojimaHandler

def test_kojima():
    handler = KojimaHandler()
    hd = "20260405"
    rno = 1
    
    print(f"--- Kojima Recon (HD:{hd} RNO:{rno}) ---")
    
    # 1. Direct Data (3 Indicators)
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
    test_kojima()
