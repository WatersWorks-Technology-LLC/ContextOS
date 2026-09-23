from typing import List, Dict, Any, Optional
from ..storage.semantic_store import SemanticStore
from ..storage.vector_index import VectorIndex
from ..storage.knowledge_graph import KnowledgeGraph
from .ollama_coprocessor import OllamaCoprocessor

class RetrievalCascade:
    """
    Multi-faceted retrieval cascade combining exact matches, BM25, vector search, graph neighborhood slicing,
    and optional local Ollama reranking.
    """
    def __init__(
        self,
        semantic_store: SemanticStore,
        vector_index: VectorIndex,
        knowledge_graph: KnowledgeGraph,
        coprocessor: Optional[OllamaCoprocessor] = None,
        shared_semantic_store: Optional[SemanticStore] = None
    ):
        self.semantic = semantic_store
        self.vector = vector_index
        self.graph = knowledge_graph
        self.coprocessor = coprocessor or OllamaCoprocessor()
        self.shared_semantic = shared_semantic_store

    def retrieve(self, prompt: str, target_files: List[str] = None, top_k: int = 20,
                 runtime_id: Optional[str] = "codex", workspace_id: Optional[str] = None,
                 project_id: Optional[str] = None) -> Dict[str, Any]:
        candidates = []

        # 1. Semantic store assertions (client local + shared truth)
        current_assertions = self.semantic.query_current_state(runtime_id=runtime_id, workspace_id=workspace_id, project_id=project_id)
        if self.shared_semantic:
            shared_assertions = self.shared_semantic.query_current_state(runtime_id=None,
                workspace_id=workspace_id, project_id=project_id)
            # Deduplicate by assertion_id
            seen_ids = {a["assertion_id"] for a in current_assertions}
            for sa in shared_assertions:
                if sa["assertion_id"] not in seen_ids:
                    current_assertions.append(sa)

        # 2. Vector / BM25 search
        vector_results = self.vector.search(prompt, top_k=top_k)
        vector_ids = {r[0] for r in vector_results}

        # 3. Graph slicing
        graph_slice = {"nodes": [], "edges": []}
        if target_files:
            graph_slice = self.graph.get_slice(target_files, max_depth=2)

        prompt_lower = prompt.lower()
        prompt_words = set(prompt_lower.split())
        for a in current_assertions:
            subj_lower = a["subject"].lower()
            obj_lower = a["object"].lower()
            subj_words = set(subj_lower.split())
            obj_words = set(obj_lower.split())
            if (prompt_words & (subj_words | obj_words)) or (subj_lower in prompt_lower or obj_lower in prompt_lower) or a["assertion_id"] in vector_ids or not prompt.strip():
                candidates.append(a)

        if not candidates and current_assertions:
            candidates = current_assertions[:top_k]

        if candidates and self.coprocessor.is_healthy():
            candidates = self.coprocessor.rerank_candidates(prompt, candidates)

        return {
            "assertions": candidates[:top_k],
            "vector_hits": vector_results,
            "graph_slice": graph_slice
        }
