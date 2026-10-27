import pandas as pd

df = pd.read_csv("data/features.csv")
df = df[df["label"].notna()].copy()

df["th_sum_group"] = pd.cut(
    df["th_sum_diff"], [-1e9, -0.5, 0.5, 1e9], labels=["A lower", "equal", "A higher"]
)
print("Share of wars won by clan A, grouped by TH sum difference:")
print(df.groupby("th_sum_group", observed=True)["label"].agg(["count", "mean"]))

print("\nCorrelation of each feature with 'A wins':")
cols = [c for c in df.columns if c.endswith("_diff") or c.startswith("matchup")]
print(df[cols + ["label"]].corr()["label"].drop("label").round(3))