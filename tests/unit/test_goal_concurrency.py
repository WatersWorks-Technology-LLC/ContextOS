import json
import multiprocessing
from pathlib import Path

from contextos.core.goals import GoalEngine


def _set_goal(data_dir, n):
    GoalEngine(Path(data_dir)).set_active_goal(f"goal {n}", session_id=f"s{n}")


def test_concurrent_processes_do_not_lose_goals(tmp_path):
    GoalEngine(tmp_path)
    ctx = multiprocessing.get_context("fork")
    procs = [ctx.Process(target=_set_goal, args=(str(tmp_path), i)) for i in range(8)]
    for p in procs:
        p.start()
    for p in procs:
        p.join()
    assert len(GoalEngine(tmp_path).data["goals"]) == 8


def test_stale_instance_does_not_drop_other_instances_goal(tmp_path):
    a, b = GoalEngine(tmp_path), GoalEngine(tmp_path)
    a.set_active_goal("one", session_id="s1")
    b.set_active_goal("two", session_id="s2")
    assert len(GoalEngine(tmp_path).data["goals"]) == 2


def test_corrupt_goals_file_is_quarantined_not_overwritten(tmp_path):
    (tmp_path / "goals.json").write_text("{not json")
    GoalEngine(tmp_path).set_active_goal("x", session_id="s1")
    assert any(p.name.startswith("goals.json.corrupt-") for p in tmp_path.iterdir())
    assert json.loads((tmp_path / "goals.json").read_text())["goals"]
