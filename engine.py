"""
engine.py — Forensic Data Agent Pipeline
=========================================
Core Principle: "Probabilistic Extraction at the Edge, Deterministic Verification at the Core."
Industrial commerce doesn't have a data extraction problem; it has a TRUTH problem.

Dependencies: Python 3.10+ stdlib ONLY (no pydantic, no external packages).

Architecture:
  Pass 1  → EvidenceGraphStore     (ingest conflicting multi-source claims, never overwrite)
  Pass 2  → UnitNormalizer         (NIST SP 811-compliant unit conversion + full audit trail)
  Pass 3  → EngineeringRuleEngine  (ELEC-001, ENV-001 deterministic physics invariants)
  Pass 4  → ConflictResolver       (weighted evidence scoring → signed canonical truth)
"""

import json
import math
import re
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from decimal import Decimal, getcontext, ROUND_HALF_UP
from enum import Enum
from typing import Any

# ── Decimal precision: NIST SP 811 / TN 1297 — never round intermediate results ──
getcontext().prec = 28


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 0 — SHARED ENUMERATIONS & CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

class SourceType(str, Enum):
    PDF_MANUAL    = "pdf_manual"
    CATALOG_TABLE = "catalog_table"
    LEGACY_SCRAPE = "legacy_scrape"
    ERP_API       = "erp_api"
    USER_OVERRIDE = "user_override"


class AnomalySeverity(str, Enum):
    WARNING  = "WARNING"
    CRITICAL = "CRITICAL"


# Source authority priors — industrial data quality hierarchy.
# Grounded in IEC 82045-2 (document management for industrial assets).
SOURCE_AUTHORITY_WEIGHTS: dict[SourceType, float] = {
    SourceType.PDF_MANUAL:    0.95,   # Manufacturer datasheet → ground truth
    SourceType.ERP_API:       0.90,   # Live ERP feed → authoritative, may lag
    SourceType.CATALOG_TABLE: 0.80,   # Distributor catalog → usually accurate
    SourceType.USER_OVERRIDE: 0.75,   # Human override → trusted but fallible
    SourceType.LEGACY_SCRAPE: 0.40,   # Web scrape → lowest trust, stale risk
}


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 1 — EVIDENCE GRAPH STORE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class EvidenceClaim:
    """
    A single assertion about a product property from one data source.
    Multiple claims compose the Evidence Graph — none are ever overwritten.

    Fields
    ------
    claim_id            : UUID-based unique identifier for this assertion.
    raw_value           : Verbatim string exactly as extracted from source.
    normalized_value    : Parsed numeric in normalized_unit.
    normalized_unit     : SI or canonical unit string (e.g. 'V', 'kg', 'W').
    source_type         : SourceType enum — determines authority weight.
    source_id           : Document name, URL, or API endpoint reference.
    source_confidence   : Extraction model confidence score ∈ [0.0, 1.0].
    temporal_timestamp  : UTC datetime the source was last seen/captured.
    extraction_method   : e.g. 'vision_llm_pass1', 'tabular_heuristic_parser'.
    physics_consistent  : Set by EngineeringRuleEngine; None = unchecked.
    evidence_score      : Computed by ConflictResolver weighted matrix.
    """
    raw_value:          str
    normalized_value:   float
    normalized_unit:    str
    source_type:        SourceType
    source_id:          str
    source_confidence:  float
    temporal_timestamp: datetime
    extraction_method:  str
    claim_id:           str              = field(default_factory=lambda: str(uuid.uuid4()))
    physics_consistent: bool | None      = field(default=None)
    evidence_score:     float | None     = field(default=None)

    def __post_init__(self) -> None:
        if not math.isfinite(self.normalized_value):
            raise ValueError(f"normalized_value must be finite, got {self.normalized_value!r}")
        if not (0.0 <= self.source_confidence <= 1.0):
            raise ValueError(f"source_confidence ∈ [0,1], got {self.source_confidence!r}")
        if not isinstance(self.source_type, SourceType):
            self.source_type = SourceType(self.source_type)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["source_type"]        = self.source_type.value
        d["temporal_timestamp"] = self.temporal_timestamp.isoformat()
        return d


@dataclass
class EvidenceProperty:
    """
    A single product property (e.g. 'electrical.voltage') holding ALL conflicting
    claims simultaneously.  resolved_value is populated only after Pass 4 runs.
    """
    property_name:         str
    claims:                list[EvidenceClaim] = field(default_factory=list)
    resolved_value:        float | None         = field(default=None)
    resolved_unit:         str | None           = field(default=None)
    resolution_confidence: float                = field(default=0.0)
    winning_claim_id:      str | None           = field(default=None)

    def add_claim(self, claim: EvidenceClaim) -> None:
        """Append without overwriting — the core invariant of Pass 1."""
        self.claims.append(claim)

    def claim_count(self) -> int:
        return len(self.claims)

    def has_conflict(self) -> bool:
        """True when ≥2 claims disagree beyond a 1% relative tolerance."""
        if len(self.claims) < 2:
            return False
        vals = [c.normalized_value for c in self.claims]
        mx = max(vals)
        if mx == 0:
            return False
        return (mx - min(vals)) / mx > 0.01

    def to_dict(self) -> dict[str, Any]:
        return {
            "property_name":         self.property_name,
            "resolved_value":        self.resolved_value,
            "resolved_unit":         self.resolved_unit,
            "resolution_confidence": self.resolution_confidence,
            "winning_claim_id":      self.winning_claim_id,
            "claims":                [c.to_dict() for c in self.claims],
        }


