import pytest
from contextos.codecs.heterogeneous_compiler import HeterogeneousPacketCompiler
from contextos.core.budget import BudgetAllocator

def test_unit_heterogeneous_compiler():
    assertions = [
        {"subject": "AuthService", "predicate": "uses", "object": "OAuth2", "kind": "decision"},
        {"subject": "PostgresDB", "predicate": "max_connections", "object": "100", "kind": "fact", "confidence": 1.0},
        {"subject": "DB_HASH", "predicate": "equals", "object": "sha256_88a", "kind": "exact"}
    ]
    invariants = ["Do not log plaintext passwords"]
    edges = [{"source": "AuthService", "target": "PostgresDB", "relation": "connects"}]

    text, checksum = HeterogeneousPacketCompiler.compile_packet(assertions, invariants, graph_edges=edges)
    assert "@INV" in text
    assert "@DEC" in text
    assert "@STATE (COLUMNAR)" in text
    assert "@DEP (GRAPH)" in text
    assert "@EXACT" in text
    assert len(checksum) == 8

def test_unit_adaptive_budgeting():
    # Simple continuation budget should be ~300 tokens
    budget = BudgetAllocator.get_adaptive_budget("simple_continuation")
    assert budget == 300

    # Complex architecture budget should be ~1500 tokens
    budget_arch = BudgetAllocator.get_adaptive_budget("architecture_query")
    assert budget_arch == 1500

    # Semantic dictionary replacement
    compressed = BudgetAllocator.apply_semantic_dictionary("Authentication using TokenService and Database")
    assert "AUTH" in compressed
    assert "TOKSVC" in compressed
    assert "DB" in compressed
