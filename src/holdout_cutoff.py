import pandas as pd

p1 = pd.read_csv("data/features.csv")
p2 = pd.read_csv("data/features_players.csv")

df = p1.merge(p2, on="war_key")
df = df[df["label"].notna()]
times = df["war_key"].str.split("_").str[-1]

print("Usable wars so far:", len(df))
print("Latest preparation start among them:", times.max())