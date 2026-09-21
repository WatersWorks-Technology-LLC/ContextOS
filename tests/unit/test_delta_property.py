import random
import pytest
from contextos.core.deltas import DifferentialKeyframeEngine

def generate_random_assertion(index: int) -> dict:
    kinds = ["fact", "decision", "state", "flag"]
    subjects = ["AuthService", "PostgresDB", "APIGateway", "WorkerPool", "CacheEngine"]
    predicates = ["status", "mode", "version", "pool_size", "active"]
    objects = ["active", "1.2.0", "100", "true", "false", "hard", "soft"]
    
    return {
        "id": f"A-{index:04d}",
        "kind": random.choice(kinds),
        "subject": random.choice(subjects),
        "predicate": random.choice(predicates),
        "object": random.choice(objects)
    }

def test_randomized_delta_chain_property():
    engine = DifferentialKeyframeEngine(max_chain_length=50)
    random.seed(42)

    # Base state S0
    curr_assertions = [generate_random_assertion(i) for i in range(1, 20)]
    curr_invariants = ["INV_SAFETY_1", "INV_SAFETY_2"]
    
    base_assertions = [dict(a) for a in curr_assertions]
    base_invariants = list(curr_invariants)

    chain_assertions = [base_assertions]
    chain_invariants = [base_invariants]

    for step in range(1, 21):
        prev_a = chain_assertions[-1]
        prev_i = chain_invariants[-1]

        next_a = [dict(a) for a in prev_a]
        for _ in range(2):
            if next_a:
                item = random.choice(next_a)
                item["object"] = f"val-{step}"
        next_a.append(generate_random_assertion(20 + step))
        if len(next_a) > 5:
            next_a.pop(0)

        next_i = list(prev_i)
        if step % 5 == 0:
            next_i.append(f"INV_STEP_{step}")

        delta_res = engine.generate_delta(
            base_commit_id=f"CMT-STEP{step-1}",
            base_assertions=prev_a,
            base_invariants=prev_i,
            current_assertions=next_a,
            current_invariants=next_i,
            chain_length=step
        )

        assert delta_res["rebased"] is False
        chain_assertions.append(next_a)
        chain_invariants.append(next_i)

        rec_a, rec_i, ok = engine.apply_delta(prev_a, prev_i, delta_res["packet_text"])
        assert ok is True
        assert engine.hash_state(rec_a, rec_i) == engine.hash_state(next_a, next_i)


def test_delta_fuzzing_fail_closed_property():
    engine = DifferentialKeyframeEngine()
    
    base_a = [{"id": "A1", "kind": "state", "subject": "S", "predicate": "p", "object": "1"}]
    base_i = ["INV1"]
    curr_a = [
        {"id": "A1", "kind": "state", "subject": "S", "predicate": "p", "object": "2"},
        {"id": "A2", "kind": "state", "subject": "S2", "predicate": "p2", "object": "v2"}
    ]
    curr_i = ["INV1"]

    delta_res = engine.generate_delta("CMT-1", base_a, base_i, curr_a, curr_i)
    valid_packet = delta_res["packet_text"]

    # 1. Corrupt Checksum -> Must fail closed
    corrupt_checksum_packet = valid_packet.replace("@CHECKSUM ", "@CHECKSUM BAD")
    _, _, ok1 = engine.apply_delta(base_a, base_i, corrupt_checksum_packet)
    assert ok1 is False

    # 2. Corrupt Content Line -> Must fail closed
    corrupt_content_packet = valid_packet.replace("~A1:object 1→2", "~A1:object 1→999")
    _, _, ok2 = engine.apply_delta(base_a, base_i, corrupt_content_packet)
    assert ok2 is False

    # 3. Empty Packet -> Must fail closed
    _, _, ok3 = engine.apply_delta(base_a, base_i, "")
    assert ok3 is False

    # 4. Replay Delta on wrong base state containing extra assertion -> Must fail closed
    wrong_base_a = [
        {"id": "A1", "kind": "state", "subject": "S", "predicate": "p", "object": "1"},
        {"id": "A999", "kind": "state", "subject": "UNEXPECTED", "predicate": "p", "object": "bad"}
    ]
    _, _, ok4 = engine.apply_delta(wrong_base_a, base_i, valid_packet)
    assert ok4 is False
