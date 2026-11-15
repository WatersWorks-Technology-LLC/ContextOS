from contextos.storage.semantic_store import SemanticStore


def test_promote_assertion_creates_promoted_record_with_origin(tmp_path):
    store = SemanticStore(tmp_path)
    store.add_assertion("A1", "svc", "uses", "sqlite", scope="session",
                        workspace_id="ws", project_id="p", origin_session="s1")
    promoted_id = store.promote_assertion("A1", "project", "verified_fact")
    assert promoted_id and promoted_id.startswith("AST-PROM-")
    rows = {r["assertion_id"]: r for r in store.query_current_state(runtime_id=None)}
    assert rows[promoted_id]["scope"] == "project"
    assert rows[promoted_id]["origin_assertion_id"] == "A1"
    assert rows[promoted_id]["origin_session"] == "s1"


def test_promote_assertion_rejects_unknown_scope_or_id(tmp_path):
    store = SemanticStore(tmp_path)
    assert store.promote_assertion("missing", "project") is None
    store.add_assertion("A1", "a", "b", "c")
    assert store.promote_assertion("A1", "bogus") is None
