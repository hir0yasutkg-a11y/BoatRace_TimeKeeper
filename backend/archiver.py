import os
import requests
import datetime
import json
from pathlib import Path
from typing import Optional

# 基本設定
BASE_URL = "http://www1.mbrace.or.jp/od2"
ARCHIVE_DIR = Path("backend/data/archive")
INDEX_FILE = ARCHIVE_DIR / "index.json"

FILE_TYPES = {
    "B": "Program",
    "K": "Results",
    "S": "Stats"
}

def fetch_official_data(date_str=None):
    """
    指定した日付（YYYYMMDD）の番組表(B)、結果(K)、成績(S)をアーカイブする。
    date_strがNoneの場合は当日分を対象とする。
    """
    if date_str is None:
        target_date = datetime.datetime.now()
    else:
        target_date = datetime.datetime.strptime(date_str, "%Y%m%d")

    yymm = target_date.strftime("%y%m")
    yymmdd = target_date.strftime("%y%m%d")
    full_year = target_date.strftime("%Y")
    month = target_date.strftime("%m")

    results = []
    
    # 公式サーバーの繊細な制限を突破するためのセッション維持
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    })

    for type_code, type_name in FILE_TYPES.items():
        # URL例: http://www1.mbrace.or.jp/od2/B/2604/b260404.lzh
        filename = f"{type_code.lower()}{yymmdd}.lzh"
        url = f"{BASE_URL}/{type_code}/{yymm}/{filename}"
        
        # 保存先ディレクトリの作成 (例: backend/data/archive/Program/2026/04/)
        save_dir = ARCHIVE_DIR / type_name / full_year / month
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / filename

        print(f"[ARCHIVER] Fetching {type_name}: {url} ...")
        # 1990年代のサーバーに合わせた高度な偽装と忍耐強い待機
        headers = {
            "Referer": f"{BASE_URL}/{type_code}/{yymm}/"
        }
        try:
            # 極低速な応答を確実に待つために 60 秒設定
            resp = session.get(url, headers=headers, timeout=60)
            if resp.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(resp.content)
                print(f"[ARCHIVER] Saved to {save_path}")
                results.append({
                    "date": target_date.strftime("%Y%m%d"),
                    "type": type_name,
                    "filename": filename,
                    "path": str(save_path),
                    "status": "success",
                    "timestamp": datetime.datetime.now().isoformat()
                })
            else:
                print(f"[ARCHIVER] Failed (Status: {resp.status_code})")
        except Exception as e:
            print(f"[ARCHIVER] Error: {e}")

    # インデックスの更新
    update_index(results)
    return results

def update_index(new_entries):
    """
    index.json を更新して、アーカイブ済みのファイルを追跡可能にする。
    """
    index_data = []
    if INDEX_FILE.exists():
        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                index_data = json.load(f)
        except:
            pass

    # 重複チェックを避けながら追記
    current_files = {entry["path"] for entry in index_data}
    for entry in new_entries:
        if entry["path"] not in current_files:
            index_data.append(entry)

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    print(f"[ARCHIVER] Index updated: {INDEX_FILE}")

if __name__ == "__main__":
    import sys
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    fetch_official_data(date_arg)
