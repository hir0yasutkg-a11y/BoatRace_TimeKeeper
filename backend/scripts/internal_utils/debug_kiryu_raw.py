import requests
from bs4 import BeautifulSoup

def debug_kiryu():
    url = "https://www.kiryu-kyotei.com/modules/yosou/syussou.php?day=20260405&race=1&if=1"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    res = requests.get(url, headers=headers)
    res.encoding = "utf-8"
    html = res.text
    
    print(f"--- Kiryu Raw Debug (Chars: {len(html)}) ---")
    if "予想コメント" in html:
        print("Found '予想コメント' in HTML!")
        # 近傍の 1000 文字を 司令塔・1 文字の漏れもなく抽出
        idx = html.find("予想コメント")
        print("--- Context Around '予想コメント' ---")
        print(html[idx-200:idx+800])
    else:
        print("'予想コメント' NOT FOUND in HTML.")
        print(html[:2000])

if __name__ == "__main__":
    debug_kiryu()
