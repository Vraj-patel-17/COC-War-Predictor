import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

MIN_LABELED = 50

df = pd.read_csv("data/features.csv")
df = df[df["label"].notna()].copy()

if len(df) < MIN_LABELED:
    print(f"Only {len(df)} labeled wars so far, need at least {MIN_LABELED}. Collect more first.")
    raise SystemExit

# Order wars by preparation start time so every test fold is newer than its training data
df["prep_time"] = df["war_key"].str.split("_").str[-1]
df = df.sort_values("prep_time").reset_index(drop=True)

features = [c for c in df.columns if c not in ("war_key", "label", "prep_time")]
X = df[features]
y = df["label"].astype(int).values

print(f"Labeled wars: {len(df)} | share where clan A wins: {y.mean():.2f}\n")

models = {
    "Logistic (TH sum only)": (
        make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)),
        ["th_sum_diff"],
    ),
    "Logistic (all features)": (
        make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)),
        features,
    ),
    "XGBoost (all features)": (
        XGBClassifier(n_estimators=200, max_depth=3, learning_rate=0.05,
                      eval_metric="logloss"),
        features,
    ),
}

oof_idx = []
probs = {name: [] for name in models}

for train_idx, test_idx in TimeSeriesSplit(n_splits=5).split(X):
    oof_idx.extend(test_idx)
    for name, (model, cols) in models.items():
        m = clone(model)
        m.fit(X.iloc[train_idx][cols], y[train_idx])
        probs[name].extend(m.predict_proba(X.iloc[test_idx][cols])[:, 1])

y_test = y[oof_idx]
n = len(y_test)
print(f"Tested on {n} wars (the first chunk is only used for training)\n")


def report(name, prob):
    prob = np.array(prob)
    pred = (prob > 0.5).astype(int)
    acc = accuracy_score(y_test, pred)
    se = np.sqrt(acc * (1 - acc) / n)
    print(f"{name:<26} acc={acc:.3f} (±{se:.3f})  "
          f"auc={roc_auc_score(y_test, prob):.3f}  logloss={log_loss(y_test, prob):.3f}")


# Rule baseline: the clan with the higher total TH level wins
rule = (X.iloc[oof_idx]["th_sum_diff"].values > 0).astype(int)
acc = accuracy_score(y_test, rule)
print(f"{'Rule: higher TH sum wins':<26} acc={acc:.3f} (±{np.sqrt(acc * (1 - acc) / n):.3f})\n")

for name, prob in probs.items():
    report(name, prob)