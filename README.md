# Clash of Clans Clan War Win Predictor

A machine learning project that predicts the outcome of Clash of Clans clan wars from the lineups of both clans, using live data collected from the official Clash of Clans API.

> **Status:** work in progress. Data collection and feature engineering are done. Model training and evaluation start once enough finished wars are collected.

## Overview

Clan wars are decided by stars and destruction percentage, and the lineups are visible during the preparation phase. This project asks: **can the winner be predicted from the lineups alone, before any attack happens?**

The API only exposes wars that are happening *right now*, with no history. So the project includes its own data pipeline: it takes snapshots of wars as they happen and records the final result when they end.

## How it works

```
Clash of Clans API
        |
        v
collector.py  (polls ~300 war-active clans)
        |
        v
wars.db  (SQLite, raw JSON snapshot per war)
        |
        v
features.py  (lineup features + win/loss label)
        |
        v
features.csv  -->  model training and evaluation
```

1. **Clan list:** `build_clan_list.py` searches the API for clans that war frequently and saves their tags.
2. **Collection:** `collector.py` polls each clan's current war and stores the full raw snapshot, keyed so the same war is never stored twice. A GitHub Actions workflow runs it every 4 hours, so no machine has to stay on.
3. **Features:** `features.py` turns each snapshot into one row of features comparing the two clans.
4. **Label:** for finished wars, the clan with more stars wins, and ties go to the higher destruction percentage.

## Features

Built only from information available during the preparation phase, so there is no leakage from attack results:

- Team size and clan level difference
- Town Hall (TH) level statistics per clan (average, max, min, sum, top-10 average) and their differences
- **Map-position matchups:** how many positions each clan wins on TH level, comparing the bases at the same map position, since that's who attacks whom

Clans are ordered by tag as "A" and "B", so the model can't learn a bias from which clan was polled.

## Project structure

```
.
├── .github/workflows/collect.yml   # scheduled cloud collection
├── data/
│   └── clans.txt                   # tracked clan tags (wars.db is gitignored)
├── notebooks/                      # exploration
├── src/
│   ├── build_clan_list.py          # builds data/clans.txt
│   ├── collector.py                # polls the API, stores war snapshots
│   ├── features.py                 # snapshots -> features.csv
│   ├── inspect_war.py              # prints the structure of one stored war
│   └── test_key.py                 # checks API key and IP setup
├── .env.example
├── requirements.txt
└── README.md
```

## Setup

**Requirements:** Python 3.10+ and a free API key from [developer.clashofclans.com](https://developer.clashofclans.com).

The API ties each key to one IP address. This project uses the [RoyaleAPI proxy](https://docs.royaleapi.com) so the key keeps working from any network. Create your key with the proxy's IP address (check their docs for the current one).

```bash
git clone https://github.com/YOUR_USERNAME/coc-war-predictor.git
cd coc-war-predictor
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

# 2. Collect wars (loops hourly; leave running, or use the cloud workflow)
python src/collector.py

# 3. Build the feature table
python src/features.py
```

### Cloud collection

The workflow in `.github/workflows/collect.yml` runs the collector every 4 hours on GitHub Actions and stores the database on a separate `data` branch. To use it, add `COC_API_KEY` and `COC_BASE_URL` as repository secrets.

To pull the latest data for modeling:

```bash
git fetch origin data
git show origin/data:data/wars.db > data/wars.db
```

## Evaluation plan

- **Baseline:** "the clan with the higher total TH level wins." A model has to beat this to be worth anything.
- **Models:** logistic regression and gradient boosting (XGBoost) first, then a small neural network as a comparison.
- **Split:** by time or by clan, never random, so the same clan doesn't appear in both train and test.
- **Metrics:** accuracy, ROC-AUC, and log loss.

## Results

_To be added once enough finished wars are collected._

## Limitations

- **Live data only.** The API has no history, so the dataset grows only as the collector runs, and a war that ends between two polls may be missed.
- **Sampling bias.** Only clans with public war logs that are actively warring are included.
- **Thin signal.** TH level alone ignores hero levels, troop levels and player skill. Adding `/players` data is a planned improvement.
- **Ties** are rare and excluded from training.

## Roadmap

- [x] API access and data collector
- [x] Cloud collection with GitHub Actions
- [x] Feature pipeline
- [ ] Baseline model and evaluation
- [ ] Add player-level features (hero levels, war stars, attack wins)
- [ ] Neural network comparison
- [ ] Small dashboard for predictions

## Disclaimer

This is an unofficial fan project and is not affiliated with or endorsed by Supercell. Clash of Clans is a trademark of Supercell.