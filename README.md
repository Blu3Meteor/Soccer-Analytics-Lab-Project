# SC Freiburg Match Dashboard

Streamlit dashboard for exploring SC Freiburg's Bundesliga 2023/24 matches using the local Impect Exam Data.

## Assistance labels

Assisted code is marked directly in each source file with these exact headings:

- `# UI Assistance` for Streamlit, HTML, CSS, SVG, and display functions.
- `# Data Processing Assistance` for loading, filtering, grouping, and formatting data.

A heading applies to the functions below it until the next heading. Mathematical blocks instead include either a Soccermatics reference or an explicit `Extra mathematical method` note.

## Data source

The data comes from the Impect open-data repository:

```text
https://github.com/ImpectAPI/open-data
```

Field and KPI semantics were checked against the supplied [Documentation.pdf](Exam%20Files/Documentation.pdf). Provider-text caveats are listed below rather than changing the source data.

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
pip install -r "requirements.txt"
```

## Completed features

The dashboard now has six dedicated sidebar views.

### Home page

- Season record card with wins, draws, losses, points, and points progression.
- Clickable match strip covering all 34 SC Freiburg Bundesliga matches.
- Match scoreboard with date, opponent, score, and result.
- Overview metrics for shots, explicit pass accuracy, attacking-event share, and opponent.
- Tabs for lineups, match statistics, goals, cards, and shot events.
- Direct link from each selected match to its advanced Match Details view.

### Match Details

- Match selector and full scoreboard for every Freiburg league fixture.
- Overview comparing both teams, including complete team PxT from Post-Shot xG KPI 1401 and each team's leading selected-action PxT player.
- Passing networks for both teams using successful teammate passes.
- Network segmentation by lineup-change windows covering bench, position, side, and tactical changes.
- Passing-network metrics for pass volume, involved players, centralisation, and the most involved player.
- Shot build-up maps showing the actions leading to a selected attempt.
- Build-up sequence metrics and tables with selected action-level PxT contributions.
- Match-level selected-action PxT player rankings and a table of the leading actions; these seven tagged sources are not labelled as total PxT.
- AI-assisted Match Heatmaps comparing the selected match with Freiburg's same-block average across the other 33 matches, with Value/Volume views, hover details, raw inputs, and a downloadable source dataset.
- Starting formations and player sides, benches, formation history, full from/to lineup changes, goal events, card events, shot events, and raw event data.

### Season Heatmaps

- Dedicated sidebar page for Freiburg's season-long shot and positive action-PxT patterns.
- Shot-origin and positive action-PxT destination maps displayed in a consistent attacking direction.
- **Value** view weighted by shot xG and positive PxT.
- **Volume** view based on shot and positive-action counts.
- Summary metrics for total xG, xG per shot, xG per match, positive selected-action PxT, and action PxT per match.
- Attacking-third shares, smoothed spatial density, hotspot markers, legends, and hover values.
- High-percentile colour scaling so one extreme zone does not hide the rest of the pitch pattern.
- Explanatory methodology panel clarifying the difference between raw totals and smoothed visuals.

### Player Rankings

- League-wide player comparison split into forwards, midfielders, wingbacks, defenders, and goalkeepers.
- Adjustable minimum-minutes filter.
- Position-specific metric sets and Freiburg player tables.
- Per-90 and attacking-event-share-adjusted counting metrics, with rate statistics retained as rates.
- Wingbacks are compared with other wingbacks using Attack PxT, expected shot assists, successful final-third passes, final-third receptions, Threat Prevented, ball wins, interceptions, and Ball Security.
- Higher Attack PxT ranks mean more attacking-phase threat added. Raw defensive PxT measures threat conceded, so it is sign-inverted and displayed as **Threat Prevented** before ranking; higher displayed values remain better.
- Goalkeeper PSxG and goals conceded are assigned to the goalkeeper active at the event time, including goalkeeper substitutions and own goals.
- Expandable player radar charts based on within-position percentile ranks.
- Raw metric values and ranks shown alongside each radar.

### League Table

- Reconstructed Bundesliga table with played, wins, draws, losses, goals, goal difference, and points.
- Freiburg row highlighting and club logos.
- Poisson regression estimates using `goals ~ home + team + opponent`.
- Model rank, expected points, attack coefficient, and concede coefficient for every club.
- Expandable regression coefficient table and explanations of the model columns.

### Attacking Threat

- Freiburg attacking-phase PxT per match, league rank, percentile rank, and project-defined net threat per match.
- League comparison by threat source, including passing, shooting, dribbling, and set pieces.
- Configurable player ranking metric and minimum-minutes filter.
- Player bar chart and detailed table covering attacking-phase PxT, net threat, receiving PxT, and attributable action-source contributions.
- Per-90, percentile-rank, value-score, and plain-language interpretation columns.
- Automated team and player observations plus expandable league context and metric notes.

### Shared dashboard work

- Custom sidebar navigation with active-page states and query-parameter routing.
- Responsive wide dashboard layout with reusable scoreboards, cards, tables, and pitch graphics.
- Cached JSON loading and cached season-level calculations for faster reruns.
- SC Freiburg visual styling with consistent typography, spacing, colours, and result indicators.

## Stat and KPI definitions

- Match list, teams, players, and lineups come from the Exam Data JSON files.
- Goals are calculated from `GOAL` and `OWN_GOAL` events.
- Shots, shots on target, passes, and red cards use `player_kpis`.
- Pass accuracy is `successful / (successful + unsuccessful + neutral)` or `S / (S + U + N)`. Neutral passes are included in the attempt denominator but are not provider-classified failures.
- Yellow and second-yellow KPI data is absent in this 2023/24 dataset, so the dashboard displays `N/A`; red-card counts remain numeric.
- Fouls, offsides, and corners are counted from the event feed.
- **Attacking-event share** is each team's percentage of eligible events tagged with `currentAttackingSquadId`. It is an event-count proxy and is never described as measured possession time.
- Complete match-level team PxT uses Post-Shot xG KPI 1401, following the provider identity `team PxT = team Post-Shot xG`.
- Selected action PxT uses seven event sources: pass, dribble, set piece, block, shot, ball win, and foul. It supports action tables and maps but is not complete team PxT.
- Player PxT source attribution additionally includes passive and fouled PxT. No-video and other PxT are excluded because the documentation says they cannot be attributed directly to a player.
- Event ordering and lineup windows use the period-aware `gameTimeInSec`; the display-time fallback also includes `(+AddedTime)`.

## Regression model

The League Table page includes a Poisson regression model following the Soccermatics lesson:

```text
https://soccermatics.readthedocs.io/en/latest/gallery/lesson5/plot_SimulateMatches.html
```

The model fits:

```text
goals ~ home + team + opponent
```

It uses Statsmodels to fit the Poisson GLM, then NumPy and SciPy to estimate each fixture's scoring rates, outcome probabilities, in-sample expected points, and expected goal difference. Pandas is used for the model table and heatmap comparisons.

## Match Details models

The Match Details page follows these Soccermatics visual ideas:

```text
https://soccermatics.readthedocs.io/en/latest/gallery/lesson1/plot_PassNetworks.html
https://soccermatics.readthedocs.io/en/latest/gallery/lesson4/plot_ActionBasedExpectedThreat.html
```

Passing networks use successful teammate passes for both teams, split at every recorded lineup change rather than only substitutions. Windows therefore include bench, position, side, and tactical changes. Formation panels show the starting formation, player side, formation history, and full from/to lineup-change details.

The complete team PxT headline sums Post-Shot xG KPI 1401. Action maps and build-up tables instead use the seven tagged event-level PxT sources listed above and are explicitly labelled **selected action PxT**.

## Season heatmap methodology

- Shot maps use each shot's starting coordinates. The Value view weights those locations by xG.
- PxT maps use the action destination when available and otherwise fall back to its starting coordinate. Destination placement is a project visualisation choice.
- Only positive values from the seven tagged-action sources are included: pass, dribble, set piece, block, shot, ball win, and foul. The map is not a complete team-PxT total.
- The pitch is divided into a 12-by-8 grid and a light 3-by-3 spatial smoothing kernel is used for display.
- Smoothing preserves the overall total, while the headline metrics are calculated directly from the unsmoothed event data.
- Heatmap colour intensity is capped near the high end of the distribution to keep secondary patterns visible.

## Methods beyond the Soccermatics examples

These calculations are useful project extensions, but they are not formulas supplied by the linked Soccermatics lessons:

| Method | Where | Note |
|---|---|---|
| Attacking-event share | `event_utils.py`, `metrics.py` | Percentage based on eligible event counts, not measured possession time. |
| Expected-points league table | `regression.py` | Applies the Poisson model in sample to the same season fixtures used for fitting. |
| Heatmap smoothing and colour cap | `season_heatmap_analysis.py` | Display-only 3×3 smoothing and a 90th-percentile colour cap. |
| Match-vs-normal heatmap | `match_heatmap_comparison.py` | Leave-one-match-out block average. |
| Net Threat, min-max scores, and wording bands | `threat.py` | Project-specific summaries and editorial thresholds. |
| Event-share adjustment and mean percentile | `player_rankings.py` | Extends the per-90/percentile radar method by rescaling counts to a 50% attacking-event-share environment and averaging metric percentiles equally. |
| Ball Security | `player_rankings.py` | Custom clamped score based on dangerous losses. |
| Goalkeeper event attribution | `player_rankings.py` | Uses lineup-derived goalkeeper intervals; `PSxG Prevented = Post-Shot xG faced - goals conceded`, with own goals assigned to the active goalkeeper of the conceding team. |
| Pass Over Expected | `player_rankings.py` | Provider-specific project calculation: successful passes minus Impect Expected Passes KPI 1783. |
| Position groups and minimum minutes | `player_rankings.py`, `threat.py` | Players are grouped by their largest minutes share and compared only with eligible peers above the selected minutes threshold. |
| Lineup-change windows and shot build-up selection | `match_details.py` | Project-specific event grouping around the visualisations, using the provider's period-aware event clock. |
| Positive action-PxT destinations | `season_heatmap_data.py` | Maps seven tagged positive action sources at their end coordinate; this is a project display choice, not the provider's team-total identity. |

The app does not train the Soccermatics xG or xT models. Shot xG, Post-Shot xG, and action/phase PxT are precomputed Impect KPIs; the app aggregates and displays them. The Poisson model, percentile radars, and passing-network ideas follow the linked Soccermatics lessons; every method in the table above is an additional project choice.

## Notes and caveats

- Yellow-card and second-yellow-card KPIs 1637/1638 are defined by the provider but absent from the supplied 2023/24 match data. Their values are therefore `N/A`, not zero.
- Across the supplied league files, the eleven event-level PxT components differ from KPI 1401 by `0.368903` in total. The dashboard therefore uses the provider's primary Post-Shot xG KPI 1401 as the authoritative complete team PxT value instead of reconstructing it from rounded components.
- The provider descriptions reproduced in `Documentation.pdf` for KPI 1415 (`OPP_PXT_SETPIECE`) and KPI 1417 (`OPP_PXT_SHOT`) appear internally inconsistent or copied. The app retains the provider IDs/names and does not rewrite `kpi_definitions.json`.
- No positional tracking data is supplied, so off-ball behaviour such as decoy runs cannot be evaluated; findings are limited to recorded events and KPIs.
