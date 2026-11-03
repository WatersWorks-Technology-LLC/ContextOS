import json

from contextos.core.shadow_experimenter import CounterfactualReplayEngine, ShadowTester
from contextos.identity import IdentityScope


def _ident(project):
    return IdentityScope("codex", "ws", project, "s1")


def test_replay_only_replays_callers_own_episodes(tmp_path):
    engine = CounterfactualReplayEngine(tmp_path)
    tester = ShadowTester(tmp_path)
    engine.record_episode("T-A", "prompt a", [], [], "ok", identity=_ident("proj_a"))
    engine.record_episode("T-B", "prompt b", [], [], "ok", identity=_ident("proj_b"))

    assert engine.replay_episodes(tester, identity=_ident("proj_a")) == 1

    records = [json.loads(l) for l in tester.file_path.read_text().splitlines()]
    assert records
    assert {r["turn_id"] for r in records} == {"REPLAY-T-A"}
