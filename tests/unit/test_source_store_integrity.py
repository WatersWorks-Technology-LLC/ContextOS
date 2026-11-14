import threading
from pathlib import Path

from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore


def _ident(project="p1", session="s1"):
    return IdentityScope("codex", "/ws", project, session, "main")


def test_same_content_other_scope_does_not_overwrite_owner(tmp_path):
    ss = SourceStore(tmp_path)
    a, b = _ident("proj_a"), _ident("proj_b")
    sid_a = ss.put_source("same tool output", identity=a)
    sid_b = ss.put_source("same tool output", identity=b)
    assert sid_a != sid_b
    assert sid_a in ss.get_sources([sid_a], identity=a, allow_legacy=False)
    assert sid_b not in ss.get_sources([sid_b], identity=a, allow_legacy=False)
    assert sid_b in ss.get_sources([sid_b], identity=b, allow_legacy=False)


def test_two_store_instances_do_not_lose_writes(tmp_path):
    s1, s2 = SourceStore(tmp_path), SourceStore(tmp_path)  # e.g. two processes
    id1 = s1.put_source("one", identity=_ident())
    id2 = s2.put_source("two", identity=_ident())
    fresh = SourceStore(tmp_path)
    assert fresh.get_source(id1) and fresh.get_source(id2)


def test_concurrent_threads_no_error_or_loss(tmp_path):
    ss = SourceStore(tmp_path)
    errors, ids = [], []
    def work(i):
        try:
            ids.append(ss.put_source(f"payload {i}", identity=_ident()))
        except Exception as e:  # pragma: no cover
            errors.append(e)
    ts = [threading.Thread(target=work, args=(i,)) for i in range(20)]
    [t.start() for t in ts]; [t.join() for t in ts]
    assert not errors
    fresh = SourceStore(tmp_path)
    assert all(fresh.get_source(i) for i in ids)
