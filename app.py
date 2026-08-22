"""
app.py — Forensic Data Agent: Streamlit Dashboard
===================================================
Core Narrative:
  LEFT  COLUMN  → Raw Evidence Graph (conflicting, unresolved multi-source claims)
  RIGHT COLUMN  → Truth Log Panel (canonical values, anomaly alerts, rejection explanations)
"""

import math
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import streamlit as st
import pandas as pd

# ── Engine import ──────────────────────────────────────────────────────────────
try:
    from engine import (
        EvidenceGraphStore,
        EvidenceClaim,
        EvidenceProperty,
        ProductEvidenceSnapshot,
        SourceType,
        ForensicAnomalyObject,
        AnomalySeverity,
        ForensicAgentPipeline,
        ResolutionResult,
        NormalizationAuditTrail,
        normalize_unit,
        build_demo_store,
    )
except ImportError as e:
    st.error(f"❌ Failed to import engine.py: {e}")
    st.stop()

try:
    from mock_data import HACKATHON_DEMO_CASES
except ImportError:
    HACKATHON_DEMO_CASES = None

# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE CONFIG & GLOBAL STYLES
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Forensic Data Agent | Industrial Intelligence",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Determine theme BEFORE CSS injection ──
_params = st.query_params
_is_dark = _params.get("theme", "dark") != "light"

# ── Theme color palettes ──
if _is_dark:
    C_BG_BASE      = "#100e0c"
    C_BG_PANEL     = "#161210"
    C_BG_CARD      = "#1e1a17"
    C_BG_INSET     = "#252019"
    C_BG_POPOVER   = "#1a1612"
    C_ACCENT_FIRE  = "#e85d04"
    C_ACCENT_TEAL  = "#00b4d8"
    C_ACCENT_GOLD  = "#f4a261"
    C_ACCENT_GREEN = "#52b788"
    C_ACCENT_RED   = "#e63946"
    C_BORDER       = "#3d3530"
    C_TEXT_PRIMARY  = "#d4cfc9"
    C_TEXT_MUTED    = "#7a6f68"
    C_TEXT_DIM      = "#4a4038"
    C_SIDEBAR_BG   = "#141210"
    C_SIDEBAR_CARD = "#1e1a17"
    C_HERO_GRAD    = "linear-gradient(118deg, #1f1a16 0%, #130f0b 55%, #1a1410 100%)"
    C_GRID_ALPHA   = "0.022"
    C_TRUTH_VAL    = "#52b788"
    C_CODE_BG      = "#252019"
    C_CODE_FG      = "#00b4d8"
    C_HOVER_BG     = "#252019"
else:
    C_BG_BASE      = "#f5f0eb"
    C_BG_PANEL     = "#ede7df"
    C_BG_CARD      = "#fff8f2"
    C_BG_INSET     = "#e8e0d6"
    C_BG_POPOVER   = "#fff8f2"
    C_ACCENT_FIRE  = "#c44b02"
    C_ACCENT_TEAL  = "#0077a8"
    C_ACCENT_GOLD  = "#b5541a"
    C_ACCENT_GREEN = "#2d6a4f"
    C_ACCENT_RED   = "#b5202c"
    C_BORDER       = "#c9bfb5"
    C_TEXT_PRIMARY  = "#1a1410"
    C_TEXT_MUTED    = "#6b5d52"
    C_TEXT_DIM      = "#9c8b80"
    C_SIDEBAR_BG   = "#ede7df"
    C_SIDEBAR_CARD = "#fff8f2"
    C_HERO_GRAD    = "linear-gradient(118deg, #fffaf5 0%, #f5ede3 55%, #fdf6ef 100%)"
    C_GRID_ALPHA   = "0.04"
    C_TRUTH_VAL    = "#2d6a4f"
    C_CODE_BG      = "#e8e0d6"
    C_CODE_FG      = "#0077a8"
    C_HOVER_BG     = "#e8e0d6"

