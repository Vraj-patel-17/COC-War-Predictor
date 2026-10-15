import os
import time
import json
import sqlite3
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ["COC_API_KEY"].strip()
BASE = os.getenv("COC_BASE_URL", "https://api.clashofclans.com/v1")
HEADERS = {"Authorization": f"Bearer {API_KEY}"}
POLL_INTERVAL = 3600 

with open("data/clans.txt") as f:
    CLAN_TAGS = [line.strip() for line in f if line.strip()]

db = sqlite3.connect("data/wars.db")
db.execute("""CREATE TABLE IF NOT EXISTS wars (
    war_key TEXT PRIMARY KEY,
    state TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    snapshot TEXT)""")


def get_current_war(tag):
    url = f"{BASE}/clans/{tag.replace('#', '%23')}/currentwar"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
    except requests.RequestException as e:
        print(f"{tag}: request failed ({e})")
        return None
    if r.status_code == 200:
        return r.json()
    if r.status_code == 429:
        print("Rate limited, sleeping 60s")
        time.sleep(60)
    return None


def make_key(war):
    tags = sorted([war["clan"]["tag"], war["opponent"]["tag"]])
    return f"{tags[0]}_{tags[1]}_{war['preparationStartTime']}"


while True:
    saved = 0
    for i, tag in enumerate(CLAN_TAGS, 1):
        war = get_current_war(tag)
        if war and war.get("state") not in (None, "notInWar"):
            db.execute(
                """INSERT INTO wars (war_key, state, snapshot) VALUES (?, ?, ?)
                   ON CONFLICT(war_key) DO UPDATE SET
                     state=excluded.state,
                     updated_at=CURRENT_TIMESTAMP,
                     snapshot=excluded.snapshot""",
                (make_key(war), war["state"], json.dumps(war)),
            )
            db.commit()
            saved += 1
        if i % 20 == 0:
            print(f"Checked {i}/{len(CLAN_TAGS)} clans, {saved} wars found so far", flush=True)
        time.sleep(0.3)
    print(f"Cycle done, {saved} wars saved/updated.", flush=True)
    if os.getenv("RUN_ONCE"):
        break
    print(f"Sleeping {POLL_INTERVAL}s", flush=True)
    time.sleep(POLL_INTERVAL)