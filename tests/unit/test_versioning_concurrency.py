from contextos.identity import IdentityScope
from contextos.storage.versioning import ContextVersionStore

IDENT = IdentityScope(runtime_id="codex", workspace_id="w", project_id="p", session_id="s", agent_id="a")


def _commit(store, text):
    return store.create_commit(text, [], [], "hybrid", identity=IDENT)["commit_id"]


def test_rollback_does_not_drop_commits_written_by_other_instance(tmp_path):
    a = ContextVersionStore(tmp_path)
    b = ContextVersionStore(tmp_path)
    first = _commit(a, "one")
    second = _commit(b, "two")  # a's in-memory view does not know about this
    a.rollback(first)
    fresh = ContextVersionStore(tmp_path)
    assert second in fresh.versions
    assert fresh.versions[first]["status"] == "failed"


def test_repair_dag_does_not_drop_commits_written_by_other_instance(tmp_path):
    a = ContextVersionStore(tmp_path)
    b = ContextVersionStore(tmp_path)
    first = _commit(a, "one")
    a.versions[first]["parent_commit"] = first  # self-parent, only repairable
    a._save()
    second = _commit(b, "two")
    a.repair_dag()
    fresh = ContextVersionStore(tmp_path)
    assert second in fresh.versions
    assert fresh.versions[first]["parent_commit"] is None
