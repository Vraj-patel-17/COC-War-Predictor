import json
import sqlite3

db = sqlite3.connect("data/wars.db")

stored = dict(db.execute("SELECT war_key, COUNT(*) FROM players GROUP BY war_key"))

complete = labeled_complete = 0
for war_key, state, snapshot in db.execute("SELECT war_key, state, snapshot FROM wars"):
    if war_key not in stored:
        continue
    war = json.loads(snapshot)
    needed = len(war["clan"]["members"]) + len(war["opponent"]["members"])
    if stored[war_key] >= needed:
        complete += 1
        if state == "warEnded":
            labeled_complete += 1

print(f"Wars with some player data:      {len(stored)}")
print(f"Wars with complete player data:  {complete}")
print(f"...of which finished (labeled):  {labeled_complete}")