import sys
import os

# Add the backend directory to python path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from scraper import GamagoriHandler
import requests # Ensure requests is handled if imported inside scraper

handler = GamagoriHandler()
hd = "20260407"
rno = 7 # 7R is usually a good test case

print(f"Testing fetch_machine_assessment for Gamagori {rno}R...")
assessments = handler.fetch_machine_assessment(rno, hd)
for waku, comment in assessments.items():
    print(f"Waku {waku}: {comment}")

print("\nTesting fetch_direct_data for Gamagori 7R...")
direct_data = handler.fetch_direct_data(rno, hd)
for exh in direct_data.get("exhibitions", []):
    print(f"Waku {exh['waku']}: {exh.get('lap')}, {exh.get('turn')}, {exh.get('straight')}")
