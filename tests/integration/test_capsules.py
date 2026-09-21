import pytest
import tempfile
from pathlib import Path
from contextos.storage.semantic_store import SemanticStore
from contextos.storage.source_store import SourceStore
from contextos.core.capsules import ContextCapsuleManager

@pytest.fixture
def capsule_mgr():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td)
        sem = SemanticStore(p)
        src = SourceStore(p)
        sid = src.put_source("Primary source text evidence for AuthService")
        sem.add_assertion("A-AUTH", "AuthService", "uses", "OAuth2", kind="decision", source_ref=sid, decision_rationale="Stateless authentication requirement")
        yield ContextCapsuleManager(sem, src)

def test_integration_demand_paging_z0_to_z4(capsule_mgr):
    # Level 0 (Z0): Identity
    z0 = capsule_mgr.expand("AuthService", level=0)
    assert z0["payload"] == "ID:AuthService"

    # Level 1 (Z1): Current State
    z1 = capsule_mgr.expand("AuthService", level=1)
    assert z1["payload"]["subject"] == "AuthService"
    assert z1["payload"]["object"] == "OAuth2"

    # Level 3 (Z3): Detailed Capsule
    z3 = capsule_mgr.expand("AuthService", level=3)
    assert z3["payload"]["rationale"] == "Stateless authentication requirement"

    # Level 4 (Z4): Raw Evidence Bundle
    z4 = capsule_mgr.expand("AuthService", level=4)
    assert len(z4["payload"]["sources"]) >= 1
