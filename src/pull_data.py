import gzip
import subprocess

subprocess.run(["git", "fetch", "origin", "data"], check=True)


def show(path):
    r = subprocess.run(["git", "show", f"origin/data:{path}"], capture_output=True)
    return r.stdout if r.returncode == 0 else None


blob = show("data/wars.db.gz")
if blob is not None:
    blob = gzip.decompress(blob)
else:
    blob = show("data/wars.db")  
    if blob is None:
        raise SystemExit("No database found on the data branch")

with open("data/wars.db", "wb") as f:
    f.write(blob)
print(f"data/wars.db updated ({len(blob) / 1e6:.1f} MB)")