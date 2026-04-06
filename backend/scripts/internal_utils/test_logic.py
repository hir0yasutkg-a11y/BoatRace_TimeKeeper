from bs4 import BeautifulSoup
import re
import json

# scraper.py のロジックをシミュレート
def test_logic():
    html = open('tmp_index.html', encoding='utf-8').read()
    soup = BeautifulSoup(html, 'lxml')
    table = soup.select_one('table.table1')
    if not table:
        print("Table not found")
        return

    results = []
    for row in table.select('tbody tr'):
        name_td = row.select_one('td.is-stadiumName')
        if not name_td: continue
        name = name_td.get_text(strip=True)
        
        row_html = str(row)
        row_txt = row.get_text(separator=" ", strip=True)
        
        grade = "General"
        if "is-gradeSG" in row_html or "SG" in row_txt: grade = "SG"
        elif "is-grade1" in row_html or "label-gradeG1" in row_html or "G1" in row_txt: grade = "G1"
        
        deadline = ""
        t_match = re.search(r'(\d{1,2}:\d{2})', row_txt)
        if t_match: deadline = t_match.group(1)
        
        results.append({"name": name, "grade": grade, "deadline": deadline})
    
    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_logic()
