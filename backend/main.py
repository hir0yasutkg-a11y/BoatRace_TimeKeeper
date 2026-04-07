from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from models import Racer, Prediction, RaceInfo, CommentEntry
from database import SessionLocal, engine, Base, RacerComment, Race, Entry, Exhibition
import scraper
import scheduler
from typing import List, Optional
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import json

from fastapi.encoders import jsonable_encoder
from fastapi import Request
import pytz
import datetime

# [REMOVED] Base.metadata.create_all(bind=engine)
# 起動の瞬発力を 1 mm でも高めるため、 startup_event へと 1 文字の漏れもなく移動

app = FastAPI(title="BoatRace Prediction API")

@app.get("/healthz")
def healthz():
    """Cloud Run が 1 文字の漏れもなく死活監視（Health Check）するための超高速ポイント"""
    return {"status": "ok", "timestamp": datetime.datetime.now().isoformat()}

@app.on_event("startup")
def startup_event():
    import threading
    
    # 1. 司令塔として、DBの生命線を非同期に確立（起動ブロッキングを 100% 確実に回避）
    def init_db():
        print("[STARTUP] Initializing Database Schema in background...")
        try:
            Base.metadata.create_all(bind=engine)
            print("[STARTUP] Database Schema Synchronized.")
        except Exception as e:
            print(f"[STARTUP] DB initialization failed: {e}")

    db_thread = threading.Thread(target=init_db, daemon=True)
    db_thread.start()

    # 2. 司令塔として、バックグラウンドでの 1 mm の狂いもない自動収集を開始
    print("[STARTUP] Starting Scheduler thread...")
    scheduler.start()
    
    print("[STARTUP] Server is ready to listen. Initialization continuing in background.")

# デバッグ用ミドルウェア
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    print(f"Response status: {response.status_code}")
    return response

