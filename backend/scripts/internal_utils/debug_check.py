from bs4 import BeautifulSoup
import re
import os

html_path = 'tmp_index.html'
if not os.path.exists(html_path):
    print(f"Error: {html_path} not found")
    exit(1)

soup = BeautifulSoup(open(html_path, encoding='utf-8').read(), 'lxml')
table = soup.select_one('table.table1')
if not table:
    print("Error: table.table1 not found")
    exit(1)

rows = table.select('tbody tr')
print(f"Total rows found: {len(rows)}\n")

for i, row in enumerate(rows):
    stadium_td = row.select_one('td.is-stadiumName')
    stadium = stadium_td.get_text(strip=True) if stadium_td else "None"
    
    # 1. すべての span とそのクラスを列挙
    spans = row.find_all('span')
    span_info = [f"<{s.get('class')}>" for s in spans if s.get('class')]
    
    # 2. すべてのテキストノードから時間を抽出
    full_text = row.get_text(separator=' ', strip=True)
    times = re.findall(r'(\d{1,2}:\d{2})', full_text)
    
    print(f"Row {i:02d}: Stadium={stadium}")
    print(f"  Spans: {', '.join(span_info[:10])}...")
    print(f"  Times found: {times}")
    print(f"  Full Text Snapshot: {full_text[:100]}...")
    print("-" * 50)
