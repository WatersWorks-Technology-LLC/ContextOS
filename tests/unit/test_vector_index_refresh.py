from contextos.storage.vector_index import VectorIndex


def test_search_sees_documents_written_by_another_instance(tmp_path):
    reader = VectorIndex(tmp_path)
    writer = VectorIndex(tmp_path)  # stands in for a second process
    writer.add_document("d1", "postgres migration plan")
    hits = reader.search("postgres")
    assert [h[0] for h in hits] == ["d1"]
