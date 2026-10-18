import os
import json
import sqlite3
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ["COC_API_KEY"].strip()
BASE = os.getenv("COC_BASE_URL", "https://api.clashofclans.com/v1")
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

# Take one real player tag from a war 
db = sqlite3.connect("data/wars.db")
snapshot = db.execute("SELECT snapshot FROM wars LIMIT 1").fetchone()[0]
tag = json.loads(snapshot)["clan"]["members"][0]["tag"]
print("Player tag:", tag)

r = requests.get(f"{BASE}/players/{tag.replace('#', '%23')}", headers=HEADERS, timeout=10)
print("Status:", r.status_code)
p = r.json()

print("\nTop-level fields:", list(p.keys()))

for field in ("townHallLevel", "townhallLevel", "expLevel", "trophies",
              "bestTrophies", "warStars", "attackWins", "defenseWins"):
    print(f"{field}:", p.get(field, "<MISSING>"))

print("\nFirst hero entry:")
heroes = p.get("heroes", [])
print(json.dumps(heroes[0], indent=2) if heroes else "<no heroes>")
print("Hero names:", [h.get("name") for h in heroes])