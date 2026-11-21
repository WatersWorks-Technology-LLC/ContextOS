from contextos.storage.semantic_store import SemanticStore


def test_promote_assertion_creates_promoted_record(tmp_path):
    store = SemanticStore(tmp_path)
    store.add_assertion("A1", "svc", "uses", "sqlite", scope="session")
    promoted = store.promote_assertion("A1", "project")
    assert promoted and promoted.startswith("AST-PROM-")
    rows = store.query_current_state(runtime_id=None)
    row = next(r for r in rows if r["assertion_id"] == promoted)
    assert row["scope"] == "project"
    assert row["origin_assertion_id"] == "A1"


def test_promote_assertion_rejects_unknown_scope_or_id(tmp_path):
    store = SemanticStore(tmp_path)
    store.add_assertion("A1", "s", "p", "o")
    assert store.promote_assertion("A1", "bogus") is None
    assert store.promote_assertion("missing", "project") is None
