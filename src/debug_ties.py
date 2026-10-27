import json
import sqlite3

db = sqlite3.connect("data/wars.db")
total = ties = 0
rows = []

for war_key, snapshot in db.execute(
    "SELECT war_key, snapshot FROM wars WHERE state = 'warEnded'"
):
    war = json.loads(snapshot)
    a, b = sorted([war["clan"], war["opponent"]], key=lambda c: c["tag"])
    total += 1
    if (a["stars"] == b["stars"]
            and a["destructionPercentage"] == b["destructionPercentage"]):
        ties += 1
        rows.append((war_key, a["stars"], b["stars"],
                     a["destructionPercentage"], b["destructionPercentage"],
                     a["attacks"], b["attacks"], war["teamSize"]))

print(f"Ended wars: {total} | exact ties (no label): {ties}")
print("key, starsA, starsB, destA, destB, attacksA, attacksB, teamSize")
for r in rows[:10]:
    print(r)