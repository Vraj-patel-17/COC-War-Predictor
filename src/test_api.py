import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ["COC_API_KEY"].strip()
BASE = os.getenv("COC_BASE_URL", "https://api.clashofclans.com/v1")
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

print("Using base URL:", BASE)

r = requests.get(f"{BASE}/locations", headers=HEADERS, params={"limit": 1}, timeout=10)

print("Status:", r.status_code)
print(r.json())