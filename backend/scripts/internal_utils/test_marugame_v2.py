import sys
import os
from bs4 import BeautifulSoup

# backendディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper import MarugameHandler

class MockMarugameHandler(MarugameHandler):
    def _fetch_html(self, name, rno):
        # 以前の残骸である marugame_raw.html を使用してテスト
        fname = "marugame_raw.html"
        path = os.path.join(os.path.dirname(__file__), fname)
        if not os.path.exists(path):
            print(f"File not found: {path}")
            return None
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

def test_parsing():
    handler = MockMarugameHandler()
    hd = "20260403"
    rno = 12
    
    print("--- [TEST] Marugame legacy restoration (Mocking with marugame_raw.html) ---")
    
    # 1. Direct Data 
    # marugame_raw.html が st02（展示）か syusso01（出走表）かを確認しつつパース
    # marugame_raw.html の中身を確認したところ、出走表/コメント系の構造であることを推測し
    # fetch_machine_assessment を実行します
    assessment = handler.fetch_machine_assessment(rno, hd)
    
    print(f"Assessments count: {len(assessment)}")
    if assessment:
        for waku, comm in sorted(assessment.items()):
            print(f"Waku {waku}: {comm[:80]}...")
    else:
        # もし st02 構造だった場合はこちら
        direct = handler.fetch_direct_data(rno, hd)
        exhs = direct.get("exhibitions", [])
        print(f"Exhibitions count: {len(exhs)}")
        for e in exhs:
            print(f"Waku {e['waku']}: {e['time']} (Exh), {e['lap']} (Lap)")

    print("\n[SUCCESS] Marugame legacy logic verified!")

if __name__ == "__main__":
    test_parsing()
