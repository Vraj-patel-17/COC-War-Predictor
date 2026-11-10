import numpy as np
import pandas as pd
from scipy.stats import binomtest
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

p1 = pd.read_csv("data/features.csv")
p2 = pd.read_csv("data/features_players.csv")

df = p1.merge(p2, on="war_key")
df = df[df["label"].notna()].copy()
df["prep_time"] = df["war_key"].str.split("_").str[-1]
df = df.sort_values("prep_time").reset_index(drop=True)
y = df["label"].astype(int).values

TH = ["th_sum_diff"]
PLAYER = ["hero_sum_diff", "hero_frac_diff", "equip_sum_diff",
          "war_stars_diff", "hero_matchup_diff"]


def make_model():
    return make_pipeline(StandardScaler(), LogisticRegression(C=0.3, max_iter=1000))


test_idx_all, prob1, prob2 = [], [], []
print("Per fold: n | acc P1 | acc P2 | logloss P1 | logloss P2 | AUC P2")
for k, (tr, te) in enumerate(TimeSeriesSplit(n_splits=5).split(df), 1):
    a = make_model().fit(df.iloc[tr][TH], y[tr]).predict_proba(df.iloc[te][TH])[:, 1]
    b = make_model().fit(df.iloc[tr][PLAYER], y[tr]).predict_proba(df.iloc[te][PLAYER])[:, 1]
    test_idx_all.extend(te)
    prob1.extend(a)
    prob2.extend(b)
    yt = y[te]
    auc = roc_auc_score(yt, b) if len(set(yt)) > 1 else float("nan")
    print(f"{k}: {len(te)} | {((a > 0.5) == yt).mean():.3f} | {((b > 0.5) == yt).mean():.3f} | "
          f"{log_loss(yt, a, labels=[0, 1]):.3f} | {log_loss(yt, b, labels=[0, 1]):.3f} | {auc:.3f}")

yt = y[test_idx_all]
prob1, prob2 = np.array(prob1), np.array(prob2)
right1, right2 = (prob1 > 0.5) == yt, (prob2 > 0.5) == yt
only2 = int((right2 & ~right1).sum())
only1 = int((right1 & ~right2).sum())
print(f"\nWars only Phase 2 got right: {only2} | only Phase 1 got right: {only1}")
print(f"Sign test p-value: {binomtest(only2, only2 + only1, 0.5).pvalue:.4f}")

print("\nPhase 2 calibration (bin of predicted P(A wins): count, actual A win rate):")
bins = pd.cut(prob2, [0, 0.4, 0.5, 0.6, 1.0])
print(pd.DataFrame({"bin": bins, "y": yt}).groupby("bin", observed=True)["y"].agg(["count", "mean"]))