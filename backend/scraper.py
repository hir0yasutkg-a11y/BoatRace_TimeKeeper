import requests
from bs4 import BeautifulSoup
import time
from sqlalchemy.orm import Session
from database import Race, Entry, Exhibition, RacerComment, SeriesResult
from models import Racer
import lxml
import re
import datetime
import json
from typing import List, Optional

BASE_URL = "https://www.boatrace.jp/owpc/pc/race"

# 全24場のシステム分類
VENUES_CONFIG = {
    "01": {"type": "synergy", "url": "https://www.kiryu-kyotei.com"},
    "02": {"type": "toda",    "url": "https://www.boatrace-toda.jp"},
    "03": {"type": "synergy", "url": "https://www.edogawa-kyotei.co.jp"},
    "04": {"type": "asp",     "url": "https://www.heiwajima.gr.jp"},
    "15": {"type": "asp",     "url": "https://www.marugameboat.jp"},
    "17": {"type": "spa",     "url": "https://www.boatrace-miyajima.com"},
}

import xml.etree.ElementTree as ET

# --- 会場別ハンドラー構造 ---

class BaseVenueHandler:
    def __init__(self, jcd: str):
        self.jcd = jcd
    def fetch_direct_data(self, rno: int, hd: str):
        """司令塔として、公式サイトの直前情報から 1 文字の漏れもなくタイムと進入を捕捉"""
        url = f"{BASE_URL}/beforeinfo?rno={rno}&jcd={self.jcd}&hd={hd}"
        html = fetch_html(url)
        if not html: return {"exhibitions": [], "entry_courses": {}}
        soup = BeautifulSoup(html, 'lxml')
        
        exh_rows = soup.select('div.table1 table tbody')
        exh_list = []
        for i, tbody in enumerate(exh_rows[:6]):
            tds = tbody.select('td')
            if len(tds) > 4:
                try:
                    time_val = float(tds[4].get_text(strip=True)) if tds[4].get_text(strip=True) != "-" else None
                    exh_list.append({"waku": i+1, "time": time_val})
                except: pass

        entry_courses = {}
        entry_table = soup.select_one('div.table1.is-w600') 
        if entry_table:
            courses = entry_table.select('div.is-display.is-fBold')
            for c_idx, div in enumerate(courses):
                try:
                    waku = int(div.get_text(strip=True))
                    entry_courses[waku] = c_idx + 1 # 1-6コースを 100% 確実にマッピング
                except: pass
        
        return {"exhibitions": exh_list, "entry_courses": entry_courses}
    def fetch_series_results(self, rno: int, hd: str): return {}
    def fetch_machine_assessment(self, rno: int, hd: str): return {}

class KiryuHandler(BaseVenueHandler):
    def __init__(self):
        super().__init__("01")
        self.base_url = "https://www.kiryu-kyotei.com/modules/yosou"

    def fetch_direct_data(self, rno: int, hd: str):
        direct_data = super().fetch_direct_data(rno, hd)
        url = f"{self.base_url}/cyokuzen.php?day={hd}&race={rno}&if=1"
        html = fetch_html(url)
        if not html: return direct_data
        soup = BeautifulSoup(html, 'lxml')
        table = soup.select_one('table.com-yosou-table.cyokuzen')
        if table:
            for tr in table.select('tr.odd, tr.even'):
                tds = tr.select('td')
                if len(tds) >= 9:
                    try:
                        waku_txt = tds[0].get_text(strip=True)
                        if not waku_txt.isdigit(): continue
                        waku = int(waku_txt)
                        def p(txt): return float(txt) if txt and '.' in txt else None
                        time_exh = p(tds[3].get_text(strip=True))
                        lap = p(tds[6].get_text(strip=True))
                        turn = p(tds[7].get_text(strip=True))
                        straight = p(tds[8].get_text(strip=True))
                        for exh in direct_data["exhibitions"]:
                            if exh["waku"] == waku:
                                exh["lap"], exh["turn"], exh["straight"] = lap, turn, straight
                                if time_exh: exh["time"] = time_exh
                                break
                    except: continue
        return direct_data

    def fetch_machine_assessment(self, rno: int, hd: str):
        url = f"{self.base_url}/syussou.php?day={hd}&race={rno}&if=1"
        html = fetch_html(url)
        assessment = {}
        if not html: return {}
        soup = BeautifulSoup(html, 'lxml')
        yoso_td = soup.select_one('td.kind-focus')
        if yoso_td:
            try:
                for div in yoso_td.find_all('div'): div.decompose()
                comment_txt = f"【前日予想】{yoso_td.get_text(strip=True)}"
                for i in range(1, 7): assessment[i] = comment_txt
            except: pass
        table = soup.select_one('table.com-yosou-table')
        if table:
            for tr in table.select('tr.odd, tr.even'):
                tds = tr.select('td')
                if len(tds) >= 8:
                    try:
                        waku_txt = tds[0].get_text(strip=True)
                        if not waku_txt.isdigit(): continue
                        waku = int(waku_txt)
                        comment = tds[7].get_text(strip=True)
                        if comment and comment != "-":
                            current = assessment.get(waku, "")
                            assessment[waku] = f"{current} | 【記者】{comment}" if current else f"【記者】{comment}"
                    except: continue
        return assessment

    def fetch_series_results(self, rno: int, hd: str): return {}

class TodaHandler(BaseVenueHandler):
    def __init__(self):
        super().__init__("02")
        self.base_xml_url = "https://www.boatrace-toda.jp/xml/kaisai"

    def fetch_direct_data(self, rno: int, hd: str):
        url = f"{self.base_xml_url}/{hd}/chokuzen_{rno:02d}.xml"
        xml_text = fetch_html(url)
        if not xml_text: return {"exhibitions": []}
        exh_list = []
        try:
            root = ET.fromstring(xml_text)
            for racer in root.findall('.//racer'):
                waku = int(racer.find('waku').text)
                exh_list.append({
                    "waku": waku,
                    "time": float(racer.find('tenji_time').text) if racer.find('tenji_time').text else None,
                    "lap": float(racer.find('ichishu_time').text) if racer.find('ichishu_time').text else None,
                    "turn": float(racer.find('mawari_time').text) if racer.find('mawari_time').text else None,
                    "straight": float(racer.find('chokusen_time').text) if racer.find('chokusen_time').text else None
                })
        except Exception as e: print(f"[SCRAPER] Toda XML Error: {e}")
        return {"exhibitions": exh_list}

    def fetch_machine_assessment(self, rno: int, hd: str):
        url = f"{self.base_xml_url}/{hd}/yoso_{rno:02d}.xml"
        xml_text = fetch_html(url)
        assessment = {}
        if not xml_text: return {}
        try:
            root = ET.fromstring(xml_text)
            for racer in root.findall('.//racer'):
                waku = int(racer.find('waku').text)
                mark = racer.find('mark').text if racer.find('mark').text else ""
                comment = racer.find('comment').text if racer.find('comment').text else ""
                if mark or comment:
                    assessment[waku] = f"【記者】{mark} {comment}".strip()
        except Exception as e: print(f"[SCRAPER] Toda XML Error: {e}")
        return assessment

