# SC Freiburg Match Dashboard

Streamlit dashboard for exploring SC Freiburg's Bundesliga 2023/24 matches using the local Impect Exam Data.

## AI assistance and code provenance

AI-assisted website design and data-extraction code is marked directly in the source. Mathematical sections are separated where practical and are never labelled manual unless their authorship has been verified. See [CODE_PROVENANCE.md](CODE_PROVENANCE.md) for the layer map, known AI-assisted analytical drafts, mixed-module boundaries, assumptions, and manual-review checklist.

## Data source

The data comes from the Impect open-data repository:

```text
https://github.com/ImpectAPI/open-data
```

## Folder setup

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

## Run the dashboard

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

## Install requirements

If the `exam` virtual environment does not have Streamlit installed:

```bash
source "Exam Files/exam/bin/activate"
pip install -r "Exam Files/requirements.txt"
```

## Completed features

The dashboard now has six dedicated sidebar views.

### Home page

- Season record card with wins, draws, losses, points, and points progression.
- Clickable match strip covering all 34 SC Freiburg Bundesliga matches.
- Match scoreboard with date, opponent, score, and result.
- Overview metrics for shots, pass accuracy, estimated possession, and opponent.
- Tabs for lineups, match statistics, goals, cards, and shot events.
- Direct link from each selected match to its advanced Match Details view.

### Match Details

- Match selector and full scoreboard for every Freiburg league fixture.
- Overview comparing both teams, including Freiburg total xT and each team's best xT player.
- Passing networks for both teams using successful teammate passes.
- Network segmentation by substitution windows so tactical changes can be inspected over time.
- Passing-network metrics for pass volume, involved players, centralisation, and the most involved player.
- Shot and goal build-up maps showing the actions leading to a selected attempt.
- Build-up sequence metrics and tables with action-level xT contributions.
- Match-level xT player rankings and a table of the leading xT actions.
- Starting lineups, benches, substitutions, goal events, card events, shot events, and raw event data.

### Season Heatmaps

- Dedicated sidebar page for Freiburg's season-long shot and positive PxT patterns.
- Shot-origin and positive-PxT destination maps displayed in a consistent attacking direction.
- **Value** view weighted by shot xG and positive PxT.
- **Volume** view based on shot and positive-action counts.
- Summary metrics for total xG, xG per shot, xG per match, positive PxT, and PxT per match.
- Attacking-third shares, smoothed spatial density, hotspot markers, legends, and hover values.
- High-percentile colour scaling so one extreme zone does not hide the rest of the pitch pattern.
- Explanatory methodology panel clarifying the difference between raw totals and smoothed visuals.

### Player Rankings

- League-wide player comparison split into forwards, midfielders, defenders, and goalkeepers.
- Adjustable minimum-minutes filter.
- Position-specific metric sets and Freiburg player tables.
- Per-90 and possession-adjusted counting metrics, with rate statistics retained as rates.
- Expandable player radar charts based on within-position percentile ranks.
- Raw metric values and ranks shown alongside each radar.

### League Table

- Reconstructed Bundesliga table with played, wins, draws, losses, goals, goal difference, and points.
- Freiburg row highlighting and club logos.
- Poisson regression estimates using `goals ~ home + team + opponent`.
- Model rank, expected points, attack coefficient, and concede coefficient for every club.
- Expandable regression coefficient table and explanations of the model columns.

### Attacking Threat

- Freiburg team PxT per match, league rank, percentile rank, and net threat per match.
- League comparison by threat source, including passing, shooting, dribbling, and set pieces.
- Configurable player ranking metric and minimum-minutes filter.
- Player bar chart and detailed table covering PxT, net threat, receiving PxT, and action-source contributions.
- Per-90, percentile-rank, value-score, and plain-language interpretation columns.
- Automated team and player observations plus expandable league context and metric notes.

### Shared dashboard work

- Custom sidebar navigation with active-page states and query-parameter routing.
- Responsive wide dashboard layout with reusable scoreboards, cards, tables, and pitch graphics.
- Cached JSON loading and cached season-level calculations for faster reruns.
- SC Freiburg visual styling with consistent typography, spacing, colours, and result indicators.

## Stat sources

- Match list, teams, players, and lineups come from the Exam Data JSON files.
- Goals are calculated from `GOAL` and `OWN_GOAL` events.
- Shots, shots on target, passes, pass accuracy, yellow cards, second yellow cards, and red cards use `player_kpis`.
- Fouls, offsides, corners, and possession are calculated from the event feed.

Possession is estimated from attacking event share because the dataset does not include a direct possession percentage field.

## Regression model

The League Table page includes a Poisson regression model following the Soccermatics lesson:

```text
https://soccermatics.readthedocs.io/en/latest/gallery/lesson5/plot_SimulateMatches.html
```

The model fits:

```text
goals ~ home + team + opponent
```

It uses the coefficients to estimate each fixture's scoring rates, outcome probabilities, expected points, and expected goal difference.

## Match Details models

The Match Details page follows these Soccermatics visual ideas:

```text
https://soccermatics.readthedocs.io/en/latest/gallery/lesson1/plot_PassNetworks.html
https://soccermatics.readthedocs.io/en/latest/gallery/lesson4/plot_ActionBasedExpectedThreat.html
```

Passing networks use successful teammate passes for both teams, split by substitution windows. The xT maps use Impect event-level PXT action KPI values from `events_kpis`.

## Season heatmap methodology

- Shot maps use each shot's starting coordinates. The Value view weights those locations by xG.
- PxT maps use the ending coordinate when available and otherwise fall back to the action's starting coordinate.
- Only positive PxT actions are included in the season map.
- The pitch is divided into a 12-by-8 grid and a light 3-by-3 spatial smoothing kernel is used for display.
- Smoothing preserves the overall total, while the headline metrics are calculated directly from the unsmoothed event data.
- Heatmap colour intensity is capped near the high end of the distribution to keep secondary patterns visible.

## Notes and caveats

- No yellow card data is present in the events_kpis folder.
- No positional / tracking data makes it impossible to evaluate general play (e.g. decoy runs, etc), so the findings are solely based on events.

## Possible next steps

- Add a dedicated per-match shot and PxT heatmap for direct game-to-game comparison.
