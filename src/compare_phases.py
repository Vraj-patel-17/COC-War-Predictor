import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

MIN_WARS = 60

p1 = pd.read_csv("data/features.csv")
p2 = pd.read_csv("data/features_players.csv")

df = p1.merge(p2, on="war_key")
df = df[df["label"].notna()].copy()

if len(df) < MIN_WARS:
    print(f"Only {len(df)} usable wars, need at least {MIN_WARS}. Collect more first.")
    raise SystemExit

df["prep_time"] = df["war_key"].str.split("_").str[-1]
df = df.sort_values("prep_time").reset_index(drop=True)
y = df["label"].astype(int).values

TH = ["th_sum_diff"]
PLAYER = ["hero_sum_diff", "hero_frac_diff", "equip_sum_diff",
          "war_stars_diff", "hero_matchup_diff"]

models = {
    "Phase 1: TH sum": TH,
    "Phase 2: player strength": PLAYER,
    "Phase 1 + Phase 2": TH + PLAYER,
}


def make_model():
    return make_pipeline(StandardScaler(), LogisticRegression(C=0.3, max_iter=1000))


probs = {name: [] for name in ["Constant (train mean)", *models]}
test_idx_all = []

for train_idx, test_idx in TimeSeriesSplit(n_splits=5).split(df):
    test_idx_all.extend(test_idx)
    probs["Constant (train mean)"].extend([y[train_idx].mean()] * len(test_idx))
    for name, cols in models.items():
        m = make_model().fit(df.iloc[train_idx][cols], y[train_idx])
        probs[name].extend(m.predict_proba(df.iloc[test_idx][cols])[:, 1])

y_test = y[test_idx_all]
n = len(y_test)
print(f"Usable wars: {len(df)} | tested on {n} | share where clan A wins: {y.mean():.2f}\n")


def per_war_logloss(p):
    p = np.clip(np.array(p), 1e-6, 1 - 1e-6)
    return -(y_test * np.log(p) + (1 - y_test) * np.log(1 - p))


losses = {}
for name, p in probs.items():
    p = np.array(p)
    acc = ((p > 0.5).astype(int) == y_test).mean()
    losses[name] = per_war_logloss(p)
    print(f"{name:<26} acc={acc:.3f} (±{np.sqrt(acc * (1 - acc) / n):.3f})  "
          f"logloss={losses[name].mean():.3f}")

print("\nLog loss improvement over Phase 1 (positive = better), mean ± std. error:")
for name in ("Phase 2: player strength", "Phase 1 + Phase 2"):
    d = losses["Phase 1: TH sum"] - losses[name]
    print(f"{name:<26} {d.mean():+.4f} ± {d.std(ddof=1) / np.sqrt(n):.4f}")