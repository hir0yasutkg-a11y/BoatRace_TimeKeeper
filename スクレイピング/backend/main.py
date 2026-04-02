from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
import scraper
import sqlite3

Base.metadata.create_all(bind=engine)

# Auto-migrate table for racer_comment
try:
    with sqlite3.connect("./boatrace_data.db") as conn:
        conn.execute("ALTER TABLE entries ADD COLUMN racer_comment VARCHAR")
except Exception:
    pass

app = FastAPI(title="BoatRace Prediction API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    scraper.scrape_and_store_race_info(db, hd, jcd, rno)
    
    # 2. データベースから取得
    racers = scraper.get_race_data_from_db(db, hd, jcd, rno)

    if not racers:
        # ロード失敗または欠場・データ無し時
        return {
            "hd": hd, "jcd": jcd, "rno": rno,
            "racers": [],
            "predictions": [],
            "error": "データが見つかりませんでした"
        }

    # 3. 勝者予測アルゴリズム (着順予測のルールベース計算)
    # 評価ロジック：勝率が高いほど＋、平均STが早いほど＋、展示タイムが早いほど＋
    predictions = []
    
    # 計算の正規化のために最大値等を取得
    exh_times = [r.exhibition_time for r in racers]
    min_exh = min(exh_times) if exh_times else 6.70
    
    for r in racers:
        base_score = r.rate_global * 10
        # STボーナス: STが0.10に近いほど高得点（最大20点）
        st_bonus = max(0, 20 - ((r.st_average - 0.10) * 100))
        # 展示タイムボーナス: 一番時計からの差が小さいほど高得点（最大30点）
        exh_diff = r.exhibition_time - min_exh
        exh_bonus = max(0, 30 - (exh_diff * 100))
        
        # 内枠有利のバイアス（1枠はインコースで圧倒的有利）
        waku_bonus = {1: 15, 2: 10, 3: 5, 4: 2, 5: 0, 6: 0}.get(r.waku, 0)
        
        total_score = base_score + st_bonus + exh_bonus + waku_bonus
        
        predictions.append({"waku": r.waku, "score": total_score})
        
    # スコア順にソートして着順を設定
    predictions.sort(key=lambda x: x["score"], reverse=True)
    for i, p in enumerate(predictions):
        p["rank_prediction"] = i + 1

    return {
        "hd": hd,
        "jcd": jcd,
        "rno": rno,
        "racers": racers,
        "predictions": predictions
    }

import requests
from bs4 import BeautifulSoup
import re

@app.get("/api/research_marugame")
def research_marugame(hd: str = "20260330", jcd: str = "15", rno: int = 12):
    import requests
    from bs4 import BeautifulSoup
    
    url = f"https://sp.macour.jp/s/race/comment/jcd/{jcd}/hd/{hd}/rno/{rno}/"
    url2 = f"https://kyoteibiyori.com/race_shussou.php?place_no={jcd}&race_no={rno}&date={hd[:4]}-{hd[4:6]}-{hd[6:]}"
    
    results = {}
    try:
        res = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        res.encoding = "utf-8"
        results["macour"] = res.text[:2000]
    except Exception as e:
        results["macour_err"] = str(e)
        
    try:
        res = requests.get(url2, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        res.encoding = "utf-8"
        results["biyori"] = res.text[:2000]
    except Exception as e:
        results["biyori_err"] = str(e)
            
    return results
