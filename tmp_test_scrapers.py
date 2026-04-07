from bs4 import BeautifulSoup
import json
import re

# Gamagori Time
print("--- Gamagori Time ---")
soup = BeautifulSoup(open("c:\\Users\\hiroy\\Documents\\Antigravity_local\\gamagori_time.html", encoding="utf-8").read(), "lxml")
time_data = {}
for tr in soup.select('table.ta_kyogi tr'):
    tds = tr.find_all('td')
    if len(tds) >= 12:
        waku_text = tds[1].get_text(strip=True)
        if waku_text.isdigit():
            waku = int(waku_text)
            lap = tds[9].get_text(strip=True)
            turn = tds[10].get_text(strip=True)
            straight = tds[11].get_text(strip=True)
            time_data[waku] = {"lap": lap, "turn": turn, "straight": straight}
print(json.dumps(time_data, indent=2, ensure_ascii=False))

# Gamagori Comment extraction from JS (or we can just fetch the JS)
print("--- Gamagori Comment URL mapping idea ---")
# To map tobang to comments you also need tobang -> waku mapping from the time or main html.
# Since we have `direct_data` with racer names and `toban`, we can download `https://www.gamagori-kyotei.com/asp/gamagori/kyogi/kyogihtml/js/comment{hd}07.js` (Wait! It's not per-race! `comment2026040707.js` is for all 12 races!)
# Let's check omura HTML since it failed before.

print("--- Omura ---")
soup = BeautifulSoup(open("c:\\Users\\hiroy\\Documents\\Antigravity_local\\omura.html", encoding="utf-8").read(), "lxml")
omura_data = {}
# look for table with class tbl_chokuzen or similar. Wait, it's ajax.
# Let's dump all table texts to see what's inside.
for table in soup.find_all('table'):
    # print first row text
    print("Table:", table.get('class', 'No class'))
    first_tr = table.find('tr')
    if first_tr:
        print("  Row:", re.sub(r'\s+', ' ', first_tr.get_text()))
    for tr in table.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) > 0:
            waku_td = tds[0]
            # Try to find img with waku
            img = waku_td.find('img')
            waku = None
            if img and 'src' in img.attrs:
                m = re.search(r'waku_(\d)', img['src'])
                if m:
                    waku = int(m.group(1))
            elif waku_td.get_text(strip=True).isdigit():
                waku = int(waku_td.get_text(strip=True))
            if waku:
                print(f"  Waku {waku} has {len(tds)} tds")
                if len(tds) >= 11:
                    print(f"    lap={tds[6].get_text(strip=True)}, turn={tds[8].get_text(strip=True)}, straight={tds[9].get_text(strip=True)}, com={tds[10].get_text(strip=True)}")
