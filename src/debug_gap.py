import json
import sqlite3

import pandas as pd

p1 = pd.read_csv("data/features.csv").set_index("war_key")
p2 = pd.read_csv("data/features_players.csv").set_index("war_key")

db = sqlite3.connect("data/wars.db")
stored = dict(db.execute("SELECT war_key, COUNT(*) FROM players GROUP BY war_key"))

counts = {
    "ended + complete (check_players rule)": 0,
    "...in features.csv": 0,
    "...with a label": 0,
    "...in features_players.csv": 0,
}
examples = []

for war_key, state, snapshot in db.execute("SELECT war_key, state, snapshot FROM wars"):
    if state != "warEnded" or war_key not in stored:
        continue
    war = json.loads(snapshot)
    needed = len(war["clan"]["members"]) + len(war["opponent"]["members"])
    if stored[war_key] < needed:
        continue
    counts["ended + complete (check_players rule)"] += 1
    in1 = war_key in p1.index
    labeled = bool(in1 and pd.notna(p1.loc[war_key, "label"]))
    in2 = war_key in p2.index
    counts["...in features.csv"] += in1
    counts["...with a label"] += labeled
    counts["...in features_players.csv"] += in2
    if not (labeled and in2) and len(examples) < 5:
        examples.append((war_key, in1, labeled, in2, stored[war_key], needed))

for k, v in counts.items():
    print(f"{k}: {v}")
print("\nDropped examples (key, in_features, labeled, in_players_csv, stored, needed):")
for e in examples:
    print(e)