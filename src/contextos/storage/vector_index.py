import json
import math
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple

class VectorIndex:
    """
    Local vector search and BM25/TF-IDF similarity engine.
    Degrades gracefully when external embedding servers (Ollama) are offline.
    """
    def __init__(self, data_dir: Path, filename: str = "vectors.json"):
        self.file_path = data_dir / filename
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.documents: Dict[str, Dict[str, Any]] = self._load()

    def _load(self) -> Dict[str, Dict[str, Any]]:
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.documents, f, indent=2)

    def _tokenize(self, text: str) -> List[str]:
        return [w.lower() for w in re.findall(r'\w+', text)]

    def add_document(self, doc_id: str, content: str, metadata: Dict[str, Any] = None):
        tokens = self._tokenize(content)
        tf = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        
        self.documents[doc_id] = {
            "doc_id": doc_id,
            "content": content,
            "tokens": tokens,
            "tf": tf,
            "metadata": metadata or {}
        }
        self._save()

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float, Dict[str, Any]]]:
        query_tokens = self._tokenize(query)
        if not query_tokens or not self.documents:
            return []

        N = len(self.documents)
        df = {}
        for token in set(query_tokens):
            df[token] = sum(1 for doc in self.documents.values() if token in doc["tf"])

        scores = []
        for doc_id, doc in self.documents.items():
            score = 0.0
            doc_len = len(doc["tokens"]) or 1
            for qt in query_tokens:
                if qt in doc["tf"]:
                    # BM25-like scoring
                    tf_val = doc["tf"][qt]
                    idf_val = math.log((N - df[qt] + 0.5) / (df[qt] + 0.5) + 1.0)
                    score += idf_val * (tf_val * 2.2) / (tf_val + 1.2 * (0.25 + 0.75 * (doc_len / 50.0)))
            if score > 0:
                scores.append((doc_id, round(score, 4), doc))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
