import requests
import json

def debug_spdata_json():
    jcd = "01"
    hd = "20260405"
    # ブラウザ解析で見つかった真のエンドポイント
    url = f"https://www.boatrace.jp/owsp/sp/spdata?hd={hd}&jcd={jcd}&type=racelist"
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"https://www.boatrace.jp/owsp/sp/race/raceindex?jcd={jcd}&hd={hd}"
    }
    
    print(f"--- Debug spdata JSON Fetch for {jcd} ---")
    res = requests.get(url, headers=headers, timeout=20)
    print(f"Status: {res.status_code}")
    
    try:
        data = res.json()
        print("Success! JSON parsed.")
        # 特定のパス: maindata.raceinfolist
        race_info_list = data.get("maindata", {}).get("raceinfolist", [])
        print(f"Found {len(race_info_list)} races.")
        for i, race in enumerate(race_info_list):
            rno = i + 1
            deadline = race.get("deadline")
            racename = race.get("racename", "").strip()
            print(f"  R{rno:02d} ({racename}): {deadline}")
    except Exception as e:
        print(f"Failed to parse JSON: {e}")
        print("--- RAW Response (2000 chars) ---")
        print(res.text[:2000])

if __name__ == "__main__":
    debug_spdata_json()
