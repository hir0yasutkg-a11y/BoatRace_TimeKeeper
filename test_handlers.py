import sys
import os

# add backend path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))
from scraper import GamagoriHandler, OmuraHandler

gamagori = GamagoriHandler()
omura = OmuraHandler()

print("== Gamagori 10R ==")
direct_data = gamagori.fetch_direct_data(10, '20260407')
print("Exhibitions:", direct_data.get("exhibitions"))
assessment = gamagori.fetch_machine_assessment(10, '20260407')
print("Comments:", assessment)

print("\n== Omura 10R ==")
direct_data2 = omura.fetch_direct_data(10, '20260407')
print("Exhibitions:", direct_data2.get("exhibitions"))
assessment2 = omura.fetch_machine_assessment(10, '20260407')
print("Comments:", assessment2)

