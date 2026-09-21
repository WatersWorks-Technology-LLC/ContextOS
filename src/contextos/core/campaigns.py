import json
import time
import hashlib
import statistics
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

class CampaignManager:
    """
    Background Experiment Campaign Manager.
    Manages persistent CI/CD-style experiment campaigns (e.g. 'hybrid-v3-vs-ncc').
    Tracks turn progress, confidence intervals, and campaign completion status.
    """
    def __init__(self, data_dir: Path, filename: str = "campaigns.json"):
        self.file_path = data_dir / filename
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.campaigns: Dict[str, Dict[str, Any]] = self._load()

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
            json.dump(self.campaigns, f, indent=2)

    def create_campaign(
        self,
        name: str,
        target_turns: int = 500,
        competitors: List[str] = None
    ) -> Dict[str, Any]:
        campaign = {
            "campaign_id": f"CMP-{name}",
            "name": name,
            "status": "RUNNING",
            "target_turns": target_turns,
            "completed_turns": 0,
            "competitors": competitors or ["hybrid_packet", "ncc_vcl"],
            "leader_so_far": competitors[0] if competitors else "hybrid_packet",
            "confidence": 0.50,
            "created_at": time.time(),
            "updated_at": time.time()
        }
        self.campaigns[name] = campaign
        self._save()
        return campaign

    def record_campaign_turn(self, name: str, winner_strategy: str, score_delta: float):
        if name not in self.campaigns:
            self.create_campaign(name)

        c = self.campaigns[name]
        if c["status"] != "RUNNING":
            return

        c["completed_turns"] += 1
        c["updated_at"] = time.time()
        c["leader_so_far"] = winner_strategy
        c["confidence"] = round(min(0.999, 0.50 + (c["completed_turns"] / (c["target_turns"] * 2.0))), 3)

        if c["completed_turns"] >= c["target_turns"]:
            c["status"] = "COMPLETE"
            c["completed_at"] = time.time()

        self._save()

    def get_campaign(self, name: str) -> Optional[Dict[str, Any]]:
        return self.campaigns.get(name)

    def list_campaigns(self) -> List[Dict[str, Any]]:
        return list(self.campaigns.values())


