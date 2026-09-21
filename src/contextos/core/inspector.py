from typing import List, Dict, Any

class HumanAuditableContextInspector:
    """
    Human-Auditable Context Inspector.
    Displays exactly what Codex received, selection rationale, Z-level, token cost, and provenance pointers.
    """
    @classmethod
    def inspect_packet(
        cls,
        context_text: str,
        assertions: List[Dict[str, Any]],
        invariants: List[str],
        commit_id: str,
        strategy_used: str,
        token_count: int,
        telemetry: Dict[str, Any]
    ) -> Dict[str, Any]:
        item_breakdown = []
        for inv in invariants:
            item_breakdown.append({
                "item_type": "invariant",
                "text": inv,
                "selection_rationale": "Pinned Level 1 safety rule",
                "resolution_level": "Z1",
                "estimated_tokens": max(1, len(inv) // 4)
            })

        for a in assertions:
            item_breakdown.append({
                "item_type": a.get("kind", "fact"),
                "assertion_id": a.get("assertion_id"),
                "text": f"{a.get('subject')} {a.get('predicate')} {a.get('object')}",
                "selection_rationale": f"High confidence ({a.get('confidence', 1.0)}) active state",
                "resolution_level": "Z1",
                "source_ref": a.get("source_ref"),
                "estimated_tokens": max(1, len(f"{a.get('subject')} {a.get('predicate')} {a.get('object')}") // 4)
            })

        return {
            "commit_id": commit_id,
            "strategy_used": strategy_used,
            "total_delivered_tokens": token_count,
            "item_count": len(item_breakdown),
            "item_breakdown": item_breakdown,
            "telemetry_breakdown": telemetry,
            "raw_context_text": context_text
        }
