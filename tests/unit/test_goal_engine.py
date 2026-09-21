import pytest
import tempfile
from pathlib import Path
from contextos.core.goals import GoalEngine

def test_goal_engine_lifecycle():
    with tempfile.TemporaryDirectory() as td:
        ge = GoalEngine(Path(td))
        
        # 1. Set goal for session-1
        goal = ge.set_active_goal(
            "Build authentication system",
            acceptance_criteria=["Implement login", "Implement logout", "Pass unit tests"],
            session_id="session-1"
        )
        assert goal["status"] == "IN_PROGRESS"
        assert len(goal["acceptance_criteria"]) == 3
        
        # Verify Session Isolation (session-2 should have no active goal yet)
        assert ge.get_active_goal(session_id="session-2") is None
        assert ge.get_active_goal(session_id="session-1")["goal_id"] == goal["goal_id"]

        # 2. Check initial stop evaluation (should return decision="block"!)
        eval1 = ge.evaluate_stop_condition("Done working", session_id="session-1")
        assert eval1["decision"] == "block"
        assert eval1["allow_stop"] is False
        assert "INCOMPLETE" in eval1["reason"]
        
        # 3. Simulate tool outputs with structured evidence parsing
        _, feedback = ge.record_checkpoint("pytest", {}, "36 passed in 0.20s", session_id="session-1")
        assert "36/36" in feedback or "verified" in feedback.lower()
        ge.verify_criterion("Implement login", "Login view added in auth.py", session_id="session-1")
        ge.verify_criterion("Implement logout", "Logout route added in auth.py", session_id="session-1")
        
        # 4. Re-evaluate stop condition (all satisfied -> return decision="allow"!)
        eval2 = ge.evaluate_stop_condition("Completed auth system", session_id="session-1")
        assert eval2["decision"] == "allow"
        assert eval2["allow_stop"] is True
        assert "fully verified" in eval2["reason"]

def test_subagent_goal_inheritance_and_concurrency():
    with tempfile.TemporaryDirectory() as td:
        ge = GoalEngine(Path(td))
        goal = ge.set_active_goal("Build Feature X", acceptance_criteria=["AC1"], session_id="sess-parent")
        
        # Test subagent goal inheritance
        subagent = ge.register_subagent("ResearchAgent", session_id="sess-parent", parent_agent_id="agent-001")
        assert subagent["inherited_goal_id"] == goal["goal_id"]
        
        # Test selective injection policy (non-eventful tool output returns None feedback)
        _, fb1 = ge.record_checkpoint("ls", {}, "file1.txt file2.txt", session_id="sess-parent")
        assert fb1 is None
        
        # Periodic 10th op triggers feedback injection
        for _ in range(9):
            _, fb_loop = ge.record_checkpoint("git_status", {}, "clean", session_id="sess-parent")
        assert fb_loop is not None
        assert "Goal 'Build Feature X'" in fb_loop


