import json
import math
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

class AutonomousExperimentRunner:
    """
    Autonomous Strategy Experimentation & Quota / Efficiency Scoring Engine.
    Silently tests context strategies, measures token quota impact, and ranks Pareto efficiency.
    """
    CANDIDATE_STRATEGIES = [
        {"name": "hybrid_packet", "codec": "hybrid_packet", "description": "Heterogeneous per-section ContextOS packet"}
    ]

    def __init__(self, data_dir: Path, filename: str = "experiments.json"):
        self.file_path = data_dir / filename
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.history: List[Dict[str, Any]] = self._load()
        self.current_turn_index = len(self.history)

    def _load(self) -> List[Dict[str, Any]]:
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2)

    def get_next_strategy(self) -> Dict[str, Any]:
        """
        Autonomously rotates candidate strategies or selects the highest-scoring Pareto strategy.
        """
        # Whole-packet codecs are not production competitors: hybrid_packet
        # remains the orchestrator while section codecs compete independently.
        return self.CANDIDATE_STRATEGIES[0]

    def record_turn_metrics(
        self,
        strategy_name: str,
        token_count: int,
        raw_token_estimate: int,
        prep_latency_ms: float,
        is_verified: bool,
        assertion_count: int,
        task_quality: float = 1.0,
        source_accuracy: float = 1.0,
        fidelity: Optional[float] = None,
        identity: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        if not identity or any(not identity.get(k) for k in ("runtime_id", "workspace_id", "project_id", "session_id", "agent_id")):
            raise ValueError("Complete identity is required for new experiment observations")
        compression_ratio = round(raw_token_estimate / max(1, token_count), 2)
        quota_tokens_saved = max(0, raw_token_estimate - token_count)
        eff_fidelity = fidelity if fidelity is not None else (1.0 if is_verified else 0.80)

        # Full Codex Outcome Utility Function:
        # U = (Fidelity^4) * (TaskQuality^3) * (SourceAccuracy^2) * (Compression^1) / (1 + LatencySec)
        latency_sec = max(0.0, prep_latency_ms / 1000.0)
        f_factor = math.pow(eff_fidelity, 4)
        q_factor = math.pow(task_quality, 3)
        s_factor = math.pow(source_accuracy, 2)

        utility_score = round((f_factor * q_factor * s_factor * compression_ratio) / (1.0 + latency_sec), 3)

        metric_record = {
            "turn_id": self.current_turn_index + 1,
            "timestamp": time.time(),
            "strategy_name": strategy_name,
            "delivered_tokens": token_count,
            "raw_token_estimate": raw_token_estimate,
            "quota_tokens_saved": quota_tokens_saved,
            "compression_ratio": compression_ratio,
            "prep_latency_ms": prep_latency_ms,
            "is_verified": is_verified,
            "assertion_count": assertion_count,
            "pareto_score": utility_score,
            "utility_score": utility_score
        }
        metric_record.update(identity)
        metric_record["identity_confidence"] = "observed"

        self.history.append(metric_record)
        self.current_turn_index += 1
        self._save()
        return metric_record

    def get_strategy_scores(self) -> Dict[str, Dict[str, Any]]:
        stats: Dict[str, Dict[str, Any]] = {}
        for record in self.history:
            strat = record["strategy_name"]
            if strat not in stats:
                stats[strat] = {
                    "runs": 0,
                    "total_saved_tokens": 0,
                    "avg_compression_ratio": 0.0,
                    "avg_latency_ms": 0.0,
                    "avg_pareto_score": 0.0,
                    "verified_runs": 0
                }

            s = stats[strat]
            s["runs"] += 1
            s["total_saved_tokens"] += record.get("quota_tokens_saved", 0)
            s["avg_compression_ratio"] += record.get("compression_ratio", 1.0)
            s["avg_latency_ms"] += record.get("prep_latency_ms", 0.0)
            s["avg_pareto_score"] += record.get("pareto_score", 0.0)
            if record.get("is_verified"):
                s["verified_runs"] += 1

        for strat, s in stats.items():
            r = s["runs"]
            s["avg_compression_ratio"] = round(s["avg_compression_ratio"] / r, 2)
            s["avg_latency_ms"] = round(s["avg_latency_ms"] / r, 2)
            s["pareto_efficiency_score"] = round(s["avg_pareto_score"] / r, 3)
            s["verification_rate"] = round(s["verified_runs"] / r, 2)

        return stats