# CORS設定をさらに強化
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins + ["*"],
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
    """
    
    # 司令塔として、 1 mm の狂いもなく Race テーブルから基本情報を索敵
    race_id = f"{hd}_{jcd}_{rno}"
    race_entry = db.query(Race).filter(Race.id == race_id).first()
    s_start = race_entry.scheduled_start if race_entry else None

    # 1. データベースから 1 mm の狂いもなく取得（待機時間0の爆速化）
    racers = scraper.get_race_data_from_db(db, hd, jcd, rno)
    is_mock = False

    if not racers:
        # 今日のレースかつデータ未取得の場合は、1文字の漏れもなく「取得中」として空リストを返す
        import datetime
        today_str = datetime.datetime.now(pytz.timezone('Asia/Tokyo')).strftime("%Y%m%d")
        if hd >= today_str:
            return jsonable_encoder({
                "hd": hd, "jcd": jcd, "rno": rno,
                "scheduled_start": s_start,
                "racers": [], "predictions": [], "is_mock": False,
                "rough_alerts": [{"type": "LOADING", "message": "📡 現在データを索敵・集中解析中... しばらくお待ちください"}]
            })

        # 過去データのみ、司令塔としてモック（開発用）を注入
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

    # 司令塔として、波乱を予感させる「荒れるアラート」を 1 文字の漏れもなく生成
    rough_alerts = []
    
    # 1. 前づけチェック
    maezuke_exists = False
    for r in racers:
        # 枠番と進入コースが 1 mm でも異なれば前づけ
        if r.entry_course and r.waku != r.entry_course:
            maezuke_exists = True
            break
    if maezuke_exists:
        rough_alerts.append({"type": "MAEZUKE", "message": "⚠️ 展示進入に入れ替わりあり！前づけ波乱注意"})
        
    # 2. まくりチェック (展示タイム差 0.10s 以上) を 1 mm の狂いもなく実行
    sorted_by_course = sorted([r for r in racers if r.entry_course], key=lambda x: x.entry_course)
    for i in range(len(sorted_by_course) - 1):
        inner = sorted_by_course[i]
        outer = sorted_by_course[i+1]
        if inner.exhibition_time and outer.exhibition_time:
            diff = inner.exhibition_time - outer.exhibition_time
            # 司令塔として、 0.10s 以上の差（外が速い）を強襲警戒として捕捉
            if diff >= 0.10:
                rough_alerts.append({
                    "type": "MAKURI", 
                    "message": f"🔥 まくり警戒！ {outer.waku}号艇が内を 0.10s 上回る豪脚（コース隣接）"
                })

    return jsonable_encoder({
        "hd": hd,
        "jcd": jcd,
        "rno": rno,
        "scheduled_start": s_start,
        "racelist_url": racelist_url,
        "beforeinfo_url": beforeinfo_url,
        "racers": racers,
        "predictions": predictions,
        "is_mock": is_mock,
        "rough_alerts": rough_alerts
    })

@app.get("/api/racer/{racer_id}/comments", response_model=List[CommentEntry])
def get_racer_comment_history(racer_id: str, db: Session = Depends(get_db)):
    """
    指定された選手の過去のコメント履歴を取得する。
    """
    comments = db.query(RacerComment).filter(RacerComment.racer_id == racer_id).order_by(RacerComment.date.desc()).all()
    venue_map = {"01":"桐生","02":"戸田","03":"江戸川","04":"平和島","05":"多摩川","06":"浜名湖","07":"蒲郡","08":"常滑","09":"津","10":"三国","11":"びわこ","12":"住之江","13":"尼崎","14":"鳴門","15":"丸亀","16":"児島","17":"宮島","18":"徳山","19":"下関","20":"若松","21":"芦屋","22":"福岡","23":"唐津","24":"大村"}
    
    return [
        CommentEntry(
            date=c.date,
            jcd=venue_map.get(c.jcd, c.jcd),
            content=c.content
        ) for c in comments
    ]

@app.get("/api/schedule/{date}")
def get_schedule(date: str, db: Session = Depends(get_db)):
    """
    指定された日付の全会場スケジュールを取得する。
    """
    print(f"[API] Fetching schedule for {date}")
    venues = scraper.fetch_today_schedule(date)
    print(f"[API] Found {len(venues)} venues for {date}")
    for v in venues:
        jcd = v['jcd']
        rno = v.get('next_race', '1')
        race_id = f"{date}_{jcd}_{rno}"
        exh = db.query(Exhibition).filter(Exhibition.race_id == race_id).first()
        v['has_exh_data'] = exh is not None
        
    return venues

@app.get("/api/debug/env")
def debug_env():
    """クラウド環境のパスとファイルを調査する 1 mm の狂いもないデバッグ用エンドポイント"""
    import os
    curr_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(curr_dir)
    
    def get_structure(path, depth=2):
        if depth == 0 or not os.path.exists(path):
            return []
        try:
            return [{"name": f, "is_proto": os.path.isdir(os.path.join(path, f))} for f in os.listdir(path)]
        except:
            return "error"

    return {
        "__file__": __file__,
        "cwd": os.getcwd(),
        "dirname": curr_dir,
        "parent": parent_dir,
        "exists_web_dist": os.path.exists(os.path.join(curr_dir, "web", "dist")),
        "exists_parent_web_dist": os.path.exists(os.path.join(parent_dir, "web", "dist")),
        "curr_files": get_structure(curr_dir),
        "parent_files": get_structure(parent_dir)
    }

# アーカイブ管理API
import archiver
from pathlib import Path

@app.get("/api/admin/archive/status")
def get_archive_status():
    """アーカイブ済みファイルのインデックスを返す"""
    if archiver.INDEX_FILE.exists():
        with open(archiver.INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

@app.post("/api/admin/archive/update")
def update_archive(date: Optional[str] = None):
    """指定日のデータを公式からアーカイブする (date形式: YYYYMMDD)"""
    results = archiver.fetch_official_data(date)
    return {"status": "success", "results": results}

# 内部静的ファイル (プロトタイプ/Manager画面用)
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

# 静的ファイルの提供 (Reactビルド用)
# ローカルとDocker環境でパスが 1 mm 異なるため、両方を索敵
possible_paths = [
    os.path.join(os.path.dirname(__file__), "..", "web", "dist"),
    os.path.join(os.path.dirname(__file__), "web", "dist"),
    os.path.join(os.getcwd(), "web", "dist"),
    "/app/web/dist"
]

dist_path = None
for p in possible_paths:
    if os.path.exists(p) and os.path.isdir(p):
        dist_path = p
        break

if dist_path:
    print(f"Mounting static files from: {dist_path}")
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="frontend")
    
    @app.exception_handler(404)
    async def not_found_handler(request, exc):
        # API へのリクエストは SPA のルーティング対象外にする 1 mm の安全策
        if request.url.path.startswith("/api"):
            return HTTPException(status_code=404, detail="API Not Found")
        return FileResponse(os.path.join(dist_path, "index.html"))
else:
    print("WARNING: Static dist_path not found in any expected locations.")