st.markdown(f"""
<style>
:root {{
    --bg-base:      {C_BG_BASE};
    --bg-panel:     {C_BG_PANEL};
    --bg-card:      {C_BG_CARD};
    --bg-inset:     {C_BG_INSET};
    --bg-popover:   {C_BG_POPOVER};
    --accent-fire:  {C_ACCENT_FIRE};
    --accent-teal:  {C_ACCENT_TEAL};
    --accent-gold:  {C_ACCENT_GOLD};
    --accent-green: {C_ACCENT_GREEN};
    --accent-red:   {C_ACCENT_RED};
    --border-main:  {C_BORDER};
    --text-primary: {C_TEXT_PRIMARY};
    --text-muted:   {C_TEXT_MUTED};
    --text-dim:     {C_TEXT_DIM};
}}

/* ═══════════════════════════════════════════════════════════
   FORENSIC DATA AGENT — Industrial Terminal (Theme-Aware)
   ═══════════════════════════════════════════════════════════ */
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:ital,wght@0,300;0,400;0,500;0,600;1,400&family=Syne:wght@700;800&family=Barlow:wght@300;400;500;600&display=swap');

/* ═══ 1. BASE — force theme on EVERY container ═══ */
html, body,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
[data-testid="stVerticalBlock"],
[data-testid="stBottomBlockContainer"],
[data-testid="stHorizontalBlock"],
.main .block-container,
.main,
section.main,
div.block-container {{
    background-color: {C_BG_BASE} !important;
    color: {C_TEXT_PRIMARY} !important;
    font-family: 'Barlow', sans-serif !important;
}}
.element-container,
.stMarkdown,
[data-testid="stMarkdownContainer"] {{
    background-color: transparent !important;
    color: {C_TEXT_PRIMARY} !important;
    font-family: 'Barlow', sans-serif !important;
}}

/* Streamlit top decoration bar */
[data-testid="stDecoration"] {{ display: none !important; }}
header[data-testid="stHeader"] {{
    background: {C_BG_BASE} !important;
    border-bottom: 1px solid {C_BORDER} !important;
}}
[data-testid="stToolbar"] {{
    background: {C_BG_BASE} !important;
}}
[data-testid="stToolbar"] button {{
    color: {C_TEXT_MUTED} !important;
}}

/* ═══ 2. CIRCUIT GRID BACKGROUND ═══ */
[data-testid="stMain"]::before,
.main::before {{
    content: '';
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(232,93,4,{C_GRID_ALPHA}) 1px, transparent 1px),
        linear-gradient(90deg, rgba(232,93,4,{C_GRID_ALPHA}) 1px, transparent 1px);
    background-size: 52px 52px;
    pointer-events: none;
    z-index: 0;
}}

/* ═══ 3. SIDEBAR ═══ */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] * {{
    --background-color: {C_SIDEBAR_BG} !important;
    --secondary-background-color: {C_SIDEBAR_CARD} !important;
    --text-color: {C_TEXT_PRIMARY} !important;
    --primary-color: {C_ACCENT_FIRE} !important;
}}
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] > div > div,
section[data-testid="stSidebar"] .stMarkdown {{
    background: {C_SIDEBAR_BG} !important;
    background-color: {C_SIDEBAR_BG} !important;
    border-right: 1px solid {C_BORDER} !important;
}}
section[data-testid="stSidebar"] *:not(.hero-badge):not(button) {{
    color: {C_TEXT_PRIMARY} !important;
}}
section[data-testid="stSidebar"] .stMarkdown h3 {{
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.68rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: {C_TEXT_MUTED} !important;
    border-bottom: 1px solid {C_BORDER} !important;
    padding-bottom: 6px !important;
}}
section[data-testid="stSidebar"] hr {{
    border-color: {C_BORDER} !important;
    opacity: 0.5;
}}

/* ── App-wide Inputs ── */
input,
div[data-baseweb="input"],
div[data-baseweb="input"] > div {{
    background: {C_BG_CARD} !important;
    background-color: {C_BG_CARD} !important;
    border-color: {C_BORDER} !important;
    color: {C_TEXT_PRIMARY} !important;
}}
input:focus,
div[data-baseweb="input"]:focus-within {{
    border-color: {C_ACCENT_FIRE} !important;
    box-shadow: 0 0 0 2px rgba(232,93,4,0.15) !important;
}}
/* ── App-wide Selectbox ── */
[data-baseweb="select"] > div,
[data-baseweb="select"] > div > div {{
    background: {C_BG_CARD} !important;
    background-color: {C_BG_CARD} !important;
    border-color: {C_BORDER} !important;
    color: {C_TEXT_PRIMARY} !important;
}}
[data-baseweb="select"] span,
[data-baseweb="select"] [role="combobox"] {{
    color: {C_TEXT_PRIMARY} !important;
    background: transparent !important;
    background-color: transparent !important;
}}
/* Dropdown popup */
[data-baseweb="popover"] > div,
[data-baseweb="menu"],
[role="listbox"],
[data-baseweb="popover"] [role="option"] {{
    background: {C_BG_POPOVER} !important;
    background-color: {C_BG_POPOVER} !important;
    border-color: {C_BORDER} !important;
    color: {C_TEXT_PRIMARY} !important;
}}
[data-baseweb="popover"] [role="option"]:hover,
[aria-selected="true"] {{
    background: {C_HOVER_BG} !important;
    background-color: {C_HOVER_BG} !important;
    color: {C_ACCENT_FIRE} !important;
}}
/* Slider */
section[data-testid="stSidebar"] [data-testid="stSlider"] [role="slider"] {{
    background: {C_ACCENT_FIRE} !important;
    background-color: {C_ACCENT_FIRE} !important;
    border-color: {C_ACCENT_FIRE} !important;
}}
section[data-testid="stSidebar"] [data-testid="stSlider"] [data-baseweb="slider"] div[class*="SliderBar"] {{
    background: {C_ACCENT_FIRE} !important;
    background-color: {C_ACCENT_FIRE} !important;
}}
/* ── App-wide Radio ── */
[data-testid="stRadio"] label,
[data-testid="stRadio"] p {{
    color: {C_TEXT_PRIMARY} !important;
}}
[data-testid="stRadio"] div[role="radio"][aria-checked="false"] {{
    background: transparent !important;
    background-color: transparent !important;
    border-color: {C_BORDER} !important;
}}
/* Number input buttons */
section[data-testid="stSidebar"] button[data-testid="stNumberInputStepDown"],
section[data-testid="stSidebar"] button[data-testid="stNumberInputStepUp"] {{
    background: {C_HOVER_BG} !important;
    background-color: {C_HOVER_BG} !important;
    border-color: {C_BORDER} !important;
    color: {C_TEXT_MUTED} !important;
}}
/* Sidebar run button */
section[data-testid="stSidebar"] .stButton > button {{
    background: transparent !important;
    color: {C_ACCENT_FIRE} !important;
    border: 1px solid {C_ACCENT_FIRE} !important;
    border-radius: 2px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    transition: all 0.15s !important;
    padding: 10px 14px !important;
    width: 100% !important;
}}
section[data-testid="stSidebar"] .stButton > button:hover {{
    background: {C_ACCENT_FIRE} !important;
    color: #fff !important;
    box-shadow: 0 0 18px rgba(232,93,4,0.35) !important;
}}
/* Theme toggle button (different style) */
section[data-testid="stSidebar"] .stButton:first-child > button {{
    border-color: {C_BORDER} !important;
    color: {C_TEXT_MUTED} !important;
    font-size: 0.7rem !important;
    padding: 5px 10px !important;
    margin-bottom: 4px !important;
}}
section[data-testid="stSidebar"] .stButton:first-child > button:hover {{
    background: {C_HOVER_BG} !important;
    color: {C_TEXT_PRIMARY} !important;
}}

/* ═══ 5. HERO BANNER ═══ */
.hero-banner {{
    background: {C_HERO_GRAD} !important;
    border: 1px solid {C_BORDER};
    border-top: 3px solid {C_ACCENT_FIRE};
    border-radius: 3px;
    padding: 38px 46px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}}
.hero-banner::before {{
    content: '';
    position: absolute;
    top: 0; left: -60%;
    width: 55%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(232,93,4,0.035), transparent);
    animation: scanline 4.5s ease-in-out infinite;
    pointer-events: none;
}}
.hero-banner::after {{
    content: '';
    position: absolute;
    inset: 0;
    background:
        radial-gradient(ellipse 55% 80% at 88% 50%, rgba(232,93,4,0.065) 0%, transparent 65%),
        radial-gradient(ellipse 35% 60% at 10% 50%, rgba(0,180,216,0.04) 0%, transparent 60%);
    pointer-events: none;
}}
@keyframes scanline {{
    0%   {{ left: -60%; }}
    100% {{ left: 115%; }}
}}
.hero-eyebrow {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    font-weight: 500;
    letter-spacing: 0.2em;
    color: {C_ACCENT_FIRE};
    text-transform: uppercase;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 12px;
}}
.hero-eyebrow::before, .hero-eyebrow::after {{
    content: '';
    display: inline-block;
    height: 1px;
    width: 28px;
    background: {C_ACCENT_FIRE};
    opacity: 0.5;
}}
.hero-title {{
    font-family: 'Syne', 'IBM Plex Mono', sans-serif;
    font-size: 2.8rem;
    font-weight: 800;
    color: {C_TEXT_PRIMARY};
    letter-spacing: -1.5px;
    line-height: 1.05;
    margin: 0 0 14px 0;
    display: block;
}}
.hero-title-fire {{
    color: {C_ACCENT_FIRE};
    display: inline;
}}
.hero-badge {{
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: rgba(232,93,4,0.1);
    border: 1px solid rgba(232,93,4,0.32);
    border-radius: 2px;
    padding: 5px 14px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    color: {C_ACCENT_FIRE};
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 18px;
    position: relative;
    z-index: 1;
}}
.hero-thesis {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.88rem;
    color: {C_TEXT_MUTED};
    margin: 0;
    line-height: 1.65;
    max-width: 660px;
    position: relative;
    z-index: 1;
}}
.hero-thesis em {{
    color: {C_ACCENT_GOLD};
    font-style: normal;
    font-weight: 500;
}}

/* ═══ 6. METRIC TILES ═══ */
.metric-tile {{
    background: {C_BG_PANEL};
    border: 1px solid {C_BORDER};
    border-top: 2px solid rgba(232,93,4,0.5);
    border-radius: 2px;
    padding: 20px 16px;
    text-align: center;
}}
.metric-number {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2.4rem;
    font-weight: 600;
    color: {C_ACCENT_FIRE};
    line-height: 1;
    letter-spacing: -1px;
}}
.metric-label {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.62rem;
    color: {C_TEXT_MUTED};
    margin-top: 7px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}}

/* ═══ 7. SECTION HEADERS ═══ */
.section-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 11px 16px;
    border-radius: 2px;
    margin-bottom: 18px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}}
.section-evidence {{
    background: rgba(230,57,70,0.07);
    border: 1px solid rgba(230,57,70,0.2);
    border-left: 3px solid {C_ACCENT_RED};
    color: {C_ACCENT_RED};
}}
.section-truth {{
    background: rgba(82,183,136,0.07);
    border: 1px solid rgba(82,183,136,0.2);
    border-left: 3px solid {C_ACCENT_GREEN};
    color: {C_ACCENT_GREEN};
}}

/* ═══ 8. CLAIM CARDS ═══ */
.claim-card {{
    background: {C_BG_CARD};
    border-radius: 2px;
    padding: 14px 16px;
    margin-bottom: 8px;
    border: 1px solid {C_BORDER};
    border-left: 3px solid {C_BORDER};
}}
.claim-card.pdf_manual    {{ border-left-color: #7b68ee; }}
.claim-card.catalog_table {{ border-left-color: #00b4d8; }}
.claim-card.legacy_scrape {{ border-left-color: #f4a261; }}
.claim-card.erp_api       {{ border-left-color: #52b788; }}
.claim-card.winner {{
    border-left-color: {C_ACCENT_FIRE};
    background: linear-gradient(90deg, rgba(232,93,4,0.08) 0%, {C_BG_CARD} 45%);
}}
.claim-value {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.12rem;
    color: {C_TEXT_PRIMARY};
    font-weight: 500;
    letter-spacing: -0.3px;
}}
.claim-source {{
    font-size: 0.74rem;
    color: {C_TEXT_MUTED};
    margin-top: 5px;
    line-height: 1.55;
    font-family: 'Barlow', sans-serif;
}}
.claim-id {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.62rem;
    color: {C_TEXT_DIM};
    margin-top: 4px;
}}

/* ═══ 9. SCORE PILLS ═══ */
.score-pill {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 2px;
    font-size: 0.7rem;
    font-weight: 600;
    font-family: 'IBM Plex Mono', monospace;
    letter-spacing: 0.04em;
}}
.score-high {{ background: rgba(82,183,136,0.12);  color: {C_ACCENT_GREEN}; border: 1px solid rgba(82,183,136,0.28); }}
.score-mid  {{ background: rgba(0,180,216,0.12);    color: {C_ACCENT_TEAL}; border: 1px solid rgba(0,180,216,0.28); }}
.score-low  {{ background: rgba(230,57,70,0.10);    color: {C_ACCENT_RED}; border: 1px solid rgba(230,57,70,0.28); }}

/* ═══ 10. ANOMALY BOXES ═══ */
.anomaly-critical {{
    background: rgba(230,57,70,0.07);
    border: 1px solid rgba(230,57,70,0.28);
    border-left: 4px solid {C_ACCENT_RED};
    border-radius: 2px;
    padding: 16px 18px;
    margin-bottom: 12px;
}}
.anomaly-warning {{
    background: rgba(244,162,97,0.07);
    border: 1px solid rgba(244,162,97,0.28);
    border-left: 4px solid {C_ACCENT_GOLD};
    border-radius: 2px;
    padding: 16px 18px;
    margin-bottom: 12px;
}}
.anomaly-title {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.76rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    color: {C_ACCENT_RED};
    margin-bottom: 8px;
    text-transform: uppercase;
}}
.anomaly-warning .anomaly-title {{ color: {C_ACCENT_GOLD}; }}
.anomaly-desc {{ font-size: 0.82rem; color: {C_TEXT_PRIMARY}; line-height: 1.6; }}
.anomaly-hint {{ font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: {C_TEXT_MUTED}; margin-top: 10px; }}

/* ═══ 11. TRUTH CARDS ═══ */
.truth-card {{
    background: {C_BG_CARD};
    border: 1px solid {C_BORDER};
    border-bottom: 2px solid rgba(82,183,136,0.4);
    border-radius: 2px;
    padding: 18px 20px;
    margin-bottom: 12px;
}}
.truth-property {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    color: {C_TEXT_MUTED};
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 6px;
}}
.truth-value {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.9rem;
    font-weight: 600;
    color: {C_TRUTH_VAL};
    letter-spacing: -1px;
    line-height: 1;
}}
.truth-confidence {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: {C_TEXT_MUTED};
    margin-top: 8px;
}}

/* ═══ 12. REJECTION LOG ═══ */
.rejection-entry {{
    background: rgba(230,57,70,0.04);
    border-left: 2px solid rgba(230,57,70,0.28);
    padding: 7px 12px;
    margin-bottom: 5px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.66rem;
    color: {C_TEXT_MUTED};
    line-height: 1.5;
}}

/* ═══ 13. EXPANDER — all states ═══ */
[data-testid="stExpander"],
div[data-testid="stExpander"] {{
    background: {C_BG_CARD} !important;
    border: 1px solid {C_BORDER} !important;
    border-radius: 2px !important;
    overflow: hidden !important;
}}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] details summary,
div[data-testid="stExpander"] summary {{
    background: {C_BG_CARD} !important;
    color: {C_TEXT_PRIMARY} !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.8rem !important;
    padding: 11px 14px !important;
    border-radius: 0 !important;
}}
[data-testid="stExpander"] details[open] > summary,
div[data-testid="stExpander"] details[open] summary {{
    background: {C_BG_INSET} !important;
    border-bottom: 1px solid {C_BORDER} !important;
}}
[data-testid="stExpander"] summary p {{
    color: {C_TEXT_PRIMARY} !important;
    background: transparent !important;
    font-family: 'IBM Plex Mono', monospace !important;
}}
/* Inner content div */
[data-testid="stExpander"] details > div,
div[data-testid="stExpander"] > details > div {{
    background: {C_BG_CARD} !important;
    padding: 12px !important;
}}

/* ═══ 14. NATIVE ALERT BOXES ═══ */
[data-testid="stAlert"],
div[role="alert"],
div[data-baseweb="notification"] {{
    background: {C_BG_CARD} !important;
    border-radius: 2px !important;
    color: {C_TEXT_PRIMARY} !important;
    font-family: 'Barlow', sans-serif !important;
}}
/* Info */
[data-testid="stAlert"][data-type="info"],
.stInfo > div {{
    border-left: 3px solid {C_ACCENT_TEAL} !important;
    background: rgba(0,180,216,0.07) !important;
}}
/* Warning */
[data-testid="stAlert"][data-type="warning"],
.stWarning > div {{
    border-left: 3px solid {C_ACCENT_GOLD} !important;
    background: rgba(244,162,97,0.07) !important;
}}
/* Success */
[data-testid="stAlert"][data-type="success"],
.stSuccess > div {{
    border-left: 3px solid {C_ACCENT_GREEN} !important;
    background: rgba(82,183,136,0.07) !important;
}}
/* Error */
[data-testid="stAlert"][data-type="error"],
.stError > div {{
    border-left: 3px solid {C_ACCENT_RED} !important;
    background: rgba(230,57,70,0.07) !important;
}}
[data-testid="stAlert"] p,
[data-testid="stAlert"] span,
[data-testid="stAlert"] strong {{
    color: {C_TEXT_PRIMARY} !important;
    font-family: 'Barlow', sans-serif !important;
}}
/* Streamlit 1.62 specific alert wrapper */
div[data-testid="stCaptionContainer"] {{
    background: transparent !important;
}}
.element-container div[data-stale="false"] div:has(> [data-testid="stAlert"]) {{
    background: transparent !important;
}}

/* ═══ 15. DATAFRAMES ═══ */
[data-testid="stDataFrame"] > div,
[data-testid="stDataFrameResizable"],
.stDataFrame {{
    background: {C_BG_CARD} !important;
    border: 1px solid {C_BORDER} !important;
    border-radius: 2px !important;
}}
[data-testid="stDataFrame"] * {{
    color: {C_TEXT_PRIMARY} !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.74rem !important;
}}
/* Glide data grid cells */
.dvn-scroller,
[role="grid"],
[role="gridcell"],
[role="columnheader"] {{
    background: {C_BG_CARD} !important;
    border-color: {C_BORDER} !important;
}}
[role="columnheader"] {{
    background: {C_BG_PANEL} !important;
    color: {C_TEXT_MUTED} !important;
    font-size: 0.68rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    border-bottom: 1px solid {C_BORDER} !important;
}}
/* Element Toolbars */
.stElementToolbar,
[data-testid="stElementToolbar"],
[data-testid="stDataFrameToolbar"],
[data-testid="stElementToolbar"] > div,
[data-testid="stDataFrameToolbar"] > div {{
    background: {C_BG_POPOVER} !important;
    background-color: {C_BG_POPOVER} !important;
    border: 1px solid {C_BORDER} !important;
    border-radius: 4px !important;
}}
.stElementToolbar button,
[data-testid="stElementToolbar"] button,
[data-testid="stDataFrameToolbar"] button {{
    background: transparent !important;
    background-color: transparent !important;
    color: {C_TEXT_PRIMARY} !important;
}}
.stElementToolbar svg,
[data-testid="stElementToolbar"] svg,
[data-testid="stDataFrameToolbar"] svg {{
    color: {C_TEXT_PRIMARY} !important;
    fill: {C_TEXT_PRIMARY} !important;
    stroke: {C_TEXT_PRIMARY} !important;
}}

/* ═══ 16. METRICS ═══ */
[data-testid="stMetric"] {{
    background: transparent !important;
}}
[data-testid="stMetric"] label,
[data-testid="metric-container"] label {{
    color: {C_TEXT_MUTED} !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.68rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}}
[data-testid="stMetricValue"],
[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    color: {C_ACCENT_FIRE} !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 1.5rem !important;
}}

/* ═══ 17. MARKDOWN OVERRIDES ═══ */
.stMarkdown p,
.stMarkdown li,
.stMarkdown span:not(.score-pill):not(.hero-title-fire),
[data-testid="stMarkdownContainer"] p,
[data-testid="stText"] {{
    color: {C_TEXT_PRIMARY} !important;
    font-family: 'Barlow', sans-serif !important;
}}
.stMarkdown code,
.stMarkdown pre,
code {{
    background: {C_CODE_BG} !important;
    color: {C_CODE_FG} !important;
    border: 1px solid {C_BORDER} !important;
    border-radius: 2px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.8rem !important;
    padding: 1px 6px !important;
}}
.stMarkdown h3 {{
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.74rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: {C_TEXT_MUTED} !important;
    border-bottom: 1px solid {C_BORDER} !important;
    padding-bottom: 6px !important;
    margin: 20px 0 12px 0 !important;
}}
[data-testid="stCaption"] p,
[data-testid="stCaption"] {{
    color: {C_TEXT_MUTED} !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.7rem !important;
}}
/* Dividers */
hr,
[data-testid="stHorizontalRule"] hr,
[data-testid="stDivider"] hr {{
    border-color: {C_BORDER} !important;
    opacity: 0.6 !important;
}}

/* ═══ 18. FOOTER ═══ */
.footer-bar {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.62rem;
    color: {C_TEXT_DIM};
    letter-spacing: 0.1em;
    text-transform: uppercase;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 20px;
    padding: 20px 0 8px 0;
}}
.footer-bar .fire {{ color: {C_ACCENT_FIRE}; }}
</style>
""", unsafe_allow_html=True)



