# Clash of Clans Clan War Win Predictor

A machine learning project that predicts the outcome of Clash of Clans clan wars **before any attack happens**, using live data collected from the official Clash of Clans API.

The central question: **how much does knowing each player's real strength (hero levels, war history) improve predictions over Town Hall levels alone?**

> **Status:** work in progress. Data collection (war lineups and player data) runs automatically in the cloud. Model evaluation starts once enough finished wars are collected.

## Overview

Clan wars are decided by stars and destruction percentage, and both lineups are visible during the preparation phase. This project predicts the winner from that preparation-phase information only, so there is no leakage from the battle itself.

The API only exposes wars happening *right now*, with no history. So the project includes its own data pipeline: it snapshots wars as they happen and records the final result when they end.

### Two-phase comparison

| | Phase 1: Town Hall baseline | Phase 2: player-strength model |
|---|---|---|
| Inputs | TH levels, map positions, clan level | Phase 1 features plus hero levels, hero equipment, war stars, trophies |
| Question | Does the lineup's TH level predict the winner? | Do player-level details add predictive power? |
| Data | All collected wars | Only wars captured during preparation after player collection started |

The result of interest is the *difference* between the two phases.

## How it works

```
Clash of Clans API
        |
        v
collector.py  (polls ~300 war-active clans)
        |
        +--> wars table     (raw war snapshot, updated until the war ends)
        +--> players table  (compact player stats, fetched once during preparation)
        |
        v
features.py  (lineup features + win/loss label)
        |
        v
features.csv  -->  train.py (baseline, logistic regression, XGBoost)
```

1. **Clan list:** `build_clan_list.py` searches the API for clans that war frequently and saves their tags.
2. **War collection:** `collector.py` polls each clan's current war and stores the full raw snapshot, keyed so the same war is never stored twice (even if both clans are tracked).
3. **Player collection:** for wars still in the preparation phase, the collector fetches each member's profile once and stores a compact record (town hall, hero levels, equipment levels, war stars, trophies). Fetching during preparation means the values match what each side had before any attack.
4. **Cloud automation:** a GitHub Actions workflow runs the collector on a schedule, so no machine has to stay on. The database is stored on a separate `data` branch.
5. **Features and label:** `features.py` turns each war into one row comparing the two clans. For finished wars, the clan with more stars wins, and ties go to the higher destruction percentage.

## Features

### Phase 1 (available now)

Built only from preparation-phase information:

- Team size and clan level difference
- TH level statistics per clan (average, max, min, sum, top-10 average) and their differences
- **Map-position matchups:** how many positions each clan wins on TH level, comparing the bases at the same map position, since that's who attacks whom

Clans are ordered by tag as "A" and "B", so the model can't learn a bias from which clan was polled. All features are differences between A and B.

### Phase 2 (data being collected)

Per player, stored in the `players` table:

- Town Hall level and Town Hall weapon level
- Hero levels, max levels, and total equipment level per hero
- Lifetime war stars, trophies, best trophies, experience level
- Attack and defense wins

These will be aggregated per clan and per map-position matchup.

## Project structure

```
.
├── .github/workflows/collect.yml   # scheduled cloud collection
├── data/
│   └── clans.txt                   # tracked clan tags (wars.db is gitignored)
├── notebooks/                      # exploration
├── src/
│   ├── build_clan_list.py          # builds data/clans.txt
│   ├── collector.py                # polls the API, stores wars and player data
│   ├── features.py                 # wars -> features.csv
│   ├── train.py                    # baseline and model training
│   ├── inspect_war.py              # prints the structure of one stored war
│   ├── inspect_player.py           # prints the structure of one player response
│   └── test_key.py                 # checks API key and IP setup
├── .env.example
├── requirements.txt
└── README.md
```

## Setup

