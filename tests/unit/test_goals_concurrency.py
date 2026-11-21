import json
import multiprocessing as mp

from contextos.core.goals import GoalEngine


def _worker(path, i):
    eng = GoalEngine(path)
    for n in range(15):
        eng.set_active_goal(f"goal {i}-{n}", session_id=f"s{i}-{n}")


def test_concurrent_processes_do_not_lose_goals(tmp_path):
    procs = [mp.Process(target=_worker, args=(tmp_path, i)) for i in range(4)]
    for p in procs:
        p.start()
    for p in procs:
        p.join()
    goals = json.loads((tmp_path / "goals.json").read_text())["goals"]
    assert len(goals) == 60


def test_corrupt_goals_file_is_preserved(tmp_path):
    (tmp_path / "goals.json").write_text("{not json")
    eng = GoalEngine(tmp_path)
    eng.set_active_goal("g")
    backups = [p for p in tmp_path.iterdir() if "corrupt" in p.name]
    assert backups and backups[0].read_text() == "{not json"