# ═══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════════

if "pipeline_result" not in st.session_state:
    st.session_state.pipeline_result = None
if "run_complete" not in st.session_state:
    st.session_state.run_complete = False


# ═══════════════════════════════════════════════════════════════════════════════
#  HELPER RENDERERS
# ═══════════════════════════════════════════════════════════════════════════════

SOURCE_ICON = {
    "pdf_manual":    "📄",
    "catalog_table": "📊",
    "legacy_scrape": "🕸️",
    "erp_api":       "🔌",
    "user_override": "👤",
}

SOURCE_COLOR = {
    "pdf_manual":    "#6366f1",
    "catalog_table": "#38bdf8",
    "legacy_scrape": "#f59e0b",
    "erp_api":       "#34d399",
    "user_override": "#a78bfa",
}


def render_score_pill(score: float) -> str:
    css_class = "score-high" if score >= 0.75 else ("score-mid" if score >= 0.5 else "score-low")
    return f'<span class="score-pill {css_class}">{score:.4f}</span>'


def render_claim_card(claim: EvidenceClaim, is_winner: bool = False) -> None:
    src    = claim.source_type.value
    icon   = SOURCE_ICON.get(src, "📦")
    winner_cls = "winner" if is_winner else src
    winner_badge = "  SELECTED" if is_winner else ""

    score_html = ""
    if claim.evidence_score is not None:
        score_html = f"&nbsp;·&nbsp;Evidence Score: {render_score_pill(claim.evidence_score)}"

    physics_html = ""
    if claim.physics_consistent is False:
        physics_html = "&nbsp;<span style='color:#f87171;font-size:0.72rem;'>⚠ Physics FAIL</span>"
    elif claim.physics_consistent is True:
        physics_html = "&nbsp;<span style='color:#4ade80;font-size:0.72rem;'>✓ Physics OK</span>"

    st.markdown(f"""
    <div class="claim-card {winner_cls}">
        <div class="claim-value">{claim.raw_value}{winner_badge}</div>
        <div class="claim-source">
            {icon} <strong>{src}</strong> &nbsp;·&nbsp; {claim.source_id}
            &nbsp;·&nbsp; Confidence: {claim.source_confidence:.0%}
            &nbsp;·&nbsp; {claim.temporal_timestamp.strftime('%Y-%m-%d')}
            {score_html}{physics_html}
        </div>
        <div class="claim-id">claim_id: {claim.claim_id}</div>
    </div>
    """, unsafe_allow_html=True)


