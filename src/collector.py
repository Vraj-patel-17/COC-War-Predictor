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
PLAYER_TIME_BUDGET = 900  

with open("data/clans.txt") as f:
    CLAN_TAGS = [line.strip() for line in f if line.strip()]

db = sqlite3.connect("data/wars.db")
db.execute("""CREATE TABLE IF NOT EXISTS wars (
    war_key TEXT PRIMARY KEY,
    state TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    snapshot TEXT)""")
db.execute("""CREATE TABLE IF NOT EXISTS players (
    war_key TEXT,
    player_tag TEXT,
    clan_tag TEXT,
    fetched_at TEXT DEFAULT CURRENT_TIMESTAMP,
    data TEXT,
    PRIMARY KEY (war_key, player_tag))""")


def get_json(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
    except requests.RequestException as e:
        print(f"request failed ({e})")
        return None
    if r.status_code == 200:
        return r.json()
    if r.status_code == 429:
        print("Rate limited, sleeping 60s")
        time.sleep(60)
    return None


def get_current_war(tag):
    return get_json(f"{BASE}/clans/{tag.replace('#', '%23')}/currentwar")


def get_player(tag):
    return get_json(f"{BASE}/players/{tag.replace('#', '%23')}")


def make_key(war):
    tags = sorted([war["clan"]["tag"], war["opponent"]["tag"]])
    return f"{tags[0]}_{tags[1]}_{war['preparationStartTime']}"


def compact_player(p):
    return {
        "th": p.get("townHallLevel"),
        "th_weapon": p.get("townHallWeaponLevel"),
        "exp": p.get("expLevel"),
        "trophies": p.get("trophies"),
        "best_trophies": p.get("bestTrophies"),
        "war_stars": p.get("warStars"),
        "attack_wins": p.get("attackWins"),
        "defense_wins": p.get("defenseWins"),
        "heroes": {
            h["name"]: [
                h["level"],
                h["maxLevel"],
                sum(e["level"] for e in h.get("equipment", [])),
            ]
            for h in p.get("heroes", [])
            if h.get("village") == "home"
        },
    }


def fetch_players(war_key, war, deadline):
    # Returns False if the time budget ran out before finishing this war
    done = {
        row[0]
        for row in db.execute(
            "SELECT player_tag FROM players WHERE war_key = ?", (war_key,)
        )
    }
    for side in (war["clan"], war["opponent"]):
        for m in side.get("members", []):
            if m["tag"] in done:
                continue
            if time.time() > deadline:
                return False
            p = get_player(m["tag"])
            if p:
                db.execute(
                    """INSERT OR IGNORE INTO players
                       (war_key, player_tag, clan_tag, data) VALUES (?, ?, ?, ?)""",
                    (war_key, m["tag"], side["tag"], json.dumps(compact_player(p))),
                )
                db.commit()
            time.sleep(0.2)
    return True


while True:
    saved = 0
    prep_wars = {}
    for i, tag in enumerate(CLAN_TAGS, 1):
        war = get_current_war(tag)
        if war and war.get("state") not in (None, "notInWar"):
            key = make_key(war)
            db.execute(
                """INSERT INTO wars (war_key, state, snapshot) VALUES (?, ?, ?)
                   ON CONFLICT(war_key) DO UPDATE SET
                     state=excluded.state,
                     updated_at=CURRENT_TIMESTAMP,
                     snapshot=excluded.snapshot""",
                (key, war["state"], json.dumps(war)),
            )
            db.commit()
            saved += 1
            if war["state"] == "preparation":
                prep_wars[key] = war
        if i % 20 == 0:
            print(f"Checked {i}/{len(CLAN_TAGS)} clans, {saved} wars found so far", flush=True)
        time.sleep(0.3)
    print(f"Cycle done, {saved} wars saved/updated.", flush=True)

    # Player data: only for wars still in preparation, so hero levels
    # match what each side had before any attack
    deadline = time.time() + PLAYER_TIME_BUDGET
    for key, war in prep_wars.items():
        if not fetch_players(key, war, deadline):
            print("Player time budget reached, rest continues next cycle", flush=True)
            break
    n = db.execute("SELECT COUNT(DISTINCT war_key) FROM players").fetchone()[0]
    print(f"Players stored for {n} wars so far", flush=True)
    row = db.execute("SELECT data FROM players ORDER BY rowid DESC LIMIT 1").fetchone()
    if row:
        print("Sample player:", row[0], flush=True)

    if os.getenv("RUN_ONCE"):
        break
    print(f"Sleeping {POLL_INTERVAL}s", flush=True)
    time.sleep(POLL_INTERVAL)