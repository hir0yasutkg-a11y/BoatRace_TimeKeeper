import sys
from bs4 import BeautifulSoup

def parse_and_dump():
    with open('sample.html', 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'lxml')
    tbodys = soup.select('tbody.is-fs12')
    
    with open('parsed_output.txt', 'w', encoding='utf-8') as out:
        if not tbodys:
            out.write("No tbodys found.\n")
            return
            
        tb = tbodys[0]
        trs = tb.select('tr')
        for i, tr in enumerate(trs):
            out.write(f'TR {i}:\n')
            for j, td in enumerate(tr.select('td')):
                txt = td.text.strip().replace('\n', '\\n').replace('\r', '')
                out.write(f'  TD {j}: {txt}\n')

parse_and_dump()
