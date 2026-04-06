import requests

url = "https://www.boatrace-miyajima.com/race_common/require/kaisai_reload.php"
data = {"race": 1, "date": 0}
headers = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest"
}

try:
    print(f"Post request to {url} with {data}...")
    res = requests.post(url, data=data, headers=headers, timeout=20)
    res.encoding = "utf-8"
    filename = "miyajima_dump.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(res.text)
    print(f"Dumped {len(res.text)} bytes to {filename}")
    # 最初の500文字を表示して疎通確認
    print("\nPreview:")
    print(res.text[:1000].replace('\n', ' '))
except Exception as e:
    print(f"Error: {e}")
