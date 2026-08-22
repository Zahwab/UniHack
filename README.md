# Industrial Data Verification Pipeline

This project implements a multi-pass data ingestion and verification architecture. It processes data from multiple industrial sources (datasheets, ERP systems, web scrapes) and verifies the information using physical invariants and unit standardization.

---

## Quickstart Guide

Follow these steps to set up the project environment and run the application.

### Step 1: Setup the Environment
Open a terminal (Command Prompt or PowerShell) in the project directory and run the setup script:

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

### Step 2: Launch the Dashboard
With your virtual environment activated, start the Streamlit UI:
```bash
streamlit run app.py
```
Open the provided Local URL (usually `http://localhost:8501`) in your web browser.

---

## Usage Examples

The Streamlit UI includes sample profiles to demonstrate the validation pipeline. Select different cases from the sidebar.

### Case 1: Power Specifications
*Demonstrates physics invariant checking across data sources.*

1. Select **Case 1: The Power Conflict** from the sidebar.
2. Click **Run Pipeline**.
3. **Observations:**
   - The system ingests and displays conflicting claims from multiple sources.
   - An **ELEC-001** validation error is raised if the provided wattage and voltage violate the standard three-phase power formula `P = √3 × V × I × PF × η`.
   - The system resolves the conflict by scoring evidence based on source authority, confidence, and recency.

### Case 2: Unit Standardization and Format Validation
*Demonstrates unit conversion and format checking.*

1. Select **Case 2: The Bad IP Code & Unit Trace** from the sidebar.
2. Click **Run Pipeline**.
3. **Observations:**
   - An **ENV-001** validation error is raised for invalid IP enclosure ratings format.
   - Values such as `250 lb` are standardized to `113 kg`, preserving appropriate significant figures.

---

## CLI Engine
To run the validation logic without the UI, execute the core engine directly:

```bash
python engine.py
```
This outputs a pipeline execution report to the terminal.

---

## Project Structure

- `engine.py` — Core validation and resolution logic.
- `app.py` — Streamlit web interface.
- `mock_data.py` — Sample data profiles for testing.
- `PITCH_DECK.md` — Project presentation and technical overview.
- `requirements.txt` — Project dependencies.