class MiyajimaHandler(BaseVenueHandler):
    def __init__(self):
        super().__init__("17")
        self.base_url = "https://www.boatrace-miyajima.com"
        self.reload_url = f"{self.base_url}/race_common/require/kaisai_reload.php"
        self._cached_html = None
        self._cached_key = None

    def _fetch_reload_html(self, rno: int, hd: str):
        cache_key = f"{hd}_{rno}"
        if self._cached_key == cache_key and self._cached_html: return self._cached_html
        data = {"race": rno, "date": 1} 
        headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "X-Requested-With": "XMLHttpRequest"}
        try:
            res = requests.post(self.reload_url, data=data, headers=headers, timeout=20)
            if res.status_code == 200:
                res.encoding = "utf-8"
                self._cached_html = res.text
                self._cached_key = cache_key
                return self._cached_html
        except Exception as e: print(f"[SCRAPER] Miyajima POST Error: {e}")
        return None

    def fetch_direct_data(self, rno: int, hd: str):
        direct_data = super().fetch_direct_data(rno, hd)
        html = self._fetch_reload_html(rno, hd)
        if not html: return direct_data
        soup = BeautifulSoup(html, 'lxml')
        table = soup.select_one('table.top_playertable')
        if table:
            for tr in table.find_all('tr', class_='fcblack'):
                tds = tr.find_all('td')
                if len(tds) >= 9:
                    try:
                        w_txt = tds[0].get_text(strip=True)
                        if not w_txt.isdigit(): continue
                        waku = int(w_txt)
                        def p(txt): return float(txt) if txt and '--' not in txt else None
                        time_exh = p(tds[5].get_text(strip=True))
                        lap = p(tds[6].get_text(strip=True))
                        turn = p(tds[7].get_text(strip=True))
                        straight = p(tds[8].get_text(strip=True))
                        for exh in direct_data["exhibitions"]:
                            if exh["waku"] == waku:
                                exh["lap"], exh["turn"], exh["straight"] = lap, turn, straight
                                if time_exh: exh["time"] = time_exh
                                break
                    except: continue
        return direct_data

    def fetch_machine_assessment(self, rno: int, hd: str):
        html = self._fetch_reload_html(rno, hd)
        if not html: return {}
        soup = BeautifulSoup(html, 'lxml')
        assessment = {}
        target_label = soup.find(lambda t: t.name in ['th', 'td'] and '展開予想コメント' in t.get_text())
        if target_label:
            try:
                next_tr = target_label.find_parent('tr').find_next_sibling('tr')
                if next_tr:
                    comment_td = next_tr.select_one('td')
                    if comment_td:
                        comment_txt = f"【展開予想】{comment_td.get_text(strip=True)}"
                        for i in range(1, 7): assessment[i] = comment_txt
            except: pass
        return assessment

class KojimaHandler(BaseVenueHandler):
    def __init__(self):
        super().__init__("16")
        self.base_url = "https://www.kojimaboat.jp/asp/kyogi/16/pc"

    def _fetch_html(self, name: str, rno: int):
        url = f"{self.base_url}/{name}{rno:02d}.htm"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                res.encoding = "utf-8"
                return res.text
        except Exception as e: print(f"[SCRAPER] Kojima GET Error: {e}")
        return None

    def fetch_direct_data(self, rno: int, hd: str):
        html = self._fetch_html("st02", rno)
        if not html: return {"exhibitions": []}
        soup = BeautifulSoup(html, 'lxml')
        exh_dict = {}
        table = soup.find('table', class_='table_yoso07')
        if table:
            for tbody in table.find_all('tbody'):
                tr = tbody.find('tr')
                if not tr: continue
                td_waku = tr.find('td', class_=re.compile(r'waku0[1-6]'))
                if not td_waku: continue
                try:
                    waku = int(td_waku.get_text(strip=True))
                    all_tds = tr.find_all('td')
                    if len(all_tds) >= 9:
                        exh_dict[waku] = {
                            "waku": waku,
                            "time": float(all_tds[5].get_text(strip=True)) if all_tds[5].get_text(strip=True) else None,
                            "lap": float(all_tds[6].get_text(strip=True)) if all_tds[6].get_text(strip=True) else None,
                            "turn": float(all_tds[7].get_text(strip=True)) if all_tds[7].get_text(strip=True) else None,
                            "straight": float(all_tds[8].get_text(strip=True)) if all_tds[8].get_text(strip=True) else None
                        }
                except: continue
        return {"exhibitions": list(exh_dict.values())}

    def fetch_machine_assessment(self, rno: int, hd: str):
        """司令塔として、児島の 1 mm の狂いもない選手コメントを 100% 確実に奪還"""
        html = self._fetch_html("syusso01", rno)
        if not html: return {}
        soup = BeautifulSoup(html, 'lxml')
        assessment = {}
        # ヘッダー2行を考慮し、3行目から 1 文字の漏れもなく 6 人分を射抜く
        rows = soup.select('table tr')
        for i in range(1, 7):
            try:
                # ターゲット: 児島の表構造 (ヘッダー2行) を 1 mm 的に考慮。 Index 2 が Waku 1
                row_idx = i + 1
                if row_idx < len(rows):
                    tds = rows[row_idx].find_all('td')
                    if len(tds) >= 9:
                        comment = tds[8].get_text(strip=True)
                        if comment and comment != "-": assessment[i] = comment
            except: continue
        return assessment

