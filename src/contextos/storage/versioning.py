import json
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

class ContextVersionStore:
    """
    Context Versioning Engine.
    Snapshots keyframes of working context, assertion states, and commit hashes.
    Guarantees instant rollback if a strategy breaks or causes semantic loss.
    """
    def __init__(self, data_dir: Path, filename: str = "versions.json"):
        self.file_path = data_dir / filename
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.versions: Dict[str, Dict[str, Any]] = self._load()

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
            json.dump(self.versions, f, indent=2)

    def create_commit(
        self,
        context_text: str,
        assertions: List[Dict[str, Any]],
        invariants: List[str],
        strategy_name: str,
        session_id: str = "default",
        parent_commit: Optional[str] = None
    ) -> Dict[str, Any]:
        content_hash = hashlib.sha256(context_text.encode("utf-8")).hexdigest()[:10]
        commit_id = f"CMT-{content_hash}"
        
        # Enforce DAG constraints: parent_commit cannot equal self commit_id or form a cycle
        if parent_commit == commit_id:
            parent_commit = None
        elif parent_commit and parent_commit in self.versions:
            curr = parent_commit
            visited_ancestors = set()
            while curr and curr in self.versions:
                if curr == commit_id:
                    parent_commit = None
                    break
                if curr in visited_ancestors:
                    break
                visited_ancestors.add(curr)
                curr = self.versions[curr].get("parent_commit")
            
        commit_record = {
            "commit_id": commit_id,
            "parent_commit": parent_commit,
            "session_id": session_id,
            "timestamp": time.time(),
            "strategy_name": strategy_name,
            "context_text": context_text,
            "assertions_count": len(assertions),
            "invariants_count": len(invariants),
            "invariants": invariants,
            "char_count": len(context_text),
            "status": "active"  # active, rolled_back, failed
        }
        
        self.versions[commit_id] = commit_record
        self._save()
        return commit_record

    def validate_dag_integrity(self) -> Dict[str, Any]:
        """
        Validates that version DAG has zero self-referential parent links and zero cycles.
        """
        self_parents = []
        missing_parents = []
        has_cycle = False
        
        for cid, record in self.versions.items():
            parent = record.get("parent_commit")
            if parent == cid:
                self_parents.append(cid)
            elif parent and parent not in self.versions:
                missing_parents.append(cid)

        # Detect cycles via DFS traversal
        visited = set()
        rec_stack = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            parent = self.versions.get(node, {}).get("parent_commit")
            if parent and parent != node and parent in self.versions:
                if parent not in visited:
                    if dfs(parent):
                        return True
                elif parent in rec_stack:
                    return True
            rec_stack.remove(node)
            return False

        for cid in list(self.versions.keys()):
            if cid not in visited:
                if dfs(cid):
                    has_cycle = True
                    break

        is_valid = len(self_parents) == 0 and not has_cycle

        return {
            "is_valid": is_valid,
            "self_parent_count": len(self_parents),
            "missing_parent_count": len(missing_parents),
            "has_cycle": has_cycle,
            "self_parents": self_parents,
            "missing_parents": missing_parents
        }

    def repair_dag(self) -> Dict[str, Any]:
        """
        Repairs any self-referential parents or cycles in the stored version DAG.
        """
        repaired_self = 0
        for cid, record in self.versions.items():
            if record.get("parent_commit") == cid:
                record["parent_commit"] = None
                repaired_self += 1

        # Break any cycles by removing parent pointers that form cycles
        visited = set()
        rec_stack = set()
        repaired_cycles = 0

        def dfs_repair(node: str) -> bool:
            nonlocal repaired_cycles
            visited.add(node)
            rec_stack.add(node)
            parent = self.versions.get(node, {}).get("parent_commit")
            if parent and parent != node and parent in self.versions:
                if parent in rec_stack:
                    # Cycle detected! Break cycle by disconnecting parent pointer
                    self.versions[node]["parent_commit"] = None
                    repaired_cycles += 1
                elif parent not in visited:
                    dfs_repair(parent)
            rec_stack.remove(node)
            return False

        for cid in list(self.versions.keys()):
            if cid not in visited:
                dfs_repair(cid)

        if repaired_self > 0 or repaired_cycles > 0:
            self._save()

        return {
            "repaired_self_parents": repaired_self,
            "repaired_cycles": repaired_cycles,
            "valid_after_repair": self.validate_dag_integrity()["is_valid"]
        }

    def rollback(self, commit_id: str) -> Optional[Dict[str, Any]]:
        """
        Marks a commit as failed/rolled_back and retrieves parent or prior stable commit.
        """
        if commit_id in self.versions:
            self.versions[commit_id]["status"] = "failed"
            parent = self.versions[commit_id].get("parent_commit")
            self._save()
            if parent and parent in self.versions:
                return self.versions[parent]
        
        # Fallback to latest active commit
        active_commits = [c for c in self.versions.values() if c.get("status") == "active"]
        if active_commits:
            active_commits.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
            return active_commits[0]
        return None

    def get_commit(self, commit_id: str) -> Optional[Dict[str, Any]]:
        return self.versions.get(commit_id)
