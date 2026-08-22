# Forensic Data Agent 🕵️‍♂️ (UniHack 2026)

**"Probabilistic Extraction at the Edge, Deterministic Verification at the Core."**

## The Problem
In industrial supply chains, product data is a mess. When procuring an industrial motor, a company might get three different voltage specifications from three different sources: an outdated internal ERP database, a supplier catalog, and a manufacturer's PDF. 

Most software forces human engineers to manually hunt down the truth, which takes hours. If they guess wrong, expensive equipment blows up. If they use a standard AI to summarize it, the AI just guesses the most common number—which is dangerous.

## The Solution
We built the **Forensic Data Agent** — a system that doesn't just extract data, it mathematically PROVES which data is correct. It ingests conflicting claims, normalizes them, and runs hard engineering physics rules (e.g., checking if `Volts × Amps = Watts`) to definitively prove which data point is a typo, and which is reality.

---

## 🏗️ The 4-Pass Architecture

1. **Input Layer (Evidence Graph):** Ingests conflicting claims from multiple sources without overwriting any data. Preserves a perfect audit trail of every claim, its source, timestamp, and confidence.
2. **Pass 1 - Unit Normalizer:** Converts raw values (e.g., lbs to kg) strictly following NIST SP 811 scientific precision rules.
3. **Pass 2 - Physics Rule Engine:** Cross-checks claims against physical reality (e.g., mathematically verifying if Watts, Volts, and Amps align using IEC formulas; checking if IP ratings match enclosure types).
4. **Pass 3 - Conflict Resolver:** Weighs sources mathematically (`Score = 40% Authority + 30% Confidence + 15% Recency + 15% Physics Bonus`) to output the absolute canonical truth with a full audit log.

---

## 🔮 Future Development: Live Data Ingestion

While the current MVP runs on simulated supply chain conflicts, our immediate roadmap integrates a live intelligence pipeline:
- **Jina Reader API:** A user inputs a live product URL, and the agent uses `r.jina.ai` to bypass complex HTML and extract clean Markdown.
- **Gemini LLM Extraction:** The clean Markdown is fed to Google's Gemini API to intelligently extract structured specs.
- **Live ERP Simulation:** The live web specs are instantly cross-referenced against a legacy SQLite ERP database to dynamically resolve real-world conflicts on the fly.
- **Freemium Limits:** A built-in monetization model that tracks extraction usage and prompts users to upgrade to premium after a set number of scrapes.

---

## 🚀 Quickstart Guide

### 1. Setup the Environment
Open a terminal in the project directory and run:

**Windows:**
```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Mac / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Launch the Dashboard
With your virtual environment activated, start the Streamlit UI:
```bash
streamlit run app.py
```
Open the provided Local URL (usually `http://localhost:8501`) in your web browser.

---

## 🧪 Usage Examples

The Streamlit UI includes sample profiles to demonstrate the validation pipeline.

### Case 1: The Power Conflict
*Demonstrates physics invariant checking across data sources.*
1. Select **Scenario 1 — Power Conflict** from the sidebar and click **Run Full Analysis**.
2. **Observation:** The system ingests conflicting voltages (400V, 415V, 380V). An `[ELEC-001]` critical violation is raised because the 380V claim physically violates the three-phase power formula. The system resolves the conflict by scoring the remaining evidence.

### Case 2: The Bad IP Code & Unit Trace
*Demonstrates unit standardization and environmental contradiction logic.*
1. Select **Scenario 2 — Environmental Conflict** from the sidebar and click **Run Full Analysis**.
2. **Observation:** An `[ENV-001]` violation is raised because an open `IP23` rating is physically impossible on a Totally Enclosed (TEFC) motor. The system isolates the correct `IP55` rating.

---

## 📂 Project Structure

- `app.py` — Streamlit dashboard and UI.
- `engine.py` — Core forensic validation and conflict resolution logic.
- `mock_data.py` — Sample conflicting data profiles for MVP testing.
- `requirements.txt` — Project dependencies.
