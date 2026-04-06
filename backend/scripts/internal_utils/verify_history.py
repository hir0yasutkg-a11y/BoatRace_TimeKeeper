import sys
import os
sys.path.append(os.getcwd())
from database import SessionLocal, RacerComment, Entry
import scraper
import datetime

def verify_comment_history():
    db = SessionLocal()
    racer_id = "5245" # 倉富 大誠選手
    jcd = "04"       # 平和島
    today = datetime.datetime.now().strftime("%Y%m%d")
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d")
    
    print(f"--- 選手コメント履歴検証: {racer_id} ---")
    
    # 1. 今日のデータをスクレイピングして保存試行
    print("Step 1: スクレイピングによる今日のコメント保存...")
    scraper.scrape_and_store_race_info(today, jcd, 1, db)
    
    # 2. 昨日分の「ダミーコメント」を手動で注入
    print("Step 2: 昨日分のダミーデータ注入...")
    dummy_id = f"{racer_id}_{jcd}_{yesterday}"
    dummy = db.query(RacerComment).filter(RacerComment.id == dummy_id).first()
    if not dummy:
        dummy = RacerComment(
            id=dummy_id, racer_id=racer_id, jcd=jcd, date=yesterday,
            content="[検証用] 昨日は足が弱かったが、今日はプロペラ叩き変えて上向き。"
        )
        db.add(dummy)
        db.commit()
    
    # 3. API相当のクエリで履歴を取得
    print("Step 3: 履歴取得テスト (降順)...")
    history = db.query(RacerComment).filter(RacerComment.racer_id == racer_id).order_by(RacerComment.date.desc()).all()
    
    for h in history:
        print(f"[{h.date}] @{h.jcd}: {h.content}")
        
    if len(history) >= 2:
        print("\nSUCCESS: 複数日のコメント履歴が時系列で保持されています！")
    else:
        print("\nRETRY: 履歴が1件しかありません。")
        
    db.close()

if __name__ == "__main__":
    verify_comment_history()
