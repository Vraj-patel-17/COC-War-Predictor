import json
import sqlite3

db = sqlite3.connect("data/wars.db")
row = db.execute("SELECT war_key, state, snapshot FROM wars LIMIT 1").fetchone()

if row is None:
    print("No wars saved yet")
else:
    key, state, snapshot = row
    war = json.loads(snapshot)
    print("Key:", key, "| State:", state)
    print("Top-level fields:", list(war.keys()))
    print("Clan fields:", list(war["clan"].keys()))
    print("First member:", json.dumps(war["clan"]["members"][0], indent=2))