**Requirements:** Python 3.10+ and a free API key from [developer.clashofclans.com](https://developer.clashofclans.com).

The API ties each key to one IP address. This project uses the [RoyaleAPI proxy](https://docs.royaleapi.com) so the key keeps working from any network. Create your key with the proxy's IP address (check their docs for the current one).

```bash
git clone https://github.com/Vraj-patel-17              /COC-War-Predictor.git
cd COC-War-Predictor
python -m venv .venv
# Windows: .venv\Scripts\activate    Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file (see `.env.example`):

```
COC_API_KEY=your_key_here
COC_BASE_URL=https://cocproxy.royaleapi.dev/v1
```

Check that the key works:

```bash
python src/test_key.py
```

## Usage

```bash
# 1. Build the list of clans to track (once)
python src/build_clan_list.py

# 2. Collect wars and player data (loops hourly; or use the cloud workflow)
python src/collector.py

# 3. Build the feature table
python src/features.py

# 4. Train and compare models (needs at least 50 labeled wars)
python src/train.py
```

### Cloud collection

The workflow in `.github/workflows/collect.yml` runs the collector on GitHub Actions and stores the database on a separate `data` branch. Add `COC_API_KEY` and `COC_BASE_URL` as repository secrets to use it. GitHub's scheduler is best-effort, so runs are roughly every 4 hours but not exact.

To pull the latest data for modeling:

```bash
git fetch origin data
git show origin/data:data/wars.db > data/wars.db
```

On Windows PowerShell, use `cmd /c "git show origin/data:data/wars.db > data\wars.db"` so the binary file isn't corrupted.

## Evaluation plan

- **Baseline:** "the clan with the higher total TH level wins." A model has to beat this to be worth anything.
- **Models:** logistic regression and gradient boosting (XGBoost) first, then a small neural network as a comparison.
- **Split:** time-ordered, so the model is always tested on newer wars than it trained on. With a small dataset, cross-validation will replace the single split for more stable scores.
- **Metrics:** accuracy, ROC-AUC, and log loss.
- **Key comparison:** Phase 1 features vs Phase 2 features on the same wars.

## Results

_Preliminary; the dataset is still growing._

Comparison on 128 decided wars with complete player data (time-ordered cross-validation, tested on 105 wars). All models use the same wars.

| Model | Accuracy | Log loss |
|---|---|---|
| Constant (predicts the training win rate) | 0.543 | 0.697 |
| Phase 1: Town Hall sum | 0.533 | 0.699 |
| Phase 2: player strength | 0.619 | 0.631 |
| Phase 1 + Phase 2 | 0.619 | 0.647 |

Town Hall level alone does no better than predicting the training win rate. Adding player-strength features (hero levels, hero equipment, war stars) improves log loss by 0.068 ± 0.038 (about 1.8 standard errors), which is suggestive but not yet statistically confirmed. Accuracy has a standard error of about ±0.05 at this sample size. The feature set was fixed before the Phase 2 comparison was first run.

## Limitations

- **Live data only.** The API has no history, so the dataset grows only as the collector runs. A war that ends between two polls may be missed, and some wars never get a final label.
- **Phase 2 has less data.** Player data can only be captured going forward, during a war's preparation phase, so the Phase 2 dataset is a subset of Phase 1.
- **Sampling bias.** Only clans with public war logs that are actively warring are included.
- **Matchmaking.** Clans are paired against similar opponents, so Town Hall differences are often small, which may limit what the baseline can learn.
- **Noisy player stats.** Some fields (such as season attack and defense wins) are often zero for war-focused players.
- **Ties** are rare and excluded from training.
- - **Draws are common and excluded.** About a quarter of finished wars end in an exact tie, where both clans 3-star every base. These are likely coordinated "farming" wars between clans, and they have no winner to predict. Models are trained and evaluated only on decided wars, so results apply to wars that have a winner. Draws are not predicted.

## Roadmap

- [x] API access and data collector
- [x] Cloud collection with GitHub Actions
- [x] Feature pipeline (Phase 1)
- [x] Baseline training script
- [x] Player-level data collection
- [ ] Phase 2 features from player data
- [x] Cross-validated phase 1
- [ ] Neural network comparison
- [ ] Small dashboard for predictions

## Disclaimer

This is an unofficial fan project and is not affiliated with or endorsed by Supercell. Clash of Clans is a trademark of Supercell.