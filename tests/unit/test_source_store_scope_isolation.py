from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore


def test_same_content_other_scope_does_not_overwrite_owner(tmp_path):
    ss = SourceStore(tmp_path)
    a = IdentityScope("codex", "/ws", "proj_a", "s1", "main")
    b = IdentityScope("codex", "/ws", "proj_b", "s1", "main")
    sid_a = ss.put_source("same tool output", identity=a)
    sid_b = ss.put_source("same tool output", identity=b)
    assert sid_a != sid_b
    assert sid_a in ss.get_sources([sid_a], identity=a, allow_legacy=False)
    assert sid_b not in ss.get_sources([sid_b], identity=a, allow_legacy=False)
    assert sid_b in ss.get_sources([sid_b], identity=b, allow_legacy=False)