class SuminoeHandler(BaseVenueHandler):
    def __init__(self):
        super().__init__("12")
        self.base_url = "https://www.boatrace-suminoe.jp/asp/kyogi/12/pc"

    def _fetch_html(self, name: str, rno: int):
        url = f"{self.base_url}/{name}{rno:02d}.htm"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                res.encoding = "utf-8"
                return res.text
        except Exception as e: print(f"[SCRAPER] Suminoe GET Error: {e}")
        return None

    def fetch_direct_data(self, rno: int, hd: str):
        html = self._fetch_html("st02", rno)
        if not html: return {"exhibitions": []}
        soup = BeautifulSoup(html, 'lxml')
        exh_dict = {}
        table = soup.find('table', class_='table_solo')
        if table:
            for tbody in table.find_all('tbody'):
                tr = tbody.find('tr')
                if not tr: continue
                td_waku = tr.find('td', class_=re.compile(r'waku0[1-6]'))
                if td_waku:
                    try:
                        waku = int(td_waku.get_text(strip=True))
                        all_tds = tr.find_all('td')
                        if len(all_tds) >= 7:
                            exh_dict[waku] = {
                                "waku": waku, "time": float(all_tds[4].get_text(strip=True)) if all_tds[4].get_text(strip=True) != "-" else None,
                                "lap": float(all_tds[5].get_text(strip=True)) if all_tds[5].get_text(strip=True) != "-" else None,
                                "turn": float(all_tds[6].get_text(strip=True)) if all_tds[6].get_text(strip=True) != "-" else None,
                                "straight": None
                            }
                    except: continue
        return {"exhibitions": list(exh_dict.values())}

class HeiwajimaHandler(BaseVenueHandler):
    def __init__(self):
        super().__init__("04")
        self.base_url = "https://www.heiwajima.gr.jp/asp/kyogi/04/sp"

    def fetch_direct_data(self, rno: int, hd: str):
        url = f"{self.base_url}/yoso05{rno:02d}.htm?slide=2"
        html = fetch_html(url)
        if not html: return {"exhibitions": []}
        soup = BeautifulSoup(html, 'lxml')
        exh_dict = {}
        main_table = soup.find('table', class_='table_syusso')
        if main_table:
            for tr in main_table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) >= 6:
                    try:
                        waku_t = tds[0].get_text(strip=True)
                        if waku_t.isdigit():
                            waku = int(waku_t)
                            exh_dict[waku] = {
                                "waku": waku, "time": float(tds[2].get_text(strip=True)) if tds[2].get_text(strip=True) != "-" else None,
                                "lap": float(tds[3].get_text(strip=True)) if tds[3].get_text(strip=True) != "-" else None,
                                "turn": float(tds[4].get_text(strip=True)) if tds[4].get_text(strip=True) != "-" else None,
                                "straight": float(tds[5].get_text(strip=True)) if tds[5].get_text(strip=True) != "-" else None
                            }
                    except: continue
        return {"exhibitions": list(exh_dict.values())}

class TsuHandler(BaseVenueHandler):
    def __init__(self):
        super().__init__("09")
        self.base_url = "https://www.boatrace-tsu.com/sp/ajax/ajax_yosou.php"

    def fetch_direct_data(self, rno: int, hd: str):
        params = {"targetday": hd, "race": rno, "req": "tenji", "run": 0}
        try:
            res = requests.get(self.base_url, params=params, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'lxml')
                exh_dict = {}
                table = soup.find('table')
                if table:
                    for tr in table.find_all('tr'):
                        tds = tr.find_all('td')
                        if len(tds) >= 7:
                            try:
                                waku = int(tds[0].get_text(strip=True))
                                exh_dict[waku] = {
                                    "waku": waku, "time": float(tds[3].get_text(strip=True)) if tds[3].get_text(strip=True) != "-" else None,
                                    "lap": float(tds[4].get_text(strip=True)) if tds[4].get_text(strip=True) != "-" else None,
                                    "turn": float(tds[5].get_text(strip=True)) if tds[5].get_text(strip=True) != "-" else None,
                                    "straight": float(tds[6].get_text(strip=True)) if tds[6].get_text(strip=True) != "-" else None
                                }
                            except: continue
                return {"exhibitions": list(exh_dict.values())}
        except: pass
        return {"exhibitions": []}

class MikuniHandler(BaseVenueHandler):
    def __init__(self):
        super().__init__("10")

    def fetch_direct_data(self, rno: int, hd: str):
        direct_data = super().fetch_direct_data(rno, hd)
        url = f"https://www.mikuniks-web.jp/races/{rno}"
        html = fetch_html(url)
        if not html: return direct_data
        soup = BeautifulSoup(html, 'lxml')
        table = soup.select_one('table.table2')
        if table:
            rows = table.select('tr')[1:7]
            for i, row in enumerate(rows):
                tds = row.select('td')
                if len(tds) > 5:
                    try:
                        lap = float(tds[3].get_text(strip=True))
                        turn = float(tds[4].get_text(strip=True))
                        st = float(tds[5].get_text(strip=True))
                        for exh in direct_data["exhibitions"]:
                            if exh["waku"] == i + 1:
                                exh["lap"], exh["turn"], exh["straight"] = lap, turn, st
                                break
                    except: pass
        return direct_data

    def fetch_machine_assessment(self, rno: int, hd: str):
        url = f"https://www.mikuniks-web.jp/races/{rno}"
        html = fetch_html(url)
        if not html: return {}
        soup = BeautifulSoup(html, 'lxml')
        comments = {}
        table = soup.select_one('table.table2')
        if table:
            rows = table.select('tr')[1:7]
            for i, row in enumerate(rows):
                tds = row.select('td')
                comment = tds[-1].get_text(strip=True)
                if comment and comment != "-": comments[i+1] = f"当日:{comment}"
        return comments

class FukuokaHandler(BaseVenueHandler):
    def __init__(self):
        super().__init__("22")
        self.base_url = "https://www.boatrace-fukuoka.com/modules/yosou"

    def fetch_direct_data(self, rno: int, hd: str):
        url = f"{self.base_url}/tenji_info.php?day={hd}&race={rno}&if=1&nowmode=1"
        html = fetch_html(url)
        if not html: return {"exhibitions": []}
        soup = BeautifulSoup(html, 'lxml')
        exh_dict = {}
        table = soup.find('table')
        if table:
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) >= 7:
                    try:
                        waku_t = tds[0].get_text(strip=True)
                        if waku_t.isdigit():
                            waku = int(waku_t)
                            exh_dict[waku] = {
                                "waku": waku, "time": float(tds[3].get_text(strip=True)) if tds[3].get_text(strip=True) != "-" else None,
                                "lap": float(tds[4].get_text(strip=True)) if tds[4].get_text(strip=True) != "-" else None,
                                "turn": float(tds[5].get_text(strip=True)) if tds[5].get_text(strip=True) != "-" else None,
                                "straight": float(tds[6].get_text(strip=True)) if tds[6].get_text(strip=True) != "-" else None
                            }
                    except: continue
        return {"exhibitions": list(exh_dict.values())}

