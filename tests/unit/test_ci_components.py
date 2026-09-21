import pytest
import tempfile
from pathlib import Path
from contextos.core.shadow_experimenter import ShadowTester, CounterfactualReplayEngine
from contextos.core.campaigns import CampaignManager, ContextCanary
from contextos.core.monitors import ContinuousMonitors, ExpansionMonitor

@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)

def test_unit_shadow_tester(tmp_dir):
    st = ShadowTester(tmp_dir)
    records = st.run_shadow_eval(
        turn_id="CMT-TEST1",
        prompt="Refactor auth module",
        assertions=[{"subject": "Auth", "predicate": "uses", "object": "OAuth2"}],
        invariants=["Rule 1"],
        production_strategy="hybrid_packet",
        production_token_count=80
    )
    assert len(records) >= 2
    assert records[0]["shadow_candidate"] != "hybrid_packet"

def test_unit_campaign_manager(tmp_dir):
    cm = CampaignManager(tmp_dir)
    c = cm.create_campaign("test-campaign", target_turns=10)
    assert c["status"] == "RUNNING"

    for _ in range(10):
        cm.record_campaign_turn("test-campaign", "hybrid_packet", 4.5)

    updated = cm.get_campaign("test-campaign")
    assert updated["status"] == "COMPLETE"
    assert updated["completed_turns"] == 10

def test_unit_context_canary(tmp_dir):
    canary = ContextCanary(tmp_dir)
    status = canary.get_status()
    assert status["stage"] in range(5)

    canary.trigger_rollback("Test regression in critical recall")
    rb_status = canary.get_status()
    assert rb_status["stage"] == 0
    assert rb_status["rollback_count"] == 1

def test_unit_expansion_monitor():
    exp = ExpansionMonitor()
    exp.record_expansion("AuthService")
    exp.record_expansion("AuthService")
    under_alloc = exp.get_under_allocated_entities(threshold=2)
    assert "AuthService" in under_alloc
