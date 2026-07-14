# PROVENANCE: AI-ASSISTED — WEBSITE CSS / VISUAL DESIGN

from __future__ import annotations

import streamlit as st


CSS = """
<style>
:root {
    --freiburg-red: #c7152a;
    --ink: #15171a;
    --soft-border: #d8dde3;
    --muted: #667085;
    --panel: #ffffff;
    --wash: #f5f7f9;
}

.block-container {
    padding-top: 1.4rem;
    padding-bottom: 2.5rem;
}

[data-testid="stSidebar"] {
    background: #f8fafc;
    border-right: 1px solid #e3e7ed;
}

[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    padding: 1.15rem 0.85rem;
}

.sidebar-shell {
    display: grid;
    gap: 0.85rem;
}

.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    padding: 0.2rem 0.1rem 0.85rem;
    border-bottom: 1px solid #e3e7ed;
}

.sidebar-badge {
    display: grid;
    place-items: center;
    width: 42px;
    height: 42px;
    border-radius: 8px;
    background: var(--freiburg-red);
    color: #ffffff;
    font-size: 0.8rem;
    font-weight: 950;
}

.sidebar-brand-title {
    color: var(--ink);
    font-size: 1rem;
    font-weight: 900;
    line-height: 1.1;
}

.sidebar-brand-subtitle {
    color: var(--muted);
    font-size: 0.73rem;
    font-weight: 750;
    margin-top: 0.12rem;
}

.sidebar-nav {
    display: grid;
    gap: 0.55rem;
}

.sidebar-link {
    display: grid;
    gap: 0.12rem;
    padding: 0.72rem 0.78rem;
    border: 1px solid #e1e7ef;
    border-radius: 8px;
    background: #ffffff;
    color: var(--ink) !important;
    text-decoration: none !important;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.sidebar-link:visited,
.sidebar-link:hover,
.sidebar-link:active {
    color: var(--ink) !important;
    text-decoration: none !important;
}

.sidebar-link:hover {
    border-color: var(--freiburg-red);
    background: #fff7f8;
}

.sidebar-link-active {
    border-color: var(--freiburg-red);
    background: #fff3f5;
    box-shadow: inset 3px 0 0 var(--freiburg-red);
}

.sidebar-link-title {
    color: var(--ink);
    font-size: 0.95rem;
    font-weight: 880;
    line-height: 1.15;
}

.sidebar-link-meta {
    color: var(--muted);
    font-size: 0.74rem;
    font-weight: 720;
}

.sidebar-footnote {
    border-top: 1px solid #e3e7ed;
    color: var(--muted);
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0.75rem 0.12rem 0;
}

.section-heading {
    color: var(--ink);
    font-size: 1rem;
    font-weight: 900;
    margin: 0 0 0.7rem;
}

.season-heatmap {
    display: grid;
    gap: 0.55rem;
}

.season-heatmap-title {
    color: #475467;
    font-size: 0.8rem;
    font-weight: 800;
    line-height: 1.25;
}

.season-heatmap svg {
    display: block;
    width: 100%;
    height: auto;
    overflow: hidden;
    border: 1px solid #263d34;
    border-radius: 10px;
    background: #142820;
    box-shadow: 0 7px 20px rgba(15, 23, 42, 0.12);
}

.heatmap-zone {
    cursor: crosshair;
    transition: filter 120ms ease, stroke 120ms ease, stroke-width 120ms ease;
}

.heatmap-zone:hover,
.heatmap-zone:focus {
    outline: none;
    stroke: rgba(255, 255, 255, 0.98);
    stroke-width: 0.7;
}

.heatmap-tooltip {
    opacity: 0;
    pointer-events: none;
    transition: opacity 90ms ease;
}

.heatmap-hover-target:hover .heatmap-tooltip,
.heatmap-hover-target:focus-within .heatmap-tooltip {
    opacity: 1;
}

.heatmap-legend {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 110px;
    gap: 0.55rem;
    align-items: center;
    color: var(--muted);
    font-size: 0.74rem;
    font-weight: 800;
}

.heatmap-scale {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    height: 10px;
    overflow: hidden;
    border: 1px solid #d8dde3;
    border-radius: 999px;
}

.heatmap-scale i {
    display: block;
}

.heatmap-scale-labels {
    grid-column: 2;
    display: flex;
    justify-content: space-between;
    margin-top: -0.35rem;
    color: var(--muted);
    font-size: 0.64rem;
    font-weight: 800;
}

h1, h2, h3 {
    letter-spacing: 0;
}

.app-kicker {
    color: var(--freiburg-red);
    font-size: 0.8rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 0.2rem;
}

.headline-row {
    border-bottom: 1px solid var(--soft-border);
    padding-bottom: 1rem;
    margin-bottom: 1rem;
}

.summary-card {
    border: 1px solid var(--soft-border);
    border-radius: 8px;
    padding: 0.85rem 1rem;
    background: var(--panel);
    min-height: 104px;
}

.summary-heading {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 0.75rem;
}

.summary-label {
    color: var(--muted);
    font-size: 0.76rem;
    font-weight: 700;
    text-transform: uppercase;
}

.summary-value {
    color: var(--ink);
    font-size: 1.45rem;
    font-weight: 800;
    white-space: nowrap;
}

.record-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.42rem;
    margin-top: 0.65rem;
}

.record-item {
    border: 1px solid #edf0f3;
    border-radius: 6px;
    padding: 0.42rem 0.35rem;
    text-align: center;
    background: #fafbfc;
}

.record-number {
    color: var(--ink);
    font-size: 1.08rem;
    font-weight: 900;
    line-height: 1;
}

.record-label {
    color: var(--muted);
    font-size: 0.66rem;
    font-weight: 800;
    margin-top: 0.15rem;
    text-transform: uppercase;
}

div.stButton > button {
    border: 1px solid var(--soft-border);
    border-radius: 8px;
    min-height: 96px;
    white-space: pre-line;
    text-align: left;
    padding: 0.65rem 0.7rem;
    color: var(--ink);
    background: #ffffff;
    box-shadow: none;
}

div.stButton > button:hover {
    border-color: var(--freiburg-red);
    color: var(--ink);
}

div.stButton > button[kind="primary"] {
    background: var(--freiburg-red);
    color: white;
    border-color: var(--freiburg-red);
}

.match-strip {
    display: flex;
    gap: 0.8rem;
    overflow-x: auto;
    overscroll-behavior-x: contain;
    scroll-snap-type: x proximity;
    padding: 0.15rem 0 0.9rem;
    margin: 0.1rem 0 0.65rem;
}

.match-strip::-webkit-scrollbar {
    height: 10px;
}

.match-strip::-webkit-scrollbar-track {
    background: #edf0f3;
    border-radius: 999px;
}

.match-strip::-webkit-scrollbar-thumb {
    background: #aeb7c2;
    border-radius: 999px;
}

.match-card {
    flex: 0 0 236px;
    scroll-snap-align: start;
    display: grid;
    grid-template-rows: auto 1fr auto;
    gap: 0.45rem;
    min-height: 124px;
    border: 1px solid var(--soft-border);
    border-radius: 8px;
    padding: 0.7rem;
    background: #ffffff;
    color: var(--ink);
    text-decoration: none;
}

.match-card,
.match-card:visited,
.match-card:hover,
.match-card:active,
.match-card * {
    text-decoration: none !important;
}

.match-card:hover {
    border-color: var(--freiburg-red);
    box-shadow: 0 10px 24px rgba(21, 23, 26, 0.08);
}

.match-card-active {
    border-color: var(--freiburg-red);
    box-shadow: inset 0 0 0 2px var(--freiburg-red);
}

.match-card-meta {
    display: flex;
    justify-content: space-between;
    color: var(--muted);
    font-size: 0.72rem;
    font-weight: 800;
    text-transform: uppercase;
}

.match-card-meta .result-pill {
    margin-top: 0;
    padding: 0.12rem 0.45rem;
    font-size: 0.68rem;
}

.match-card-score {
    display: grid;
    grid-template-columns: minmax(54px, 1fr) auto minmax(54px, 1fr);
    align-items: center;
    gap: 0.45rem;
}

.match-card-team {
    display: grid;
    justify-items: center;
    gap: 0.25rem;
    min-width: 0;
}

.match-card-team img {
    width: 34px;
    height: 34px;
    object-fit: contain;
}

.match-card-code {
    font-size: 0.84rem;
    font-weight: 900;
    overflow-wrap: anywhere;
}

.match-card-scoreline {
    min-width: 62px;
    text-align: center;
    font-size: 1.3rem;
    font-weight: 950;
    line-height: 1;
}

.match-card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.5rem;
    color: var(--muted);
    font-size: 0.76rem;
    font-weight: 800;
}

.scoreboard {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
    align-items: center;
    gap: 1rem;
    border: 1px solid var(--soft-border);
    border-radius: 8px;
    padding: 1.1rem;
    background: var(--panel);
}

.team-name {
    font-size: clamp(1.05rem, 2vw, 1.45rem);
    font-weight: 800;
    overflow-wrap: anywhere;
}

.scoreboard-team {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    min-width: 0;
}

.scoreboard-team-away {
    justify-content: flex-end;
}

.scoreboard-team-away .scoreboard-team-text {
    text-align: right;
}

.scoreboard-logo {
    width: 58px;
    height: 58px;
    object-fit: contain;
    flex: 0 0 58px;
}

.scoreboard-center {
    display: grid;
    justify-items: center;
    text-align: center;
}

.team-meta {
    color: var(--muted);
    font-size: 0.85rem;
    margin-top: 0.15rem;
}

.scoreline {
    min-width: 132px;
    text-align: center;
    color: var(--ink);
    font-size: clamp(2rem, 5vw, 3.2rem);
    font-weight: 900;
    line-height: 1;
}

.result-pill {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    padding: 0.25rem 0.55rem;
    margin-top: 0.45rem;
    background: var(--wash);
    color: var(--ink);
    font-size: 0.78rem;
    font-weight: 800;
}

.result-W {
    background: #e7f6ee;
    color: #087443;
}

.result-D {
    background: #fff4dc;
    color: #9a5b00;
}

.result-L {
    background: #ffe8e8;
    color: #b42318;
}

.detail-link {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    min-height: 50px;
    margin: 0.9rem 0 0.35rem;
    padding: 0.65rem 0.9rem;
    border: 1px solid var(--freiburg-red);
    border-radius: 8px;
    background: #fff3f5;
    color: var(--freiburg-red) !important;
    font-size: 0.92rem;
    font-weight: 900;
    text-decoration: none !important;
}

.detail-link:hover {
    background: var(--freiburg-red);
    color: #ffffff !important;
}

[data-testid="stSegmentedControl"] {
    width: 100%;
    margin: 0.95rem 0 1rem;
}

[data-testid="stSegmentedControl"] > div {
    width: 100%;
}

[data-testid="stSegmentedControl"] [role="radiogroup"] {
    display: flex;
    width: 100%;
    gap: 0;
    overflow: hidden;
    border: 1px solid var(--soft-border);
    border-radius: 8px;
    background: #ffffff;
}

[data-testid="stSegmentedControl"] [role="radiogroup"] button,
[data-testid="stSegmentedControl"] [role="radiogroup"] label {
    flex: 1 1 0;
    justify-content: center;
    min-height: 42px;
    border-radius: 0;
    text-align: center;
}

[data-testid="stSegmentedControl"] [role="radiogroup"] button p,
[data-testid="stSegmentedControl"] [role="radiogroup"] label p {
    width: 100%;
    text-align: center;
}

.stat-row {
    display: grid;
    grid-template-columns: minmax(72px, 0.35fr) minmax(110px, 0.3fr) minmax(72px, 0.35fr);
    gap: 0.75rem;
    align-items: center;
    border-bottom: 1px solid #edf0f3;
    padding: 0.65rem 0;
}

.stat-row:last-child {
    border-bottom: 0;
}

.stat-value {
    font-size: 1.02rem;
    font-weight: 850;
}

.stat-name {
    color: var(--muted);
    font-size: 0.86rem;
    font-weight: 750;
    text-align: center;
}

.align-right {
    text-align: right;
}

.event-chip {
    display: inline-block;
    border: 1px solid var(--soft-border);
    border-radius: 999px;
    padding: 0.14rem 0.5rem;
    margin-right: 0.25rem;
    color: var(--muted);
    font-size: 0.76rem;
    font-weight: 700;
}

.league-table-wrap {
    border: 1px solid var(--soft-border);
    border-radius: 8px;
    overflow-x: auto;
    background: #ffffff;
}

.league-table {
    width: 100%;
    min-width: 1040px;
    border-collapse: collapse;
}

.league-table th {
    background: #f5f7f9;
    color: var(--muted);
    font-size: 0.74rem;
    font-weight: 850;
    padding: 0.62rem 0.65rem;
    text-align: right;
    text-transform: uppercase;
}

.league-table th:nth-child(2) {
    text-align: left;
}

.league-table td {
    border-top: 1px solid #edf0f3;
    color: var(--ink);
    font-size: 0.88rem;
    font-weight: 700;
    padding: 0.62rem 0.65rem;
    text-align: right;
}

.league-table td:nth-child(2) {
    text-align: left;
}

.league-table-club {
    display: flex;
    align-items: center;
    gap: 0.55rem;
    min-width: 0;
}

.league-table-logo {
    width: 26px;
    height: 26px;
    object-fit: contain;
    flex: 0 0 26px;
}

.league-table-freiburg td {
    background: #fff3f5;
    color: #8f1020;
}

.league-table-points {
    font-weight: 950;
}

.league-table-model {
    color: #344054;
    font-variant-numeric: tabular-nums;
}

.model-summary {
    display: grid;
    grid-template-columns: minmax(0, 1.25fr) repeat(2, minmax(0, 0.8fr));
    gap: 0.65rem;
    margin: 0 0 1rem;
}

.model-summary > div {
    border: 1px solid var(--soft-border);
    border-radius: 8px;
    padding: 0.68rem 0.78rem;
    background: #ffffff;
}

.model-summary span {
    display: block;
    color: var(--muted);
    font-size: 0.7rem;
    font-weight: 800;
    text-transform: uppercase;
}

.model-summary strong {
    display: block;
    color: var(--ink);
    font-size: 0.9rem;
    font-weight: 900;
    margin-top: 0.12rem;
    overflow-wrap: anywhere;
}

.advanced-pitch {
    width: 100%;
    max-width: 980px;
    margin: 0.75rem auto 1rem;
    border: 1px solid var(--soft-border);
    border-radius: 8px;
    overflow: hidden;
    background: #1f6f45;
}

.advanced-pitch svg {
    display: block;
    width: 100%;
    height: auto;
}

.lineup-pitch {
    position: relative;
    width: 100%;
    max-width: 560px;
    aspect-ratio: 72 / 100;
    min-height: 520px;
    margin: 0.4rem auto 1rem;
    overflow: hidden;
    border: 2px solid rgba(255, 255, 255, 0.9);
    border-radius: 8px;
    background:
        linear-gradient(rgba(255,255,255,0.16) 2px, transparent 2px) 0 50% / 100% 2px no-repeat,
        linear-gradient(90deg, rgba(255,255,255,0.12), rgba(255,255,255,0.12)) 0 0 / 100% 100%,
        repeating-linear-gradient(
            90deg,
            #2f8f53 0,
            #2f8f53 13%,
            #2b844d 13%,
            #2b844d 26%
        );
    box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.35);
}

.lineup-pitch::before,
.lineup-pitch::after {
    content: "";
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    border: 2px solid rgba(255, 255, 255, 0.72);
    pointer-events: none;
}

.lineup-pitch::before {
    top: -2px;
    width: 58%;
    height: 15%;
    border-top: 0;
}

.lineup-pitch::after {
    bottom: -2px;
    width: 58%;
    height: 15%;
    border-bottom: 0;
}

.pitch-center-circle {
    position: absolute;
    left: 50%;
    top: 50%;
    width: 26%;
    aspect-ratio: 1;
    transform: translate(-50%, -50%);
    border: 2px solid rgba(255, 255, 255, 0.72);
    border-radius: 50%;
}

.player-marker {
    position: absolute;
    display: grid;
    justify-items: center;
    gap: 0.18rem;
    width: 76px;
    transform: translate(-50%, -50%);
    color: #ffffff;
    text-align: center;
}

.player-shirt {
    display: grid;
    place-items: center;
    width: 34px;
    height: 34px;
    border: 2px solid rgba(255, 255, 255, 0.95);
    border-radius: 50%;
    background: var(--freiburg-red);
    color: #ffffff;
    font-size: 0.86rem;
    font-weight: 900;
    box-shadow: 0 3px 9px rgba(0, 0, 0, 0.28);
}

.player-name {
    max-width: 76px;
    padding: 0.08rem 0.28rem;
    border-radius: 4px;
    background: rgba(21, 23, 26, 0.68);
    font-size: 0.68rem;
    font-weight: 800;
    line-height: 1.1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.lineup-note {
    color: var(--muted);
    font-size: 0.78rem;
    margin: -0.25rem 0 0.6rem;
    text-align: center;
}

.sub-table {
    width: 100%;
    border-collapse: collapse;
    overflow: hidden;
    border: 1px solid #edf0f3;
    border-radius: 8px;
    background: #ffffff;
}

.sub-table th {
    background: #f5f7f9;
    color: var(--muted);
    font-size: 0.72rem;
    font-weight: 850;
    padding: 0.55rem 0.6rem;
    text-align: left;
    text-transform: uppercase;
}

.sub-table td {
    border-top: 1px solid #edf0f3;
    color: var(--ink);
    font-size: 0.84rem;
    font-weight: 700;
    padding: 0.55rem 0.6rem;
}

.sub-move {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 52px;
    border-radius: 999px;
    padding: 0.18rem 0.44rem;
    font-size: 0.78rem;
    font-weight: 900;
}

.sub-in {
    background: #e7f6ee;
    color: #087443;
}

.sub-out {
    background: #ffe8e8;
    color: #b42318;
}

.sub-moved {
    background: #edf0f3;
    color: #344054;
}

.radar-wrap {
    display: grid;
    grid-template-columns: minmax(280px, 0.7fr) minmax(240px, 0.3fr);
    gap: 1rem;
    align-items: center;
}

.radar-wrap svg {
    width: 100%;
    max-height: 520px;
}

.radar-values {
    width: 100%;
    border-collapse: collapse;
}

.radar-values th {
    background: #f5f7f9;
    color: var(--muted);
    font-size: 0.72rem;
    font-weight: 850;
    padding: 0.48rem 0.55rem;
    text-align: right;
    text-transform: uppercase;
}

.radar-values th:first-child {
    text-align: left;
}

.radar-values td {
    border-top: 1px solid #edf0f3;
    color: var(--ink);
    font-size: 0.84rem;
    font-weight: 700;
    padding: 0.48rem 0.55rem;
    text-align: right;
}

.radar-values td:first-child {
    text-align: left;
}

@media (max-width: 700px) {
    .scoreboard {
        grid-template-columns: 1fr;
        text-align: center;
    }

    .scoreline {
        min-width: 0;
    }

    .scoreboard-team,
    .scoreboard-team-away {
        justify-content: center;
    }

    .scoreboard-team-away .scoreboard-team-text {
        text-align: center;
    }

    .stat-row {
        grid-template-columns: 1fr;
        text-align: center;
        gap: 0.15rem;
    }

    .align-right {
        text-align: center;
    }

    .lineup-pitch {
        min-height: 460px;
    }

    .model-summary {
        grid-template-columns: 1fr;
    }

    .radar-wrap {
        grid-template-columns: 1fr;
    }
}
</style>
"""


def apply_styles() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