@dataclass
class ProductEvidenceSnapshot:
    """
    Top-level container: one snapshot per product SKU.
    `properties` maps dot-path keys (e.g. 'electrical.voltage') to EvidenceProperty.
    """
    product_id:  str
    captured_at: datetime                      = field(default_factory=lambda: datetime.now(timezone.utc))
    properties:  dict[str, EvidenceProperty]  = field(default_factory=dict)

    def upsert_claim(self, property_path: str, claim: EvidenceClaim) -> None:
        """Idempotent: creates EvidenceProperty on first sight, then appends claim."""
        if property_path not in self.properties:
            self.properties[property_path] = EvidenceProperty(property_name=property_path)
        self.properties[property_path].add_claim(claim)

    def conflicted_properties(self) -> list[str]:
        return [k for k, v in self.properties.items() if v.has_conflict()]

    def to_dict(self) -> dict[str, Any]:
        return {
            "product_id":  self.product_id,
            "captured_at": self.captured_at.isoformat(),
            "properties":  {k: v.to_dict() for k, v in self.properties.items()},
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


class EvidenceGraphStore:
    """
    In-memory store for ProductEvidenceSnapshots.
    Production adapter: swap `_store` dict for a Redis hash or Postgres JSONB column.
    """

    def __init__(self) -> None:
        self._store: dict[str, ProductEvidenceSnapshot] = {}

    def ingest_claim(
        self,
        product_id:        str,
        property_path:     str,
        raw_value:         str,
        normalized_value:  float,
        normalized_unit:   str,
        source_type:       SourceType,
        source_id:         str,
        source_confidence: float,
        extraction_method: str,
        timestamp:         datetime | None = None,
    ) -> EvidenceClaim:
        """
        Primary ingestion entry-point for Pass 1.
        Returns the created EvidenceClaim for downstream chaining.
        """
        if product_id not in self._store:
            self._store[product_id] = ProductEvidenceSnapshot(product_id=product_id)

        claim = EvidenceClaim(
            raw_value=raw_value,
            normalized_value=normalized_value,
            normalized_unit=normalized_unit,
            source_type=source_type,
            source_id=source_id,
            source_confidence=source_confidence,
            extraction_method=extraction_method,
            temporal_timestamp=timestamp or datetime.now(timezone.utc),
        )
        self._store[product_id].upsert_claim(property_path, claim)
        return claim

    def get_snapshot(self, product_id: str) -> ProductEvidenceSnapshot | None:
        return self._store.get(product_id)

    def all_product_ids(self) -> list[str]:
        return list(self._store.keys())


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 2 — NIST-COMPLIANT UNIT NORMALIZER  (Pass 2)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class NormalizationAuditTrail:
    """
    Immutable audit trace for a single unit conversion.

    Per NIST SP 811 + TN 1297:
      - All intermediate calculations kept at full Decimal(28) precision.
      - Rounding is applied ONLY at the final display/serialization boundary.
      - Conversion factors sourced from NIST SP 811 Appendix B (exact where marked).
    """
    raw_string:                  str
    parsed_magnitude:            str
    parsed_unit_raw:             str
    base_si_unit:                str
    conversion_factor_exact:     str    # Exact Decimal string per NIST SP 811 Appendix B
    unrounded_float_calculation: str    # Full-precision Decimal result before rounding
    significant_digits_detected: int
    precision_policy_rule:       str
    final_display_value:         str
    final_numeric_value:         float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ── Conversion table: unit_alias → (base_SI_unit, exact_factor per NIST SP 811 Appendix B)
_UNIT_TABLE: dict[str, tuple[str, str]] = {
    # Mass
    "lb":   ("kg",    "0.45359237"),           # Exact, NIST SP 811 Appendix B
    "lbs":  ("kg",    "0.45359237"),
    "oz":   ("kg",    "0.028349523125"),        # Exact
    "ton":  ("kg",    "907.18474"),             # Short ton (US)
    "kg":   ("kg",    "1"),
    # Power
    "kw":   ("W",     "1000"),
    "mw":   ("W",     "1000000"),
    "hp":   ("W",     "745.69987158227022"),    # Mechanical HP, NIST SP 811
    "w":    ("W",     "1"),
    # Length
    "in":   ("m",     "0.0254"),                # Exact per NIST SP 811
    "ft":   ("m",     "0.3048"),                # Exact
    "mm":   ("m",     "0.001"),
    "cm":   ("m",     "0.01"),
    "m":    ("m",     "1"),
    # Pressure
    "psi":  ("Pa",    "6894.757293168"),        # NIST SP 811
    "bar":  ("Pa",    "100000"),
    "pa":   ("Pa",    "1"),
    # Rotational speed
    "rpm":  ("rad/s", "0.10471975511965977"),   # 2π/60
}

_PARSE_RE = re.compile(
    r"^\s*(?P<mag>-?\d+(?:[.,]\d+)?(?:[eE][+-]?\d+)?)\s*(?P<unit>[a-zA-Z/]+)\s*$"
)


def _count_sig_figs(mag_str: str) -> int:
    """
    Conservative NIST significant figure count.

    Rules applied (NIST SP 811 §3.3):
      1. All non-zero digits are significant.
      2. Zeros between non-zero digits are significant.
      3. Trailing zeros WITH a decimal point are significant.
      4. Trailing zeros WITHOUT a decimal point are ambiguous → treated as NOT significant.
      5. Leading zeros are never significant.
    """
    # Strip sign and exponent
    base = re.sub(r"[eE][+-]?\d+$", "", mag_str).replace("-", "").replace("+", "")
    has_decimal = "." in base
    digits = base.replace(",", "").replace(".", "").lstrip("0")
    if not digits:
        return 1  # "0" → 1 sig fig by convention
    return len(digits) if has_decimal else (len(digits.rstrip("0")) or 1)


def normalize_unit(raw_string: str) -> NormalizationAuditTrail:
    """
    Convert a measurement string to SI base units with a full NIST-compliant audit trail.

    Pass 2-A: Parse magnitude and unit from raw string.
    Pass 2-B: Multiply at full Decimal(28) precision — never round mid-chain (NIST TN 1297).
    Pass 2-C: Count significant figures from INPUT per NIST SP 811 §3.3.
    Pass 2-D: Quantize to sig-fig boundary with ROUND_HALF_UP ONLY at serialization.

    Examples
    --------
    >>> normalize_unit("250 lb")   # → "113. kg"  (2 sig figs from "25")
    >>> normalize_unit("0.75 kW")  # → "750. W"   (2 sig figs)
    >>> normalize_unit("5.25 in")  # → "0.1334 m" (3 sig figs)
    """
    match = _PARSE_RE.match(raw_string)
    if not match:
        raise ValueError(
            f"[UnitNormalizer] Cannot parse '{raw_string}'. "
            "Expected: '<number> <unit>'  e.g. '250 lb', '0.75 kW', '5.25 in'."
        )

    mag_str  = match.group("mag").replace(",", ".")
    unit_raw = match.group("unit")
    unit_key = unit_raw.lower()

    if unit_key not in _UNIT_TABLE:
        raise ValueError(
            f"[UnitNormalizer] Unknown unit '{unit_raw}'. "
            f"Supported units: {sorted(_UNIT_TABLE.keys())}"
        )

    base_unit, factor_str = _UNIT_TABLE[unit_key]
    factor  = Decimal(factor_str)
    mag_dec = Decimal(mag_str)

    # Pass 2-B: Full-precision intermediate (NIST: do not round mid-chain)
    unrounded = mag_dec * factor

    # Pass 2-C: Significant figures from the input string
    sig_figs = _count_sig_figs(mag_str)
    policy   = (
        f"NIST_SP811_sig_fig_retention | input_sig_figs={sig_figs} | "
        f"factor_source='NIST SP 811 Appendix B' | factor={factor_str!r} | "
        f"rounding=ROUND_HALF_UP at sig_fig boundary only"
    )

    # Pass 2-D: Round at the serialization boundary only
    if unrounded == 0:
        rounded     = Decimal("0")
        display_str = "0"
    else:
        order          = unrounded.adjusted()          # floor(log10(|result|))
        rounding_place = order - (sig_figs - 1)
        quant_exp      = Decimal(10) ** rounding_place
        rounded        = unrounded.quantize(quant_exp, rounding=ROUND_HALF_UP)
        display_str    = str(rounded)

    return NormalizationAuditTrail(
        raw_string=raw_string,
        parsed_magnitude=mag_str,
        parsed_unit_raw=unit_raw,
        base_si_unit=base_unit,
        conversion_factor_exact=factor_str,
        unrounded_float_calculation=str(unrounded),
        significant_digits_detected=sig_figs,
        precision_policy_rule=policy,
        final_display_value=f"{display_str} {base_unit}",
        final_numeric_value=float(rounded),
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 3 — FORENSIC ANOMALY OBJECT  (Pass 3 output carrier)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ForensicAnomalyObject:
    """
    Emitted by the EngineeringRuleEngine when an invariant is violated.

    Design constraints:
      - NEVER raises an exception — the pipeline thread must not die.
      - Carries enough context for the dashboard to render a full alert card.
      - `to_alert_dict()` produces a flat dict for Streamlit st.error consumption.
    """
    invariant_code:         str
    severity:               AnomalySeverity
    product_id:             str
    conflicting_variables:  dict[str, Any]
    description:            str
    remediation_hint:       str
    anomaly_id:             str               = field(default_factory=lambda: f"ano_{uuid.uuid4().hex[:8]}")
    mathematical_delta_pct: float | None      = field(default=None)
    detected_at:            datetime          = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_alert_dict(self) -> dict[str, str]:
        return {
            "Invariant":    self.invariant_code,
            "Severity":     self.severity.value,
            "Product":      self.product_id,
            "Delta":        f"{self.mathematical_delta_pct:.2f}%" if self.mathematical_delta_pct is not None else "N/A",
            "Description":  self.description,
            "Remediation":  self.remediation_hint,
        }

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["severity"]     = self.severity.value
        d["detected_at"]  = self.detected_at.isoformat()
        return d


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 4 — ENGINEERING RULE ENGINE  (Pass 3 Deterministic Verification)
# ═══════════════════════════════════════════════════════════════════════════════

# IEC 60034-5 / IEC 60529 IP code regex
# Format:  IP  [0-6 | X]  [0-9 | X]  [A|B|C|D]?  [H|M|S|W]?
_IP_REGEX = re.compile(
    r"^IP"
    r"(?P<first>[0-6X])"
    r"(?P<second>[0-9X])"
    r"(?P<additional>[ABCD])?"
    r"(?P<supplementary>[HMSW])?$"
)

# Minimum IP first-digit per cooling method (IEC 60034-1 / IEC 60034-6 design rules)
_COOLING_IP_MINIMUMS: dict[str, int] = {
    "TEFC": 4,   # Totally Enclosed Fan Cooled → minimum IP4X
    "TENV": 4,   # Totally Enclosed Non-Ventilated → minimum IP4X
    "ODP":  2,   # Open Drip Proof → minimum IP2X
    "WP1":  2,   # Weather Protected Type I
    "WP2":  5,   # Weather Protected Type II → minimum IP5X
    "XPRF": 6,   # Explosion Proof → minimum IP6X
}


class EngineeringRuleEngine:
    """
    Deterministic verification layer (Pass 3).

    Contract:
      - Every check method returns None on PASS.
      - Returns a ForensicAnomalyObject on FAIL — never raises.
      - Any unexpected exception inside a check is caught and wrapped into a FAO.
    """

    # ── ELEC-001: Three-Phase Power Invariant ────────────────────────────────

    @staticmethod
    def check_elec_001(
        product_id:   str,
        p_out_kw:     float,
        voltage_v:    float,
        current_a:    float,
        power_factor: float,
        efficiency:   float,
        tolerance:    float = 0.05,   # 5% — nominal rounding allowance per IEC 60034-1
    ) -> ForensicAnomalyObject | None:
        """
        ELEC-001 — Three-Phase Power Invariant Consistency Check
        ─────────────────────────────────────────────────────────
        Physics Formula (IEC 60034-1):
            P_electrical_in  = √3 × V_line × I_line × cos(φ)
            P_shaft_out      = P_electrical_in × η
            Invariant:  |P_stated - P_shaft_out| / P_stated ≤ tolerance

        Where:
          V_line   = Line-to-line supply voltage [V]
          I_line   = Full-load line current [A]
          cos(φ)   = Power factor, dimensionless ∈ (0, 1]
          η        = Motor efficiency, dimensionless ∈ (0, 1]

        Severity thresholds:
          Δ ≤ 5%   → PASS
          5% < Δ ≤ 15% → WARNING  (likely catalog rounding)
          Δ > 15%  → CRITICAL     (probable data source error or wrong product)
        """
        try:
            if any(v is None for v in [p_out_kw, voltage_v, current_a, power_factor, efficiency]):
                return None  # Insufficient data — skip

            if p_out_kw <= 0:
                raise ValueError(f"p_out_kw must be > 0, got {p_out_kw}")
            if not (0 < power_factor <= 1.0):
                raise ValueError(f"power_factor ∈ (0,1], got {power_factor}")
            if not (0 < efficiency <= 1.0):
                raise ValueError(f"efficiency ∈ (0,1], got {efficiency}")

            p_out_w              = p_out_kw * 1000.0
            p_electrical_in_w    = math.sqrt(3) * voltage_v * current_a * power_factor
            p_theoretical_out_w  = p_electrical_in_w * efficiency
            delta_w              = abs(p_out_w - p_theoretical_out_w)
            pct_error            = delta_w / p_out_w

            if pct_error <= tolerance:
                return None  # PASS ✓

            severity = (
                AnomalySeverity.CRITICAL if pct_error > 0.15
                else AnomalySeverity.WARNING
            )

            return ForensicAnomalyObject(
                invariant_code="ELEC-001",
                severity=severity,
                product_id=product_id,
                conflicting_variables={
                    "P_out_stated_kW":     p_out_kw,
                    "P_out_stated_W":      p_out_w,
                    "V_line_V":            voltage_v,
                    "I_full_load_A":       current_a,
                    "PF_cos_phi":          power_factor,
                    "eta_efficiency":      efficiency,
                    "P_electrical_in_W":   round(p_electrical_in_w, 2),
                    "P_theoretical_out_W": round(p_theoretical_out_w, 2),
                    "delta_W":             round(delta_w, 2),
                    "tolerance_applied":   f"{tolerance*100:.0f}%",
                },
                mathematical_delta_pct=round(pct_error * 100, 3),
                description=(
                    f"[ELEC-001] Physics invariant violated for '{product_id}'. "
                    f"Stated P_out = {p_out_w:.1f} W. "
                    f"Computed P_out = √3 × {voltage_v}V × {current_a}A × {power_factor} × {efficiency} "
                    f"= {p_theoretical_out_w:.1f} W. "
                    f"Discrepancy = {pct_error*100:.2f}% (threshold: {tolerance*100:.0f}%)."
                ),
                remediation_hint=(
                    "Primary suspects: (1) Catalog lists INPUT current instead of OUTPUT current. "
                    "(2) Voltage claim is from wrong regional supply (e.g. 380V legacy EU vs 400V IEC 60038). "
                    "(3) Efficiency value is from a different load point (75% load vs 100% load nameplate). "
                    "Cross-reference against IEC 60034-1 Table 1 rated values."
                ),
            )

        except Exception as exc:
            return ForensicAnomalyObject(
                invariant_code="ELEC-001",
                severity=AnomalySeverity.WARNING,
                product_id=product_id,
                conflicting_variables={"exception": str(exc), "inputs": {
                    "p_out_kw": p_out_kw, "voltage_v": voltage_v,
                    "current_a": current_a, "power_factor": power_factor,
                    "efficiency": efficiency,
                }},
                description=f"[ELEC-001] Rule evaluation raised exception: {exc}",
                remediation_hint="Inspect input values for None, NaN, or type errors.",
            )

    # ── ENV-001: IEC 60034-5 / IEC 60529 IP Code Validation ─────────────────

    @staticmethod
    def check_env_001(
        product_id:     str,
        ip_rating_raw:  str,
        cooling_method: str | None = None,
    ) -> ForensicAnomalyObject | None:
        """
        ENV-001 — IEC 60034-5 / IEC 60529 Enclosure Classification Check
        ──────────────────────────────────────────────────────────────────
        Three-layer validation:

        Layer 1 — Structural regex:
            Pattern: ^IP[0-6X][0-9X][ABCD]?[HMSW]?$
            Catches: OCR errors, missing digits, invalid suffix letters.

        Layer 2 — Semantic digit range:
            Second numeral > 6 implies immersion rating (rare for motors).
            Flags as WARNING for human review.

        Layer 3 — Cross-property physics cross-check:
            Cooling method IC code (IEC 60034-6) implies a minimum IP first digit.
            e.g. TEFC (totally enclosed) → first digit MUST be ≥ 4.
            IP23 + TEFC = physically impossible → CRITICAL anomaly.
        """
        try:
            clean = ip_rating_raw.strip().upper()
            match = _IP_REGEX.match(clean)

            # ── Layer 1: Format ──
            if not match:
                return ForensicAnomalyObject(
                    invariant_code="ENV-001",
                    severity=AnomalySeverity.CRITICAL,
                    product_id=product_id,
                    conflicting_variables={"ip_rating_raw": ip_rating_raw, "cleaned": clean},
                    description=(
                        f"[ENV-001-L1] IP rating '{ip_rating_raw}' fails IEC 60034-5 structural regex. "
                        "Expected pattern: IP[0-6X][0-9X][ABCD]?[HMSW]?  "
                        "(e.g. 'IP55', 'IP65W', 'IP23M', 'IP54B')."
                    ),
                    remediation_hint=(
                        "Common OCR errors: 'IPS5' (S instead of digit), 'IP5 5' (space mid-code). "
                        "Check source PDF rendering at the rating plate region."
                    ),
                )

            first  = match.group("first")
            second = match.group("second")

            # ── Layer 2: Immersion digit flag ──
            if second not in ("X",) and int(second) > 6:
                return ForensicAnomalyObject(
                    invariant_code="ENV-001",
                    severity=AnomalySeverity.WARNING,
                    product_id=product_id,
                    conflicting_variables={
                        "ip_rating": clean,
                        "second_numeral": second,
                        "meaning": {
                            "7": "Temporary immersion (30 min, 1m depth)",
                            "8": "Continuous immersion (manufacturer-specified depth)",
                            "9": "High-pressure/high-temp water jet (IEC 60034-5:2020)",
                        }.get(second, "Immersion class"),
                    },
                    description=(
                        f"[ENV-001-L2] Second digit '{second}' implies immersion rating. "
                        "This is valid per IEC 60529 but highly unusual for standard rotating machines. "
                        "Verify this is intentional and not an OCR artefact."
                    ),
                    remediation_hint=(
                        "If confirmed, add 'verified_immersion=true' to the product record. "
                        "Otherwise re-extract from manufacturer datasheet rating plate section."
                    ),
                )

            # ── Layer 3: Cross-property physics cross-check ──
            if cooling_method and first != "X":
                first_digit  = int(first)
                min_required = _COOLING_IP_MINIMUMS.get(cooling_method.upper())

                if min_required is not None and first_digit < min_required:
                    return ForensicAnomalyObject(
                        invariant_code="ENV-001",
                        severity=AnomalySeverity.CRITICAL,
                        product_id=product_id,
                        conflicting_variables={
                            "ip_rating":        clean,
                            "cooling_method":   cooling_method,
                            "ip_first_digit":   first_digit,
                            "minimum_required": min_required,
                            "standard_ref":     "IEC 60034-6 IC code cross-reference",
                        },
                        description=(
                            f"[ENV-001-L3] Physical contradiction: Cooling method '{cooling_method}' "
                            f"requires IP first digit ≥ {min_required} (IP{min_required}X), "
                            f"but extracted rating is {clean} (first digit = {first_digit}). "
                            f"A totally enclosed motor CANNOT have an open enclosure rating."
                        ),
                        remediation_hint=(
                            f"This '{cooling_method}' motor is physically enclosed by definition. "
                            f"IP{first_digit}X is an open-frame rating — a physical impossibility. "
                            "Source is either: (a) an incorrect legacy record, "
                            "(b) a mis-scraped product variant, or (c) a confirmed catalog typo."
                        ),
                    )

            return None  # All three layers PASS ✓

        except Exception as exc:
            return ForensicAnomalyObject(
                invariant_code="ENV-001",
                severity=AnomalySeverity.WARNING,
                product_id=product_id,
                conflicting_variables={"exception": str(exc)},
                description=f"[ENV-001] Rule evaluation raised exception: {exc}",
                remediation_hint="Inspect ip_rating_raw for None, encoding issues, or unexpected format.",
            )


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 5 — CONFLICT RESOLVER  (Pass 4 Weighted Evidence Matrix)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class EvidenceScoreBreakdown:
    """Decomposed score for each claim — powers the Truth Log Panel audit view."""
    claim_id:             str
    authority_score:      float   # SOURCE_AUTHORITY_WEIGHTS[source_type]
    confidence_score:     float   # source_confidence from extraction model
    recency_score:        float   # exp(-λ × age_days) decay
    physics_bonus:        float   # 1.0 / 0.5 / 0.0 for pass / unchecked / fail
    final_evidence_score: float   # Weighted sum
    rank:                 int     # 1 = winner

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ResolutionResult:
    """Complete output of ConflictResolver for one EvidenceProperty."""
    property_name:         str
    winning_claim_id:      str
    winning_value:         float
    winning_unit:          str
    resolution_confidence: float
    score_breakdown:       list[EvidenceScoreBreakdown]
    rejection_log:         list[str] = field(default_factory=list)
    was_contested:         bool      = False

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


class ConflictResolver:
    """
    Weighted Evidence Matrix Scoring Engine (Pass 4).

    ┌─────────────────────────────────────────────────────────────────────────┐
    │  Evidence Score Formula                                                 │
    │                                                                         │
    │  S(claim_i) = w_a × Authority(source_type_i)                           │
    │             + w_c × source_confidence_i                                 │
    │             + w_r × RecencyDecay(timestamp_i, newest_timestamp)         │
    │             + w_p × PhysicsBonus(physics_consistent_i)                  │
    │                                                                         │
    │  Weights (Σ = 1.0):                                                     │
    │    w_a = 0.40  (Source authority — structural, most important)           │
    │    w_c = 0.30  (Extraction confidence — model-assigned probability)      │
    │    w_r = 0.15  (Recency — newer catalogs preferred)                      │
    │    w_p = 0.15  (Physics consistency — deterministic bonus/penalty)       │
    │                                                                         │
    │  PhysicsBonus:                                                          │
    │    physics_consistent = True  →  1.0  (confirmed by invariant engine)   │
    │    physics_consistent = None  →  0.5  (not yet checked, neutral prior)  │
    │    physics_consistent = False →  0.0  (penalised — failed invariant)    │
    │                                                                         │
    │  RecencyDecay:                                                          │
    │    score = exp(-λ × age_days), λ = 0.005                                │
    │    Half-life ≈ 139 days — tuned for industrial catalog refresh cycles   │
    └─────────────────────────────────────────────────────────────────────────┘

    Winner = argmax S(claim_i) for all claims in property.claims
    """

    W_AUTHORITY    = 0.40
    W_CONFIDENCE   = 0.30
    W_RECENCY      = 0.15
    W_PHYSICS      = 0.15
    RECENCY_LAMBDA = 0.005    # Exponential decay constant

    @classmethod
    def _recency_score(cls, claim_ts: datetime, newest_ts: datetime) -> float:
        """Exponential decay: newest claim scores 1.0, older claims decay smoothly."""
        if claim_ts.tzinfo is None:
            claim_ts = claim_ts.replace(tzinfo=timezone.utc)
        if newest_ts.tzinfo is None:
            newest_ts = newest_ts.replace(tzinfo=timezone.utc)
        age_days = max(0.0, (newest_ts - claim_ts).total_seconds() / 86400.0)
        return math.exp(-cls.RECENCY_LAMBDA * age_days)

    @classmethod
    def _physics_bonus(cls, physics_consistent: bool | None) -> float:
        if physics_consistent is True:
            return 1.0
        if physics_consistent is False:
            return 0.0
        return 0.5  # None = unchecked = neutral prior

    @classmethod
    def resolve(cls, prop: EvidenceProperty) -> ResolutionResult:
        """
        Score all claims, rank them, select the winner, populate prop.resolved_value,
        and return a complete ResolutionResult with rejection audit log.
        """
        if not prop.claims:
            raise ValueError(f"Cannot resolve '{prop.property_name}' — no claims present.")

        was_contested = prop.has_conflict()
        newest_ts     = max(c.temporal_timestamp for c in prop.claims)

        breakdowns: list[EvidenceScoreBreakdown] = []

        for claim in prop.claims:
            authority  = SOURCE_AUTHORITY_WEIGHTS.get(claim.source_type, 0.50)
            confidence = claim.source_confidence
            recency    = cls._recency_score(claim.temporal_timestamp, newest_ts)
            physics    = cls._physics_bonus(claim.physics_consistent)

            score = (
                cls.W_AUTHORITY  * authority
              + cls.W_CONFIDENCE * confidence
              + cls.W_RECENCY    * recency
              + cls.W_PHYSICS    * physics
            )

            claim.evidence_score = round(score, 6)

            breakdowns.append(EvidenceScoreBreakdown(
                claim_id=claim.claim_id,
                authority_score=round(authority, 4),
                confidence_score=round(confidence, 4),
                recency_score=round(recency, 4),
                physics_bonus=round(physics, 4),
                final_evidence_score=round(score, 6),
                rank=0,
            ))

        # Rank by descending score
        breakdowns.sort(key=lambda b: b.final_evidence_score, reverse=True)
        for rank, bd in enumerate(breakdowns, start=1):
            bd.rank = rank

        winner_bd    = breakdowns[0]
        winning_claim = next(c for c in prop.claims if c.claim_id == winner_bd.claim_id)

        # Mutate EvidenceProperty with resolved state (in-place)
        prop.resolved_value        = winning_claim.normalized_value
        prop.resolved_unit         = winning_claim.normalized_unit
        prop.resolution_confidence = round(winner_bd.final_evidence_score, 4)
        prop.winning_claim_id      = winner_bd.claim_id

        # Build rejection audit log for Truth Log Panel
        rejection_log: list[str] = []
        for bd in breakdowns[1:]:
            rejected = next(c for c in prop.claims if c.claim_id == bd.claim_id)
            rejection_log.append(
                f"REJECTED claim {bd.claim_id[:10]}…  "
                f"value={rejected.normalized_value} {rejected.normalized_unit}  "
                f"source={rejected.source_type.value}  "
                f"score={bd.final_evidence_score:.6f} (winner={winner_bd.final_evidence_score:.6f})  "
                f"Δ_authority={winner_bd.authority_score - bd.authority_score:+.4f}  "
                f"Δ_recency={winner_bd.recency_score - bd.recency_score:+.4f}  "
                f"Δ_physics={winner_bd.physics_bonus - bd.physics_bonus:+.4f}"
            )

        return ResolutionResult(
            property_name=prop.property_name,
            winning_claim_id=winner_bd.claim_id,
            winning_value=winning_claim.normalized_value,
            winning_unit=winning_claim.normalized_unit,
            resolution_confidence=round(winner_bd.final_evidence_score, 4),
            score_breakdown=breakdowns,
            rejection_log=rejection_log,
            was_contested=was_contested,
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 6 — FULL PIPELINE ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class PipelineRunResult:
    product_id:    str
    snapshot:      ProductEvidenceSnapshot
    resolution_map: dict[str, ResolutionResult]       = field(default_factory=dict)
    anomalies:      list[ForensicAnomalyObject]       = field(default_factory=list)
    unit_traces:    dict[str, NormalizationAuditTrail] = field(default_factory=dict)


class ForensicAgentPipeline:
    """
    Orchestrates all four passes for a single product.
    Stateless per invocation — safe for horizontal scaling.
    """

    def __init__(self, store: EvidenceGraphStore) -> None:
        self.store  = store
        self.engine = EngineeringRuleEngine()

    def run(
        self,
        product_id:     str,
        elec_params:    dict[str, float] | None = None,
        ip_rating:      str | None              = None,
        cooling_method: str | None              = None,
    ) -> PipelineRunResult:
        """
        Execute all four passes and return a complete PipelineRunResult.

        Parameters
        ----------
        product_id      : Target product in the EvidenceGraphStore.
        elec_params     : Keys: p_out_kw, voltage_v, current_a, power_factor, efficiency.
        ip_rating       : Raw IP code string for ENV-001 check.
        cooling_method  : Motor cooling type string (e.g. 'TEFC').
        """
        snapshot = self.store.get_snapshot(product_id)
        if not snapshot:
            raise ValueError(f"No snapshot found for product_id='{product_id}'")

        result = PipelineRunResult(product_id=product_id, snapshot=snapshot)

        # ── Pass 2: Unit normalization traces for extractable raw values ──
        for prop_path, prop in snapshot.properties.items():
            for claim in prop.claims:
                try:
                    trace = normalize_unit(claim.raw_value)
                    result.unit_traces[f"{prop_path}::{claim.claim_id[:8]}"] = trace
                except ValueError:
                    pass  # Non-unit strings (model codes, IP ratings) skipped gracefully

        # ── Pass 3: Physics invariant checks ──
        if elec_params:
            ano = self.engine.check_elec_001(product_id=product_id, **elec_params)
            if ano:
                result.anomalies.append(ano)
                # Mark voltage claims as physics-inconsistent to penalise them in Pass 4
                v_key = "electrical.voltage"
                if v_key in snapshot.properties:
                    for claim in snapshot.properties[v_key].claims:
                        if abs(claim.normalized_value - elec_params.get("voltage_v", 0)) < 1:
                            claim.physics_consistent = False

        if ip_rating:
            ano = self.engine.check_env_001(
                product_id=product_id,
                ip_rating_raw=ip_rating,
                cooling_method=cooling_method,
            )
            if ano:
                result.anomalies.append(ano)

        # ── Pass 4: Conflict resolution ──
        for prop_path, prop in snapshot.properties.items():
            try:
                res = ConflictResolver.resolve(prop)
                result.resolution_map[prop_path] = res
            except Exception as exc:
                print(f"[ConflictResolver] Skipped '{prop_path}': {exc}")

        return result


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 7 — DEMO SEED DATA  (Killer Demo Blueprint)
# ═══════════════════════════════════════════════════════════════════════════════

def build_demo_store() -> tuple[EvidenceGraphStore, dict[str, Any]]:
    """
    Seeds the EvidenceGraphStore with the canonical hackathon demo scenario:

    Product: ABB M3AA 75kW three-phase induction motor
      - Three conflicting voltage claims (400V/415V/380V from three sources)
      - IP rating contradiction: legacy scrape says IP23, PDF says IP55
      - Cooling method: TEFC → ENV-001 will flag IP23 as physically impossible
      - ELEC-001 will evaluate the three-phase power invariant against ingested values

    On stage, the pipeline will:
      1. Keep all conflicting claims alive (never overwrite)
      2. Fire ENV-001 CRITICAL on IP23 + TEFC
      3. Resolve voltage → PDF Manual 400V wins (highest authority + recency)
      4. Show full rejection audit log explaining why 380V was eliminated
    """
    store = EvidenceGraphStore()
    PID   = "MTR-ABB-M3AA-75KW"

    # ── electrical.voltage: three conflicting claims ──
    store.ingest_claim(
        product_id=PID, property_path="electrical.voltage",
        raw_value="400V",   normalized_value=400.0, normalized_unit="V",
        source_type=SourceType.PDF_MANUAL,    source_id="ABB_M3AA_Manual_v3.pdf",
        source_confidence=0.95, extraction_method="vision_llm_pass1",
        timestamp=datetime(2023, 11, 15, 8, 30, tzinfo=timezone.utc),
    )
    store.ingest_claim(
        product_id=PID, property_path="electrical.voltage",
        raw_value="415 V", normalized_value=415.0, normalized_unit="V",
        source_type=SourceType.CATALOG_TABLE, source_id="Grainger_Catalog_2024_p44",
        source_confidence=0.85, extraction_method="tabular_heuristic_parser",
        timestamp=datetime(2024, 1, 22, 14, 15, tzinfo=timezone.utc),
    )
    store.ingest_claim(
        product_id=PID, property_path="electrical.voltage",
        raw_value="380v",  normalized_value=380.0, normalized_unit="V",
        source_type=SourceType.LEGACY_SCRAPE, source_id="archive.industrialparts.com/2021",
        source_confidence=0.40, extraction_method="regex_dom_scrape",
        timestamp=datetime(2021, 5, 10, 9, 11, tzinfo=timezone.utc),
    )

    # ── mechanical.weight ──
    store.ingest_claim(
        product_id=PID, property_path="mechanical.weight",
        raw_value="485 lb", normalized_value=220.0, normalized_unit="kg",
        source_type=SourceType.PDF_MANUAL, source_id="ABB_M3AA_Manual_v3.pdf",
        source_confidence=0.95, extraction_method="vision_llm_pass1",
        timestamp=datetime(2023, 11, 15, 8, 30, tzinfo=timezone.utc),
    )

    # ── electrical.ip_rating: deliberate legacy typo for live demo ──
    store.ingest_claim(
        product_id=PID, property_path="electrical.ip_rating",
        raw_value="IP23", normalized_value=23.0, normalized_unit="IP_code",
        source_type=SourceType.LEGACY_SCRAPE, source_id="archive.industrialparts.com/2021",
        source_confidence=0.40, extraction_method="regex_dom_scrape",
        timestamp=datetime(2021, 5, 10, 9, 11, tzinfo=timezone.utc),
    )
    store.ingest_claim(
        product_id=PID, property_path="electrical.ip_rating",
        raw_value="IP55", normalized_value=55.0, normalized_unit="IP_code",
        source_type=SourceType.PDF_MANUAL, source_id="ABB_M3AA_Manual_v3.pdf",
        source_confidence=0.95, extraction_method="vision_llm_pass1",
        timestamp=datetime(2023, 11, 15, 8, 30, tzinfo=timezone.utc),
    )

    elec_params = {
        "p_out_kw":     75.0,
        "voltage_v":    400.0,
        "current_a":    132.0,
        "power_factor": 0.87,
        "efficiency":   0.955,
    }

    return store, {
        "elec_params":    elec_params,
        "ip_rating":      "IP23",
        "cooling_method": "TEFC",
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  CLI SMOKE TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    SEP = "=" * 72

    store, demo_kwargs = build_demo_store()
    pipeline = ForensicAgentPipeline(store)

    result = pipeline.run(
        product_id="MTR-ABB-M3AA-75KW",
        elec_params=demo_kwargs["elec_params"],
        ip_rating=demo_kwargs["ip_rating"],
        cooling_method=demo_kwargs["cooling_method"],
    )

    print(f"\n{SEP}")
    print("  FORENSIC DATA AGENT — Pipeline Run Report")
    print(SEP)
    print(f"\n  Product ID : {result.product_id}")
    print(f"  Snapshot   : {result.snapshot.captured_at.isoformat()}")
    print(f"  Properties : {len(result.snapshot.properties)}")
    print(f"  Total Claims: {sum(p.claim_count() for p in result.snapshot.properties.values())}")
    print(f"  Contested  : {result.snapshot.conflicted_properties()}")

    print(f"\n  ── Pass 3: Forensic Anomalies ({len(result.anomalies)}) ──")
    if result.anomalies:
        for ano in result.anomalies:
            print(f"\n  [{ano.severity.value}] {ano.invariant_code} | Δ={ano.mathematical_delta_pct}%")
            print(f"  Description : {ano.description}")
            print(f"  Remediation : {ano.remediation_hint}")
    else:
        print("  ✓ All invariants passed.")

    print(f"\n  ── Pass 4: Resolution Map ──")
    for prop, res in result.resolution_map.items():
        contested = "⚔ CONTESTED" if res.was_contested else "✓ uncontested"
        print(f"\n  {prop:30s} → {res.winning_value} {res.winning_unit}  "
              f"[score={res.resolution_confidence:.4f}] [{contested}]")
        for log_line in res.rejection_log:
            print(f"    ✗ {log_line}")

    print(f"\n  ── Pass 2: Unit Normalization Traces ──")
    for key, trace in result.unit_traces.items():
        print(f"  {trace.raw_string:12s} → {trace.final_display_value:16s}"
              f"  (unrounded={trace.unrounded_float_calculation}, sig_figs={trace.significant_digits_detected})")

    print(f"\n{SEP}\n")
