import json
import time
import uuid
import re
import fcntl
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

class GoalEngine:
    """
    ContextOS Hardened Multi-Tenant & Session-Isolated Autonomous Goal Engine.
    - POSIX File Locking (fcntl) for concurrent process/thread safety across Codex sessions & subagents
    - Subagent goal inheritance and parent-child agent scope hierarchy
    - Selective PostToolUse context injection policy (infers context only on state changes or every 10 ops)
    - Empirical evidence verification engine (exit codes, test counts, build statuses)
    - Codex Stop hook block decision gate (clean empty dict on allowed stop)
    """
    def __init__(self, data_dir: Path, filename: str = "goals.json"):
        self.file_path = data_dir / filename
        self.lock_path = data_dir / "goals.json.lock"
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load_with_lock()

    def _load_with_lock(self) -> Dict[str, Any]:
        with open(self.lock_path, "w") as lock_file:
            fcntl.flock(lock_file, fcntl.LOCK_SH)
            try:
                if self.file_path.exists():
                    try:
                        with open(self.file_path, "r", encoding="utf-8") as f:
                            return json.load(f)
                    except Exception:
                        pass
                return {
                    "sessions": {},
                    "subagents": {},
                    "goals": {}
                }
            finally:
                fcntl.flock(lock_file, fcntl.LOCK_UN)

    def _save_with_lock(self):
        with open(self.lock_path, "w") as lock_file:
            fcntl.flock(lock_file, fcntl.LOCK_EX)
            try:
                temp_file = self.file_path.with_suffix(".tmp")
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(self.data, f, indent=2)
                temp_file.replace(self.file_path)
            finally:
                fcntl.flock(lock_file, fcntl.LOCK_UN)

    def _get_identity_key(
        self,
        runtime_id: str = "codex",
        workspace_id: str = "default",
        project_id: str = "default",
        session_id: str = "default",
        agent_id: str = "main"
    ) -> str:
        return f"{runtime_id}:{workspace_id}:{project_id}:{session_id}:{agent_id}"

    def set_active_goal(
        self,
        description: str,
        acceptance_criteria: List[str] = None,
        session_id: str = "default",
        runtime_id: str = "codex",
        workspace_id: str = "default",
        project_id: str = "default",
        agent_id: str = "main",
        parent_agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        self.data = self._load_with_lock()
        goal_id = f"GOL-{uuid.uuid4().hex[:8]}"
        criteria = acceptance_criteria or [
            "Implementation completed without errors",
            "Unit and integration tests passing cleanly",
            "Verification evidence documented"
        ]
        goal = {
            "goal_id": goal_id,
            "runtime_id": runtime_id,
            "workspace_id": workspace_id,
            "project_id": project_id,
            "session_id": session_id,
            "agent_id": agent_id,
            "parent_agent_id": parent_agent_id,
            "description": description,
            "status": "IN_PROGRESS",
            "created_at": time.time(),
            "updated_at": time.time(),
            "op_count": 0,
            "acceptance_criteria": [
                {"id": f"AC-{i+1}", "criterion": c, "verified": False, "evidence": None}
                for i, c in enumerate(criteria)
            ],
            "checkpoints": [],
            "completion_evaluations": []
        }
        self.data["goals"][goal_id] = goal
        if "sessions" not in self.data:
            self.data["sessions"] = {}
        
        # Store both 5-part full key and 4-part legacy key for fallback compatibility
        full_key = self._get_identity_key(runtime_id, workspace_id, project_id, session_id, agent_id)
        legacy_key = f"{runtime_id}:{workspace_id}:{project_id}:{session_id}"
        self.data["sessions"][full_key] = goal_id
        self.data["sessions"][legacy_key] = goal_id
        self.data["sessions"][session_id] = goal_id
        self._save_with_lock()
        return goal

    def register_subagent(
        self,
        subagent_id: str = "subagent-1",
        subagent_role: str = "research",
        session_id: str = "default",
        runtime_id: str = "codex",
        workspace_id: str = "default",
        project_id: str = "default",
        parent_agent_id: str = "main"
    ) -> Dict[str, Any]:
        self.data = self._load_with_lock()
        parent_goal = self.get_active_goal(
            session_id=session_id,
            runtime_id=runtime_id,
            workspace_id=workspace_id,
            project_id=project_id,
            agent_id=parent_agent_id
        )
        subagent_entry = {
            "subagent_id": subagent_id,
            "role": subagent_role,
            "session_id": session_id,
            "parent_agent_id": parent_agent_id,
            "inherited_goal_id": parent_goal["goal_id"] if parent_goal else None,
            "created_at": time.time()
        }
        if "subagents" not in self.data:
            self.data["subagents"] = {}
        self.data["subagents"][f"{session_id}:{subagent_id}"] = subagent_entry
        
        if parent_goal:
            sub_key = self._get_identity_key(runtime_id, workspace_id, project_id, session_id, subagent_id)
            self.data["sessions"][sub_key] = parent_goal["goal_id"]
            
        self._save_with_lock()
        return subagent_entry

    def get_active_goal(
        self,
        session_id: str = "default",
        runtime_id: str = "codex",
        workspace_id: str = "default",
        project_id: str = "default",
        agent_id: str = "main"
    ) -> Optional[Dict[str, Any]]:
        self.data = self._load_with_lock()
        sessions = self.data.get("sessions", {})
        full_key = self._get_identity_key(runtime_id, workspace_id, project_id, session_id, agent_id)
        legacy_key = f"{runtime_id}:{workspace_id}:{project_id}:{session_id}"
        # Legacy session-only keys are unsafe across projects/workspaces. Keep
        # them readable only when the stored goal's full scope matches.
        gid = sessions.get(full_key) or sessions.get(legacy_key)
        if not gid and session_id in sessions:
            candidate = self.data.get("goals", {}).get(sessions[session_id])
            expected = (runtime_id, workspace_id, project_id, session_id, agent_id)
            actual = tuple((candidate or {}).get(k) for k in ("runtime_id", "workspace_id", "project_id", "session_id", "agent_id"))
            if actual == expected:
                gid = sessions[session_id]
        if gid and gid in self.data["goals"]:
            return self.data["goals"][gid]
        return None


    def parse_structured_evidence(self, tool_name: str, tool_output: str) -> Dict[str, Any]:
        evidence = {
            "tool": tool_name,
            "timestamp": time.time(),
            "is_test_run": False,
            "test_passed": 0,
            "test_failed": 0,
            "is_clean_test": False,
            "is_clean_build": False
        }
        output_lower = tool_output.lower()

        pytest_match = re.search(r'(\d+)\s+passed(?:,\s*(\d+)\s+failed)?(?:,\s*(\d+)\s+error)?', output_lower)
        if pytest_match or "passed in" in output_lower:
            evidence["is_test_run"] = True
            passed_cnt = int(pytest_match.group(1)) if pytest_match and pytest_match.group(1) else 0
            failed_cnt = int(pytest_match.group(2)) if pytest_match and pytest_match.group(2) else 0
            error_cnt = int(pytest_match.group(3)) if pytest_match and pytest_match.group(3) else 0
            
            evidence["test_passed"] = passed_cnt
            evidence["test_failed"] = failed_cnt + error_cnt
            if passed_cnt > 0 and failed_cnt == 0 and error_cnt == 0:
                evidence["is_clean_test"] = True

        if "exited with code 0" in output_lower or "successfully built" in output_lower:
            evidence["is_clean_build"] = True

        return evidence

    def record_checkpoint(self, tool_name: str, tool_input: Any, tool_output: str, session_id: str = "default", identity=None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        self.data = self._load_with_lock()
        goal = self.get_active_goal(**identity.as_dict()) if identity else self.get_active_goal(session_id=session_id)
        if not goal:
            return None, None

        evidence_struct = self.parse_structured_evidence(tool_name, tool_output)
        state_changed = False
        
        for ac in goal["acceptance_criteria"]:
            if not ac["verified"]:
                crit_lower = ac["criterion"].lower()
                if "test" in crit_lower or "unit" in crit_lower:
                    if evidence_struct["is_clean_test"]:
                        ac["verified"] = True
                        ac["evidence"] = f"Empirical pass ({evidence_struct['test_passed']} passed, 0 failed/errors)"
                        state_changed = True
                elif "build" in crit_lower or "compile" in crit_lower:
                    if evidence_struct["is_clean_build"]:
                        ac["verified"] = True
                        ac["evidence"] = f"Empirical build success (Exit code 0 captured via {tool_name})"
                        state_changed = True


        goal["op_count"] = goal.get("op_count", 0) + 1
        periodic_trigger = (goal["op_count"] % 10 == 0)

        checkpoint = {
            "timestamp": time.time(),
            "tool_name": tool_name,
            "input_summary": str(tool_input)[:150],
            "verified_criteria_count": sum(1 for ac in goal["acceptance_criteria"] if ac["verified"])
        }
        goal["checkpoints"].append(checkpoint)
        goal["updated_at"] = time.time()
        self._save_with_lock()

        # Selective context injection policy: ONLY inject if state changed or periodic (every 10 ops)
        if not state_changed and not periodic_trigger:
            return goal, None

        verified_cnt = sum(1 for ac in goal["acceptance_criteria"] if ac["verified"])
        total_cnt = len(goal["acceptance_criteria"])
        unverified = [ac["criterion"] for ac in goal["acceptance_criteria"] if not ac["verified"]]
        
        feedback_str = (
            f"ContextOS Checkpoint [{goal['goal_id']}]: Goal '{goal['description']}' ({verified_cnt}/{total_cnt} verified).\n"
            f"Next unverified criteria: {', '.join(unverified[:2]) if unverified else 'All verified'}"
        )
        return goal, feedback_str

    def verify_criterion(self, criterion_id: str, evidence: str, session_id: str = "default") -> bool:
        self.data = self._load_with_lock()
        goal = self.get_active_goal(session_id=session_id)
        if not goal:
            return False
        crit_lower = criterion_id.lower()
        for ac in goal["acceptance_criteria"]:
            if ac["id"].lower() == crit_lower or crit_lower in ac["criterion"].lower() or ac["criterion"].lower() in crit_lower:
                ac["verified"] = True
                ac["evidence"] = evidence
                goal["updated_at"] = time.time()
                self._save_with_lock()
                return True
        return False


    def evaluate_stop_condition(self, final_response_text: str = "", session_id: str = "default", identity=None) -> Dict[str, Any]:
        """
        Evaluates whether Codex is permitted to STOP or must BLOCK/CONTINUE working.
        - Unfulfilled goals -> decision="block" with continuation prompt
        - Completed goals -> decision="allow" (maps to clean empty dict response)
        """
        self.data = self._load_with_lock()
        goal = self.get_active_goal(**identity.as_dict()) if identity else self.get_active_goal(session_id=session_id)
        if not goal or goal["status"] == "COMPLETED":
            return {
                "decision": "allow",
                "allow_stop": True,
                "reason": "No active unfulfilled goals"
            }

        unverified = [ac for ac in goal["acceptance_criteria"] if not ac["verified"]]
        verified = [ac for ac in goal["acceptance_criteria"] if ac["verified"]]

        if not unverified:
            goal["status"] = "COMPLETED"
            goal["completed_at"] = time.time()
            self._save_with_lock()
            return {
                "decision": "allow",
                "allow_stop": True,
                "reason": f"Active Goal {goal['goal_id']} fully verified: all {len(verified)} acceptance criteria satisfied."
            }

        missing_str = "\n".join([f"- ❌ [{ac['id']}] {ac['criterion']}" for ac in unverified])
        verified_str = "\n".join([f"- ✅ [{ac['id']}] {ac['criterion']}: {ac['evidence']}" for ac in verified]) if verified else "- None"

        continuation_reason = (
            f"ContextOS Goal Execution Gate: Active Goal '{goal['description']}' is INCOMPLETE.\n\n"
            f"Verified Criteria:\n{verified_str}\n\n"
            f"Unfulfilled Acceptance Criteria:\n{missing_str}\n\n"
            f"Action Required: Continue execution until all remaining criteria are empirically verified."
        )

        eval_record = {
            "timestamp": time.time(),
            "decision": "block",
            "unverified_count": len(unverified),
            "verified_count": len(verified)
        }
        goal["completion_evaluations"].append(eval_record)
        self._save_with_lock()

        return {
            "decision": "block",
            "allow_stop": False,
            "reason": continuation_reason,
            "goal_id": goal["goal_id"],
            "unverified_criteria": [ac["criterion"] for ac in unverified]
        }
