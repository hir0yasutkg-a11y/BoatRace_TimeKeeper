import requests
import json

def verify():
    url = "http://127.0.0.1:8000/api/prediction/20260331/15/10"
    print(f"Requesting: {url}")
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            data = r.json()
            print("Successfully fetched data!")
            print(f"Race: Marugame 10R ({data.get('date')})")
            for racer in data.get('racers', []):
                print(f"Waku {racer['waku']}: {racer['name']}")
                print(f"  Rate: {racer['rate_global']}, ST: {racer['st_average']}")
                print(f"  Lap: {racer['lap_time']}, Turn: {racer['turn_time']}, Straight: {racer['straight_time']}")
                print(f"  Comment: {racer['comment']}")
                print("-" * 20)
        else:
            print(f"Error: Status code {r.status_code}")
            print(r.text)
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    verify()