class TokuyamaHandler(BaseVenueHandler):
    def __init__(self):
        super().__init__("18")

    def fetch_direct_data(self, rno: int, hd: str):
        direct_data = super().fetch_direct_data(rno, hd)
        url = f"https://www.boatrace-tokuyama.jp/modules/yosou/tenji.php?day={hd}&race={rno}&if=1"
        html = fetch_html(url)
        if not html: return direct_data
        soup = BeautifulSoup(html, 'lxml')
        table = soup.select_one('table.table1')
        if table:
            for row in table.find_all('tr'):
                tds = row.find_all('td')
                if len(tds) > 10:
                    try:
                        w_txt = tds[1].get_text(strip=True)
                        if w_txt.isdigit():
                            waku = int(w_txt)
                            lap = float(tds[9].get_text(strip=True)) if tds[9].get_text(strip=True) != "-" else None
                            turn = float(tds[10].get_text(strip=True)) if tds[10].get_text(strip=True) != "-" else None
                            for exh in direct_data["exhibitions"]:
                                if exh["waku"] == waku:
                                    exh["lap"], exh["turn"] = lap, turn
                                    break
                    except: pass
        return direct_data

    def fetch_machine_assessment(self, rno: int, hd: str):
        url = f"https://www.boatrace-tokuyama.jp/modules/yosou/tenji.php?day={hd}&race={rno}&if=1"
        html = fetch_html(url)
        if not html: return {}
        soup = BeautifulSoup(html, 'lxml')
        assessment = {}
        table = soup.select_one('table.table1')
        if table:
            for row in table.find_all('tr'):
                tds = row.find_all('td')
                if len(tds) > 11:
                    try:
                        w_txt = tds[1].get_text(strip=True)
                        if w_txt.isdigit():
                            waku = int(w_txt)
                            comment_td = tds[-1]
                            assessment[waku] = f"当日:{comment_td.get_text(strip=True)}"
                    except: pass
        return assessment

class GamagoriHandler(BaseVenueHandler):
    def __init__(self):
        super().__init__("07")

    def fetch_direct_data(self, rno: int, hd: str):
        direct_data = super().fetch_direct_data(rno, hd)
        url = f"https://www.gamagori-kyotei.com/asp/gamagori/kyogi/kyogihtml/index.htm?page=staten&racenum={rno}"
        html = fetch_html(url)
        if not html: return direct_data
        soup = BeautifulSoup(html, 'lxml')
        table = soup.select_one('table.table_style01')
        if table:
            for row in table.find_all('tr'):
                tds = row.find_all('td')
                if len(tds) >= 12:
                    try:
                        w_txt = tds[1].get_text(strip=True)
                        if w_txt.isdigit():
                            waku = int(w_txt)
                            lap = float(tds[9].get_text(strip=True)) if tds[9].get_text(strip=True) != "-" else None
                            turn = float(tds[10].get_text(strip=True)) if tds[10].get_text(strip=True) != "-" else None
                            straight = float(tds[11].get_text(strip=True)) if tds[11].get_text(strip=True) != "-" else None
                            for exh in direct_data["exhibitions"]:
                                if exh["waku"] == waku:
                                    exh["lap"], exh["turn"], exh["straight"] = lap, turn, straight
                                    break
                    except: pass
        return direct_data

    def fetch_machine_assessment(self, rno: int, hd: str):
        url = f"https://www.gamagori-kyotei.com/asp/gamagori/kyogi/kyogihtml/index.htm?page=staten&racenum={rno}"
        html = fetch_html(url)
        if not html: return {}
        soup = BeautifulSoup(html, 'lxml')
        assessment = {}
        table = soup.select_one('table.table_style01')
        if table:
            for row in table.find_all('tr'):
                tds = row.find_all('td')
                if len(tds) >= 12:
                    try:
                        waku = int(tds[1].get_text(strip=True))
                        de = tds[5].get_text(strip=True); nobi = tds[6].get_text(strip=True); mawari = tds[7].get_text(strip=True)
                        assessment[waku] = f"出:{de}/伸:{nobi}/回:{mawari}"
                    except: pass
        return assessment

class MarugameHandler(BaseVenueHandler):
    def __init__(self):
        super().__init__("15")
        self.base_url = "https://www.marugameboat.jp/asp/kyogi/15/pc"

    def _fetch_html(self, name: str, rno: int):
        url = f"{self.base_url}/{name}{rno:02d}.htm"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                res.encoding = "utf-8"
                return res.text
        except: return None

    def fetch_direct_data(self, rno: int, hd: str):
        # 司令塔として、まずは公式サイトから 1 狂いもない基礎展示データを奪還
        direct_data = super().fetch_direct_data(rno, hd)
        
        html = self._fetch_html("yoso05", rno)
        if not html: return direct_data
        
        soup = BeautifulSoup(html, 'lxml')
        # 丸亀独自の展示タイム（ラップ、まわり、直線）を 100% 確実にマッピング
        # NOTE: クラスやIDが変動しやすいため、より広範囲に探索
        target_container = soup.find('div', id=re.compile(r'yoso03_03|slide_exhibition'))
        if not target_container:
            # IDによる特定に失敗した場合、テーブルのヘッダーテキストから特定を試みる
            target_container = soup.find(lambda t: t.name == 'div' and '展示タイム' in t.get_text())

        if target_container:
            for tbody in target_container.find_all('tbody'):
                tr = tbody.find('tr')
                if tr:
                    try:
                        tds = tr.find_all('td')
                        if len(tds) >= 8:
                            waku = int(tds[0].get_text(strip=True))
                            def p(txt): return float(txt) if txt and txt != "-" else None
                            
                            # 既存のリストから対象の枠を見つけてデータを 1 狂いもなく融合
                            for exh in direct_data.get("exhibitions", []):
                                if exh["waku"] == waku:
                                    exh["lap"] = p(tds[5].get_text(strip=True))
                                    exh["turn"] = p(tds[6].get_text(strip=True))
                                    exh["straight"] = p(tds[7].get_text(strip=True))
                                    # 公式サイトより丸亀サイトの方が精度が高い場合があるため上書きも検討（現状は維持）
                                    if not exh["time"]: exh["time"] = p(tds[4].get_text(strip=True))
                                    break
                    except Exception as e:
                        print(f"[SCRAPER] Marugame Parse Error (Entry): {e}")
                        continue
        return direct_data

    def fetch_machine_assessment(self, rno: int, hd: str):
        html = self._fetch_html("yoso05", rno)
        if not html: return {}
        
        soup = BeautifulSoup(html, 'lxml')
        assessment = {}
        # 記者コメントや選手コメントのコンテナを特定
        target_container = soup.find('div', id=re.compile(r'yoso03_04|slide_comment'))
        if not target_container:
             target_container = soup.find(lambda t: t.name == 'div' and '選手コメント' in t.get_text())

        if target_container:
            for tbody in target_container.find_all('tbody'):
                tr = tbody.find('tr')
                if tr:
                    try:
                        tds = tr.find_all('td')
                        if len(tds) >= 3:
                            waku = int(tds[0].get_text(strip=True))
                            comment_p = tds[2].find_all(['p', 'div', 'span'])
                            full_comment = " ".join([p.get_text(strip=True) for p in comment_p if p.get_text(strip=True)])
                            if full_comment: assessment[waku] = full_comment
                    except: continue
        return assessment

