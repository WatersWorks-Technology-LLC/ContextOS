import pytest
from contextos.storage.semantic_store import SemanticStore


def test_add_assertion_does_not_overwrite_other_workspace(tmp_path):
    sem = SemanticStore(tmp_path)
    sem.add_assertion("A-1", "s", "p", "workspace A secret", workspace_id="wsA", project_id="p1")
    with pytest.raises(ValueError):
        sem.add_assertion("A-1", "s", "p", "workspace B", workspace_id="wsB", project_id="p1")
    rows = sem.query_current_state(runtime_id="codex", workspace_id="wsA", project_id="p1")
    assert [r["object"] for r in rows] == ["workspace A secret"]


def test_add_assertion_same_scope_still_replaces(tmp_path):
    sem = SemanticStore(tmp_path)
    sem.add_assertion("A-1", "s", "p", "old", workspace_id="w", project_id="p")
    sem.add_assertion("A-1", "s", "p", "new", workspace_id="w", project_id="p")
    assert sem.query_current_state(workspace_id="w", project_id="p")[0]["object"] == "new"
