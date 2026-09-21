import time
from typing import Dict, Any, List

class ExpansionMonitor:
    """
    Expansion Monitor & Compiler Feedback Loop.
    Tracks if Codex repeatedly calls `expand X` on the same entity.
    Provides allocation feedback to increase initial Z-level allocation for under-allocated items.
    """
    def __init__(self):
        self.expansion_counts: Dict[str, int] = {}

    def record_expansion(self, entity_id: str):
        self.expansion_counts[entity_id] = self.expansion_counts.get(entity_id, 0) + 1

    def get_under_allocated_entities(self, threshold: int = 2) -> List[str]:
        return [ent for ent, count in self.expansion_counts.items() if count >= threshold]

class ContinuousMonitors:
    """
    Quiet Background Health & Integrity Monitors.
    - Semantic Drift Monitor
    - Entity Drift Monitor
    - Provenance Monitor
    - Expansion Monitor (Compiler Feedback)
    - Context Cost Monitor (P50/P95 Token Cost Moving Average)
    """
    def __init__(self):
        self.expansion_monitor = ExpansionMonitor()
        self.turn_costs: List[int] = []

    def record_turn_cost(self, token_count: int):
        self.turn_costs.append(token_count)
        if len(self.turn_costs) > 1000:
            self.turn_costs.pop(0)

    def get_cost_moving_average(self) -> Dict[str, float]:
        if not self.turn_costs:
            return {"p50_tokens": 0.0, "p95_tokens": 0.0, "avg_tokens": 0.0}

        sorted_c = sorted(self.turn_costs)
        p50_idx = int(len(sorted_c) * 0.50)
        p95_idx = int(len(sorted_c) * 0.95)

        return {
            "p50_tokens": float(sorted_c[p50_idx]),
            "p95_tokens": float(sorted_c[min(p95_idx, len(sorted_c)-1)]),
            "avg_tokens": round(sum(self.turn_costs) / len(self.turn_costs), 2)
        }