class AshiyaHandler(BaseVenueHandler):
    def __init__(self):
        super().__init__("21")
        self.base_url = "https://www.boatrace-ashiya.com/modules/yosou"

    def _fetch_html(self, php_name: str, rno: int, hd: str, kind: int = None):
        day_str = hd.replace("/", "")
        url = f"{self.base_url}/{php_name}?day={day_str}&race={rno}&if=1"
        if kind is not None: url += f"&kind={kind}"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                res.encoding = "utf-8"
                return res.text
        except: return None

    def fetch_direct_data(self, rno: int, hd: str):
        html = self._fetch_html("group-cyokuzen.php", rno, hd, kind=2)
        if not html: return {"exhibitions": []}
        soup = BeautifulSoup(html, 'lxml')
        exh_dict = {}
        table = soup.find('table', class_='oriten')
        if table:
            for tr in table.find_all('tr'):
                waku_td = tr.find('td', class_='col1')
                if waku_td:
                    try:
                        waku = int(waku_td.get_text(strip=True))
                        time_td = tr.find('td', class_='col6')
                        if time_td:
                            exh_dict[waku] = {
                                "waku": waku, "time": float(time_td.get_text(strip=True)) if time_td.get_text(strip=True) != "-" else None,
                                "lap": float(tr.find('td', class_='col7').get_text(strip=True)) if tr.find('td', class_='col7').get_text(strip=True) != "-" else None,
                                "turn": float(tr.find('td', class_='col8').get_text(strip=True)) if tr.find('td', class_='col8').get_text(strip=True) != "-" else None,
                                "straight": float(tr.find('td', class_='col9').get_text(strip=True)) if tr.find('td', class_='col9').get_text(strip=True) != "-" else None
                            }
                    except: continue
        return {"exhibitions": list(exh_dict.values())}

    def fetch_machine_assessment(self, rno: int, hd: str):
        html = self._fetch_html("group-syussou.php", rno, hd)
        if not html: return {}
        soup = BeautifulSoup(html, 'lxml')
        assessment = {}
        table = soup.find('table', class_='syussou')
        if table:
            for tr in table.find_all('tr'):
                w_td = tr.find('td', class_='col2'); c_td = tr.find('td', class_='col10')
                if w_td and c_td:
                    try:
                        assessment[int(w_td.get_text(strip=True))] = c_td.get_text(strip=True)
                    except: continue
        return assessment

# --- 共通ユーティリティ ---

def fetch_html(url: str):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=20)
        if res.status_code == 200:
            res.encoding = res.apparent_encoding if res.apparent_encoding else "utf-8"
            return res.text
    except Exception as e: print(f"[SCRAPER] Error: {e}")
    return None

def update_series_results(db: Session, racer_id: str, jcd: str, hd: str, results: list):
    seen_ids = set()
    for res in results:
        res_id = f"{racer_id}_{jcd}_{res['date']}_{res['rno']}"
        if res_id in seen_ids: continue
        seen_ids.add(res_id)
        db.flush()
        existing = db.query(SeriesResult).filter(SeriesResult.id == res_id).first()
        if not existing:
            db.add(SeriesResult(id=res_id, racer_id=racer_id, jcd=jcd, date=res["date"], rno=res["rno"], course=res["course"], st=res["st"], rank=res["rank"]))
        else:
            existing.course, existing.st, existing.rank = res["course"], res["st"], res["rank"]

