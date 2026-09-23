import pytest
import tempfile
from pathlib import Path
from contextos.storage.source_store import SourceStore
from contextos.identity import IdentityScope
from contextos.core.provenance_audit import ProvenanceAuditor
from contextos.core.drift_audit import SemanticDriftAuditor

@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)

def test_unit_provenance_auditor_strict_rules(tmp_dir):
    ss = SourceStore(tmp_dir)
    sid = ss.put_source("Authentic evidence source snippet", identity=IdentityScope("codex", "workspace", "project", "session", "main"))
    auditor = ProvenanceAuditor(ss)

    assertions = [
        {"assertion_id": "A1", "subject": "AuthService", "kind": "decision", "source_ref": sid},
        {"assertion_id": "A2", "subject": "DB", "kind": "fact", "source_ref": sid}
    ]
    audit = auditor.audit_packet_provenance(assertions)
    assert audit["critical_provenance_ratio"] == 1.0
    assert audit["ordinary_provenance_ratio"] == 1.0
    assert audit["critical_passed"] is True
    assert audit["ordinary_passed"] is True

def test_unit_drift_auditor():
    current = [
        {"assertion_id": "A1", "subject": "AuthService", "predicate": "uses", "object": "OAuth2"},
        {"assertion_id": "A2", "subject": "PostgresDB", "predicate": "max_connections", "object": "100"}
    ]
    superseded = [
        {"assertion_id": "A0", "subject": "AuthService", "predicate": "uses", "object": "SessionTokens"}
    ]

    drift = SemanticDriftAuditor.audit_drift(current, superseded)
    assert drift["zero_drift_passed"] is True
    assert drift["drift_score"] == 1.0
