"""Shared visual theme for the Streamlit dashboard."""

import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=STIX+Two+Text:wght@400;600&family=Source+Code+Pro:wght@400;600&display=swap');

:root {
    --ns-primary: #BBF351;
    --ns-secondary: #00BCFF;
    --ns-danger: #DC2626;
    --ns-warning: #D97706;
    --ns-success: #16A34A;
    --ns-surface: #141414;
    --ns-bg: #0A0A0A;
    --ns-bg-accent: #101719;
    --ns-text: #F0F0F0;
    --ns-text-muted: #9CA3AF;
    --ns-border: #2A2A2A;
    --ns-font-body: 'Roboto', sans-serif;
    --ns-font-display: 'STIX Two Text', serif;
    --ns-font-mono: 'Source Code Pro', monospace;
}

html,
body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"],
[data-testid="stMain"] {
    font-family: var(--ns-font-body) !important;
    background:
        radial-gradient(circle at top left, rgba(0,188,255,0.08), transparent 26%),
        radial-gradient(circle at top right, rgba(187,243,81,0.08), transparent 24%),
        linear-gradient(180deg, var(--ns-bg-accent), var(--ns-bg)) !important;
    color: var(--ns-text) !important;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

[data-testid="stMainBlockContainer"] {
    max-width: 1200px;
    padding-top: 2.2rem;
    padding-bottom: 3rem;
}

h1 {
    font-family: var(--ns-font-display) !important;
    color: var(--ns-primary) !important;
    text-shadow: 0 0 24px rgba(187, 243, 81, 0.45);
    letter-spacing: -0.02em;
}

h2, h3, h4 {
    font-family: var(--ns-font-display) !important;
    color: var(--ns-text) !important;
}

p, li, label, span, div {
    color: var(--ns-text);
}

a {
    color: var(--ns-secondary) !important;
}

.ns-hero {
    padding: 1.5rem 0 1rem 0;
}

.ns-kicker {
    margin-bottom: 0.6rem;
    color: var(--ns-secondary);
    font-family: var(--ns-font-mono);
    font-size: 0.82rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
}

.ns-subtle,
.ns-muted,
[data-testid="stCaptionContainer"] {
    color: var(--ns-text-muted) !important;
}

[data-testid="stSidebar"] {
    background: rgba(20, 20, 20, 0.94) !important;
    border-right: 1px solid var(--ns-border) !important;
}

[data-testid="stSidebar"] h3 {
    color: var(--ns-primary) !important;
    font-family: var(--ns-font-display) !important;
}

[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem;
}

[data-testid="metric-container"] {
    background: linear-gradient(180deg, rgba(20,20,20,0.95), rgba(10,10,10,0.92)) !important;
    border: 1px solid var(--ns-border) !important;
    border-radius: 10px !important;
    padding: 1rem !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
}

[data-testid="metric-container"] label {
    color: var(--ns-text-muted) !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

[data-testid="stMetricValue"] {
    color: var(--ns-primary) !important;
    font-family: var(--ns-font-display) !important;
    text-shadow: 0 0 14px rgba(187,243,81,0.24);
}

[data-testid="baseButton-primary"] {
    background: rgba(187,243,81,0.06) !important;
    color: var(--ns-primary) !important;
    border: 1px solid rgba(187,243,81,0.9) !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease !important;
}

[data-testid="baseButton-primary"]:hover {
    transform: translateY(-1px);
    background: rgba(187,243,81,0.12) !important;
    box-shadow: 0 0 18px rgba(187,243,81,0.28) !important;
}

[data-testid="baseButton-secondary"] {
    background: rgba(20,20,20,0.85) !important;
    color: var(--ns-text-muted) !important;
    border: 1px solid var(--ns-border) !important;
    border-radius: 6px !important;
}

[data-testid="baseButton-secondary"]:hover {
    color: var(--ns-secondary) !important;
    border-color: rgba(0,188,255,0.55) !important;
}

[data-testid="stDownloadButton"] button {
    background: rgba(0,188,255,0.06) !important;
    color: var(--ns-secondary) !important;
    border: 1px solid rgba(0,188,255,0.7) !important;
    border-radius: 6px !important;
}

.stCodeBlock,
code,
pre {
    font-family: var(--ns-font-mono) !important;
    background: #0D0D0D !important;
    border: 1px solid var(--ns-border) !important;
    color: var(--ns-text) !important;
}

[data-testid="stExpander"] {
    border: 1px solid var(--ns-border) !important;
    border-radius: 8px !important;
    background: rgba(20,20,20,0.88) !important;
}

[data-testid="stExpander"] summary {
    color: var(--ns-text) !important;
}

[data-testid="stTabs"] [role="tablist"] {
    gap: 0.25rem;
}

[data-testid="stTabs"] [role="tab"] {
    color: var(--ns-text-muted) !important;
    font-family: var(--ns-font-body) !important;
    border-radius: 6px 6px 0 0 !important;
}

[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: var(--ns-primary) !important;
    border-bottom: 2px solid var(--ns-primary) !important;
}

hr {
    border-color: var(--ns-border) !important;
}

[data-testid="stDataFrame"],
[data-testid="stTable"] {
    border: 1px solid var(--ns-border) !important;
    border-radius: 8px !important;
    overflow: hidden;
}

[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input {
    background: rgba(20,20,20,0.95) !important;
    border: 1px solid var(--ns-border) !important;
    border-radius: 6px !important;
    color: var(--ns-text) !important;
    font-family: var(--ns-font-body) !important;
}

[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus,
[data-testid="stNumberInput"] input:focus,
[data-testid="stDateInput"] input:focus {
    border-color: var(--ns-primary) !important;
    box-shadow: 0 0 0 1px rgba(187,243,81,0.55) !important;
}

[data-testid="stSelectbox"] div[data-baseweb="select"],
[data-testid="stMultiSelect"] div[data-baseweb="select"] {
    background: rgba(20,20,20,0.95) !important;
    border: 1px solid var(--ns-border) !important;
    border-radius: 6px !important;
}

[data-testid="stAlert"] {
    border-radius: 8px !important;
    border: 1px solid var(--ns-border) !important;
    background: rgba(20,20,20,0.92) !important;
}

.ns-tag {
    display: inline-block;
    padding: 0.22rem 0.85rem;
    border-radius: 3px;
    font-size: 0.75rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-weight: 700;
    font-family: var(--ns-font-mono);
    border: 1.5px solid currentColor;
}

.ns-tag.good {
    color: var(--ns-primary);
    box-shadow: 0 0 8px rgba(187,243,81,0.3), inset 0 0 8px rgba(187,243,81,0.05);
}

.ns-tag.info {
    color: var(--ns-secondary);
    box-shadow: 0 0 8px rgba(0,188,255,0.3), inset 0 0 8px rgba(0,188,255,0.05);
}

.ns-tag.warn {
    color: #F59E0B;
    box-shadow: 0 0 8px rgba(245,158,11,0.28), inset 0 0 8px rgba(245,158,11,0.05);
}

.ns-tag.bad {
    color: var(--ns-danger);
    animation: neon-pulse 2s ease-in-out infinite;
}

.ns-tag.idle {
    color: #6B7280;
    border-color: #3A3A3A;
}

@keyframes neon-pulse {
    0%, 100% { box-shadow: 0 0 8px rgba(220,38,38,0.3); }
    50% { box-shadow: 0 0 18px rgba(220,38,38,0.65); }
}

.ns-card {
    background: linear-gradient(180deg, rgba(20,20,20,0.94), rgba(12,12,12,0.9));
    border: 1px solid var(--ns-border);
    border-radius: 10px;
    padding: 1.15rem 1.25rem;
    margin-bottom: 1rem;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.ns-card:hover {
    border-color: rgba(187,243,81,0.4);
    box-shadow: 0 0 18px rgba(187,243,81,0.08);
}

.ns-card-title {
    display: block;
    margin-bottom: 0.55rem;
    font-family: var(--ns-font-display);
    font-size: 1rem;
    color: var(--ns-primary);
    letter-spacing: 0.02em;
}

.ns-card p:last-child {
    margin-bottom: 0;
}

.ns-badge-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.ns-nav-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.95rem;
}

.ns-nav-table th,
.ns-nav-table td {
    padding: 0.72rem 0.85rem;
    border-bottom: 1px solid var(--ns-border);
    text-align: left;
    vertical-align: top;
}

.ns-nav-table th {
    color: var(--ns-text-muted);
    font-family: var(--ns-font-mono);
    font-size: 0.76rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.ns-nav-table tr:last-child td {
    border-bottom: 0;
}

.ns-nav-table td:first-child {
    color: var(--ns-primary);
    font-weight: 600;
}

.ns-status-line {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
}
</style>
"""


def apply_theme() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
