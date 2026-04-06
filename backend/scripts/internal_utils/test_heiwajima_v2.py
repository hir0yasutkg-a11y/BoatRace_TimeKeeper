import sys
import os
from bs4 import BeautifulSoup

# backendディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper import HeiwajimaHandler

def test_heiwajima_live():
    handler = HeiwajimaHandler()
    hd = "20260404"
    rno = 12 # 最終レースを狙う
    
    print(f"--- [TEST] Heiwajima LIVE restoration (Race {rno}) ---")
    
    # 実際のリクエストを投げて、SJISデコードとパースが通るか確認
    direct = handler.fetch_direct_data(rno, hd)
    exhs = direct.get("exhibitions", [])
    
    print(f"Exhibitions count: {len(exhs)}")
    if exhs:
        for e in sorted(exhs, key=lambda x: x['waku']):
            print(f"Waku {e['waku']}: {e['time']} (Exh), {e['lap']} (Lap), {e['turn']} (Turn), {e['straight']} (Straight)")
            # 取得できていれば成功
    else:
        print("No live data returned. (Possibly cleared after race end)")
        # 接続テスト
        html = handler._fetch_html("07original", rno)
        if html and "展示タイム" in html:
            print("HTML fetched and looks valid (SJIS decoded).")
        else:
            print("Failed to fetch or decode HTML.")

    print("\n[VERIFICATION] Heiwajima logic check completed.")

if __name__ == "__main__":
    test_heiwajima_live()
