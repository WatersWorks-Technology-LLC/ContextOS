from typing import List, Dict, Any

class CurrentStateProjector:
    """
    Surfaces current active state, filters dead context, and extracts active conflicts & invariants.
    """
    @classmethod
    def project(cls, candidate_assertions: List[Dict[str, Any]]) -> Dict[str, Any]:
        current_active = []
        conflicts = []
        invariants = []

        for a in candidate_assertions:
            status = a.get("status", "current")
            kind = a.get("kind", "fact")

            if kind in ("invariant", "constraint"):
                invariants.append(f"{a['subject']} {a['predicate']} {a['object']}")

            if status == "current":
                current_active.append(a)
            elif status in ("proposed", "rejected"):
                conflicts.append(a)

        return {
            "active_assertions": current_active,
            "conflicts": conflicts,
            "invariants": list(set(invariants))
        }
