import requests
from bs4 import BeautifulSoup

def inspect():
    h = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'}
    r = requests.get('https://www.heiwajima.gr.jp/asp/kyogi/04/sp/yoso0601.htm', headers=h)
    soup = BeautifulSoup(r.text, 'lxml')
    table = soup.find('table')
    if not table:
        print("No table found")
        return
    
    for i, row in enumerate(table.find_all('tr')):
        cols = [td.get_text(separator=" ", strip=True) for td in row.find_all(['td', 'th'])]
        print(f"Row {i}: {cols}")
        # クラス名も確認
        for j, td in enumerate(row.find_all(['td', 'th'])):
            print(f"  Col {j} class: {td.get('class')}")

if __name__ == "__main__":
    inspect()
