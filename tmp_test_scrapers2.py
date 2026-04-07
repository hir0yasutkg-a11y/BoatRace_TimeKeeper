from bs4 import BeautifulSoup
import json
import re

print("--- Omura extraction test ---")
soup = BeautifulSoup(open("c:\\Users\\hiroy\\Documents\\Antigravity_local\\omura_iframe.html", encoding="utf-8").read(), "lxml")
table = soup.find('table', id='tblchokuzen_detail')
omura_data = {}
if table:
    for tr in table.find_all('tr'):
        ths = tr.find_all('th')
        tds = tr.find_all('td')
        if len(ths) >= 2 and len(tds) >= 5:
            waku_text = ths[0].get_text(strip=True)
            if waku_text.isdigit():
                waku = int(waku_text)
                omura_data[waku] = {
                    "lap": tds[2].get_text(strip=True),
                    "turn": tds[3].get_text(strip=True),
                    "straight": tds[4].get_text(strip=True),
                }

kisya = soup.find('div', id='kisyacomment')
kisya_text = ""
if kisya:
    kisya_text = kisya.get_text(separator=' ', strip=True)

print("Omura times:", json.dumps(omura_data, indent=2))
print("Omura comment:", kisya_text[:100])