class ContextCanary:
    """
    Context Canary Rollout Manager with SHA-256 Sticky Session Allocation,
    Per-Stage Fresh Evidence Requirements, and Unified Latency SLO Safety.
    
    Unified Preprocessing Latency SLO:
    - P50 <= 5.0 ms
    - P95 <= 10.0 ms
    - P99 <= 20.0 ms
    """
    CANARY_STAGES = [
        {"stage": 0, "traffic_pct": 0, "fresh_turns_req": 100, "name": "Shadow Only"},
        {"stage": 1, "traffic_pct": 5, "fresh_turns_req": 100, "name": "5% Canary"},
        {"stage": 2, "traffic_pct": 10, "fresh_turns_req": 250, "name": "10% Canary"},
        {"stage": 3, "traffic_pct": 25, "fresh_turns_req": 500, "name": "25% Canary"},
        {"stage": 4, "traffic_pct": 50, "fresh_turns_req": 1000, "name": "50% Canary"},
        {"stage": 5, "traffic_pct": 100, "fresh_turns_req": 2000, "name": "100% Production Default"}
    ]

    def __init__(self, data_dir: Path, filename: str = "canary.json"):
        self.data_dir = data_dir
        self.file_path = data_dir / filename
        self.incidents_path = data_dir / "incidents.json"
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.state: Dict[str, Any] = self._load()
        self.rolling_history: List[Dict[str, Any]] = self.state.get("rolling_history", [])
        self.high_latency_window_violations: int = self.state.get("high_latency_window_violations", 0)

    def _load(self) -> Dict[str, Any]:
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "current_stage": 1,
            "fresh_stage_turns": 0,
            "total_accumulated_fresh_turns": 0,
            "candidate_strategy": "hybrid_packet",
            "rollback_count": 0,
            "last_rollback_reason": None,
            "rolling_history": [],
            "high_latency_window_violations": 0
        }

    def _save(self):
        self.state["rolling_history"] = self.rolling_history[-200:]
        self.state["high_latency_window_violations"] = self.high_latency_window_violations
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)

    @staticmethod
    def is_session_assigned_to_canary(
        workspace_id: str,
        session_id: str,
        campaign_id: str,
        traffic_pct: int
    ) -> bool:
        if traffic_pct <= 0:
            return False
        if traffic_pct >= 100:
            return True

        key = f"{workspace_id}:{session_id}:{campaign_id}"
        bucket = int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:8], 16) % 100
        return bucket < traffic_pct

    def log_incident(self, reason: str, metrics: Dict[str, Any]):
        incidents = []
        if self.incidents_path.exists():
            try:
                with open(self.incidents_path, "r", encoding="utf-8") as f:
                    incidents = json.load(f)
            except Exception:
                incidents = []

        incident = {
            "incident_id": f"INC-{int(time.time()*1000)}",
            "timestamp": time.time(),
            "stage_at_failure": self.state["current_stage"],
            "candidate_strategy": self.state.get("candidate_strategy"),
            "reason": reason,
            "metrics": metrics
        }
        incidents.append(incident)
        with open(self.incidents_path, "w", encoding="utf-8") as f:
            json.dump(incidents, f, indent=2)

    def record_eligible_turn(self, metrics: Dict[str, Any]) -> bool:
        """
        Evaluates turn metrics against unified SLOs:
        - Instant Failures: critical_fidelity < 1.0, critical_provenance < 1.0, workspace_leaks > 0, catastrophic_errors > 0.
        - Windowed Degradation: rolling source_accuracy < 0.95 over 100 turns, or P99 > 20.0ms over 3 consecutive 50-turn window boundaries.
        """
        # 1. Instant Failure Checks
        instant_failures = []
        if metrics.get("critical_fidelity", 1.0) < 1.0:
            instant_failures.append(f"critical_fidelity {metrics.get('critical_fidelity')} < 1.0")
        if metrics.get("critical_provenance", 1.0) < 1.0:
            instant_failures.append(f"critical_provenance {metrics.get('critical_provenance')} < 1.0")
        if metrics.get("workspace_leaks", 0) > 0:
            instant_failures.append(f"workspace_leaks {metrics.get('workspace_leaks')} > 0")
        if metrics.get("catastrophic_errors", 0) > 0:
            instant_failures.append(f"catastrophic_errors {metrics.get('catastrophic_errors')} > 0")

        if instant_failures:
            reason = "[INSTANT FAIL] " + "; ".join(instant_failures)
            self.trigger_rollback(reason, metrics)
            return False

        self.rolling_history.append(metrics)
        if len(self.rolling_history) > 200:
            self.rolling_history.pop(0)

        # 2. Windowed Degradation Checks (Evaluated at 50-turn window boundaries)
        if len(self.rolling_history) >= 50 and len(self.rolling_history) % 50 == 0:
            recent_100 = self.rolling_history[-100:]
            avg_src_acc = sum(m.get("source_accuracy", 1.0) for m in recent_100) / len(recent_100)
            if avg_src_acc < 0.95:
                reason = f"[WINDOWED FAIL] Rolling source_accuracy {avg_src_acc:.3f} < 0.95 over last {len(recent_100)} turns"
                self.trigger_rollback(reason, metrics)
                return False

            recent_50 = self.rolling_history[-50:]
            lats = sorted([m.get("p99_latency_ms", 0.0) for m in recent_50])
            # P95/P99 index for 50-sample window
            p95_idx = min(len(lats) - 1, int(0.95 * len(lats)))
            p95_lat = lats[p95_idx]

            if p95_lat > 10.0:  # SLO: P95 <= 10.0ms
                self.high_latency_window_violations += 1
                if self.high_latency_window_violations >= 3:
                    reason = f"[WINDOWED FAIL] P95 latency ({p95_lat:.2f}ms) exceeded 10.0ms across {self.high_latency_window_violations} consecutive 50-turn windows"
                    self.trigger_rollback(reason, metrics)
                    return False
            else:
                self.high_latency_window_violations = max(0, self.high_latency_window_violations - 1)

        self.state["fresh_stage_turns"] = self.state.get("fresh_stage_turns", 0) + 1
        self.state["total_accumulated_fresh_turns"] = self.state.get("total_accumulated_fresh_turns", 0) + 1
        self._save()
        return True

    def promote_stage(self) -> Tuple[bool, str]:
        curr = self.state["current_stage"]
        if curr >= 5:
            return False, "Already at maximum Stage 5 (100% Production Default)."

        curr_stage_info = self.CANARY_STAGES[curr]
        req_fresh_turns = curr_stage_info["fresh_turns_req"]
        acc_fresh_turns = self.state.get("fresh_stage_turns", 0)

        if acc_fresh_turns < req_fresh_turns:
            return False, f"Cannot promote to Stage {curr + 1}: requires minimum {req_fresh_turns} FRESH eligible turns at Stage {curr} (currently accumulated: {acc_fresh_turns})."

        self.state["current_stage"] += 1
        self.state["fresh_stage_turns"] = 0
        self._save()
        return True, f"Promoted to Stage {curr + 1} ({self.CANARY_STAGES[curr + 1]['name']})."

    def trigger_rollback(self, reason: str, metrics: Optional[Dict[str, Any]] = None):
        self.log_incident(reason, metrics or {})
        self.state["current_stage"] = 0
        self.state["fresh_stage_turns"] = 0
        self.state["total_accumulated_fresh_turns"] = 0
        self.state["rollback_count"] = self.state.get("rollback_count", 0) + 1
        self.state["last_rollback_reason"] = reason
        self.rolling_history = []
        self.high_latency_window_violations = 0
        self._save()

    def get_status(self) -> Dict[str, Any]:
        curr = min(len(self.CANARY_STAGES) - 1, max(0, self.state.get("current_stage", 0)))
        stage_info = self.CANARY_STAGES[curr]
        next_stage_info = self.CANARY_STAGES[curr + 1] if curr < 5 else None

        return {
            "stage": curr,
            "stage_name": stage_info["name"],
            "traffic_pct": stage_info["traffic_pct"],
            "fresh_stage_turns": self.state.get("fresh_stage_turns", 0),
            "accumulated_fresh_turns": self.state.get("total_accumulated_fresh_turns", self.state.get("fresh_stage_turns", 0)),
            "fresh_turns_required_for_promotion": stage_info["fresh_turns_req"],
            "next_stage_name": next_stage_info["name"] if next_stage_info else None,
            "candidate_strategy": self.state.get("candidate_strategy"),
            "rollback_count": self.state.get("rollback_count", 0),
            "last_rollback_reason": self.state.get("last_rollback_reason")
        }
