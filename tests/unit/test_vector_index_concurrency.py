from contextos.storage.vector_index import VectorIndex


def test_two_index_instances_do_not_lose_each_others_documents(tmp_path):
    a = VectorIndex(tmp_path)
    b = VectorIndex(tmp_path)
    a.add_document("d1", "alpha content")
    b.add_document("d2", "beta content")
    fresh = VectorIndex(tmp_path)
    assert set(fresh.documents) == {"d1", "d2"}
    assert a.search("beta")  # a stale reader sees the other writer's data


def test_save_is_atomic_and_leaves_no_temp_file(tmp_path):
    v = VectorIndex(tmp_path)
    v.add_document("d1", "alpha")
    assert [p.name for p in tmp_path.iterdir() if p.suffix == ".tmp"] == []
