# THE FORENSIC DATA AGENT
## Hackathon Pitch Deck — Full Engineering Narrative

---

## SLIDE 1 — HOOK SLIDE

### 🎤 Speaker Opening Script (30-second verbal delivery)

> "Every industrial equipment company in the world is racing to digitize its catalog.
> They're spending millions on OCR, LLMs, and scraping pipelines.
> And yet — a buyer in Manchester orders a 75-kilowatt motor based on a catalog that says 415 volts,
> the actual nameplate says 400 volts, and the archived product page says 380.
> The machine gets wired wrong. The insulation fails. The plant stops.
>
> This is not an extraction problem. Every company already extracted the data.
> They extracted three different, conflicting *versions* of the truth.
>
> **Industrial commerce has a TRUTH problem.**
>
> We built a Forensic Data Agent that doesn't pick the loudest source —
> it subpoenas all of them, weighs the physics, and signs off on a canonical truth.
> Let us show you how."

**[Advance slide]**

---

## SLIDE 2 — THE PROBLEM STATEMENT

### Visual: Three contradictory spec sheets for the same motor.

| Source | Voltage Claimed | Confidence | Date |
|---|---|---|---|
| 📄 PDF Manufacturer Manual | **400V** | High | Nov 2023 |
| 📊 Distributor Catalog | **415V** | Medium | Jan 2024 |
| 🕸️ Legacy Web Scrape | **380V** | Low | May 2021 |

> **Which one is true?**
> A naive system picks one and deletes the others. Ours keeps all three alive — permanently —
> and uses physics, timestamps, and source authority to mathematically prove which is canonical.

---

## SLIDE 3 — THE CORE ARCHITECTURE

```
┌──────────────────────────────────────────────────────────────────────┐
│                      FORENSIC DATA AGENT PIPELINE                    │
│         "Probabilistic Extraction at the Edge,                       │
│          Deterministic Verification at the Core"                     │
├────────────┬────────────┬────────────────────┬────────────────────── ┤
│   PASS 1   │   PASS 2   │      PASS 3         │       PASS 4          │
│            │            │                    │                       │
│  Evidence  │   NIST     │  Physics Invariant  │   Conflict           │
│  Graph     │   Unit     │  Rule Engine        │   Resolver           │
│  Ingestion │  Normalizer│                    │   (Weighted Matrix)  │
│            │            │  ELEC-001 ✓/✗      │                       │
│  No claim  │  Audit     │  ENV-001  ✓/✗      │   Evidence Score      │
│  ever      │  trail     │                    │   S = 0.40×Auth       │
│  deleted   │  preserved │  → ForensicAnomaly  │     + 0.30×Conf      │
│            │            │    Object (never    │     + 0.15×Recency   │
│            │            │    crashes thread)  │     + 0.15×Physics   │
└────────────┴────────────┴────────────────────┴───────────────────────┘
```

---

## SLIDE 4 — FEATURE SCORECARD vs HACKATHON CONSTRAINTS

### How Our Architecture Answers Every Judging Criterion

| Hackathon Criterion | Our Implementation | Demonstrable Feature |
|---|---|---|
| **Structured Data Generation** | `ProductEvidenceSnapshot` (Pydantic v2) — fully typed, serializable JSON schema that preserves ALL conflicting claims under `electrical.voltage.claims[]` | Live JSON snapshot rendered in dashboard |
| **Accuracy & Consistency** | `ConflictResolver` weighted matrix: S = 0.40×Authority + 0.30×Confidence + 0.15×Recency + 0.15×PhysicsBonus. Canonical truth is mathematically signed, not guessed | Evidence Score Breakdown table shown in real-time |
| **AI Validation Layer** | `EngineeringRuleEngine` with ELEC-001 (three-phase power invariant: P_out ≈ √3·V·I·PF·η) and ENV-001 (IEC 60034-5 IP code regex + cross-property cooling physics check) | Live anomaly cards with CRITICAL/WARNING severity |
| **Scalable Catalog Engine** | `EvidenceGraphStore` is a thin wrapper over a swappable dict — production adapter drops in Redis or Postgres. `ForensicAgentPipeline.run()` is stateless per product, scales horizontally | Architecture diagram + code modularity |

---

## SLIDE 5 — THE MATH (Show your engineering rigor)

### ELEC-001: Three-Phase Power Invariant

```
P_out_theoretical = √3 × V_line × I_line × cos(φ) × η

Where:
  V_line = Line-to-line voltage    [V]
  I_line = Full-load line current  [A]
  cos(φ) = Power Factor           [dimensionless, 0–1]
  η      = Motor efficiency       [dimensionless, 0–1]
  
Tolerance Δ = |P_stated - P_theoretical| / P_stated ≤ 5%

If Δ > 5%  → ForensicAnomalyObject (WARNING)
If Δ > 15% → ForensicAnomalyObject (CRITICAL)
Thread: NEVER raised as exception. Pipeline continues.
```

### Evidence Score Formula

```
S(claim_i) = 0.40 × Authority(source_type)
           + 0.30 × extraction_confidence
           + 0.15 × exp(-0.005 × age_days)     ← Exponential recency decay
           + 0.15 × PhysicsBonus               ← 1.0 / 0.5 / 0.0 (pass/unchecked/fail)

Winner = argmax S(claim_i)   ∀ claims in property.claims[]
```

### ENV-001: IP Code Validation (Three-Layer)

