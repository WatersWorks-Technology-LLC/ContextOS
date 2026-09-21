import json
from pathlib import Path
from contextos.hooks.adapter import HookAdapter

def main():
    print("=== LIVE END-TO-END CODEX LIFECYCLE CHAIN TEST ===")
    data_dir = Path("/Users/watersworksbackend/Downloads/ContextOS_Documentation/.contextos")
    adapter = HookAdapter()

    sess_a = "session-e2e-a"
    sess_b = "session-e2e-b"

    # Step 1: Session Hydration
    print("\n1. Hydrating Session A...")
    start_res = adapter.on_session_start(session_id=sess_a)
    print("Hydrated Context:\n", start_res["additionalContext"])

    # Step 2: Establish Goal
    print("\n2. Submitting User Prompt with Goal...")
    prompt = "/goal Build authenticating API with 3 criteria: 1. Implement auth handler 2. Run unit tests 3. Document endpoint"
    turn_res = adapter.on_user_prompt_submit(prompt, session_id=sess_a)
    print("Turn Context Prepared (Token Count):", turn_res["token_count"])

    # Step 3: Run Routine Tool (ls) -> Selective Injection (Expect Empty Dict)
    print("\n3. PostToolUse for 'ls' (routine tool)...")
    post_ls = adapter.on_post_tool_use("ls", {"path": "."}, "file1.py file2.py", session_id=sess_a)
    print("PostToolUse 'ls' Feedback (Selective Injection):", post_ls)
    assert post_ls == {}, "Routine tool should not inject redundant context"

    # Step 4: Run Test Tool -> Empirical Evidence Captured & State Changed -> Injects Feedback
    print("\n4. PostToolUse for 'pytest' (Clean Test Evidence)...")
    post_test = adapter.on_post_tool_use("pytest", {"cmd": "pytest"}, "38 passed in 0.26s", session_id=sess_a)
    print("PostToolUse 'pytest' Feedback:\n", post_test.get("additionalContext"))
    assert "additionalContext" in post_test, "State change MUST inject updated context feedback"

    # Step 5: Test Subagent Inheritance
    print("\n5. Subagent Start (Subagent A inherits Parent Goal)...")
    sub_res = adapter.on_subagent_start("SecurityAuditor", "Audit auth handler", session_id=sess_a, parent_agent_id="agent-main")
    print("Subagent Context:\n", sub_res["additionalContext"][:250])
    assert "Inherited Session Goal" in sub_res["additionalContext"]

    # Step 6: Test Stop Hook Evaluation (Incomplete Goal -> Block Decision)
    print("\n6. Codex Stop Hook Attempt (Incomplete Goal)...")
    stop_incomplete = adapter.on_stop("Done with initial work", session_id=sess_a)
    print("Stop Hook Decision (Incomplete):", stop_incomplete["decision"])
    print("Stop Hook Reason:\n", stop_incomplete["reason"])
    assert stop_incomplete["decision"] == "block", "Incomplete goal MUST block stop!"

    # Step 7: Complete remaining criteria
    print("\n7. Verifying remaining criteria...")
    adapter.goals.verify_criterion("Implement auth handler", "auth.py added", session_id=sess_a)
    adapter.goals.verify_criterion("Document endpoint", "README updated", session_id=sess_a)

    # Step 8: Test Stop Hook Evaluation (Completed Goal -> Allow Decision)
    print("\n8. Codex Stop Hook Attempt (Fully Verified Goal)...")
    stop_complete = adapter.on_stop("Completed all criteria", session_id=sess_a)
    print("Stop Hook Result (Completed):", stop_complete)
    assert stop_complete["decision"] == "allow", "Completed goal MUST allow stop!"


    # Step 9: Verify Session B Isolation
    print("\n9. Session B Isolation Check...")
    goal_b = adapter.goals.get_active_goal(session_id=sess_b)
    print("Session B Active Goal:", goal_b)
    assert goal_b is None, "Session B must remain completely isolated from Session A"

    print("\n=== LIVE END-TO-END CHAIN TEST PASSED CLEANLY ===")

if __name__ == "__main__":
    main()
