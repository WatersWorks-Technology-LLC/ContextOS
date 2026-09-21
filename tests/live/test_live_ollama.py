import pytest
from contextos.core.ollama_coprocessor import OllamaCoprocessor

def test_live_ollama_embeddings_and_extraction():
    coprocessor = OllamaCoprocessor()
    assert coprocessor.is_healthy() is True, "Live Ollama daemon must be running on http://localhost:11434"

    # Test Live Embedding
    emb = coprocessor.get_embedding("ContextOS semantic memory test query")
    assert emb is not None
    assert len(emb) == 768  # nomic-embed-text 768d vector

    # Test Live Schema-Constrained Extraction
    transcript = "We decided to migrate AuthService from session cookies to OAuth2 JWT tokens because we need stateless microservices."
    extracted = coprocessor.extract_semantic_ir(transcript)
    assert isinstance(extracted, list)
