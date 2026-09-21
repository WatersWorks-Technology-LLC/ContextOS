import pytest
import json
import tempfile
from pathlib import Path
from contextos.core.certificate import ReleaseCertificateManager
from contextos.storage.versioning import ContextVersionStore

def test_release_certificate_cannot_lie():
    """
    Test that ReleaseCertificateManager strictly refuses to issue a 1.0.0
    production release certificate when any canary, latency, provenance,
    incident, or DAG gate criterion fails.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        cert_mgr = ReleaseCertificateManager(data_dir)

        # 1. Canary Stage 2 (10% Canary), 0 fresh turns, 5 rollbacks
        canary_status = {
            "stage": 2,
            "stage_name": "10% Canary",
            "fresh_turns": 0,
            "accumulated_fresh_turns": 350,
            "rollback_count": 5
        }
        provenance_audit = {
            "critical_provenance_ratio": 1.0,
            "ordinary_provenance_ratio": 1.0
        }
        drift_audit = {"drift_score": 1.0}
        incidents = [
            {"type": "latency_slo_breach", "category": "latency", "details": "P99 22.5ms"},
            {"type": "rollback_triggered", "category": "latency", "details": "Rollback to Stage 1"}
        ]
        tournament_res = {"active_meta_strategy": "hybrid_packet"}
        latencies = [2.5, 4.0, 22.5]  # P99 > 20ms breach

        # Attempting 1.0.0 must fail with ValueError
        with pytest.raises(ValueError) as excinfo:
            cert_mgr.export_all_evidence_reports(
                canary_status=canary_status,
                provenance_audit=provenance_audit,
                drift_audit=drift_audit,
                incidents=incidents,
                tournament_res=tournament_res,
                latencies_ms=latencies,
                control_tokens=10000,
                contextos_tokens=100,
                version="1.0.0"
            )
        assert "Refusing to issue 1.0.0 production certificate" in str(excinfo.value)
        assert not cert_mgr.is_production_100_ready()

        # Exporting without requesting 1.0.0 explicitly should result in RC3 designation
        cert = cert_mgr.export_all_evidence_reports(
            canary_status=canary_status,
            provenance_audit=provenance_audit,
            drift_audit=drift_audit,
            incidents=incidents,
            tournament_res=tournament_res,
            latencies_ms=latencies,
            control_tokens=10000,
            contextos_tokens=100,
            version="1.0-rc3"
        )
        assert cert["version"] == "1.0-rc3"
        assert not cert_mgr.is_production_100_ready()


def test_version_dag_validation_and_repair():
    """
    Test that ContextVersionStore rejects self-referential parents,
    detects cycles, and repairs broken DAG structures.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        vstore = ContextVersionStore(data_dir)

        # 1. Create a root commit with parent=None
        c1 = vstore.create_commit("Text 1", [], [], "strat1", "sess1", parent_commit=None)
        assert c1["parent_commit"] is None

        # 2. Attempt self-parent commit
        cid1 = c1["commit_id"]
        c2 = vstore.create_commit("Text 2", [], [], "strat1", "sess1", parent_commit=cid1)
        cid2 = c2["commit_id"]

        # Directly inject self-parent to simulate legacy corrupt data
        vstore.versions[cid2]["parent_commit"] = cid2
        vstore._save()

        dag_status = vstore.validate_dag_integrity()
        assert dag_status["is_valid"] is False
        assert dag_status["self_parent_count"] == 1

        # Repair DAG
        repair_res = vstore.repair_dag()
        assert repair_res["repaired_self_parents"] == 1
        assert repair_res["valid_after_repair"] is True
        assert vstore.validate_dag_integrity()["is_valid"] is True


def test_version_dag_cycle_detection():
    """
    Test cycle detection in commit DAG (CMT-A -> CMT-B -> CMT-A).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        vstore = ContextVersionStore(data_dir)

        c1 = vstore.create_commit("A", [], [], "s", "sess", parent_commit=None)
        c2 = vstore.create_commit("B", [], [], "s", "sess", parent_commit=c1["commit_id"])

        # Inject cycle: c1 parent points to c2
        vstore.versions[c1["commit_id"]]["parent_commit"] = c2["commit_id"]
        vstore._save()

        dag_status = vstore.validate_dag_integrity()
        assert dag_status["has_cycle"] is True
        assert dag_status["is_valid"] is False

        # Repair cycle
        repair_res = vstore.repair_dag()
        assert repair_res["valid_after_repair"] is True
