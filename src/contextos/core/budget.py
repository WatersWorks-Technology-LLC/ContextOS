import re
from typing import List, Dict, Any, Tuple

class BudgetAllocator:
    """
    Adaptive Budgeting & Token Optimization Engine.
    - Adaptive Budget Tiers based on prompt task category:
      - Simple continuation: 100 - 300 tokens
      - Normal engineering: 300 - 800 tokens
      - Complex architecture: 800 - 1500 tokens
      - Historical analysis: 1500 - 2500 tokens
    - Context Macros & Semantic Dictionaries for token compression.
    """
    SEMANTIC_DICTIONARY = {
        "Authentication": "AUTH",
        "TokenService": "TOKSVC",
        "Database": "DB",
        "PostgreSQL": "PG",
        "Microservices": "MSVC",
        "Configuration": "CFG"
    }

    @classmethod
    def get_adaptive_budget(cls, category: str, default_max: int = 1500) -> int:
        if category == "simple_continuation":
            return 300
        elif category in ("feature_work", "refactoring"):
            return 800
        elif category in ("architecture_query", "debugging"):
            return 1500
        elif category == "historical_analysis":
            return min(2500, default_max)
        return 800

    @classmethod
    def apply_semantic_dictionary(cls, text: str) -> str:
        for full_word, token_sym in cls.SEMANTIC_DICTIONARY.items():
            text = text.replace(full_word, token_sym)
        return text

    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        return max(1, len(text) // 4)

    @classmethod
    def allocate(
        cls,
        assertions: List[Dict[str, Any]],
        invariants: List[str],
        category: str = "general",
        max_budget_tokens: int = 1500
    ) -> Tuple[List[Dict[str, Any]], List[str], int]:
        
        target_budget = cls.get_adaptive_budget(category, default_max=max_budget_tokens)
        allocated_invariants = []
        allocated_assertions = []
        used_tokens = 0

        # 1. High priority: Pinned invariants
        for inv in invariants:
            compressed_inv = cls.apply_semantic_dictionary(inv)
            cost = cls.estimate_tokens(compressed_inv) + 4
            if used_tokens + cost <= target_budget:
                allocated_invariants.append(compressed_inv)
                used_tokens += cost
            else:
                break

        # 2. Medium priority: High confidence current state assertions
        sorted_assertions = sorted(
            assertions,
            key=lambda x: (x.get("kind") in ("decision", "constraint"), x.get("confidence", 1.0)),
            reverse=True
        )

        for a in sorted_assertions:
            subj = cls.apply_semantic_dictionary(a.get('subject', ''))
            obj = cls.apply_semantic_dictionary(a.get('object', ''))
            cost = cls.estimate_tokens(f"{subj} {a.get('predicate')} {obj}") + 6
            if used_tokens + cost <= target_budget:
                allocated_assertions.append({**a, "subject": subj, "object": obj})
                used_tokens += cost

        return allocated_assertions, allocated_invariants, used_tokens