```
Layer 1 — Regex: ^IP[0-6X][0-9X][ABCD]?[HMSW]?$
Layer 2 — Semantic: second digit > 6 → immersion flag (rare for motors)
Layer 3 — Physics cross-check: 
           TEFC motor → IP first digit MUST be ≥ 4
           IP23 + TEFC = PHYSICAL IMPOSSIBILITY → CRITICAL anomaly
```

---

## SLIDE 6 — THE KILLER DEMO BLUEPRINT

### 🎬 Stage Demo Script: "Catching the Official Engineering Typo"

**Setup (pre-loaded in the app):**

- Product: **ABB M3AA 75kW three-phase induction motor**
- Three voltage sources ingested: 400V (PDF), 415V (catalog), 380V (legacy web)
- IP rating ingested from legacy scrape: **IP23**
- Motor cooling method: **TEFC** (Totally Enclosed Fan Cooled)

---

**Act 1 — Open the Evidence Graph Panel**

> "Here's what every other system sees: three different voltages, and it just picks one.
> We keep all three, alive, with their source, confidence, and timestamp."
>
> *[Point to the three claim cards in the left panel — highlight the conflict badge]*

---

**Act 2 — Click "Run Forensic Pipeline"**

> "We're now running our four-pass Forensic Pipeline."

**What fires on stage:**

```
PASS 1: 3 voltage claims ingested. 0 overwrites.
PASS 2: "400V" → 400.0 V (NIST audit trail preserved)
         "485 lb" → 220.0 kg (significant figures: 3)
PASS 3: ENV-001 CRITICAL → "IP23" on a TEFC motor is physically impossible.
         A TEFC motor is totally enclosed. IP23 means it's open. Contradiction.
         → ForensicAnomalyObject fires. Thread continues.
PASS 4: Voltage resolution:
         PDF Manual wins: score=0.8823
         Catalog rejected: score=0.7612 (older, lower physics bonus)
         Legacy scrape rejected: score=0.4105 (low authority, physics FAIL, oldest)
```

---

**Act 3 — Point to the Truth Log Panel**

> "Our system didn't just find the right voltage — it proved WHY 380V is wrong.
> The legacy scrape's value was flagged by the three-phase power invariant,
> its physics bonus dropped to zero, and it was automatically eliminated.
>
> And the IP23 on a totally enclosed motor?
> That's an official engineering typo that has been sitting in a distributor database
> since 2021. Our physics invariant caught it in milliseconds."

---

**Act 4 — Close**

> "This is not a search engine. This is a forensic engine.
> It doesn't retrieve data — it establishes truth.
> And in industrial commerce, truth is the product."

---

## SLIDE 7 — SCALABILITY ARCHITECTURE

```
Production Deployment Path
──────────────────────────

EvidenceGraphStore
  └── dict (demo) → Redis Cluster (production)
       └── 100M+ claims, O(1) lookup per product_id

ForensicAgentPipeline.run()
  └── Stateless, async-ready
       └── Deploy on Cloud Run / Lambda (per-product)
            └── Horizontal scale: 1 worker per 1,000 products/min

EngineeringRuleEngine
  └── Currently: ELEC-001, ENV-001
       └── Extensible: MECH-001 (bearing load), THM-001 (thermal dissipation)
            └── Each rule: <50 lines, self-contained, returns FAO or None

ConflictResolver
  └── Weights tunable per industry vertical
       └── Heavy equipment: w_authority=0.45 (manuals more trusted)
       └── E-commerce: w_recency=0.30 (freshness more trusted)
```

---

## SLIDE 8 — TECHNICAL STACK & STANDARDS COMPLIANCE

| Component | Technology | Standard |
|---|---|---|
| Data Models | Pydantic v2 (strict typing) | JSON Schema Draft-07 |
| Unit Conversion | Python `decimal.Decimal` (28-digit precision) | **NIST SP 811** Appendix B |
| Precision Policy | Sig-fig detection + ROUND_HALF_UP at boundary | **NIST TN 1297** |
| Electrical Check | Three-phase power formula: √3·V·I·PF·η | **IEC 60034-1** |
| Enclosure Check | Regex + semantic + cross-property validation | **IEC 60034-5 / IEC 60529** |
| Dashboard | Streamlit + pandas | — |

---

## SLIDE 9 — CLOSING STATEMENT

### 🎤 Speaker Closing Script (15 seconds)

> "Every industrial catalog has three versions of the truth hiding inside it.
> We built the only system that reads all three,
> weighs them against the laws of physics,
> and tells you — with mathematical proof — which one to trust.
>
> **Forensic Data Agent.**
> Because in industry, the wrong number doesn't just fail validation —
> it fails a factory."

---

## APPENDIX: ONE-LINE PITCH VARIANTS

| Context | Pitch |
|---|---|
| **30-second elevator** | "We built a four-pass AI pipeline that ingests conflicting industrial data from multiple sources without overwriting any of them, then uses physics invariants to mathematically prove which value is canonical truth." |
| **Technical judge** | "Our ConflictResolver scores evidence claims on a weighted matrix: 40% source authority, 30% extraction confidence, 15% exponential recency decay, 15% physics consistency — producing a deterministic canonical truth with a full rejection audit log." |
| **Business judge** | "When an industrial buyer specs the wrong motor because three catalogs disagreed on voltage, that's a warranty claim, a plant shutdown, and a lost customer. We prevent that with forensic-grade data verification." |
