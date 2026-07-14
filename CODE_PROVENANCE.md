# Code provenance and analysis ownership

This file separates website/data-assistance code from mathematical analysis. It is intended to make the use of LLM assistance explicit and auditable.

## Labels used in the source

- **AI-ASSISTED — DATA EXTRACTION / TRANSFORMATION**: Reads, filters, joins, labels, or reshapes Impect data. It does not make a football-performance claim.
- **AI-ASSISTED — WEBSITE DESIGN / VISUALISATION**: Streamlit layout, CSS, SVG/HTML generation, tables, controls, and chart presentation.
- **AI-ASSISTED DRAFT — MATHEMATICAL ANALYSIS**: A calculation proposed or written with LLM assistance. It must not be presented as manually authored.
- **AUTHORSHIP TO VERIFY — MATHEMATICAL / STATISTICAL ANALYSIS**: Existing analytical code whose provenance cannot be established from the current repository state.
- **MIXED MODULE**: A legacy file containing more than one of the categories above. The function map below identifies its boundaries.

Only the person who wrote and understands an analytical section should replace an `AI-ASSISTED DRAFT` or `AUTHORSHIP TO VERIFY` label with `MANUAL`. Changing a label without verifying authorship would misrepresent the work.

## Fully separated heatmap feature

| Layer | File | Provenance | Responsibility |
|---|---|---|---|
| Data | `Exam Files/freiburg_app/season_heatmap_data.py` | AI-assisted | Read Impect events/KPIs, transform coordinates, filter Freiburg events, and aggregate 12-by-8 grids. |
| Mathematics | `Exam Files/freiburg_app/season_heatmap_analysis.py` | AI-assisted draft; manual review required | Apply the mass-preserving 3-by-3 smoothing kernel, choose the display cap, and calculate attacking-third shares. |
| Visual | `Exam Files/freiburg_app/season_heatmaps.py` | AI-assisted | Build Streamlit metrics and controls, map values to colours, draw SVG pitches, and show hover tooltips. |

### Advanced Match Details comparison

- `match_heatmap_scaffold.py` is AI-assisted Streamlit website/data-display code.
- `season_heatmap_data.py` prepares one raw row per match and pitch block.
- `match_heatmap_comparison.py` is an **AI-assisted mathematical analysis**. It compares the selected block with the arithmetic mean of the same block in the other 33 matches and reports `selected - normal`.
- `match_heatmap_comparison_plot.py` contains the **AI-assisted SVG plots**. Red means above the other-match average, blue means below it, and no smoothing is applied.
- None of the comparison analysis or plotting code is human-authored.

### Heatmap mathematics to understand before assessment

1. **Grid definition:** the 105m by 68m pitch is divided into 12 equal x bins and 8 equal y bins.
2. **Value maps:** shot blocks sum Impect xG; threat blocks sum positive Impect PxT. These values are supplied by Impect rather than estimated by this app.
3. **Volume maps:** the same blocks count shots or positive-PxT events with valid coordinates.
4. **Smoothing:** every raw block distributes its value over its valid 3-by-3 neighbourhood with weights `[[1,2,1],[2,4,2],[1,2,1]]`. Edge weights are renormalised so the grid total is preserved.
5. **Colour cap:** the display maximum is the indexed 90% point among positive smoothed blocks. Values above it use the strongest colour. This affects appearance only.
6. **Attacking-third share:** with left-to-right attack, the numerator is the sum of columns 8–11 and the denominator is the complete raw grid sum.
7. **Important limitation:** smoothing is only a visual aid. It is not a fitted spatial density model and must not be interpreted as evidence that events occurred between block centres.

## Repository-wide module map

### AI-assisted website and extraction modules

- `freiburg_dashboard.py`: Streamlit entry point.
- `app.py`: page routing.
- `components.py`, `home.py`, `styles.py`: presentation and website design.
- `config.py`: data paths and Impect KPI identifiers.
- `data.py`, `events.py`, `matches.py`: JSON loading, filtering, formatting, and table preparation.
- `lineups.py`: lineup extraction and pitch/table presentation. Marker positions are a design mapping, not tracking analysis.
- `season_heatmap_data.py`, `season_heatmaps.py`: heatmap extraction and presentation as described above.

### Analytical modules

- `metrics.py`: score reconstruction, attacking-event-share possession proxy, match statistics, season points, and xG aggregation.
- `regression.py`: **AI-assisted mathematical analysis** for Poisson GLM fitting, expected-goal rates, score probabilities, and expected points. It is not human-authored.
- `season_heatmap_analysis.py`: AI-assisted analytical draft; this one is known not to be manual.

### Mixed legacy modules

#### `league.py`

- Analysis/transformation: `build_league_table` requires authorship verification; the imported `build_regression_outputs` calculation is explicitly AI-assisted.
- AI-assisted presentation: `render_league_table_page` and the HTML table.

#### `match_details.py`

- AI-assisted extraction/formatting: coordinate conversion, event/KPI lookups, match selectors, and table-row preparation.
- Analysis requiring authorship verification: `_match_segments`, `_pass_network_rows`, centralisation, xT aggregation, shot build-up selection, and player xT summaries.
- AI-assisted visuals: `_pitch_background`, `_svg_wrapper`, `_render_pass_network`, `_render_build_up_map`, and `render_match_details_page`.

#### `player_rankings.py`

- AI-assisted extraction: KPI/event aggregation and player-row preparation.
- Analysis requiring authorship verification: `_finalize_row`, `_per90`, `_adjusted_value`, `_percentile_rank`, and `_score_position_rows`.
- AI-assisted visuals: `_radar_svg`, `_render_position_table`, and `render_player_rankings_page`.

#### `threat.py`

- AI-assisted extraction: KPI lookup and season player/team aggregation.
- Analysis requiring authorship verification: net-threat definitions, per-90 conversions, percentile ranks, min-max value scores, semantic bands, and generated inferences.
- AI-assisted visuals: metric guide, tables/charts, and `render_threat_page`.

## Manual review checklist

Before changing any analytical provenance label to `MANUAL`, the author should be able to do all of the following without relying on an LLM-generated explanation:

1. State the input fields and why each one is appropriate.
2. Write the formula or algorithm independently.
3. Explain every denominator, filter, fallback, threshold, and clipping rule.
4. Reproduce one small example by hand.
5. Explain limitations and identify cases where the result could mislead.
6. Add or run tests that check totals, edge cases, and expected ordering.
7. Rewrite any section that the author cannot confidently defend.

## Key assumptions requiring particular attention

- `compute_possession` is an attacking-event-share proxy, not measured ball-possession time.
- xG and PxT values come from Impect KPIs; this project does not train those models.
- Per-90 values divide by recorded minutes and multiply by 90.
- Possession-adjusted player metrics rescale attacking or defensive per-90 values to a 50% possession environment.
- Percentile ranks measure ordering within the eligible comparison group; they do not measure the size of the performance gap.
- Min-max value scores are sensitive to the comparison group's extreme values.
- The Poisson model assumes the specified log-linear goal structure and truncates enumerated scorelines at ten goals per team before renormalisation.
