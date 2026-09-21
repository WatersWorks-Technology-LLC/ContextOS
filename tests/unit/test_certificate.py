import pytest
import tempfile
from pathlib import Path
from contextos.core.certificate import ReleaseCertificateManager

def test_export_all_evidence_reports():
    with tempfile.TemporaryDirectory() as td:
        data_dir = Path(td)
        mgr = ReleaseCertificateManager(data_dir=data_dir)

        canary_status = {"stage": 1, "stage_name": "5% Canary", "accumulated_fresh_turns": 100}
        provenance = {"critical_provenance_ratio": 1.0, "ordinary_provenance_ratio": 0.98}
        drift = {"drift_score": 1.0}
        incidents = []
        tournament_res = {"active_meta_strategy": "hybrid_packet", "section_codecs": {"@INV": "ncc_vcl"}}
        latencies = [2.1, 2.5, 3.2]

        cert = mgr.export_all_evidence_reports(
            canary_status=canary_status,
            provenance_audit=provenance,
            drift_audit=drift,
            incidents=incidents,
            tournament_res=tournament_res,
            latencies_ms=latencies,
            control_tokens=100000,
            contextos_tokens=1000,
            version="1.0-rc2"
        )

        assert (data_dir / "RELEASE_CERTIFICATE.json").exists()
        assert (data_dir / "FINAL_CANARY_REPORT.json").exists()
        assert (data_dir / "PROVENANCE_AUDIT.json").exists()
        assert (data_dir / "DRIFT_AUDIT.json").exists()
        assert (data_dir / "INCIDENT_SUMMARY.json").exists()
        assert (data_dir / "CODEC_TOURNAMENT.json").exists()
        assert (data_dir / "LATENCY_REPORT.json").exists()
        assert (data_dir / "TOKEN_EFFICIENCY.json").exists()
        assert not (data_dir / "CONTEXTOS_1.0.0_READY").exists()

def test_production_100_ready_flag():
    with tempfile.TemporaryDirectory() as td:
        data_dir = Path(td)
        mgr = ReleaseCertificateManager(data_dir=data_dir)

        canary_status_100 = {"stage": 5, "stage_name": "100% Production Default", "fresh_turns": 2000, "accumulated_fresh_turns": 3850}
        provenance = {"critical_provenance_ratio": 1.0, "ordinary_provenance_ratio": 0.98}
        drift = {"drift_score": 1.0}
        incidents = []
        tournament_res = {"active_meta_strategy": "hybrid_packet", "section_codecs": {"@INV": "ncc_vcl"}}
        latencies = [2.1, 2.5, 3.2]

        cert = mgr.export_all_evidence_reports(
            canary_status=canary_status_100,
            provenance_audit=provenance,
            drift_audit=drift,
            incidents=incidents,
            tournament_res=tournament_res,
            latencies_ms=latencies,
            control_tokens=100000,
            contextos_tokens=1000
        )

        assert cert["version"] == "1.0.0"
        assert (data_dir / "CONTEXTOS_1.0.0_READY").exists()
        assert mgr.is_production_100_ready() is True
