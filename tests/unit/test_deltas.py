import pytest
from contextos.core.deltas import DifferentialKeyframeEngine

def test_differential_keyframe_delta_roundtrip():
    engine = DifferentialKeyframeEngine(max_chain_length=5)
    
    base_assertions = [
        {"id": "A-T7", "kind": "state", "subject": "T7", "predicate": "status", "object": "ACT"},
        {"id": "A-C4", "kind": "state", "subject": "C4", "predicate": "mode", "object": "soft"},
        {"id": "A-Q9", "kind": "state", "subject": "Q9", "predicate": "state", "object": "OPEN"}
    ]
    base_invariants = ["NO_GLOBAL_MUTATION"]
    
    curr_assertions = [
        {"id": "A-T7", "kind": "state", "subject": "T7", "predicate": "status", "object": "DONE"},
        {"id": "A-C4", "kind": "state", "subject": "C4", "predicate": "mode", "object": "hard"},
        {"id": "A-D31", "kind": "state", "subject": "D31", "predicate": "added", "object": "true"},
        {"id": "A-Q9", "kind": "state", "subject": "Q9", "predicate": "state", "object": "RES"}
    ]
    curr_invariants = ["NO_GLOBAL_MUTATION", "ENFORCE_CHECKSUM"]
    
    delta = engine.generate_delta(
        base_commit_id="CMT-82A91",
        base_assertions=base_assertions,
        base_invariants=base_invariants,
        current_assertions=curr_assertions,
        current_invariants=curr_invariants,
        chain_length=1
    )
    
    assert delta["rebased"] is False
    assert "@BASE CMT-82A91" in delta["packet_text"]
    assert "@Δ" in delta["packet_text"]
    assert "~A-T7:object ACT→DONE" in delta["packet_text"]
    assert "+INV:ENFORCE_CHECKSUM" in delta["packet_text"]
    
    # Reconstruct
    rec_a, rec_i, ok = engine.apply_delta(base_assertions, base_invariants, delta["packet_text"])
    assert ok is True
    assert rec_i == curr_invariants
    t7_item = next(a for a in rec_a if a.get("id") == "A-T7")
    assert t7_item["object"] == "DONE"

def test_differential_keyframe_max_chain_rebase():
    engine = DifferentialKeyframeEngine(max_chain_length=3)
    
    base_assertions = [{"id": "A-S1", "kind": "state", "subject": "S1", "predicate": "v", "object": "1"}]
    base_invariants = ["INV1"]
    curr_assertions = [{"id": "A-S1", "kind": "state", "subject": "S1", "predicate": "v", "object": "2"}]
    curr_invariants = ["INV1"]
    
    delta = engine.generate_delta(
        base_commit_id="CMT-111",
        base_assertions=base_assertions,
        base_invariants=base_invariants,
        current_assertions=curr_assertions,
        current_invariants=curr_invariants,
        chain_length=4
    )
    
    assert delta["rebased"] is True
    assert delta["reason"] == "max_chain_length_exceeded"
    assert delta["packet_text"] is None
