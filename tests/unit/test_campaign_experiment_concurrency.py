from contextos.core.campaigns import CampaignManager, ContextCanary
from contextos.core.experiment_runner import AutonomousExperimentRunner
from contextos.identity import IdentityScope


def _ident():
    return IdentityScope(runtime_id="r", workspace_id="w", project_id="p", session_id="s", agent_id="a")


def _metrics():
    return dict(strategy_name="hybrid_packet", token_count=10, raw_token_estimate=100,
                prep_latency_ms=1.0, is_verified=True, assertion_count=1, identity=_ident().as_dict())


def test_experiment_runner_second_writer_does_not_drop_first(tmp_path):
    a, b = AutonomousExperimentRunner(tmp_path), AutonomousExperimentRunner(tmp_path)
    a.record_turn_metrics(**_metrics())
    b.record_turn_metrics(**_metrics())
    fresh = AutonomousExperimentRunner(tmp_path)
    assert len(fresh.history) == 2
    assert sorted(r["turn_id"] for r in fresh.history) == [1, 2]


def test_campaign_manager_second_writer_does_not_drop_first(tmp_path):
    a, b = CampaignManager(tmp_path), CampaignManager(tmp_path)
    a.create_campaign("one", identity=_ident())
    b.create_campaign("two", identity=_ident())
    assert len(CampaignManager(tmp_path).list_campaigns()) == 2


def test_incident_log_second_writer_does_not_drop_first(tmp_path):
    a, b = ContextCanary(tmp_path), ContextCanary(tmp_path)
    a.log_incident("first", {})
    b.log_incident("second", {})
    import json
    assert len(json.loads((tmp_path / "incidents.json").read_text())) == 2


def test_corrupt_campaign_file_is_preserved(tmp_path):
    (tmp_path / "campaigns.json").write_text("{bad")
    CampaignManager(tmp_path).create_campaign("one", identity=_ident())
    assert list(tmp_path.glob("campaigns.json.corrupt*"))


def test_canary_second_writer_does_not_drop_first(tmp_path):
    a, b = ContextCanary(tmp_path), ContextCanary(tmp_path)
    assert a.record_eligible_turn({})
    assert b.record_eligible_turn({})
    fresh = ContextCanary(tmp_path)
    assert fresh.state["fresh_stage_turns"] == 2
    assert len(fresh.rolling_history) == 2


def test_canary_rollback_by_other_instance_is_not_overwritten(tmp_path):
    a, b = ContextCanary(tmp_path), ContextCanary(tmp_path)
    b.trigger_rollback("boom")
    assert a.record_eligible_turn({})
    fresh = ContextCanary(tmp_path)
    assert fresh.state["rollback_count"] == 1
    assert fresh.state["current_stage"] == 0


def test_corrupt_canary_file_is_preserved(tmp_path):
    (tmp_path / "canary.json").write_text("{bad")
    ContextCanary(tmp_path).record_eligible_turn({})
    assert list(tmp_path.glob("canary.json.corrupt*"))
