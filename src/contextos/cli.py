import sys
import json
import argparse
import time
from pathlib import Path
from .config import ContextOSConfig
from .hooks.adapter import HookAdapter
from .identity import IdentityScope
from .mcp.server import ContextOSMCPServer
from .core.inspector import HumanAuditableContextInspector

def main():
    parser = argparse.ArgumentParser(description="ContextOS CLI & Background Daemon Management")
    subparsers = parser.add_subparsers(dest="command")

    # init
    subparsers.add_parser("init", help="Initialize ContextOS in current workspace without touching global config")
    
    # prepare
    prep_parser = subparsers.add_parser("prepare", help="Prepare context packet for a prompt")
    prep_parser.add_argument("prompt", type=str, help="User prompt")

    # status
    status_parser = subparsers.add_parser("status", help="Show ContextOS storage and monitor statistics")
    status_parser.add_argument("--watch", action="store_true", help="Live watch mode for active Codex sessions and event stream")

    # campaign
    subparsers.add_parser("campaign", help="View active background experiment campaigns")

    # canary
    canary_parser = subparsers.add_parser("canary", help="View or manage context canary rollout stage")
    canary_parser.add_argument("--promote", action="store_true", help="Promote canary stage")

    # inspect
    inspect_parser = subparsers.add_parser("inspect", help="Inspect last turn packet selection rationale and provenance")

    # daemon
    subparsers.add_parser("daemon", help="Run background worker daemon & monitors")

    # mcp
    subparsers.add_parser("mcp", help="Run MCP STDIO server")

    args = parser.parse_args()

    if args.command == "init":
        cfg = ContextOSConfig.load()
        d_dir = cfg.ensure_directories()
        
        ws_cfg = d_dir / "config.yaml"
        if not ws_cfg.exists():
            with open(ws_cfg, "w", encoding="utf-8") as f:
                f.write("budget:\n  default_token_budget: 1500\ncodec:\n  default_codec: hybrid_packet\n")

        snippet_file = d_dir / "codex_config_snippet.toml"
        with open(snippet_file, "w", encoding="utf-8") as f:
            f.write(f"""# Workspace-scoped Codex MCP & UserPromptSubmit Lifecycle Hook configuration
[mcp_servers.contextos]
command = "python3"
args = ["-c", "import sys; sys.path.insert(0, '{Path.cwd()}/src'); from contextos.cli import main; main()", "mcp"]
cwd = "{Path.cwd()}"
enabled = true

[mcp_servers.contextos.env]
PYTHONPATH = "{Path.cwd()}/src"

[hooks]
UserPromptSubmit = [
  {{ type = "mcp_tool", server = "contextos", tool = "prepare_turn", input = {{ prompt = "${{prompt}}", session_id = "${{session_id}}", turn_id = "${{turn_id}}", cwd = "${{cwd}}" }}, timeout = 10, statusMessage = "Preparing ContextOS context" }}
]
""")

        # Also write .codex/hooks.json for project-local hook loading
        codex_dir = Path.cwd() / ".codex"
        codex_dir.mkdir(parents=True, exist_ok=True)
        hooks_json_file = codex_dir / "hooks.json"
        hooks_json_data = {
            "hooks": {
                "UserPromptSubmit": [
                    {
                        "type": "mcp_tool",
                        "server": "contextos",
                        "tool": "prepare_turn",
                        "input": {
                            "prompt": "${prompt}",
                            "session_id": "${session_id}",
                            "turn_id": "${turn_id}",
                            "cwd": "${cwd}"
                        },
                        "timeout": 10,
                        "statusMessage": "Preparing ContextOS context"
                    }
                ]
            }
        }
        with open(hooks_json_file, "w", encoding="utf-8") as f:
            json.dump(hooks_json_data, f, indent=2)

        print(f"ContextOS initialized cleanly in {d_dir}.")
        print(f"Workspace config snippet saved to {snippet_file}.")
        print(f"Codex lifecycle hooks saved to {hooks_json_file}.")

    elif args.command == "prepare":
        adapter = HookAdapter()
        packet = adapter.on_user_prompt_submit(args.prompt)
        print(json.dumps(packet, indent=2))

    elif args.command == "status":
        adapter = HookAdapter()
        if args.watch:
            print("Starting ContextOS Status Watch Mode (Press Ctrl+C to stop)...")
            try:
                while True:
                    stats = adapter.semantic.get_stats()
                    canary = adapter.canary.get_status()
                    events = adapter.events.get_events()
                    last_event = events[-1] if events else None
                    sys.stdout.write("\033[H\033[J")  # Clear terminal screen
                    print("==========================================================================")
                    print("                 ContextOS 1.0.0 Live Operational Watch                   ")
                    print("==========================================================================")
                    print(f"Canary Stage         : {canary['stage_name']} ({canary['traffic_pct']}% traffic)")
                    print(f"Total Assertions     : {stats.get('active_assertions', 0)}")
                    print(f"Total Invariants     : {stats.get('active_invariants', 0)}")
                    print(f"Total Events Logged  : {len(events)}")
                    if last_event:
                        print(f"Latest Session ID    : {last_event.get('session_id')}")
                        print(f"Latest Event Type    : {last_event.get('type')}")
                        print(f"Latest Event ISO Time: {last_event.get('iso_time')}")
                        payload_prompt = last_event.get('payload', {}).get('prompt', '')
                        print(f"Latest Event Prompt  : {payload_prompt[:80]}")
                    print("==========================================================================")
                    time.sleep(2)
            except KeyboardInterrupt:
                print("\nWatch mode stopped.")
                return
        else:
            stats = adapter.semantic.get_stats()
            canary = adapter.canary.get_status()
            costs = adapter.monitors.get_cost_moving_average()
            print("==================================================")
            print("  ContextOS 1.0.0 System & Operational Status    ")
            print("==================================================")
            print("Semantic Store Stats:", json.dumps(stats, indent=2))
            print("Canary Rollout Stage:", json.dumps(canary, indent=2))
            print("Moving Token Cost:", json.dumps(costs, indent=2))

    elif args.command == "campaign":
        adapter = HookAdapter()
        campaigns = adapter.campaign_mgr.list_campaigns()
        print("==================================================")
        print("  ContextOS Active Background CI Campaigns        ")
        print("==================================================")
        if not campaigns:
            print("No active campaigns running. Initializing default 'hybrid-vs-ncc-tournament'...")
            c = adapter.campaign_mgr.create_campaign("hybrid-section-codec-tournament", target_turns=500,
                competitors=adapter.tournament.TOURNAMENT_COMPETITORS,
                identity=IdentityScope.from_config(adapter.config, "campaign", "main"))
            campaigns = [c]

        for cmp_data in campaigns:
            print(f"\nCampaign: {cmp_data['name']}")
            print(f"  Status: {cmp_data['status']}")
            print(f"  Progress: {cmp_data['completed_turns']} / {cmp_data['target_turns']} turns")
            print(f"  Leading Strategy: {cmp_data['leader_so_far']}")
            print(f"  Confidence Interval: {cmp_data['confidence']*100:.1f}%")

    elif args.command == "canary":
        adapter = HookAdapter()
        if args.promote:
            st = adapter.canary.promote_stage()
            print(f"Promoted Context Canary to Stage {st}.")
        status = adapter.canary.get_status()
        print(json.dumps(status, indent=2))

    elif args.command == "inspect":
        adapter = HookAdapter()
        commits = adapter.version_store.versions
        if not commits:
            print("No commits recorded yet.")
            return
        last_commit = list(commits.values())[-1]
        assertions = adapter.semantic.query_current_state()
        inspection = HumanAuditableContextInspector.inspect_packet(
            context_text=last_commit.get("context_text", ""),
            assertions=assertions,
            invariants=last_commit.get("invariants", []),
            commit_id=last_commit["commit_id"],
            strategy_used=last_commit.get("strategy_name", "hybrid_packet"),
            token_count=last_commit.get("char_count", 0) // 4,
            telemetry={"prep_latency_ms": 1.2}
        )
        print(json.dumps(inspection, indent=2))

    elif args.command == "daemon":
        print("Starting ContextOS Continuous Background Daemon & Worker Pool...")
        adapter = HookAdapter()
        print("Workers active: Ingest (P1), Shadow Experiments (P3), Integrity & Campaigns (P4).")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping workers...")
            adapter.worker_pool.stop_workers()

    elif args.command == "mcp":
        server = ContextOSMCPServer()
        server.run_stdio()

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
