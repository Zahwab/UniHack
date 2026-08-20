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

st.markdown("""
<style>
/* ── Base & Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0a0e1a;
    color: #e2e8f0;
}

/* ── Hero banner ── */
.hero-banner {
    background: linear-gradient(135deg, #1a1f35 0%, #0d1226 50%, #12192e 100%);
    border: 1px solid #2d3654;
    border-radius: 16px;
    padding: 32px 40px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.hero-banner::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle at 30% 50%, rgba(99,102,241,0.08) 0%, transparent 60%),
                radial-gradient(circle at 70% 50%, rgba(6,182,212,0.06) 0%, transparent 60%);
    pointer-events: none;
}
.hero-title {
    font-size: 2.2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #818cf8 0%, #38bdf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 8px 0;
    letter-spacing: -0.5px;
}
.hero-thesis {
    font-size: 1.05rem;
    color: #94a3b8;
    font-style: italic;
    margin: 0;
}
.hero-badge {
    display: inline-block;
    background: rgba(99,102,241,0.15);
    border: 1px solid rgba(99,102,241,0.4);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.75rem;
    color: #818cf8;
    font-weight: 600;
    letter-spacing: 0.5px;
    margin-bottom: 12px;
}

/* ── Section headers ── */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 14px 20px;
    border-radius: 10px;
    margin-bottom: 16px;
    font-size: 1rem;
    font-weight: 600;
    letter-spacing: 0.3px;
}
.section-evidence {
    background: rgba(239,68,68,0.08);
    border: 1px solid rgba(239,68,68,0.25);
    color: #fca5a5;
}
.section-truth {
    background: rgba(34,197,94,0.08);
    border: 1px solid rgba(34,197,94,0.25);
    color: #86efac;
}

/* ── Claim cards ── */
.claim-card {
    background: #111827;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 10px;
    border-left: 4px solid #374151;
    position: relative;
}
.claim-card.pdf_manual    { border-left-color: #6366f1; }
.claim-card.catalog_table { border-left-color: #38bdf8; }
.claim-card.legacy_scrape { border-left-color: #f59e0b; }
.claim-card.erp_api       { border-left-color: #34d399; }
.claim-card.winner        { border-left-color: #22c55e; background: rgba(34,197,94,0.06); }

.claim-value  { font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; color: #f8fafc; font-weight: 500; }
.claim-source { font-size: 0.78rem; color: #64748b; margin-top: 4px; }
.claim-id     { font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #475569; }

/* ── Score pill ── */
.score-pill {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
}
.score-high   { background: rgba(34,197,94,0.15);  color: #4ade80;  border: 1px solid rgba(34,197,94,0.3); }
.score-mid    { background: rgba(99,102,241,0.15); color: #818cf8;  border: 1px solid rgba(99,102,241,0.3); }
.score-low    { background: rgba(239,68,68,0.12);  color: #fca5a5;  border: 1px solid rgba(239,68,68,0.3); }

/* ── Anomaly boxes ── */
.anomaly-critical {
    background: rgba(239,68,68,0.08);
    border: 1px solid rgba(239,68,68,0.35);
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 12px;
}
.anomaly-warning {
    background: rgba(245,158,11,0.08);
    border: 1px solid rgba(245,158,11,0.35);
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 12px;
}
.anomaly-title { font-size: 0.85rem; font-weight: 700; color: #fca5a5; margin-bottom: 6px; }
.anomaly-warning .anomaly-title { color: #fcd34d; }
.anomaly-desc  { font-size: 0.82rem; color: #94a3b8; line-height: 1.5; }
.anomaly-hint  { font-size: 0.78rem; color: #64748b; margin-top: 8px; font-style: italic; }

/* ── Truth card ── */
.truth-card {
    background: linear-gradient(135deg, rgba(34,197,94,0.06), rgba(6,182,212,0.04));
    border: 1px solid rgba(34,197,94,0.2);
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 14px;
}
.truth-property { font-size: 0.78rem; color: #64748b; font-family: 'JetBrains Mono', monospace; }
.truth-value    { font-size: 1.5rem; font-weight: 700; color: #4ade80; font-family: 'JetBrains Mono', monospace; }
.truth-confidence { font-size: 0.78rem; color: #34d399; margin-top: 4px; }

/* ── Rejection log ── */
.rejection-entry {
    background: rgba(239,68,68,0.05);
    border-left: 3px solid rgba(239,68,68,0.3);
    border-radius: 0 6px 6px 0;
    padding: 8px 12px;
    margin-bottom: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: #94a3b8;
}

/* ── Metric tiles ── */
.metric-tile {
    background: #111827;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 16px 20px;
    text-align: center;
}
.metric-number { font-size: 2rem; font-weight: 700; color: #818cf8; }
.metric-label  { font-size: 0.78rem; color: #64748b; margin-top: 4px; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #0d1226 !important;
    border-right: 1px solid #1e293b;
}

/* ── Streamlit chrome overrides ── */
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #4f46e5);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #818cf8, #6366f1);
    box-shadow: 0 4px 20px rgba(99,102,241,0.35);
    transform: translateY(-1px);
}
div[data-testid="stExpander"] {
    background: #111827;
    border: 1px solid #1e293b;
    border-radius: 10px;
}
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
    winner_badge = "  ✅ SELECTED" if is_winner else ""

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
    contested_badge = "⚔️ Contested" if res.was_contested else "✅ Uncontested"
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
    st.markdown("""
    <div style="text-align:center; padding: 20px 0 10px 0;">
        <div style="font-size:2.5rem;">🔬</div>
        <div style="font-size:1.1rem; font-weight:700; color:#818cf8;">Forensic Data Agent</div>
        <div style="font-size:0.75rem; color:#475569; margin-top:4px;">Industrial Intelligence Platform</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### ⚙️ Pipeline Configuration")

    demo_opts = {"DEFAULT_DEMO": "Original Demo (ABB M3AA 75kW)"}
    if HACKATHON_DEMO_CASES:
        demo_opts.update({k: f"{k} ({v['asset_name']})" for k, v in HACKATHON_DEMO_CASES.items()})

    selected_demo_key = st.selectbox(
        "🎭 Select Demo Case",
        options=list(demo_opts.keys()),
        format_func=lambda x: demo_opts[x]
    )

    mode = st.radio(
        "Data Source",
        ["🎭 Live Demo", "✍️ Manual Input"],
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

    run_btn = st.button("🚀 Run Forensic Pipeline", use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  PIPELINE EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

if run_btn:
    with st.spinner("🔬 Running 4-pass Forensic Pipeline..."):
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
    <div class="hero-badge">PROBABILISTIC EDGE · DETERMINISTIC CORE</div>
    <div class="hero-title">🔬 Forensic Data Agent</div>
    <p class="hero-thesis">"Industrial commerce doesn't have a data extraction problem — it has a TRUTH problem."</p>
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
    st.info("👈 Configure the pipeline in the sidebar and click **Run Forensic Pipeline** to begin.")


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
                f"⚔️ **{len(contested_props)} contested propert{'y' if len(contested_props)==1 else 'ies'} detected:** "
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
                        f"<div style='font-size:0.78rem;color:#64748b;margin-top:6px;'>"
                        f"📐 Value spread: {min(vals)} → {max(vals)} {prop.claims[0].normalized_unit} "
                        f"(Δ={spread:.1f})</div>",
                        unsafe_allow_html=True,
                    )

        st.divider()
        st.markdown("### 🧪 Unit Normalization Traces")
        if result.unit_traces:
            for trace_key, trace in result.unit_traces.items():
                with st.expander(f"🔢 `{trace.raw_string}` → `{trace.final_display_value}`"):
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
            st.markdown(f"### 🚨 {len(result.anomalies)} Forensic Anomal{'y' if len(result.anomalies)==1 else 'ies'} Detected")
            for ano in result.anomalies:
                render_anomaly(ano)
        else:
            st.success("✅ **All physics invariants passed.** No anomalies detected.")

        st.divider()

        # ── Canonical Truth Values ──
        st.markdown("### 🎯 Canonical Truth Values")
        for prop_name, res in result.resolution_map.items():
            render_truth_card(prop_name, res)

        st.divider()

        # ── Evidence Score Breakdown ──
        st.markdown("### 📊 Evidence Score Breakdown Matrix")
        st.caption(
            "S(claim) = 0.40×Authority + 0.30×Confidence + 0.15×Recency + 0.15×PhysicsBonus"
        )

        for prop_name, res in result.resolution_map.items():
            with st.expander(f"📈 `{prop_name}` — Score Matrix", expanded=res.was_contested):
                render_score_table(res)

        st.divider()

        # ── Unit Normalizer Sandbox ──
        st.markdown("### 🔬 Live Unit Normalizer Sandbox")
        st.caption("NIST SP 811-compliant conversion with full audit trail")

        sandbox_input = st.text_input(
            "Enter measurement string",
            placeholder="e.g.  250 lb  ·  0.75 kW  ·  5.25 in",
        )
        if sandbox_input:
            try:
                trace = normalize_unit(sandbox_input)
                st.success(f"✅ `{trace.raw_string}` → **`{trace.final_display_value}`**")
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
                st.success(f"✅ `{ip_sandbox}` passes all IEC 60034-5 / IEC 60529 validation layers.")


# ═══════════════════════════════════════════════════════════════════════════════
#  FOOTER
# ═══════════════════════════════════════════════════════════════════════════════

st.divider()
st.markdown("""
<div style="text-align:center; padding:16px; color:#475569; font-size:0.78rem;">
    🔬 <strong>Forensic Data Agent</strong> &nbsp;·&nbsp; Industrial Intelligence Pipeline &nbsp;·&nbsp;
    Hackathon Edition 2026 &nbsp;·&nbsp; 
    Built on: Pydantic v2 · NIST SP 811 · IEC 60034 · IEC 60529
</div>
""", unsafe_allow_html=True)
