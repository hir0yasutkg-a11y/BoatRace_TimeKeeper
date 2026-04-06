import requests
from bs4 import BeautifulSoup

def debug_table_list(toban):
    url = f"https://www.boatrace.jp/owpc/pc/data/racersearch/course?toban={toban}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Referer": "https://www.boatrace.jp/owpc/pc/data/racersearch/profile?toban=" + toban
    }
    
    session = requests.Session()
    session.get(f"https://www.boatrace.jp/owpc/pc/data/racersearch/profile?toban={toban}", headers=headers)
    res = session.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'lxml')
    
    # ページ内のh3（見出し）とtableをすべて抽出
    print(f"--- Racer {toban} Table List ---")
    
    # 見出しとテーブルの対応を探る
    containers = soup.select('div.grid-unit.unit1, div.grid-unit.unit2')
    for i, container in enumerate(containers):
        h3 = container.find('h3')
        table = container.find('table')
        title = h3.text.strip() if h3 else "No Title"
        has_table = "Yes" if table else "No"
        print(f"[{i}] {title} | Table: {has_table}")
        if table:
            # 最初の1行だけサンプル表示
            first_row = table.select_one('tbody tr')
            if first_row:
                print(f"    Sample: {first_row.get_text(separator='|')[:100]}")

if __name__ == "__main__":
    debug_table_list("3590")
