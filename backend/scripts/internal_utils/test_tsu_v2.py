import sys
import os
from bs4 import BeautifulSoup

# backendディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper import TsuHandler

def test_tsu_live():
    handler = TsuHandler()
    hd = "20260404"
    rno = 12 # 最終レース
    
    print(f"--- [TEST] Tsu AJAX restoration (Race {rno} on {hd}) ---")
    
    # AJAX(tenji)経由で実データを取得
    direct = handler.fetch_direct_data(rno, hd)
    exhs = direct.get("exhibitions", [])
    
    print(f"Exhibitions count: {len(exhs)}")
    if exhs:
        for e in sorted(exhs, key=lambda x: x['waku']):
            print(f"Waku {e['waku']}: {e['time']} (Exh), {e['lap']} (Lap), {e['turn']} (Turn), {e['straight']} (Straight)")
            # 取得できていれば成功
    else:
        print("No AJAX data returned. (Possibly cleared after race end)")
        # 接続テスト
        xml_res = handler._fetch_ajax("tenji", rno, hd)
        if xml_res:
             print("AJAX response fetched successfully.")
             if "table" in xml_res:
                 print("Table structure detected in AJAX response.")
        else:
             print("Failed to fetch AJAX response.")

    print("\n[VERIFICATION] Tsu logic check completed.")

if __name__ == "__main__":
    test_tsu_live()
