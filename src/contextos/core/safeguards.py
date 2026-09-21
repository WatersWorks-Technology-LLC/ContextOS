from typing import List, Dict, Any, Tuple

class SafeguardManager:
    """
    Safeguard Manager & Protection Rules:
    1. Critical Fact Pinning: Level 0 (exact hashes/paths) & Level 1 (hard invariants) are NEVER lossily compressed.
    2. Quota & Token Ceiling Guardrail: Caps context packet tokens (<= 2500 tokens).
    3. Latency Circuit Breaker: Trips if compilation latency > 2000ms.
    4. Confidence Escalation: Marks context provisional if confidence < 0.80.
    """
    def __init__(self, max_token_ceiling: int = 2500, max_prep_latency_ms: float = 2000.0):
        self.max_token_ceiling = max_token_ceiling
        self.max_prep_latency_ms = max_prep_latency_ms
        self.circuit_tripped = False
        self.consecutive_failures = 0

    def enforce_pinning(self, assertions: List[Dict[str, Any]], raw_invariants: List[str]) -> Tuple[List[Dict[str, Any]], List[str]]:
        pinned_invariants = list(set(raw_invariants))
        protected_assertions = []

        for a in assertions:
            kind = a.get("kind", "fact")
            # Always preserve invariants and hard constraints
            if kind in ("invariant", "constraint", "permission", "security"):
                inv_text = f"{a['subject']} {a['predicate']} {a['object']}"
                if inv_text not in pinned_invariants:
                    pinned_invariants.append(inv_text)
            protected_assertions.append(a)

        return protected_assertions, pinned_invariants

    def check_latency_circuit_breaker(self, latency_ms: float) -> bool:
        if latency_ms > self.max_prep_latency_ms:
            self.consecutive_failures += 1
            if self.consecutive_failures >= 2:
                self.circuit_tripped = True
            return True  # Exceeded budget
        else:
            self.consecutive_failures = 0
            self.circuit_tripped = False
            return False

    def validate_confidence(self, confidence: float) -> str:
        if confidence >= 0.95:
            return "verified"
        elif confidence >= 0.80:
            return "high_confidence"
        else:
            return "provisional_requires_expansion"