def render_anomaly(ano: ForensicAnomalyObject) -> None:
    css_cls = "anomaly-critical" if ano.severity == AnomalySeverity.CRITICAL else "anomaly-warning"
    sev_icon = "🔴" if ano.severity == AnomalySeverity.CRITICAL else "🟡"
    delta_str = f" | Δ={ano.mathematical_delta_pct:.2f}%" if ano.mathematical_delta_pct else ""

    st.markdown(f"""
    <div class="{css_cls}">
        <div class="anomaly-title">{sev_icon} [{ano.severity.value}] {ano.invariant_code}{delta_str}</div>
        <div class="anomaly-desc">{ano.description}</div>
        <div class="anomaly-hint">🔧 Remediation: {ano.remediation_hint}</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("🔍 Conflicting Variables Detail", expanded=False):
        st.json(ano.conflicting_variables)


def render_truth_card(prop_name: str, res: ResolutionResult) -> None:
    contested_badge = "Contested" if res.was_contested else "Uncontested"
    st.markdown(f"""
    <div class="truth-card">
        <div class="truth-property">{prop_name} &nbsp;·&nbsp; {contested_badge}</div>
        <div class="truth-value">{res.winning_value} {res.winning_unit}</div>
        <div class="truth-confidence">
            Resolution Confidence: {res.resolution_confidence:.4f} &nbsp;·&nbsp;
            Source claim: <code>{res.winning_claim_id[:12]}…</code>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if res.rejection_log:
        st.markdown("**Rejection Audit Log:**")
        for entry in res.rejection_log:
            st.markdown(
                f'<div class="rejection-entry">✗ {entry}</div>',
                unsafe_allow_html=True
            )


def render_score_table(res: ResolutionResult) -> None:
    rows = []
    for bd in res.score_breakdown:
        rows.append({
            "Rank":          f"#{bd.rank}",
            "Claim ID":      bd.claim_id[:12] + "…",
            "Authority (×0.40)": f"{bd.authority_score:.4f}",
            "Confidence (×0.30)": f"{bd.confidence_score:.4f}",
            "Recency (×0.15)": f"{bd.recency_score:.4f}",
            "Physics (×0.15)": f"{bd.physics_bonus:.4f}",
            "Final Score":   f"{bd.final_evidence_score:.6f}",
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR — CONTROLS
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    # ── Theme toggle (URL-param based — doesn't reset pipeline state) ──
    params = st.query_params
    is_dark = params.get("theme", "dark") != "light"
    if is_dark:
        if st.button("Light Mode", key="theme_toggle"):
            st.query_params["theme"] = "light"
            st.rerun()
    else:
        if st.button("Dark Mode", key="theme_toggle"):
            st.query_params["theme"] = "dark"
            st.rerun()
    # Inject theme CSS variable override for light mode
    if not is_dark:
        st.markdown("""
        <style>
        /* ═══ LIGHT THEME — full override of all hardcoded dark values ═══ */
        :root {
            --bg-base:      #f5f0eb !important;
            --bg-panel:     #ede7df !important;
            --bg-card:      #fff8f2 !important;
            --bg-inset:     #e8e0d6 !important;
            --bg-popover:   #fff8f2 !important;
            --accent-fire:  #c44b02 !important;
            --accent-teal:  #0077a8 !important;
            --accent-gold:  #b5541a !important;
            --accent-green: #2d6a4f !important;
            --accent-red:   #b5202c !important;
            --border-main:  #c9bfb5 !important;
            --border-hot:   rgba(196,75,2,0.45) !important;
            --text-primary: #1a1410 !important;
            --text-muted:   #6b5d52 !important;
            --text-dim:     #9c8b80 !important;
        }

        /* ── Main app backgrounds ── */
        html, body,
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"],
        [data-testid="stVerticalBlock"],
        [data-testid="stBottomBlockContainer"],
        [data-testid="stHorizontalBlock"],
        .main .block-container,
        .main,
        section.main,
        div.block-container {
            background-color: #f5f0eb !important;
            color: #1a1410 !important;
        }
        .element-container,
        .stMarkdown,
        [data-testid="stMarkdownContainer"] {
            background-color: transparent !important;
            color: #1a1410 !important;
        }

        /* ── Circuit grid: lighter for light mode ── */
        [data-testid="stMain"]::before, .main::before {
            background-image:
                linear-gradient(rgba(196,75,2,0.04) 1px, transparent 1px),
                linear-gradient(90deg, rgba(196,75,2,0.04) 1px, transparent 1px) !important;
        }

        /* ── Header ── */
        header[data-testid="stHeader"] {
            background: #f5f0eb !important;
            border-bottom: 1px solid #c9bfb5 !important;
        }
        [data-testid="stToolbar"] {
            background: #f5f0eb !important;
        }
        [data-testid="stToolbar"] button { color: #6b5d52 !important; }

        /* ── Sidebar ── */
        section[data-testid="stSidebar"],
        section[data-testid="stSidebar"] > div,
        section[data-testid="stSidebar"] > div > div,
        section[data-testid="stSidebar"] .stMarkdown {
            background: #ede7df !important;
            background-color: #ede7df !important;
            border-right: 1px solid #c9bfb5 !important;
        }
        section[data-testid="stSidebar"] *:not(.hero-badge):not(button) {
            color: #1a1410 !important;
        }
        section[data-testid="stSidebar"] .stMarkdown h3 {
            color: #6b5d52 !important;
            border-bottom: 1px solid #c9bfb5 !important;
        }
        section[data-testid="stSidebar"] hr {
            border-color: #c9bfb5 !important;
        }

        /* ── App-wide inputs ── */
        input,
        div[data-baseweb="input"],
        div[data-baseweb="input"] > div {
            background: #fff8f2 !important;
            background-color: #fff8f2 !important;
            border-color: #c9bfb5 !important;
            color: #1a1410 !important;
        }
        input:focus,
        div[data-baseweb="input"]:focus-within {
            border-color: #c44b02 !important;
            box-shadow: 0 0 0 2px rgba(196,75,2,0.15) !important;
        }

        /* ── App-wide selectbox ── */
        [data-baseweb="select"] > div,
        [data-baseweb="select"] > div > div {
            background: #fff8f2 !important;
            background-color: #fff8f2 !important;
            border-color: #c9bfb5 !important;
            color: #1a1410 !important;
        }
        [data-baseweb="select"] span,
        [data-baseweb="select"] [role="combobox"] {
            color: #1a1410 !important;
        }

        /* ── Dropdown popover ── */
        [data-baseweb="popover"] > div,
        [data-baseweb="menu"],
        [role="listbox"],
        [data-baseweb="popover"] [role="option"] {
            background: #fff8f2 !important;
            background-color: #fff8f2 !important;
            border-color: #c9bfb5 !important;
            color: #1a1410 !important;
        }
        [data-baseweb="popover"] [role="option"]:hover,
        [aria-selected="true"] {
            background: #e8e0d6 !important;
            background-color: #e8e0d6 !important;
            color: #c44b02 !important;
        }

        /* ── App-wide radio ── */
        [data-testid="stRadio"] label,
        [data-testid="stRadio"] p {
            color: #1a1410 !important;
        }
        [data-testid="stRadio"] div[role="radio"][aria-checked="false"] {
            background: #fff8f2 !important;
            background-color: #fff8f2 !important;
            border-color: #c9bfb5 !important;
        }

        /* ── Number input buttons ── */
        section[data-testid="stSidebar"] button[data-testid="stNumberInputStepDown"],
        section[data-testid="stSidebar"] button[data-testid="stNumberInputStepUp"] {
            background: #e8e0d6 !important;
            background-color: #e8e0d6 !important;
            border-color: #c9bfb5 !important;
            color: #6b5d52 !important;
        }

        /* ── Sidebar run button ── */
        section[data-testid="stSidebar"] .stButton > button {
            background: transparent !important;
            color: #c44b02 !important;
            border: 1px solid #c44b02 !important;
        }
        section[data-testid="stSidebar"] .stButton > button:hover {
            background: #c44b02 !important;
            color: #fff !important;
            box-shadow: 0 0 18px rgba(196,75,2,0.3) !important;
        }
        section[data-testid="stSidebar"] .stButton:first-child > button {
            border-color: #c9bfb5 !important;
            color: #6b5d52 !important;
        }
        section[data-testid="stSidebar"] .stButton:first-child > button:hover {
            background: #e8e0d6 !important;
            color: #1a1410 !important;
        }

        /* ── Hero banner ── */
        .hero-banner {
            background: linear-gradient(118deg, #fffaf5 0%, #f5ede3 55%, #fdf6ef 100%) !important;
            border: 1px solid #c9bfb5 !important;
            border-top: 3px solid #c44b02 !important;
        }
        .hero-banner::after {
            background:
                radial-gradient(ellipse 55% 80% at 88% 50%, rgba(196,75,2,0.06) 0%, transparent 65%),
                radial-gradient(ellipse 35% 60% at 10% 50%, rgba(0,119,168,0.04) 0%, transparent 60%) !important;
        }
        .hero-eyebrow { color: #c44b02 !important; }
        .hero-eyebrow::before, .hero-eyebrow::after { background: #c44b02 !important; }
        .hero-title { color: #1a1410 !important; }
        .hero-title-fire { color: #c44b02 !important; }
        .hero-badge {
            background: rgba(196,75,2,0.08) !important;
            border: 1px solid rgba(196,75,2,0.3) !important;
            color: #c44b02 !important;
        }
        .hero-thesis { color: #6b5d52 !important; }
        .hero-thesis em { color: #b5541a !important; }

        /* ── Metric tiles ── */
        .metric-tile {
            background: #ede7df !important;
            border: 1px solid #c9bfb5 !important;
            border-top: 2px solid rgba(196,75,2,0.5) !important;
        }
        .metric-number { color: #c44b02 !important; }
        .metric-label { color: #6b5d52 !important; }

        /* ── Section headers ── */
        .section-evidence {
            background: rgba(181,32,44,0.06) !important;
            border: 1px solid rgba(181,32,44,0.2) !important;
            border-left: 3px solid #b5202c !important;
            color: #b5202c !important;
        }
        .section-truth {
            background: rgba(45,106,79,0.06) !important;
            border: 1px solid rgba(45,106,79,0.2) !important;
            border-left: 3px solid #2d6a4f !important;
            color: #2d6a4f !important;
        }

        /* ── Claim cards ── */
        .claim-card {
            background: #fff8f2 !important;
            border: 1px solid #c9bfb5 !important;
            border-left: 3px solid #c9bfb5 !important;
        }
        .claim-card.winner {
            border-left-color: #c44b02 !important;
            background: linear-gradient(90deg, rgba(196,75,2,0.07) 0%, #fff8f2 45%) !important;
        }
        .claim-value { color: #1a1410 !important; }
        .claim-source { color: #6b5d52 !important; }
        .claim-id { color: #9c8b80 !important; }

        /* ── Score pills ── */
        .score-high { background: rgba(45,106,79,0.1) !important;  color: #2d6a4f !important; border: 1px solid rgba(45,106,79,0.3) !important; }
        .score-mid  { background: rgba(0,119,168,0.1) !important;   color: #0077a8 !important; border: 1px solid rgba(0,119,168,0.3) !important; }
        .score-low  { background: rgba(181,32,44,0.08) !important;  color: #b5202c !important; border: 1px solid rgba(181,32,44,0.3) !important; }

        /* ── Anomaly boxes ── */
        .anomaly-critical {
            background: rgba(181,32,44,0.06) !important;
            border: 1px solid rgba(181,32,44,0.25) !important;
            border-left: 4px solid #b5202c !important;
        }
        .anomaly-warning {
            background: rgba(181,84,26,0.06) !important;
            border: 1px solid rgba(181,84,26,0.25) !important;
            border-left: 4px solid #b5541a !important;
        }
        .anomaly-title { color: #b5202c !important; }
        .anomaly-warning .anomaly-title { color: #b5541a !important; }
        .anomaly-desc { color: #1a1410 !important; }
        .anomaly-hint { color: #6b5d52 !important; }

        /* ── Truth cards ── */
        .truth-card {
            background: #fff8f2 !important;
            border: 1px solid #c9bfb5 !important;
            border-bottom: 2px solid rgba(45,106,79,0.4) !important;
        }
        .truth-property { color: #6b5d52 !important; }
        .truth-value { color: #2d6a4f !important; }
        .truth-confidence { color: #6b5d52 !important; }

        /* ── Rejection log ── */
        .rejection-entry {
            background: rgba(181,32,44,0.04) !important;
            border-left: 2px solid rgba(181,32,44,0.25) !important;
            color: #6b5d52 !important;
        }

        /* ── Expanders ── */
        [data-testid="stExpander"],
        div[data-testid="stExpander"] {
            background: #fff8f2 !important;
            border: 1px solid #c9bfb5 !important;
        }
        [data-testid="stExpander"] summary,
        div[data-testid="stExpander"] summary {
            background: #fff8f2 !important;
            color: #1a1410 !important;
        }
        [data-testid="stExpander"] details[open] > summary,
        div[data-testid="stExpander"] details[open] summary {
            background: #e8e0d6 !important;
            border-bottom: 1px solid #c9bfb5 !important;
        }
        [data-testid="stExpander"] summary p {
            color: #1a1410 !important;
        }
        [data-testid="stExpander"] details > div,
        div[data-testid="stExpander"] > details > div {
            background: #fff8f2 !important;
        }

        /* ── Alert boxes ── */
        [data-testid="stAlert"],
        div[role="alert"],
        div[data-baseweb="notification"] {
            background: #fff8f2 !important;
            color: #1a1410 !important;
        }
        [data-testid="stAlert"] p,
        [data-testid="stAlert"] span,
        [data-testid="stAlert"] strong {
            color: #1a1410 !important;
        }

        /* ── DataFrames ── */
        [data-testid="stDataFrame"] > div,
        [data-testid="stDataFrameResizable"],
        .stDataFrame {
            background: #fff8f2 !important;
            border: 1px solid #c9bfb5 !important;
        }
        [data-testid="stDataFrame"] * { color: #1a1410 !important; }
        .dvn-scroller, [role="grid"], [role="gridcell"], [role="columnheader"] {
            background: #fff8f2 !important;
            border-color: #c9bfb5 !important;
        }
        [role="columnheader"] {
            background: #ede7df !important;
            color: #6b5d52 !important;
            border-bottom: 1px solid #c9bfb5 !important;
        }

        /* ── Element Toolbars ── */
        .stElementToolbar,
        [data-testid="stElementToolbar"],
        [data-testid="stDataFrameToolbar"],
        [data-testid="stElementToolbar"] > div,
        [data-testid="stDataFrameToolbar"] > div {
            background: #fff8f2 !important;
            background-color: #fff8f2 !important;
            border: 1px solid #c9bfb5 !important;
            border-radius: 4px !important;
        }
        .stElementToolbar button,
        [data-testid="stElementToolbar"] button,
        [data-testid="stDataFrameToolbar"] button {
            background: transparent !important;
            background-color: transparent !important;
            color: #1a1410 !important;
        }
        .stElementToolbar svg,
        [data-testid="stElementToolbar"] svg,
        [data-testid="stDataFrameToolbar"] svg {
            color: #1a1410 !important;
            fill: #1a1410 !important;
            stroke: #1a1410 !important;
        }

        /* ── Metrics ── */
        [data-testid="stMetricValue"],
        [data-testid="metric-container"] [data-testid="stMetricValue"] {
            color: #c44b02 !important;
        }
        [data-testid="stMetric"] label,
        [data-testid="metric-container"] label {
            color: #6b5d52 !important;
        }

        /* ── Markdown text ── */
        .stMarkdown p, .stMarkdown li,
        .stMarkdown span:not(.score-pill):not(.hero-title-fire),
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stText"] {
            color: #1a1410 !important;
        }
        .stMarkdown code, .stMarkdown pre, code {
            background: #e8e0d6 !important;
            color: #0077a8 !important;
            border: 1px solid #c9bfb5 !important;
        }
        .stMarkdown h3 {
            color: #6b5d52 !important;
            border-bottom: 1px solid #c9bfb5 !important;
        }
        [data-testid="stCaption"] p,
        [data-testid="stCaption"] {
            color: #6b5d52 !important;
        }
        hr, [data-testid="stHorizontalRule"] hr, [data-testid="stDivider"] hr {
            border-color: #c9bfb5 !important;
        }

        /* ── Footer ── */
        .footer-bar { color: #9c8b80 !important; }
        .footer-bar .fire { color: #c44b02 !important; }

        /* ── Sidebar inline styles (hardcoded dark) ── */
        section[data-testid="stSidebar"] div[style*="#d4cfc9"],
        section[data-testid="stSidebar"] div[style*="color:#d4cfc9"] {
            color: #1a1410 !important;
        }
        section[data-testid="stSidebar"] div[style*="#4a4038"],
        section[data-testid="stSidebar"] div[style*="color:#4a4038"] {
            color: #6b5d52 !important;
        }
        </style>
        """, unsafe_allow_html=True)

    brand_name_color   = "#d4cfc9" if is_dark else "#1a1410"
    brand_sub_color    = "#4a4038" if is_dark else "#6b5d52"
    brand_accent_color = "#e85d04" if is_dark else "#c44b02"
    st.markdown(f"""
    <div style="padding:18px 4px 10px 4px;">
        <div style="font-family:'IBM Plex Mono',monospace;font-size:0.6rem;letter-spacing:0.18em;color:{brand_accent_color};text-transform:uppercase;margin-bottom:8px;">// sys.agent.forensic</div>
        <div style="font-family:'Syne',sans-serif;font-size:1.25rem;font-weight:800;color:{brand_name_color};letter-spacing:-0.5px;line-height:1.1;">Forensic<br/><span style='color:{brand_accent_color};'>Data Agent</span></div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:0.62rem;color:{brand_sub_color};margin-top:8px;letter-spacing:0.06em;text-transform:uppercase;">Industrial Intelligence</div>
    </div>
    """, unsafe_allow_html=True)


    st.divider()
    st.markdown("### Pipeline Configuration")

    demo_opts = {"DEFAULT_DEMO": "Original Demo (ABB M3AA 75kW)"}
    if HACKATHON_DEMO_CASES:
        demo_opts.update({k: f"{k} ({v['asset_name']})" for k, v in HACKATHON_DEMO_CASES.items()})

    selected_demo_key = st.selectbox(
        "Select Demo Case",
        options=list(demo_opts.keys()),
        format_func=lambda x: demo_opts[x]
    )

    mode = st.radio(
        "Data Source",
        ["Live Demo", "Manual Input"],
        index=0,
    )

    st.divider()
    st.markdown("### 🧮 ELEC-001 Parameters")

    p_out     = st.number_input("Rated Output (kW)",    value=75.0,  min_value=0.1)
    voltage   = st.number_input("Voltage (V)",           value=400.0, min_value=1.0)
    current   = st.number_input("Full-Load Current (A)", value=132.0, min_value=0.1)
    pf        = st.slider("Power Factor",     0.50, 1.00, 0.87, 0.01)
    efficiency= st.slider("Efficiency (η)",   0.50, 1.00, 0.955, 0.001)
    tolerance = st.slider("Invariant Tolerance (%)", 1, 20, 5) / 100.0

    st.divider()
    st.markdown("### 🏭 ENV-001 Parameters")
    ip_raw     = st.text_input("IP Rating (raw)", value="IP23")
    cooling    = st.selectbox("Cooling Method", ["TEFC","TENV","ODP","WP1","WP2","XPRF"])

    st.divider()

    run_btn = st.button("Run Forensic Pipeline", use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  PIPELINE EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

if run_btn:
    with st.spinner("Running 4-pass Forensic Pipeline..."):
        if "Demo" in mode:
            if selected_demo_key == "DEFAULT_DEMO" or not HACKATHON_DEMO_CASES:
                store, demo_kwargs = build_demo_store()
                product_id = "MTR-ABB-M3AA-75KW"
                elec_params = demo_kwargs["elec_params"]
                ip_check    = demo_kwargs["ip_rating"]
                cool_check  = demo_kwargs["cooling_method"]
            else:
                case_data = HACKATHON_DEMO_CASES[selected_demo_key]
                store = EvidenceGraphStore()
                product_id = selected_demo_key
                from datetime import datetime
                
                context_map = {
                    "Datasheet": SourceType.PDF_MANUAL,
                    "Installation Manual": SourceType.PDF_MANUAL,
                    "Marketing Web Portal": SourceType.LEGACY_SCRAPE,
                    "Legacy Database": SourceType.ERP_API,
                }
                
                for claim in case_data["ingested_claims"]:
                    store.ingest_claim(
                        product_id=product_id,
                        property_path=claim["field_path"],
                        raw_value=claim["raw_value"],
                        normalized_value=claim.get("normalized_value", 0.0),
                        normalized_unit=claim.get("normalized_unit", "unit"),
                        source_type=context_map.get(claim["source"]["context_type"], SourceType.USER_OVERRIDE),
                        source_id=claim["source"]["document_name"],
                        source_confidence=claim["source"]["extraction_confidence"],
                        extraction_method="mock_data",
                        timestamp=datetime.now(timezone.utc),
                    )
                
                if selected_demo_key == "CASE-001_MOTOR":
                    elec_params = {
                        "p_out_kw": 75.0, "voltage_v": 415.0, "current_a": 130.0,
                        "power_factor": 0.87, "efficiency": 0.955
                    }
                    ip_check = None
                    cool_check = None
                else:
                    elec_params = None
                    ip_check = "IP99-X"
                    cool_check = "TEFC"
        else:
            store      = EvidenceGraphStore()
            product_id = "MANUAL-PRODUCT-001"
            # Ingest a synthetic single-source record for manual mode
            from datetime import datetime
            store.ingest_claim(
                product_id=product_id, property_path="electrical.voltage",
                raw_value=f"{int(voltage)}V", normalized_value=voltage, normalized_unit="V",
                source_type=SourceType.PDF_MANUAL, source_id="manual_input",
                source_confidence=0.90, extraction_method="user_interface",
                timestamp=datetime.now(timezone.utc),
            )
            elec_params = {
                "p_out_kw": p_out, "voltage_v": voltage, "current_a": current,
                "power_factor": pf, "efficiency": efficiency,
            }
            ip_check   = ip_raw
            cool_check = cooling

        pipeline = ForensicAgentPipeline(store)
        run_kwargs = {
            "product_id": product_id,
            "ip_rating": ip_check,
            "cooling_method": cool_check,
        }
        if elec_params:
            run_kwargs["elec_params"] = {**elec_params, "tolerance": tolerance} if "tolerance" not in elec_params else elec_params
            
        result = pipeline.run(**run_kwargs)

    st.session_state.pipeline_result = result
    st.session_state.run_complete    = True


# ═══════════════════════════════════════════════════════════════════════════════
#  HERO BANNER
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="hero-banner">
    <div class="hero-eyebrow">Probabilistic Edge &nbsp;·&nbsp; Deterministic Core</div>
    <div class="hero-title">Forensic <span class="hero-title-fire">Data Agent</span></div>
    <div class="hero-badge">&#x25A0; Industrial Intelligence Pipeline &nbsp;·&nbsp; Hackathon 2026</div>
    <p class="hero-thesis">
        &ldquo;Industrial commerce doesn&rsquo;t have a data extraction problem &mdash;
        it has a <em>TRUTH problem</em>.&rdquo;
    </p>
</div>
""", unsafe_allow_html=True)

# ── Top metric bar ──
if st.session_state.run_complete and st.session_state.pipeline_result:
    res = st.session_state.pipeline_result
    m1, m2, m3, m4, m5 = st.columns(5)

    total_claims    = sum(p.claim_count() for p in res.snapshot.properties.values())
    contested       = len(res.snapshot.conflicted_properties())
    anomaly_count   = len(res.anomalies)
    resolved_count  = len(res.resolution_map)
    avg_confidence  = (
        sum(r.resolution_confidence for r in res.resolution_map.values()) / resolved_count
        if resolved_count else 0
    )

    for col, number, label in zip(
        [m1, m2, m3, m4, m5],
        [total_claims, contested, anomaly_count, resolved_count, f"{avg_confidence:.3f}"],
        ["Total Claims", "Contested Props", "Anomalies Found", "Props Resolved", "Avg Confidence"],
    ):
        col.markdown(f"""
        <div class="metric-tile">
            <div class="metric-number">{number}</div>
            <div class="metric-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
else:
    st.info("Configure the pipeline in the sidebar and click **Run Forensic Pipeline** to begin.")


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN TWO-COLUMN LAYOUT
# ═══════════════════════════════════════════════════════════════════════════════

if st.session_state.run_complete and st.session_state.pipeline_result:
    result   = st.session_state.pipeline_result
    snapshot = result.snapshot

    left_col, right_col = st.columns([1, 1], gap="large")

    # ═══════════════════════════════════════════════════════════════════════════
    #  LEFT — RAW EVIDENCE GRAPH
    # ═══════════════════════════════════════════════════════════════════════════
    with left_col:
        st.markdown("""
        <div class="section-header section-evidence">
            ⚗️ Raw Evidence Graph &nbsp;·&nbsp;
            <span style="font-weight:400; font-size:0.88rem;">
                All conflicting claims preserved — no destructive overwrites
            </span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"**Product:** `{result.product_id}`")
        st.markdown(f"**Snapshot captured:** `{snapshot.captured_at.strftime('%Y-%m-%d %H:%M UTC')}`")

        contested_props = snapshot.conflicted_properties()
        if contested_props:
            st.warning(
                f"**{len(contested_props)} contested propert{'y' if len(contested_props)==1 else 'ies'} detected:** "
                + ", ".join(f"`{p}`" for p in contested_props)
            )

        st.divider()

        for prop_name, prop in snapshot.properties.items():
            with st.expander(
                f"{'⚔️' if prop.has_conflict() else '✅'} `{prop_name}` — {prop.claim_count()} claim(s)",
                expanded=True,
            ):
                winner_id = result.resolution_map.get(prop_name, {})
                if hasattr(winner_id, "winning_claim_id"):
                    winner_id = winner_id.winning_claim_id
                else:
                    winner_id = None

                for claim in sorted(prop.claims, key=lambda c: c.source_confidence, reverse=True):
                    is_winner = (claim.claim_id == winner_id)
                    render_claim_card(claim, is_winner=is_winner)

                if prop.has_conflict():
                    vals = [c.normalized_value for c in prop.claims]
                    spread = max(vals) - min(vals)
                    st.markdown(
                        f"<div style='font-size:0.78rem;color:var(--text-muted);margin-top:6px;'>"
                        f"Value spread: {min(vals)} → {max(vals)} {prop.claims[0].normalized_unit} "
                        f"(Δ={spread:.1f})</div>",
                        unsafe_allow_html=True,
                    )

        st.divider()
        st.markdown("### Unit Normalization Traces")
        if result.unit_traces:
            for trace_key, trace in result.unit_traces.items():
                with st.expander(f"`{trace.raw_string}` → `{trace.final_display_value}`"):
                    col_a, col_b = st.columns(2)
                    col_a.metric("Input",            trace.raw_string)
                    col_b.metric("SI Output",        trace.final_display_value)
                    st.markdown(f"""
                    | Field | Value |
                    |-------|-------|
                    | Parsed Magnitude | `{trace.parsed_magnitude}` |
                    | Parsed Unit | `{trace.parsed_unit_raw}` |
                    | Base SI Unit | `{trace.base_si_unit}` |
                    | Conversion Factor | `{trace.conversion_factor_exact}` |
                    | **Unrounded Calculation** | `{trace.unrounded_float_calculation}` |
                    | Significant Figures | `{trace.significant_digits_detected}` |
                    | Precision Policy | `{trace.precision_policy_rule}` |
                    """)
        else:
            st.info("No unit normalization traces generated.")

    # ═══════════════════════════════════════════════════════════════════════════
    #  RIGHT — TRUTH LOG PANEL
    # ═══════════════════════════════════════════════════════════════════════════
    with right_col:
        st.markdown("""
        <div class="section-header section-truth">
            ⚖️ Truth Log Panel &nbsp;·&nbsp;
            <span style="font-weight:400; font-size:0.88rem;">
                Canonical values, anomaly alerts, and rejection explanations
            </span>
        </div>
        """, unsafe_allow_html=True)

        # ── Forensic Anomaly Alerts ──
        if result.anomalies:
            st.markdown(f"### {len(result.anomalies)} Forensic Anomal{'y' if len(result.anomalies)==1 else 'ies'} Detected")
            for ano in result.anomalies:
                render_anomaly(ano)
        else:
            st.success("**All physics invariants passed.** No anomalies detected.")

        st.divider()

        # ── Canonical Truth Values ──
        st.markdown("### 🎯 Canonical Truth Values")
        for prop_name, res in result.resolution_map.items():
            render_truth_card(prop_name, res)

        st.divider()

        # ── Evidence Score Breakdown ──
        st.markdown("### Evidence Score Breakdown Matrix")
        st.caption(
            "S(claim) = 0.40×Authority + 0.30×Confidence + 0.15×Recency + 0.15×PhysicsBonus"
        )

        for prop_name, res in result.resolution_map.items():
            with st.expander(f"📈 `{prop_name}` — Score Matrix", expanded=res.was_contested):
                render_score_table(res)

        st.divider()

        # ── Unit Normalizer Sandbox ──
        st.markdown("### Live Unit Normalizer Sandbox")
        st.caption("NIST SP 811-compliant conversion with full audit trail")

        sandbox_input = st.text_input(
            "Enter measurement string",
            placeholder="e.g.  250 lb  ·  0.75 kW  ·  5.25 in",
        )
        if sandbox_input:
            try:
                trace = normalize_unit(sandbox_input)
                st.success(f"`{trace.raw_string}` → **`{trace.final_display_value}`**")
                st.markdown(f"""
                | Field | Value |
                |-------|-------|
                | Unrounded Result | `{trace.unrounded_float_calculation} {trace.base_si_unit}` |
                | Significant Figures | `{trace.significant_digits_detected}` |
                | Conversion Factor | `{trace.conversion_factor_exact}` (NIST SP 811 Appendix B) |
                | Precision Policy | `{trace.precision_policy_rule}` |
                """)
            except ValueError as err:
                st.error(f"❌ {err}")

        # ── IP Validator Sandbox ──
        st.markdown("### 🏭 Live IP Rating Validator")
        ip_sandbox = st.text_input("IP Code to validate", placeholder="e.g. IP55, IP23, IP65W")
        cool_sandbox = st.selectbox("Cooling (for cross-check)", ["TEFC","TENV","ODP","WP1","WP2","XPRF", "(none)"], key="cool_s")

        if ip_sandbox:
            from engine import EngineeringRuleEngine
            engine_live = EngineeringRuleEngine()
            cool_val = None if cool_sandbox == "(none)" else cool_sandbox
            ano_live = engine_live.check_env_001("SANDBOX", ip_sandbox, cool_val)
            if ano_live:
                render_anomaly(ano_live)
            else:
                st.success(f"`{ip_sandbox}` passes all IEC 60034-5 / IEC 60529 validation layers.")


# ═══════════════════════════════════════════════════════════════════════════════
#  FOOTER
# ═══════════════════════════════════════════════════════════════════════════════

st.divider()
st.markdown("""
<div style="
    display:flex; align-items:center; justify-content:center; gap:24px;
    padding:20px 0 8px 0;
    font-family:'IBM Plex Mono',monospace; font-size:0.64rem;
    letter-spacing:0.1em; text-transform:uppercase; color:#3d3530;
">
    <span style='color:#e85d04;'>&#x25A0;</span>
    <span>Forensic Data Agent</span>
    <span style='color:#3d3530;'>&#x2F;</span>
    <span>NIST SP&nbsp;811</span>
    <span style='color:#3d3530;'>&#x2F;</span>
    <span>IEC&nbsp;60034</span>
    <span style='color:#3d3530;'>&#x2F;</span>
    <span>IEC&nbsp;60529</span>
    <span style='color:#3d3530;'>&#x2F;</span>
    <span>Hackathon&nbsp;2026</span>
    <span style='color:#e85d04;'>&#x25A0;</span>
</div>
""", unsafe_allow_html=True)
