from contextos.identity import IdentityScope
from contextos.storage.semantic_store import SemanticStore


def _store(tmp_path):
    ident = IdentityScope("codex", "ws", "proj", "s1", "main")
    st = SemanticStore(tmp_path)
    kw = dict(runtime_id="codex", workspace_id="ws", project_id="proj",
              origin_session="s1", origin_agent="main")
    st.add_assertion("A1", "db", "uses", "postgres", **kw)
    st.add_assertion("A2", "cache", "ttl", "100% of keys_set", **kw)
    return st, ident


def test_percent_and_underscore_match_literally(tmp_path):
    st, ident = _store(tmp_path)
    # "%" used to match every row; "_" used to match any single character.
    assert [r["assertion_id"] for r in st.search_assertions("%", identity=ident)] == ["A2"]
    assert [r["assertion_id"] for r in st.search_assertions("keys_set", identity=ident)] == ["A2"]
    assert st.search_assertions("keys-set", identity=ident) == []
    assert [r["assertion_id"] for r in st.search_assertions("postgres", identity=ident)] == ["A1"]
