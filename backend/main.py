from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
import scraper
from models import Racer, Prediction, RaceInfo
from typing import List, Optional
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

Base.metadata.create_all(bind=engine)

app = FastAPI(title="BoatRace Prediction API")

# CORS設定を追加
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/prediction/{hd}/{jcd}/{rno}")
def get_prediction(hd: str, jcd: str, rno: int, db: Session = Depends(get_db)):
    """
    指定された日付(hd)、場(jcd)、レース番号(rno)の予想と直前情報を返す。
    DBに無ければスクレイピングをして保存する。
    """
    
    # 1. DBにデータがあるか確認、無ければスクレイピング
    success = scraper.scrape_and_store_race_info(hd, jcd, rno, db)
    
    # 2. データベースから取得
    racers = scraper.get_race_data_from_db(db, hd, jcd, rno)
    is_mock = False

    if not racers:
        # 失敗時はモック（開発用）
        seed_val = int(jcd) * 100 + int(rno)
        venue_map = {"01": "桐生", "02": "戸田", "03": "江戸川", "04": "平和島", "12": "住之江", "15": "丸亀", "24": "大村"}
        v_name = venue_map.get(jcd, f"会場{jcd}")
        
        import random
        rng = random.Random(seed_val)
        
        names_base = ["峰", "毒島", "馬場", "桐生", "石野", "菊地"]
        racers = []
        for i in range(1, 7):
            name_suffix = rng.choice(["選手", "プロ", "スター", "エース"])
            racers.append(Racer(
                waku=i, 
                name=f"{v_name} {names_base[i-1]}{name_suffix}", 
                rate_global=round(rng.uniform(5.5, 9.8), 2), 
                st_average=round(rng.uniform(0.10, 0.18), 3), 
                exhibition_time=round(rng.uniform(6.50, 6.90), 2),
                comment="サンプルコメントです。本番データが取れるとここが変わります。"
            ))
        is_mock = True

    # 3. 勝者予測アルゴリズム
    predictions = []
    exh_times = [r.exhibition_time for r in racers if r.exhibition_time > 0]
    min_exh = min(exh_times) if exh_times else 6.70
    
    for r in racers:
        base_score = r.rate_global * 10
        st_bonus = max(0, 20 - ((r.st_average - 0.10) * 100))
        exh_diff = r.exhibition_time - min_exh if r.exhibition_time > 0 else 0.5
        exh_bonus = max(0, 30 - (exh_diff * 100))
        waku_bonus = {1: 20, 2: 12, 3: 8, 4: 4, 5: 2, 6: 0}.get(r.waku, 0)
        
        total_score = base_score + st_bonus + exh_bonus + waku_bonus
        predictions.append({"waku": r.waku, "score": total_score})
        
    predictions.sort(key=lambda x: x["score"], reverse=True)
    for i, p in enumerate(predictions):
        p["rank_prediction"] = i + 1

    racelist_url = f"{scraper.BASE_URL}/racelist?rno={rno}&jcd={jcd}&hd={hd}"
    beforeinfo_url = f"{scraper.BASE_URL}/beforeinfo?rno={rno}&jcd={jcd}&hd={hd}"

    return {
        "hd": hd,
        "jcd": jcd,
        "rno": rno,
        "racelist_url": racelist_url,
        "beforeinfo_url": beforeinfo_url,
        "racers": racers,
        "predictions": predictions,
        "is_mock": is_mock
    }

@app.get("/api/schedule/{date}")
def get_schedule(date: str):
    return scraper.fetch_today_schedule(date)

# 静的ファイルの提供 (Reactビルド用)
# dist フォルダがある場合のみマウント
dist_path = os.path.join(os.path.dirname(__file__), "web/dist")
if os.path.exists(dist_path):
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="static")

    @app.exception_handler(404)
    async def not_found_handler(request, exc):
        # SPAのルーティングをサポートするため、404時は index.html を返す
        return FileResponse(os.path.join(dist_path, "index.html"))