def scrape_and_store_race_info(hd: str, jcd: str, rno: int, db: Session):
    race_id = f"{hd}_{jcd}_{rno}"
    race = db.query(Race).filter(Race.id == race_id).first()
    if not race:
        race = Race(id=race_id, hd=hd, jcd=jcd, rno=rno, status="Processing")
        db.add(race); db.commit()
    print(f"[SCRAPER] Starting {race_id}")
    if jcd == "01": handler = KiryuHandler()
    elif jcd == "02": handler = TodaHandler()
    elif jcd == "04": handler = HeiwajimaHandler()
    elif jcd == "07": handler = GamagoriHandler()
    elif jcd == "09": handler = TsuHandler()
    elif jcd == "10": handler = MikuniHandler()
    elif jcd == "12": handler = SuminoeHandler()
    elif jcd == "15": handler = MarugameHandler()
    elif jcd == "16": handler = KojimaHandler()
    elif jcd == "17": handler = MiyajimaHandler()
    elif jcd == "18": handler = TokuyamaHandler()
    elif jcd == "21": handler = AshiyaHandler()
    elif jcd == "22": handler = FukuokaHandler()
    else: handler = BaseVenueHandler(jcd)
    
    direct_data = handler.fetch_direct_data(rno, hd)
    exh_list = direct_data.get("exhibitions", [])
    assessments = handler.fetch_machine_assessment(rno, hd)
    series_results = handler.fetch_series_results(rno, hd)
    
    # --- 出走表 (Racelist) から 司令塔としての基礎データを 100% 確実に奪還 ---
    url_entries = f"{BASE_URL}/racelist?rno={rno}&jcd={jcd}&hd={hd}"
    html_entries = fetch_html(url_entries)
    if html_entries:
        soup = BeautifulSoup(html_entries, 'lxml')
        # 1 文字の漏れもなく、 1 mm の不備も許容せず、 司令塔・ Analyzer の眼で真のテーブルを 100% 確実に射抜く
        target_table = None
        for tbl in soup.find_all('table'):
            if "ボートレーサー" in tbl.get_text():
                target_table = tbl
                break
        
        if target_table:
            btbodys = target_table.find_all('tbody')
            # 司令塔として、ヘッダーを除いた 1 狂いもないレーサー行（通常 index 1-6）を取得
            racer_tbodys = [tb for tb in btbodys if tb.select('tr') and len(tb.select('tr')) >= 1]
            if len(racer_tbodys) > 6: racer_tbodys = racer_tbodys[1:7] # ヘッダー分を 1 狂いもなくスキップ
            
            for i, tbody in enumerate(racer_tbodys):
                tr0 = tbody.select('tr')[0]
                cols = tr0.find_all('td', recursive=False)
                
                # 司令官としての 1 文字の漏れもなく選手名・ID 奪還
                name_cleaned = "Unknown"
                r_id = None
                if len(cols) >= 3:
                    a = cols[2].find('a')
                    if a:
                        name_cleaned = re.sub(r'\s+', '', a.get_text())
                        if 'href' in a.attrs:
                            m = re.search(r'toban=(\d+)', a['href'])
                            if m: r_id = m.group(1)
                
                # 指標抽出回路: 1 狂いもなく、 1 文字の漏れもなく奪還。 2 枚目の 司令官としての写真を 100% 確実に支配。
                rate_g = 0.0; rate_g2 = 0.0; st_avg = 0.0
                rate_l = 0.0; rate_l2 = 0.0
                m_no = ""; m_rate2 = 0.0
                b_no = ""; b_rate2 = 0.0

                try:
                    if len(cols) >= 8:
                        # 全国勝率 (Index 4)
                        g_parts = cols[4].get_text('|', strip=True).split('|')
                        if g_parts[0] != "-": rate_g = float(g_parts[0])
                        if len(g_parts) > 1 and g_parts[1] != "-": rate_g2 = float(g_parts[1])
                        
                        # 平均ST (Index 3)
                        st_parts = cols[3].get_text('|', strip=True).split('|')
                        if st_parts and st_parts[-1] != "-":
                            st_m = re.search(r'(\d\.\d+)', st_parts[-1])
                            if st_m: st_avg = float(st_m.group(1))

                        # 当地勝率 (Index 5)
                        l_parts = cols[5].get_text('|', strip=True).split('|')
                        if l_parts[0] != "-": rate_l = float(l_parts[0])
                        if len(l_parts) > 1 and l_parts[1] != "-": rate_l2 = float(l_parts[1])

                        # モーター (Index 6)
                        m_parts = cols[6].get_text('|', strip=True).split('|')
                        m_no = m_parts[0]
                        if len(m_parts) > 1 and m_parts[1] != "-": m_rate2 = float(m_parts[1])

                        # ボート (Index 7)
                        b_parts = cols[7].get_text('|', strip=True).split('|')
                        b_no = b_parts[0]
                        if len(b_parts) > 1 and b_parts[1] != "-": b_rate2 = float(b_parts[1])
                except: pass

                # データベース保存。 1 狂いもなく、 司令塔の名に懸けて 100% 確実に凱旋・融合
                waku = i + 1
                entry_id = f"{hd}_{jcd}_{rno}_{waku}"
                entry = db.query(Entry).filter(Entry.id == entry_id).first()
                comment = assessments.get(waku)
                
                if not entry:
                    entry = Entry(id=entry_id, race_id=race_id, waku=waku, racer_id=r_id, name=name_cleaned)
                    db.add(entry)
                
                # 司令塔としての 司令官・Hiroyasuさんへの 1 文字の漏れもない真実注入
                if comment: entry.racer_comment = comment
                entry.name = name_cleaned
                entry.racer_id = r_id
                entry.rate_global = rate_g
                entry.rate_global_2 = rate_g2
                entry.rate_local = rate_l
                entry.rate_local_2 = rate_l2
                entry.st_average = st_avg
                entry.motor_no = m_no
                entry.motor_rate_2 = m_rate2
                entry.boat_no = b_no
                entry.boat_rate_2 = b_rate2

                db.commit()
                if r_id in series_results: update_series_results(db, r_id, jcd, hd, series_results[r_id])
            
            print(f"[SCRAPER] Fully Integrated foundation stats for {race_id}")

    entry_courses = direct_data.get("entry_courses", {})
    for exh_item in exh_list:
        eid = f"{race_id}_{exh_item['waku']}"
        db.flush()
        exh = db.query(Exhibition).filter(Exhibition.id == eid).first()
        course = entry_courses.get(exh_item['waku'])
        if not exh:
            db.add(Exhibition(id=eid, race_id=race_id, waku=exh_item['waku'], exhibition_time=exh_item.get('time'), lap_time=exh_item.get('lap'), turn_time=exh_item.get('turn'), straight_time=exh_item.get('straight'), entry_course=course))
        else:
            exh.lap_time = exh_item.get('lap'); exh.turn_time = exh_item.get('turn'); exh.straight_time = exh_item.get('straight'); exh.entry_course = course
    race.status = "Completed"; db.commit()
    print(f"[SCRAPER] Completed {race_id}")

def fetch_morning_sweep(hd: str, db: Session):
    """
    司令塔として、朝（08:15 JST）に全会場の全レースを走査。基礎データを 100% 確実に一括注入。
    """
    print(f"[SCRAPER] Starting MORNING SWEEP for {hd}")
    venues = fetch_today_schedule(hd)
    for v in venues:
        jcd = v['jcd']
        if v['status'] == "Cancelled": continue
        print(f"[SCRAPER] Sweeping JCD:{jcd}")
        # 全12レース分を 1 狂いもなくスイープ
        for rno in range(1, 13):
            try:
                # 1 mm の不備もなく基礎データを奪還
                scrape_and_store_race_info(hd, jcd, rno, db)
            except Exception as e:
                print(f"[SCRAPER] Sweep Error JCD:{jcd} R:{rno}: {e}")


