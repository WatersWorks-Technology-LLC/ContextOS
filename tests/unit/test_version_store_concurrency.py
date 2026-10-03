from contextos.identity import IdentityScope
from contextos.storage.versioning import ContextVersionStore

ID = IdentityScope("codex", "workspace", "project", "s1", "main")


def test_version_store_second_writer_does_not_drop_first(tmp_path):
    a, b = ContextVersionStore(tmp_path), ContextVersionStore(tmp_path)
    ca = a.create_commit("ctx a", [], [], "s", identity=ID)["commit_id"]
    cb = b.create_commit("ctx b", [], [], "s", identity=ID)["commit_id"]
    assert set(ContextVersionStore(tmp_path).versions) == {ca, cb}


def test_version_store_corrupt_file_preserved(tmp_path):
    (tmp_path / "versions.json").write_text("{not json")
    ContextVersionStore(tmp_path).create_commit("ctx", [], [], "s", identity=ID)
    assert list(tmp_path.glob("versions.json.corrupt-*"))
