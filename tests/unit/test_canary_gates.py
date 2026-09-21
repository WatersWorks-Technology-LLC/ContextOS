import pytest
import tempfile
from pathlib import Path
from contextos.core.campaigns import ContextCanary

def test_sticky_session_canary_assignment():
    # Verify hash determinism across session IDs
    b1 = ContextCanary.is_session_assigned_to_canary("repo_a", "sess-123", "cmp1", traffic_pct=25)
    b2 = ContextCanary.is_session_assigned_to_canary("repo_a", "sess-123", "cmp1", traffic_pct=25)
    assert b1 == b2  # Must be identical for the same session!
    
    # 0% traffic always returns False
    assert ContextCanary.is_session_assigned_to_canary("repo_a", "sess-123", "cmp1", traffic_pct=0) is False
    # 100% traffic always returns True
    assert ContextCanary.is_session_assigned_to_canary("repo_a", "sess-123", "cmp1", traffic_pct=100) is True

def test_canary_fresh_turns_and_instant_rollback():
    with tempfile.TemporaryDirectory() as td:
        data_dir = Path(td)
        canary = ContextCanary(data_dir=data_dir)
        
        status = canary.get_status()
        assert status["stage"] == 1
        assert status["traffic_pct"] == 5
        
        # Insufficient fresh turns -> promotion fails
        ok, msg = canary.promote_stage()
        assert ok is False
        assert "requires minimum 100 FRESH eligible turns" in msg

        metrics_pass = {
            "critical_fidelity": 1.0,
            "critical_provenance": 1.0,
            "workspace_leaks": 0,
            "catastrophic_errors": 0,
            "task_quality": 1.0,
            "source_accuracy": 0.98,
            "p99_latency_ms": 2.5
        }
        for _ in range(100):
            canary.record_eligible_turn(metrics_pass)
            
        ok, msg = canary.promote_stage()
        assert ok is True
        assert canary.get_status()["stage"] == 2
        assert canary.get_status()["traffic_pct"] == 10

        # Single Instant Failure -> Immediate rollback to Stage 0
        metrics_instant_fail = dict(metrics_pass, critical_fidelity=0.9)
        rec = canary.record_eligible_turn(metrics_instant_fail)
        assert rec is False
        assert canary.get_status()["stage"] == 0
        assert canary.get_status()["rollback_count"] == 1
        assert "[INSTANT FAIL]" in canary.get_status()["last_rollback_reason"]
