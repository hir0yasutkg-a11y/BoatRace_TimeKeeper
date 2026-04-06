import requests
import sys

def debug_fetch(toban):
    url = f"https://www.boatrace.jp/owpc/pc/data/racersearch/course?toban={toban}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Referer": "https://www.boatrace.jp/owpc/pc/data/racersearch/profile?toban=" + toban
    }
    
    print(f"--- Fetching: {url} ---")
    try:
        # セッションを使ってCookieを維持
        session = requests.Session()
        # 一旦プロフィールページを叩く（リファラを作るため）
        session.get(f"https://www.boatrace.jp/owpc/pc/data/racersearch/profile?toban={toban}", headers=headers, timeout=10)
        
        # 本命のコース別成績ページを取得
        res = session.get(url, headers=headers, timeout=10)
        print(f"Status Code: {res.status_code}")
        print(f"Response Length: {len(res.text)}")
        
        if "table1" in res.text:
            print("SUCCESS: table.table1 was found in the HTML!")
        else:
            print("FAILURE: table.table1 not found.")
            # 取得したHTMLの断片を保存
            with open("debug_fail.html", "w", encoding="utf-8") as f:
                f.write(res.text[:5000])
                
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    debug_fetch("3590")
