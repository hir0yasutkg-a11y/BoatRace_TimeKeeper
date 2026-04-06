import sys
import os
from bs4 import BeautifulSoup

# backendディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper import FukuokaHandler

def test_fukuoka_live():
    handler = FukuokaHandler()
    hd = "20260404"
    rno = 12 # 最終レース
    
    print(f"--- [TEST] Fukuoka PHP restoration (Race {rno} on {hd}) ---")
    
    # 独自PHP経由で実データを取得
    direct = handler.fetch_direct_data(rno, hd)
    exhs = direct.get("exhibitions", [])
    
    print(f"Exhibitions count: {len(exhs)}")
    if exhs:
        for e in sorted(exhs, key=lambda x: x['waku']):
            print(f"Waku {e['waku']}: {e['time']} (Exh), {e['lap']} (Lap), {e['turn']} (Turn), {e['straight']} (Straight)")
            # 取得できていれば成功
    else:
        print("No live data returned (at 00:15). Checking PHP accessibility...")
        html = handler._fetch_php("tenji_info", rno, hd)
        if html:
            print("PHP endpoint is accessible.")
            if "table" in html:
                print("Table structure detected in PHP response.")
        else:
            print("Failed to fetch PHP response.")

    print("\n[VERIFICATION] Fukuoka logic check completed.")

if __name__ == "__main__":
    test_fukuoka_live()