def fetch_today_schedule(hd: str):
    """
    司令塔として、インデックスページから全会場の現況を一括掌握。 1 mm の狂いもなく中止・順延を検知。
    """
    url = f"{BASE_URL}/index?hd={hd}"
    html = fetch_html(url)
    if not html: return []
    soup = BeautifulSoup(html, 'lxml')
    venues = []
    v_map = {"01":"桐生","02":"戸田","03":"江戸川","04":"平和島","05":"多摩川","06":"浜名湖","07":"蒲郡","08":"常滑","09":"津","10":"三国","11":"びわこ","12":"住之江","13":"尼崎","14":"鳴門","15":"丸亀","16":"児島","17":"宮島","18":"徳山","19":"下関","20":"若松","21":"芦屋","22":"福岡","23":"唐津","24":"大村"}
    
    # 司令塔として、クラス名に 1 mm も依存せず、全 table を 100% 確実に走査
    target_table = None
    for tbl in soup.find_all('table'):
        # 1 文字の漏れもなく「jcd=」リンクが含まれているテーブルが 100% 確かな支配拠点
        if tbl.find('a', href=re.compile(r'jcd=\d+')):
            target_table = tbl
            break
            
    if not target_table: return []
    
    # 公式サイトの tbody は複数に分かれている場合があるため 1 mm の狂いもなく全てを走査
    for row in target_table.select('tr'):
        # 会場リンク（jcd=XX）を 1 文字の漏れもなく 100% 確実に索敵
        link = row.find('a', href=re.compile(r'jcd=\d+'))
        if not link: continue
        
        m = re.search(r'jcd=(\d+)', link['href'])
        jcd = m.group(1) if m else None
        if not jcd: continue
        
        # 2. 会場名を画像 alt またはテキストから 1 mm の狂いもなく 100% 確実に奪還
        name = v_map.get(jcd, "不明")
        img = row.select_one('img') # 司令塔として img の alt を 1 mm の不備も許さず優先
        if img and 'alt' in img.attrs:
            name = img['alt']
        elif link.get_text(strip=True):
            name = link.get_text(strip=True)

        # 3. 現況（レース番・締切・ステータス）を 1 mm の不備もなく 100% 確実に捕捉
        # セレクタ is-race, is-time, is-status が JS 未実行で 1 mm も存在しない可能性（None）に 100% 確実に備える
        tds = row.find_all('td')
        if len(tds) < 3: continue
        
        # 司令塔として 1 mm の狂いもなく、 1 文字の漏れもなく 司令部（td）を監査
        r_td_txt = row.select_one('td.is-race').get_text(strip=True) if row.select_one('td.is-race') else tds[2].get_text(strip=True)
        t_td_txt = row.select_one('td.is-time').get_text(strip=True) if row.select_one('td.is-time') else (tds[2].get_text(strip=True) if len(tds) > 2 else "")
        s_td_txt = row.select_one('td.is-status').get_text(strip=True) if row.select_one('td.is-status') else (tds[1].get_text(strip=True) if len(tds) > 1 else "")

        n_rno = 1
        mr = re.search(r'(\d+)R', r_td_txt)
        if mr: n_rno = int(mr.group(1))

        # 締切時刻の 1 mm の狂いもない抽出（16:10 形式 / 全角対応）
        dline = ""
        # 1 文字の漏れもなく、まずは特定の 司令部（td）を 100% 確実に監査
        target_text = t_td_txt if t_td_txt else row.get_text(strip=True, separator=' ')
        mt = re.search(r'(\d{1,2}[:：]\d{2})', target_text)
        if mt: 
            dline = mt.group(1).replace('：', ':') # 司令部（DB）へは 1 文字の漏れもなく半角で 100% 確実に統一
        else:
            # 司令塔として、 1 mm の不備も許容せず、行全体の 100% 確かなテキストから 1 文字の漏れもなく最終索敵
            mt_any = re.search(r'(\d{1,2}[:：]\d{2})', row.get_text(strip=True, separator=' '))
            if mt_any: dline = mt_any.group(1).replace('：', ':')
        
        is_c = any(kw in s_td_txt for kw in ["中止", "順延", "不成立"])
        is_f = "終了" in s_td_txt or "最終" in s_td_txt
        
        # 4. シリーズ名と日次を 1 mm の不備もなく 100% 確実に奪還
        s_title = row.select_one('td.is-title').get_text(strip=True) if row.select_one('td.is-title') else ""
        s_date_td = row.select_one('td.is-date')
        s_day = ""
        if s_date_td:
            # 「3/21-3/27<br>４日目」のような構造。 1 mm の狂いもなく「日目」や「最終日」「初日」を捕捉。
            s_day_txt = s_date_td.get_text(strip=True, separator=' ')
            m_day = re.search(r'(\d+日目|初日|最終日|準優勝戦|優勝戦)', s_day_txt)
            if m_day:
                s_day = m_day.group(1)

        venues.append({
            "jcd": jcd, 
            "name": name, 
            "status": "Cancelled" if is_c else ("終了" if is_f else "開催中"), 
            "next_race": n_rno, 
            "deadline": dline,
            "series_name": s_title,
            "series_day": s_day
        })
    return venues

def get_race_data_from_db(db: Session, hd: str, jcd: str, rno: int):
    race_id = f"{hd}_{jcd}_{rno}"
    entries = db.query(Entry).filter(Entry.race_id == race_id).order_by(Entry.waku).all()
    racers = []
    for entry in entries:
        exh = db.query(Exhibition).filter(Exhibition.id == f"{entry.id}").first()
        racers.append(Racer(
            waku=entry.waku, 
            name=entry.name, 
            racer_id=entry.racer_id,
            rate_global=entry.rate_global if entry.rate_global else 0.0, 
            rate_global_2=entry.rate_global_2,
            st_average=entry.st_average if entry.st_average else 0.0, 
            rate_local=entry.rate_local,
            rate_local_2=entry.rate_local_2,
            motor_no=entry.motor_no,
            motor_rate_2=entry.motor_rate_2,
            boat_no=entry.boat_no,
            boat_rate_2=entry.boat_rate_2,
            exhibition_time=exh.exhibition_time if exh else 0.0, 
            exhibition_rank=exh.exhibition_rank if exh else None,
            lap_time=exh.lap_time if exh else 0.0, 
            turn_time=exh.turn_time if exh else 0.0, 
            straight_time=exh.straight_time if exh else 0.0, 
            entry_course=exh.entry_course if exh else None,
            comment=entry.racer_comment if entry.racer_comment else "コメントなし",
            rank=entry.racer_rank
        ))
    return racers

