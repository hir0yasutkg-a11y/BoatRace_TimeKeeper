import requests

BASE_URL = "http://www1.mbrace.or.jp/od2"
variations = [
    ("B/2604/b260404.lzh", "B/2604/"),
    ("b/2604/b260404.lzh", "b/2604/"),
    ("B/2604/B260404.lzh", "B/2604/"),
    ("b/2604/B260404.lzh", "b/2604/"),
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

for path, ref_part in variations:
    url = f"{BASE_URL}/{path}"
    current_headers = headers.copy()
    current_headers["Referer"] = f"{BASE_URL}/{ref_part}"
    
    try:
        resp = requests.head(url, headers=current_headers, timeout=5)
        print(f"[CHECK] URL: {url} | Referer: {current_headers['Referer']} | Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"!!! SUCCESS: Use URL={url}, Referer={current_headers['Referer']}")
            # 一応中身もちょっとだけ見る
            resp_get = requests.get(url, headers=current_headers, timeout=5, stream=True)
            print(f"!!! REAL STATUS: {resp_get.status_code} | Content Length: {resp_get.headers.get('Content-Length')}")
    except Exception as e:
        print(f"[CHECK] Error for {url}: {e}")
