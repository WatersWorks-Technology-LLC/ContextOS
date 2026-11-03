import json
from contextos.core.certificate import ReleaseCertificateManager

READY = {"stage": 5, "fresh_turns": 2000, "accumulated_fresh_turns": 3850}
PROV = {"critical_provenance_ratio": 1.0, "ordinary_provenance_ratio": 1.0}
DRIFT = {"drift_score": 1.0}


def _export(mgr, latencies, canary=READY, version="1.0-rc2"):
    return mgr.export_all_evidence_reports(
        canary_status=canary, provenance_audit=PROV, drift_audit=DRIFT, incidents=[],
        tournament_res={}, latencies_ms=latencies, control_tokens=1000, contextos_tokens=100,
        version=version)


def test_no_latency_samples_cannot_pass_slo_or_issue_1_0_0(tmp_path):
    mgr = ReleaseCertificateManager(data_dir=tmp_path)
    cert = _export(mgr, [])
    report = json.loads((tmp_path / "LATENCY_REPORT.json").read_text())
    assert report["slo_compliance"] is False
    assert cert["version"] != "1.0.0"
    assert not mgr.is_production_100_ready()


def test_certificate_reports_actual_canary_observations(tmp_path):
    mgr = ReleaseCertificateManager(data_dir=tmp_path)
    canary = {"stage": 1, "accumulated_fresh_turns": 120, "fresh_turns": 20, "shadow_observations": 7}
    cert = _export(mgr, [1.0, 2.0], canary=canary)
    assert cert["canary_fresh_turns"] == 20
    assert cert["shadow_observations"] == 7
