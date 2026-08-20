# The Forensic Data Agent for Industrial Commerce 🔬

> *"Industrial commerce doesn’t have a data extraction problem; it has a TRUTH problem."*

**Core Architecture Principle:** Probabilistic Extraction at the Edge, Deterministic Verification at the Core.

This project is a multi-pass data architecture designed to ingest conflicting claims from multiple industrial sources (datasheets, legacy ERPs, web scrapes) and mathematically prove the "canonical truth" using deterministic physics invariants and NIST-compliant unit resolution.

---

## 🚀 Quickstart Guide

We have included a setup script to instantly create a virtual environment, install dependencies, and prepare the project.

### Step 1: Setup the Environment
Open a terminal (Command Prompt or PowerShell) in the project directory and run the setup script:

**Windows:**
```cmd
run_this
```
*(This executes `python -m venv .venv && call .\.venv\Scripts\activate.bat && pip install -r requirements.txt`)*

**Mac / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Launch the Dashboard
With your virtual environment activated, start the Streamlit UI:
```bash
streamlit run app.py
```
Open the provided Local URL (usually `http://localhost:8501`) in your web browser.

---

## 🧪 How to Demo the Features

The Streamlit UI contains adversarial mock profiles designed to showcase the pipeline's capabilities. Use the sidebar to navigate the demo cases.

### Case 1: The Power Conflict
*Showcases Pass 3 Physics Invariant checking and conflict resolution.*

1. Select **Case 1: The Power Conflict** from the dropdown menu in the sidebar.
2. Click **🚀 Run Forensic Pipeline**.
3. **What to observe:**
   - **The Left Column** displays conflicting claims ingested into the Evidence Graph without overwriting each other.
   - **The Right Column** detects a **[CRITICAL] ELEC-001** physics violation. The mathematical engine verifies that the stated wattage (90kW) and voltage (415V) violate the standard three-phase power formula `P = √3 × V × I × PF × η`. 
   - The **Conflict Resolver** scores the remaining evidence (Authority + Confidence + Recency) and explicitly logs *why* it rejected the false marketing claim.

### Case 2: The Bad IP Code & Unit Trace
*Showcases Pass 2 NIST-compatible unit precision truncation and Regex validation.*

1. Select **Case 2: The Bad IP Code & Unit Trace** from the dropdown menu in the sidebar.
2. Click **🚀 Run Forensic Pipeline**.
3. **What to observe:**
   - **The Right Column** catches a **[CRITICAL] ENV-001** anomaly because the legacy database supplied an invalid `IP99-X` rating, caught by the IEC 60034-5 regex checker.
   - Scroll down to view the **Unit Normalization Audit Trail**. The engine converts `250 lb` into kilograms (`113 kg`) without losing precision in the intermediate steps, enforcing strict significant-digit policies according to NIST SP 811.

---

## ⚙️ Running the Headless Engine (CLI)
If you want to test the architecture without the UI, you can run the raw Python engine directly. The `engine.py` file is entirely dependency-free (Python 3.10+ standard library only) for maximum portability.

```bash
python engine.py
```
This will output a terminal-based ASCII "Pipeline Run Report" with the full mathematical breakdown and rejection logs.

---

## 📂 Project Structure

- `engine.py` — The core 4-pass pipeline (Evidence Graph, Unit Normalizer, Rule Engine, Conflict Resolver).
- `app.py` — The Streamlit presentation dashboard.
- `mock_data.py` — Adversarial test cases and conflicting source profiles.
- `PITCH_DECK.md` — The structured hackathon presentation flow and speaker scripts.
- `run_this` — Quickstart batch script for environment initialization.
- `requirements.txt` — Project dependencies (`streamlit`, `pandas`, `pydantic`).
