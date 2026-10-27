import json
import sqlite3
from collections import defaultdict

import pandas as pd

FEATURES = ("hero_sum", "hero_frac", "equip_sum", "war_stars")


def player_strength(data):
    heroes = data.get("heroes") or {}
    levels = [h[0] for h in heroes.values()]
    fracs = [h[0] / h[1] for h in heroes.values() if h[1]]
    return {
        "hero_sum": sum(levels),  # raw hero strength
        "hero_frac": sum(fracs) / len(fracs) if fracs else 0.0,  # how maxed for their TH
        "equip_sum": sum(h[2] for h in heroes.values() if len(h) > 2),
        "war_stars": data.get("war_stars") or 0,  # lifetime war experience
    }


def side_rows(members, players):
    # None if any member is missing player data (incomplete war)
    rows = []
    for m in members:
        data = players.get(m["tag"])
        if data is None:
            return None
        s = player_strength(data)
        s["pos"] = m["mapPosition"]
        rows.append(s)
    return rows


def mean(rows, key):
    return sum(r[key] for r in rows) / len(rows)


def build_row(war_key, war, players):
    # Same A/B ordering as features.py, so labels line up
    a, b = sorted([war["clan"], war["opponent"]], key=lambda c: c["tag"])
    sa = side_rows(a.get("members", []), players)
    sb = side_rows(b.get("members", []), players)
    if not sa or not sb:
        return None

    row = {"war_key": war_key}
    for k in FEATURES:
        row[f"{k}_diff"] = mean(sa, k) - mean(sb, k)

    # Map-position matchups by hero strength (who attacks whom)
    pa = {r["pos"]: r["hero_sum"] for r in sa}
    pb = {r["pos"]: r["hero_sum"] for r in sb}
    common = set(pa) & set(pb)
    row["hero_matchup_diff"] = (
        sum(pa[p] > pb[p] for p in common) - sum(pa[p] < pb[p] for p in common)
    )
    return row


if __name__ == "__main__":
    db = sqlite3.connect("data/wars.db")

    players_by_war = defaultdict(dict)
    for war_key, tag, data in db.execute(
        "SELECT war_key, player_tag, data FROM players"
    ):
        players_by_war[war_key][tag] = json.loads(data)

    rows = []
    for war_key, snapshot in db.execute("SELECT war_key, snapshot FROM wars"):
        if war_key not in players_by_war:
            continue
        row = build_row(war_key, json.loads(snapshot), players_by_war[war_key])
        if row:
            rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv("data/features_players.csv", index=False)
    print(f"{len(df)} wars with complete player data")
    print(df.head())