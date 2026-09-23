import pytest
import tempfile
from pathlib import Path
from contextos.storage.source_store import SourceStore
from contextos.codecs.heterogeneous_compiler import HeterogeneousPacketCompiler
from contextos.core.experiment_runner import AutonomousExperimentRunner
from contextos.core.tournament import CodecTournamentEngine
from contextos.core.provenance_audit import ProvenanceAuditor
from contextos.core.inspector import HumanAuditableContextInspector
from contextos.identity import IdentityScope

@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)

def test_unit_heterogeneous_block_compiler():
    assertions = [
        {"subject": "Auth", "predicate": "uses", "object": "OAuth2", "kind": "decision", "source_ref": "SRC-01"},
        {"subject": "MFA_ENABLED", "predicate": "is", "object": "true", "kind": "flag"}
    ]
    invariants = ["Rule 1"]
    timeline = [{"iso_time": "2026-09-20T20:00:00Z", "event": "D02 deployed"}]

    text, checksum = HeterogeneousPacketCompiler.compile_packet(assertions, invariants, timeline_events=timeline, include_visual_summary=True)
    assert "@INV (NCC-VCL)" in text
    assert "@FLAGS (BITSET)" in text
    assert "@TIME (TIMELINE)" in text
    assert "@SRC (HANDLES)" in text
    assert "@VISUAL (VCL-A)" in text
    assert len(checksum) == 8

def test_unit_codec_tournament(tmp_dir):
    er = AutonomousExperimentRunner(tmp_dir)
    tournament = CodecTournamentEngine(er)
    assertions = [{"subject": "DB", "predicate": "max_conn", "object": "100", "kind": "fact"}]
    res = tournament.run_tournament(assertions, ["Invariant 1"], identity=IdentityScope("codex", "workspace", "project", "session", "main").as_dict())
    assert "winner" in res
    assert "rankings" in res
    assert len(res["match_details"]) >= 3

def test_unit_provenance_auditor(tmp_dir):
    ss = SourceStore(tmp_dir)
    sid = ss.put_source("Authentic evidence content", identity=IdentityScope("codex", "workspace", "project", "session", "main"))
    auditor = ProvenanceAuditor(ss)

    assertions = [
        {"assertion_id": "A1", "subject": "Auth", "kind": "decision", "source_ref": sid},
        {"assertion_id": "A2", "subject": "DB", "kind": "fact", "source_ref": "SRC-MISSING"}
    ]
    audit = auditor.audit_packet_provenance(assertions)
    assert audit["critical_provenance_ratio"] == 1.0
    assert audit["ordinary_provenance_ratio"] == 0.0
    assert audit["critical_passed"] is True

def test_unit_context_inspector():
    inspection = HumanAuditableContextInspector.inspect_packet(
        context_text="=== PINNED ===",
        assertions=[{"subject": "DB", "predicate": "timeout", "object": "30s", "kind": "constraint"}],
        invariants=["Rule 1"],
        commit_id="CMT-123",
        strategy_used="hybrid_packet",
        token_count=45,
        telemetry={"prep_latency_ms": 1.2}
    )
    assert inspection["commit_id"] == "CMT-123"
    assert len(inspection["item_breakdown"]) == 2
