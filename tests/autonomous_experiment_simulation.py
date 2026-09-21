import json
from contextos.config import ContextOSConfig
from contextos.hooks.adapter import HookAdapter

def run_simulation():
    print("======================================================================")
    print("  ContextOS Autonomous Strategy Experimentation & Self-Healing Test   ")
    print("======================================================================")

    config = ContextOSConfig.load()
    adapter = HookAdapter(config=config)

    # 1. Seed store
    adapter.semantic.add_assertion("A-D10", "Database", "uses", "PostgreSQL", kind="decision")
    adapter.semantic.add_assertion("A-INV2", "Security", "must_not", "disable_tls", kind="invariant")

    # 2. Simulate 10 consecutive turns across different user prompt requests
    parent_commit = None
    prompts = [
        "How is PostgreSQL connected in Database?",
        "Check security TLS configuration rules.",
        "Add new endpoint for user profile retrieval.",
        "Refactor authentication middleware module.",
        "Why is database connection pooling enabled?",
        "Fix bug in JWT token parsing function.",
        "What is the maximum database connection pool size?",
        "Explain security TLS enforcement across microservices.",
        "Implement rate limiting middleware on API gateway.",
        "Optimize vector search retrieval cascade latency."
    ]

    print("\nSimulating 10 Autonomous Turns...")
    print(f"{'Turn':<6} | {'Strategy':<16} | {'Codec':<16} | {'Tokens Saved':<12} | {'Pareto Score':<12} | {'Commit ID':<14}")
    print("-" * 85)

    for i, p in enumerate(prompts):
        res = adapter.on_user_prompt_submit(p, session_id="auto-sim-01", parent_commit=parent_commit)
        parent_commit = res["commit_id"]

        print(f"{i+1:<6} | {res['strategy_used']:<16} | {res['codec_used']:<16} | {res['quota_impact']['tokens_saved']:<12} | {res['quota_impact']['pareto_score']:<12} | {res['commit_id']:<14}")

    # 3. View cumulative strategy scoring breakdown
    scores = adapter.experimenter.get_strategy_scores()
    print("\n----------------------------------------------------------------------")
    print("  Cumulative Quota & Pareto Efficiency Strategy Ranking")
    print("----------------------------------------------------------------------")
    print(json.dumps(scores, indent=2))

    # 4. Verify Versioning & Incident Log
    commits_count = len(adapter.version_store.versions)
    incidents_count = len(adapter.self_healing.incident_log)
    print(f"\nTotal Keyframe Commits Versioned: {commits_count}")
    print(f"Total Self-Healing Incidents Recovered: {incidents_count}")
    print("======================================================================")

if __name__ == "__main__":
    run_simulation()
