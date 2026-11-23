"""Regression: GoalEngine read-modify-write must be atomic across processes."""
import multiprocessing
import tempfile
from pathlib import Path

from contextos.core.goals import GoalEngine


def _worker(data_dir, worker, n):
    ge = GoalEngine(Path(data_dir))
    for i in range(n):
        ge.set_active_goal(f"goal {worker}-{i}", session_id=f"s{worker}-{i}")


def test_concurrent_processes_do_not_lose_goals():
    workers, per = 4, 25
    with tempfile.TemporaryDirectory() as td:
        ctx = multiprocessing.get_context("fork")
        procs = [ctx.Process(target=_worker, args=(td, w, per)) for w in range(workers)]
        for p in procs:
            p.start()
        for p in procs:
            p.join(60)
            assert p.exitcode == 0
        goals = GoalEngine(Path(td)).data["goals"]
        assert len(goals) == workers * per
