import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

class OllamaCoprocessor:
    """
    Ollama Context Coprocessor client & router.
    Performs vector embeddings, local extraction, reranking, and verification.
    Degrades gracefully to deterministic fallbacks if Ollama is unreachable or model fails.
    """
    def __init__(self, host: str = "http://localhost:11434", embedding_model: str = "nomic-embed-text:latest", fast_model: str = "qwen2.5:1.5b"):
        self.host = host.rstrip("/")
        self.embedding_model = embedding_model
        self.fast_model = fast_model

    def is_healthy(self) -> bool:
        try:
            req = urllib.request.Request(f"{self.host}/api/tags", headers={"User-Agent": "ContextOS/1.0"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                return resp.status == 200
        except Exception:
            return False

    def get_embedding(self, text: str) -> Optional[List[float]]:
        url = f"{self.host}/api/embeddings"
        payload = json.dumps({"model": self.embedding_model, "prompt": text}).encode("utf-8")
        try:
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("embedding")
        except Exception:
            # Fallback to None if embedding model call fails
            return None

    def rerank_candidates(self, prompt: str, candidates: List[Dict[str, Any]], model: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Reranks candidates using fast local LLM or returns original candidate order if offline.
        """
        if not candidates or not self.is_healthy():
            return candidates

        target_model = model or self.fast_model
        prompt_summary = f"Query: {prompt}\nCandidates:\n"
        for i, c in enumerate(candidates[:10]):
            prompt_summary += f"{i+1}. {c.get('subject')} {c.get('predicate')} {c.get('object')}\n"

        url = f"{self.host}/api/generate"
        req_payload = json.dumps({
            "model": target_model,
            "prompt": f"Order the candidates 1..N by relevance to the query. Return JSON format: {{\x22relevant_indices\x22: [1, 2, ...]}}.\n{prompt_summary}",
            "stream": False,
            "format": "json"
        }).encode("utf-8")

        try:
            req = urllib.request.Request(url, data=req_payload, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                resp_text = data.get("response", "{}")
                parsed = json.loads(resp_text)
                indices = parsed.get("relevant_indices", [])
                
                reranked = []
                seen = set()
                for idx in indices:
                    if isinstance(idx, int) and 1 <= idx <= len(candidates) and idx not in seen:
                        reranked.append(candidates[idx - 1])
                        seen.add(idx)
                
                for i, c in enumerate(candidates):
                    if (i + 1) not in seen:
                        reranked.append(c)

                return reranked if reranked else candidates
        except Exception:
            # Fail open gracefully
            return candidates

    def extract_semantic_ir(self, raw_transcript: str, model: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Converts raw text/history into structured, schema-constrained Context IR assertions using live Ollama inference.
        """
        if not raw_transcript.strip() or not self.is_healthy():
            return []

        target_model = model or self.fast_model
        prompt = f"""Extract canonical assertions, decisions, and constraints from the transcript.
Return JSON format:
{{
  "assertions": [
    {{"subject": "AuthService", "predicate": "uses", "object": "OAuth2", "kind": "decision", "confidence": 0.95}}
  ]
}}

Transcript:
{raw_transcript[:2000]}"""

        url = f"{self.host}/api/generate"
        payload = json.dumps({
            "model": target_model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }).encode("utf-8")

        try:
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                resp_text = data.get("response", "{}")
                parsed = json.loads(resp_text)
                return parsed.get("assertions", [])
        except Exception:
            return []
