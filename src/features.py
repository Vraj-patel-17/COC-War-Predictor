import json
import sqlite3
import pandas as pd


def side_stats(members):
    ths = sorted((m["townhallLevel"] for m in members), reverse=True)
    return {
        "th_avg": sum(ths) / len(ths),
        "th_max": ths[0],
        "th_min": ths[-1],
        "th_sum": sum(ths),
        "top10_avg": sum(ths[:10]) / len(ths[:10]),
    }


def matchup_counts(members_a, members_b):
    a = {m["mapPosition"]: m["townhallLevel"] for m in members_a}
    b = {m["mapPosition"]: m["townhallLevel"] for m in members_b}
    positions = set(a) & set(b)
    a_higher = sum(a[p] > b[p] for p in positions)
    b_higher = sum(a[p] < b[p] for p in positions)
    return a_higher, b_higher


def get_label(a, b):
    if a["stars"] != b["stars"]:
        return int(a["stars"] > b["stars"])
    if a["destructionPercentage"] != b["destructionPercentage"]:
        return int(a["destructionPercentage"] > b["destructionPercentage"])
    return None


def build_row(war_key, war):
    a, b = sorted([war["clan"], war["opponent"]], key=lambda c: c["tag"])
    if not a.get("members") or not b.get("members"):
        return None

    sa, sb = side_stats(a["members"]), side_stats(b["members"])
    a_higher, b_higher = matchup_counts(a["members"], b["members"])

    row = {
        "war_key": war_key,
        "team_size": war["teamSize"],
        "clan_level_diff": a["clanLevel"] - b["clanLevel"],
        "matchup_a_higher": a_higher,
        "matchup_b_higher": b_higher,
        "matchup_diff": a_higher - b_higher,
    }
    for k in sa:
        row[f"{k}_diff"] = sa[k] - sb[k]

    if war["state"] == "warEnded":
        row["label"] = get_label(a, b)
    else:
        row["label"] = None
    return row


if __name__ == "__main__":
    db = sqlite3.connect("data/wars.db")
    rows = []
    for war_key, snapshot in db.execute("SELECT war_key, snapshot FROM wars"):
        row = build_row(war_key, json.loads(snapshot))
        if row:
            rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv("data/features.csv", index=False)

    labeled = df["label"].notna().sum()
    print(f"{len(df)} wars processed, {labeled} labeled (warEnded)")
    print(df.head())