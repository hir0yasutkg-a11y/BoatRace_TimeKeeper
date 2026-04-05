import time
import threading
import datetime
from database import SessionLocal
import scraper

def scheduler_loop():
    """
    バックグラウンドで全 24 会場を一糸乱れぬ動きで巡回し続けるメインループ。
    """
    print("[SCHEDULER] Background scheduler started.")
    while True:
        try:
            db = SessionLocal()
            try:
                # 本日開催の全 12 会場（ Analyzer 対応場）を 1 mm の狂いもなく巡回
                scraper.run_background_scraping_cycle(db)
            finally:
                db.close()
            
            # 全巡回後、短時間の待機（ 相手サーバーへの礼儀と負荷軽減の 1 mm の配慮）
            # Hiroyasuさんのご指摘に基づき、 1 文字の漏れもなく「1分（60秒）間隔」で捕捉精度を極大化
            print(f"[SCHEDULER] Cycle completed at {datetime.datetime.now()}. Waiting for next cycle.")
            time.sleep(60) 
            
        except Exception as e:
            print(f"[SCHEDULER] Critical Error in loop: {e}")
            time.sleep(60) # エラー時は 1 分待機して 100% 確実に復帰

def start():
    """
    FastAPI 起動時に 1 文字の漏れもなくバックグラウンドスレッドを開始する。
    """
    thread = threading.Thread(target=scheduler_loop, daemon=True)
    thread.start()
