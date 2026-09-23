import json

from contextos.config import ContextOSConfig
from contextos.core.experiment_runner import AutonomousExperimentRunner
from contextos.core.campaigns import CampaignManager
from contextos.core.goals import GoalEngine
from contextos.core.tournament import CodecTournamentEngine
from contextos.codecs.heterogeneous_compiler import HeterogeneousPacketCompiler
from contextos.identity import IdentityScope
from contextos.storage.event_store import EventStore
from contextos.storage.source_store import SourceStore
from contextos.storage.versioning import ContextVersionStore


def test_event_and_source_identity_filters(tmp_path):
    one = IdentityScope("codex", "workspace-a", "project-a", "same-session", "agent-a")
    two = IdentityScope("codex", "workspace-b", "project-a", "same-session", "agent-a")
    events = EventStore(tmp_path)
    events.append_event("Prompt", {}, identity=one)
    events.append_event("Prompt", {}, identity=two)
    assert len(events.get_events(identity=one)) == 1
    assert events.get_events(identity=one)[0]["workspace_id"] == "workspace-a"

    sources = SourceStore(tmp_path)
    sid = sources.put_source("private context", identity=one)
    assert sid in sources.get_sources([sid], identity=one)
    assert sid not in sources.get_sources([sid], identity=two)


def test_goal_bare_session_alias_cannot_cross_workspace(tmp_path):
    goals = GoalEngine(tmp_path)
    goals.set_active_goal("A", session_id="shared", workspace_id="workspace-a", project_id="p")
    assert goals.get_active_goal(session_id="shared", workspace_id="workspace-b", project_id="p") is None


def test_version_records_identity(tmp_path):
    identity = IdentityScope("codex", "w", "p", "s", "agent")
    versions = ContextVersionStore(tmp_path)
    row = versions.create_commit("context", [], [], "hybrid_packet", "s", identity=identity)
    assert row["identity_confidence"] == "observed"
    assert row["agent_id"] == "agent"


def test_tournament_drives_hybrid_section_compiler(tmp_path):
    engine = CodecTournamentEngine(AutonomousExperimentRunner(tmp_path))
    identity = IdentityScope("codex", "workspace", "project", "session", "main").as_dict()
    result = engine.run_tournament(
        [{"kind": "fact", "subject": "A", "predicate": "rel", "object": "B"}], ["keep"], identity=identity
    )
    assert "hybrid_packet" not in result["match_details"]
    assert result["active_meta_strategy"] == "hybrid_packet"
    packet, _ = HeterogeneousPacketCompiler.compile_packet(
        [{"kind": "fact", "subject": "A", "predicate": "rel", "object": "B"}], [],
        section_codecs={"@STATE": "native_graph"}
    )
    assert "@STATE (NATIVE_GRAPH)" in packet
    assert "(A)-[rel]->(B)" in packet


def test_experiments_and_campaigns_are_identity_scoped(tmp_path):
    one = IdentityScope("codex", "workspace-a", "project-a", "session", "agent")
    two = IdentityScope("codex", "workspace-b", "project-a", "session", "agent")
    runner = AutonomousExperimentRunner(tmp_path)
    row = runner.record_turn_metrics("hybrid_packet", 12, 20, 1, True, 1, identity=one.as_dict())
    assert row["workspace_id"] == "workspace-a"

    campaigns = CampaignManager(tmp_path)
    campaigns.create_campaign("section-codecs", identity=one)
    campaigns.record_campaign_turn("section-codecs", "ncc_vcl", 1.2, identity=one,
        details={"section_codecs": {"@INV": "ncc_vcl"}})
    assert campaigns.get_campaign("section-codecs", identity=one)["completed_turns"] == 1
    assert campaigns.get_campaign("section-codecs", identity=two) is None
    assert campaigns.get_campaign("section-codecs", identity=one)["observations"][0]["details"]["section_codecs"]["@INV"] == "ncc_vcl"


def test_config_directory_partitions_workspace_and_project(tmp_path):
    base = tmp_path / "work"
    a = ContextOSConfig(workspace_dir=base, workspace_id="workspace-a", project_id="p")
    b = ContextOSConfig(workspace_dir=base, workspace_id="workspace-b", project_id="p")
    assert a.ensure_client_directory() != b.ensure_client_directory()
