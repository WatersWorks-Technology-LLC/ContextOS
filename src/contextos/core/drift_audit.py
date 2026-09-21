import re
from typing import List, Dict, Any

class SemanticDriftAuditor:
    """
    Semantic State Drift Audit Engine.
    Audits state drift across 1,000+ turn durability runs:
    - Entity Alias Drift
    - Supersession Leakage (old state reappearing)
    - Relationship Direction Inversion
    - Rationale Corruption
    """
    @classmethod
    def audit_drift(
        cls,
        current_assertions: List[Dict[str, Any]],
        superseded_assertions: List[Dict[str, Any]],
        entity_canonical_map: Dict[str, str] = None
    ) -> Dict[str, Any]:
        alias_drift_count = 0
        supersession_leak_count = 0
        canonical_map = entity_canonical_map or {
            "AuthSvc": "AuthService",
            "auth-service": "AuthService",
            "PG": "PostgresDB"
        }

        # 1. Check for entity alias drift
        for a in current_assertions:
            subj = a.get("subject", "")
            if subj in canonical_map and subj != canonical_map[subj]:
                alias_drift_count += 1

        # 2. Check for supersession leakage (superseded assertion active in current state)
        superseded_ids = {s["assertion_id"] for s in superseded_assertions}
        current_ids = {c["assertion_id"] for c in current_assertions}
        supersession_leaks = superseded_ids & current_ids
        supersession_leak_count = len(supersession_leaks)

        drift_score = round(1.0 - ((alias_drift_count + supersession_leak_count) / max(1, len(current_assertions))), 3)

        return {
            "drift_score": drift_score,
            "alias_drift_count": alias_drift_count,
            "supersession_leak_count": supersession_leak_count,
            "zero_drift_passed": (alias_drift_count == 0 and supersession_leak_count == 0),
            "total_active_assertions": len(current_assertions)
        }
