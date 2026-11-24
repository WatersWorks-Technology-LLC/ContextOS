import tempfile
from pathlib import Path

import pytest

from contextos.identity import IdentityScope
from contextos.storage.semantic_store import SemanticStore
from contextos.storage.source_store import SourceStore


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


def test_promote_assertion_creates_promoted_record(tmp_dir):
    store = SemanticStore(tmp_dir)
    store.add_assertion("A1", "svc", "uses", "sqlite", scope="session")
    promoted = store.promote_assertion("A1", "project")
    assert promoted and promoted.startswith("AST-PROM-")
    rows = store.query_current_state(runtime_id=None)
    row = next(r for r in rows if r["assertion_id"] == promoted)
    assert row["scope"] == "project" and row["origin_assertion_id"] == "A1"


def test_source_store_two_writers_do_not_lose_updates(tmp_dir):
    ident = IdentityScope("codex", "ws", "proj", "s1", "main")
    a = SourceStore(tmp_dir)
    b = SourceStore(tmp_dir)  # simulates a second process with a stale cache
    sa = a.put_source("from A", identity=ident)
    sb = b.put_source("from B", identity=ident)
    fresh = SourceStore(tmp_dir)
    assert fresh.get_source(sa) is not None
    assert fresh.get_source(sb) is not None
    # a reader with a stale cache still sees the other writer's data
    assert a.get_source(sb) is not None
