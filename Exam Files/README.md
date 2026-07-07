# SC Freiburg Match Dashboard

Streamlit dashboard for exploring SC Freiburg's Bundesliga 2023/24 matches using the local Impect Exam Data.

## Folder Setup

Keep the app files and data files separate:

```text
Soccer Analytics Lab/
  Exam Files/
    freiburg_dashboard.py
    requirements.txt
    exam/
  Exam Data/
    open-data/
      data/
```

The dashboard reads data from:

```text
Exam Data/open-data/data
```

## Run The Dashboard

From the project root:

```bash
cd "/Users/ayushmangukia/Downloads/Soccer Analytics Lab"
source "Exam Files/exam/bin/activate"
streamlit run "Exam Files/freiburg_dashboard.py"
```

Then open the local Streamlit URL shown in the terminal, usually:

```text
http://localhost:8501
```

If Streamlit asks for an email on first run, press Enter to skip it.

## Install Requirements

If the `exam` virtual environment does not have Streamlit installed:

```bash
source "Exam Files/exam/bin/activate"
pip install -r "Exam Files/requirements.txt"
```

## What It Shows

- A top slider for all 34 SC Freiburg league matches.
- Clickable result boxes for each match.
- Match overview with score, date, opponent, and Freiburg result.
- Lineups, benches, and substitutions for both teams.
- Match stats: shots, shots on target, possession, passes, pass accuracy, fouls, yellow cards, red cards, offsides, and corners.
- Goal, card, and shot event tables.

## Stat Sources

- Match list, teams, players, and lineups come from the Exam Data JSON files.
- Goals are calculated from `GOAL` and `OWN_GOAL` events.
- Shots, shots on target, passes, pass accuracy, yellow cards, second yellow cards, and red cards use `player_kpis`.
- Fouls, offsides, corners, and possession are calculated from the event feed.

Possession is estimated from attacking event share because the dataset does not include a direct possession percentage field.
