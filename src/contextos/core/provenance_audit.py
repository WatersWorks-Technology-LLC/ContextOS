from typing import List, Dict, Any
from ..storage.source_store import SourceStore

class ProvenanceAuditor:
    """
    Source Coverage & Provenance Audit Engine.
    Strict Production Rules:
    - Critical assertions (L0/L1 invariants & decisions): 100% reachable provenance required.
    - Ordinary assertions (facts/state): >= 95% reachable provenance required.
    """
    def __init__(self, source_store: SourceStore):
        self.sources = source_store

    def audit_packet_provenance(self, assertions: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not assertions:
            return {
                "source_coverage_ratio": 1.0,
                "critical_provenance_ratio": 1.0,
                "ordinary_provenance_ratio": 1.0,
                "critical_passed": True,
                "ordinary_passed": True,
                "audit_details": []
            }

        critical_total = 0
        critical_valid = 0
        ordinary_total = 0
        ordinary_valid = 0
        audit_details = []

        for a in assertions:
            kind = a.get("kind", "fact")
            is_critical = kind in ("invariant", "constraint", "decision", "security")
            src_ref = a.get("source_ref")
            has_source = False
            source_payload = None

            if src_ref:
                source_payload = self.sources.get_source(src_ref)
                if source_payload:
                    has_source = True

            if is_critical:
                critical_total += 1
                if has_source:
                    critical_valid += 1
            else:
                ordinary_total += 1
                if has_source:
                    ordinary_valid += 1

            audit_details.append({
                "assertion_id": a.get("assertion_id"),
                "subject": a.get("subject"),
                "is_critical": is_critical,
                "source_ref": src_ref,
                "reachable": has_source,
                "sha256": source_payload.get("sha256") if source_payload else None
            })

        critical_ratio = round(critical_valid / max(1, critical_total), 3) if critical_total > 0 else 1.0
        ordinary_ratio = round(ordinary_valid / max(1, ordinary_total), 3) if ordinary_total > 0 else 1.0
        overall_ratio = round((critical_valid + ordinary_valid) / len(assertions), 3)

        return {
            "source_coverage_ratio": overall_ratio,
            "critical_provenance_ratio": critical_ratio,
            "ordinary_provenance_ratio": ordinary_ratio,
            "critical_passed": critical_ratio == 1.0,
            "ordinary_passed": ordinary_ratio >= 0.95,
            "audit_details": audit_details
        }
