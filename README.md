# Forensic Data Agent

A deterministic, multi-pass data verification pipeline for industrial product intelligence. Resolves conflicting specifications from heterogeneous sources using physics invariants, unit standardization, and weighted evidence scoring.

---

## Problem Statement

Industrial procurement depends on accurate product specifications. In practice, the same product attribute — voltage rating, enclosure class, power output — often returns different values depending on the source consulted: internal ERP records, supplier catalogs, and manufacturer documentation routinely conflict.

Manual reconciliation is slow, error-prone, and does not scale. Probabilistic AI summarization is unreliable for safety-critical data. The Forensic Data Agent solves this with a deterministic, explainable, and auditable resolution engine.

---

## Architecture Overview

The pipeline processes all ingested claims through four sequential passes:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Data Sources                             │
│       PDF Datasheets │ ERP Databases │ Live Web Scrapes         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Pass 1: Evidence Graph                        │
│  Ingests all conflicting claims without overwriting.            │
│  Preserves source, authority, confidence, and timestamp.        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Pass 2: Unit Normalizer                       │
│  Converts all values to SI units.                               │
│  Enforces NIST SP 811 significant-figure precision rules.       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Pass 3: Physics Rule Engine                      │
│  Validates claims against IEC engineering standards.            │
│  Flags contradictions (e.g., P ≠ √3·V·I·PF·η) as violations.  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Pass 4: Conflict Resolver                       │
│  Scores each claim:                                             │
│    Authority 40% · Confidence 30% · Recency 15% · Physics 15%  │
│  Outputs the canonical value with a full, written audit log.    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Differentiators

| Capability | Standard AI Extraction | Forensic Data Agent |
|---|---|---|
| Source handling | Last-write wins | Full evidence graph preserved |
| Unit conversion | Approximate | NIST SP 811 strict precision |
| Validation | None | IEC physics invariant checks |
| Conflict resolution | Probabilistic | Deterministic, weighted scoring |
| Explainability | Black box | Complete audit log per decision |

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- `pip` package manager

### Installation

Clone the repository and set up a virtual environment:

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Running the Application

```bash
streamlit run app.py
```

The dashboard will be available at `http://localhost:8501`.

To run the core engine directly without the UI:

```bash
python engine.py
```

---

## Demonstration Scenarios

The dashboard ships with two pre-loaded conflict scenarios.

### Scenario 1 — Electrical Specification Conflict

Three sources provide conflicting voltage ratings for the same motor: 400V (PDF manual), 415V (ERP database), and 380V (supplier website).

The Physics Rule Engine validates each claim against the three-phase power formula. The 380V claim fails: it is mathematically inconsistent with the stated power output and current draw. The resolver scores the remaining claims and selects 400V from the PDF manual, which carries the highest authority weight and no physics penalties.

**Anomaly raised:** `ELEC-001 — Three-Phase Power Invariant Violation`

### Scenario 2 — Environmental Rating Conflict

A supplier catalog specifies an `IP23` ingress protection rating. The motor is classified as Totally Enclosed Fan Cooled (TEFC). IP23 denotes an open, vented enclosure — a physical impossibility for a sealed motor.

The rule engine flags the contradiction against IEC 60034-5 enclosure standards and isolates the correct `IP55` rating from a higher-authority source.

**Anomaly raised:** `ENV-001 — IP Rating / Enclosure Type Contradiction`

---

## Roadmap

The current version operates on simulated conflict data. The following capabilities are in active development:

- **Live Web Ingestion** — Integration with the Jina Reader API (`r.jina.ai`) to extract clean structured text from any live manufacturer URL.
- **LLM-Assisted Extraction** — Google Gemini API integration to parse unstructured Markdown into validated specification schemas.
- **Live ERP Cross-Reference** — Real-time conflict generation between scraped web data and internal SQLite ERP records.
- **Freemium Access Tiers** — Session-based usage tracking with a defined free tier and a premium upgrade path for enterprise access.

---

## Project Structure

```
.
├── app.py              # Streamlit dashboard and UI
├── engine.py           # Core verification and resolution pipeline
├── mock_data.py        # Conflict scenario data for MVP demonstration
└── requirements.txt    # Python dependencies
```

---

## License

MIT
