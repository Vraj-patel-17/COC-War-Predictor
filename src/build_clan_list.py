import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ["COC_API_KEY"].strip()
BASE = os.getenv("COC_BASE_URL", "https://api.clashofclans.com/v1")
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

TARGET = 300
tags, after = [], None

while len(tags) < TARGET:
    params = {"warFrequency": "always", "minMembers": 30, "limit": 100}
    if after:
        params["after"] = after
    r = requests.get(f"{BASE}/clans", headers=HEADERS, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    tags += [c["tag"] for c in data["items"]]
    after = data.get("paging", {}).get("cursors", {}).get("after")
    if not after or not data["items"]:
        break

os.makedirs("data", exist_ok=True)
with open("data/clans.txt", "w") as f:
    f.write("\n".join(dict.fromkeys(tags)))

print(f"Saved {len(set(tags))} clan tags to data/clans.txt")