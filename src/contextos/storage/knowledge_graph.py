from typing import Dict, List, Set, Any

class KnowledgeGraph:
    """
    In-memory graph topology & neighborhood dependency slicing engine.
    Encodes relations, code import paths, and architectural dependencies.
    """
    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.adjacency: Dict[str, List[Dict[str, str]]] = {}

    def add_node(self, node_id: str, label: str, node_type: str = "entity", attributes: Dict[str, Any] = None):
        self.nodes[node_id] = {
            "id": node_id,
            "label": label,
            "type": node_type,
            "attributes": attributes or {}
        }
        if node_id not in self.adjacency:
            self.adjacency[node_id] = []

    def add_edge(self, source: str, target: str, relation: str = "depends_on"):
        if source not in self.nodes:
            self.add_node(source, source)
        if target not in self.nodes:
            self.add_node(target, target)
        
        self.adjacency[source].append({"target": target, "relation": relation})

    def get_slice(self, root_ids: List[str], max_depth: int = 2) -> Dict[str, Any]:
        visited_nodes: Set[str] = set()
        visited_edges: List[Dict[str, str]] = []
        queue = [(node_id, 0) for node_id in root_ids if node_id in self.nodes]

        while queue:
            curr_id, depth = queue.pop(0)
            if curr_id in visited_nodes or depth > max_depth:
                continue

            visited_nodes.add(curr_id)

            for neighbor in self.adjacency.get(curr_id, []):
                target = neighbor["target"]
                visited_edges.append({
                    "source": curr_id,
                    "target": target,
                    "relation": neighbor["relation"]
                })
                if target not in visited_nodes and depth + 1 <= max_depth:
                    queue.append((target, depth + 1))

        return {
            "nodes": [self.nodes[nid] for nid in visited_nodes if nid in self.nodes],
            "edges": visited_edges
        }
