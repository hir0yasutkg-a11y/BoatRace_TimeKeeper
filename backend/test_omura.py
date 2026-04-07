import sys
import os

# Add the backend directory to python path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from scraper import OmuraHandler
handler = OmuraHandler()

hd = "20260407"
rno = 1

print(f"Testing fetch_direct_data for Omura {rno}R...")
direct_data = handler.fetch_direct_data(rno, hd)
for exh in direct_data.get("exhibitions", []):
    print(exh)

print(f"\nTesting fetch_machine_assessment for Omura {rno}R...")
assessments = handler.fetch_machine_assessment(rno, hd)
for waku, comment in assessments.items():
    print(f"Waku {waku}: {comment}")
