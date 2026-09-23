from typing import Dict, Any, Optional
from ..identity import IdentityScope
from ..storage.semantic_store import SemanticStore
from ..storage.source_store import SourceStore

class ContextCapsuleManager:
    """
    Z0–Z4 Resolution Paging Architecture & Demand Paging Manager.
    - Level 0 (Z0): Identity Handle (e.g. AUTH)
    - Level 1 (Z1): Current Active State
    - Level 2 (Z2): Key Relationships & Graph Neighborhood
    - Level 3 (Z3): Detailed Semantic Capsule (Attributes, Rationale, Closed Branches)
    - Level 4 (Z4): Raw Primary Evidence Bundle
    """
    def __init__(self, semantic_store: SemanticStore, source_store: SourceStore):
        self.semantic = semantic_store
        self.sources = source_store

    def expand(self, target_id: str, level: int = 3, identity: Optional[IdentityScope] = None) -> Dict[str, Any]:
        """
        Demand Paging Tool execution (MCP `expand`).
        Escalates semantic resolution level from Z0 up to Z4.
        """
        # Find assertions matching target_id
        matches = self.semantic.search_assertions(target_id, identity=identity)
        if not matches:
            return {"id": target_id, "level": level, "status": "not_found", "payload": None}

        primary = matches[0]

        if level == 0:
            # Identity handle
            return {
                "id": target_id,
                "level": 0,
                "resolution": "identity",
                "payload": f"ID:{primary['subject']}"
            }

        elif level == 1:
            # Current State
            return {
                "id": target_id,
                "level": 1,
                "resolution": "current_state",
                "payload": {
                    "subject": primary["subject"],
                    "predicate": primary["predicate"],
                    "object": primary["object"],
                    "status": primary["status"]
                }
            }

        elif level == 2:
            # Key Relationships
            relations = [
                f"{m['subject']} {m['predicate']} {m['object']}"
                for m in matches
            ]
            return {
                "id": target_id,
                "level": 2,
                "resolution": "relationships",
                "payload": relations
            }

        elif level == 3:
            # Detailed Semantic Capsule
            conflicts_closed = self.semantic.query_conflicts_and_closed_branches(identity=identity)
            return {
                "id": target_id,
                "level": 3,
                "resolution": "detailed_capsule",
                "payload": {
                    "assertions": matches,
                    "rationale": primary.get("decision_rationale"),
                    "closed_branch": primary.get("closed_branch_condition"),
                    "temporal": {
                        "observed_at": primary.get("observed_at"),
                        "valid_from": primary.get("valid_from"),
                        "valid_until": primary.get("valid_until"),
                        "superseded_at": primary.get("superseded_at")
                    },
                    "known_conflicts": conflicts_closed["conflicts"]
                }
            }

        elif level == 4:
            # Raw Evidence Bundle
            source_refs = [m["source_ref"] for m in matches if m.get("source_ref")]
            raw_evidence = self.sources.get_sources(source_refs, max_chars=12000, identity=identity, allow_legacy=identity is None) if source_refs else {}
            return {
                "id": target_id,
                "level": 4,
                "resolution": "raw_evidence_bundle",
                "payload": {
                    "assertions": matches,
                    "sources": raw_evidence
                }
            }

        return {"id": target_id, "level": level, "status": "invalid_level", "payload": None}
