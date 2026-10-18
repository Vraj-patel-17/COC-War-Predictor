import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from xgboost import XGBClassifier

MIN_LABELED = 50

df = pd.read_csv("data/features.csv")
df = df[df["label"].notna()].copy()

if len(df) < MIN_LABELED:
    print(f"Only {len(df)} labeled wars so far, need at least {MIN_LABELED}. Collect more first.")
    raise SystemExit

df["prep_time"] = df["war_key"].str.split("_").str[-1]
df = df.sort_values("prep_time").reset_index(drop=True)
split = int(len(df) * 0.8)
train, test = df.iloc[:split], df.iloc[split:]

features = [c for c in df.columns if c not in ("war_key", "label", "prep_time")]
X_train, y_train = train[features], train["label"].astype(int)
X_test, y_test = test[features], test["label"].astype(int)


def report(name, prob):
    pred = (prob > 0.5).astype(int)
    print(f"{name:<22} acc={accuracy_score(y_test, pred):.3f}  "
          f"auc={roc_auc_score(y_test, prob):.3f}  logloss={log_loss(y_test, prob):.3f}")


print(f"Train: {len(train)} wars | Test: {len(test)} wars\n")

baseline = (test["th_sum_diff"] > 0).astype(float).clip(0.05, 0.95)
report("Baseline (higher TH sum)", baseline)

logreg = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
logreg.fit(X_train, y_train)
report("Logistic regression", logreg.predict_proba(X_test)[:, 1])

xgb = XGBClassifier(n_estimators=200, max_depth=3, learning_rate=0.05,
                    eval_metric="logloss")
xgb.fit(X_train, y_train)
report("XGBoost", xgb.predict_proba(X_test)[:, 1])