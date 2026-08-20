# mock_data.py
"""
Adversarial test cases designed to showcase the Forensic Agent's features.
These profiles deliberately inject typos and source contradictions.
"""

HACKATHON_DEMO_CASES = {
    "CASE-001_MOTOR": {
        "asset_name": "ABB High-Performance Induction Motor",
        "description": "Showcases Pass 3 Physics Invariant checking and conflict resolution.",
        "ingested_claims": [
            {
                "claim_id": "CLAIM-101",
                "field_path": "mechanical.power",
                "raw_value": "75 kW",
                "normalized_value": 75.0,
                "normalized_unit": "kW",
                "source": {
                    "document_name": "abb_technical_datasheet_v4.pdf",
                    "page_number": 12,
                    "context_type": "Datasheet",
                    "extraction_confidence": 0.98
                }
            },
            {
                "claim_id": "CLAIM-102",
                "field_path": "mechanical.power",
                "raw_value": "90 kW",
                "normalized_value": 90.0,
                "normalized_unit": "kW",
                "source": {
                    "document_name": "marketing_brochure_web_scrape.html",
                    "page_number": 1,
                    "context_type": "Marketing Web Portal",
                    "extraction_confidence": 0.85
                }
            },
            {
                "claim_id": "CLAIM-103",
                "field_path": "electrical.voltage",
                "raw_value": "415 V",
                "normalized_value": 415.0,
                "normalized_unit": "V",
                "source": {
                    "document_name": "abb_technical_datasheet_v4.pdf",
                    "page_number": 12,
                    "context_type": "Datasheet",
                    "extraction_confidence": 0.99
                }
            },
            {
                "claim_id": "CLAIM-104",
                "field_path": "electrical.current",
                "raw_value": "130 A",
                "normalized_value": 130.0,
                "normalized_unit": "A",
                "source": {
                    "document_name": "abb_technical_datasheet_v4.pdf",
                    "page_number": 12,
                    "context_type": "Datasheet",
                    "extraction_confidence": 0.97
                }
            }
        ]
    },
    "CASE-002_PUMP": {
        "asset_name": "Goulds Heavy Duty Centrifugal Pump",
        "description": "Showcases Pass 2 NIST-compatible unit precision truncation trail.",
        "ingested_claims": [
            {
                "claim_id": "CLAIM-201",
                "field_path": "physical.weight",
                "raw_value": "250 lb",
                "source": {
                    "document_name": "goulds_installation_guide.pdf",
                    "page_number": 4,
                    "context_type": "Installation Manual",
                    "extraction_confidence": 0.95
                }
            },
            {
                "claim_id": "CLAIM-202",
                "field_path": "environmental.protection",
                "raw_value": "IP99-X",  # Deliberate syntax failure
                "source": {
                    "document_name": "legacy_erp_dump.json",
                    "page_number": 1,
                    "context_type": "Legacy Database",
                    "extraction_confidence": 0.90
                }
            }
        ]
    }
}