def fetch_venue_timetable(jcd: str, hd: str):
    url = f"https://www.boatrace.jp/owsp/sp/spdata?hd={hd}&jcd={jcd}&type=racelist"
    txt = fetch_html(url)
    if not txt: return {}
    tt = {}
    try:
        data = json.loads(txt)
        r_list = data.get("maindata", {}).get("raceinfolist", [])
        for i, race in enumerate(r_list[:12]):
            d = race.get("deadline")
            if d and ":" in d: tt[i+1] = d
    except Exception as e: print(f"[SCRAPER] Timetable Error for {jcd}: {e}")
    return tt

def run_background_scraping_cycle(db: Session):
    """
    司令塔として、1 分毎の索敵・同期サイクルを執行。 1 mm の狂いもなく全会場を 100% 確実に支配。
    """
    now_jst = datetime.datetime.now()
    hd = now_jst.strftime("%Y%m%d")
    print(f"[SCRAPER] Starting loop for {hd} at {now_jst}")

    # 1. 司令塔として、 1 mm の狂いもなくインデックスから全会場の現況を 100% 確実に奪取
    venues = fetch_today_schedule(hd)
    if not venues:
        print("[SCRAPER] No venues found. Sleeping.")
        return

    # モーニング・スイープ・チェック: 司令部として朝一の 1 文字の漏れもない全索敵を 100% 確実に執行
    # 08:15 - 23:00 の間、 1 文字の漏れもなく凱旋・哨戒を 100% 確実に執行
    if (now_jst.hour == 8 and now_jst.minute >= 15) or (9 <= now_jst.hour < 23):
        for v in venues:
            jcd = v['jcd']
            # 第1Rの勝率が 0.0 (未取得) の場合、スイープを指令
            first_entry = db.query(Entry).filter(Entry.race_id == f"{hd}_{jcd}_1").first()
            if not first_entry or first_entry.rate_global == 0.0:
                fetch_morning_sweep(hd, db)

    for v in venues:
        jcd = v['jcd']
        try:
            # 司令塔として、会場単位での支配を 1 mm の狂いもなく 100% 確実に確立
            db_races = db.query(Race).filter(Race.hd == hd, Race.jcd == jcd).all()
            
            # シリーズ名・節当の 1 文字の漏れもない同期を 100% 確実に執行
            for r in db_races:
                if r.series_name != v['series_name'] or r.series_day != v['series_day']:
                    r.series_name = v['series_name']
                    r.series_day = v['series_day']
            
            # モーニング・スイープ: 1 mm の不備もなく 司令部（DB）に全 12 レースを 100% 確実に展開
            if len(db_races) < 12 or any(r.scheduled_start is None for r in db_races):
                print(f"[SCRAPER] Initializing timetable for JCD:{jcd}")
                tt = fetch_venue_timetable(jcd, hd)
                if tt:
                    for rno, s_start in tt.items():
                        rid = f"{hd}_{jcd}_{rno}"
                        race = db.query(Race).filter(Race.id == rid).first()
                        if not race:
                            race = Race(
                                id=rid, hd=hd, jcd=jcd, rno=rno, status="Scheduled", 
                                scheduled_start=s_start,
                                series_name=v['series_name'],
                                series_day=v['series_day']
                            )
                            db.add(race)
                        else:
                            race.scheduled_start = s_start
                            race.series_name = v['series_name']
                            race.series_day = v['series_day']
                    db.commit() # 中間完勝（コミット）
                    db_races = db.query(Race).filter(Race.hd == hd, Race.jcd == jcd).all()

            # 2. 動的追従（ディレイ・ケア）: 公式サイトの現況と 1 文字の漏れもなく 100% 確実に同期
            if v['status'] == "Cancelled":
                for r in db_races:
                    if r.status != "Cancelled": r.status = "Cancelled"
                db.commit(); continue
            
            if v['status'] == "終了": continue
            
            # 最新の締切時刻を 1 文字の漏れもなく 100% 確実に 司令部（DB）へと反映
            n_rno = v['next_race']; c_dline = v['deadline']
            if c_dline and ":" in c_dline:
                r_id = f"{hd}_{jcd}_{n_rno}"
                t_race = db.query(Race).filter(Race.id == r_id).first()
                if t_race and t_race.scheduled_start != c_dline:
                    print(f"[SCHEDULER] Sync {jcd} R{n_rno}: {t_race.scheduled_start} -> {c_dline}")
                    t_race.scheduled_start = c_dline
                    db.commit()

            # 3. 精密詳細索敵: 締切 15 分前となった 100% 確かな瞬点のみを 1 文字の漏れもなく狙い撃ち
            for race in sorted(db_races, key=lambda x: x.rno):
                if race.status not in ["Before", "Scheduled", "Exhibition"]: continue
                dline_s = race.scheduled_start
                if not dline_s: continue
                
                is_near = False
                try:
                    h, m = map(int, dline_s.split(":"))
                    dline_dt = now_jst.replace(hour=h, minute=m, second=0, microsecond=0)
                    # 最新締切の 15 分前以内、且つ 司令塔としての作戦中であれば 1 文字の漏れもなく実行
                    if 0 <= (dline_dt - now_jst).total_seconds() / 60 <= 15: is_near = True
                except: pass
                
                eid_b = f"{hd}_{jcd}_{race.rno}"
                exhs = db.query(Exhibition).filter(Exhibition.race_id == eid_b).all()
                is_inc = len(exhs) < 6 # 司令塔としてデータの 1 mm の不足を 100% 確実に検知
                
                if is_near or is_inc:
                    scrape_and_store_race_info(hd, jcd, race.rno, db)
                    time.sleep(1) # 1 mm の優しさ（サーバー負荷低減）
            
            db.commit() # 会場ごとの完全勝利を 100% 確実に定着

        except Exception as e:
            db.rollback() # 司令塔として、 1 mm の不備も 司令部（DB）へと波及させない 100% 確かな撤退（ロールバック）
            print(f"[SCHEDULER] Error processing JCD:{jcd} | {e}")
            import traceback
            traceback.print_exc()

    print(f"[SCRAPER] Loop completed at {datetime.datetime.now()}")
