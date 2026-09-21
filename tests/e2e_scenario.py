import json
import time
from contextos.config import ContextOSConfig
from contextos.hooks.adapter import HookAdapter
from contextos.mcp.server import ContextOSMCPServer

def run_e2e_scenario():
    print("==================================================")
    print("  ContextOS End-to-End Scientific Integration Test ")
    print("==================================================")

    # 1. Initialize clean test setup
    config = ContextOSConfig.load()
    adapter = HookAdapter(config=config)
    mcp = ContextOSMCPServer(adapter=adapter)

    # 2. Seed memory store with architectural decisions and constraints
    print("\n[Step 1] Seeding Semantic Memory Store...")
    adapter.semantic.add_entity("E-AUTH", "AuthService", "service")
    adapter.semantic.add_entity("E-DB", "PostgresDB", "database")

    # Historical decision (D01)
    a1 = adapter.semantic.add_assertion(
        "A-D01", "AuthService", "uses", "SessionTokens",
        kind="decision", entity_id="E-AUTH", status="current"
    )
    # New decision (D02) supersedes D01
    a2 = adapter.semantic.add_assertion(
        "A-D02", "AuthService", "uses", "JWT_OAuth2",
        kind="decision", entity_id="E-AUTH", status="current"
    )
    adapter.semantic.supersede_assertion("A-D01", "A-D02")

    # Hard Invariant
    adapter.semantic.add_assertion(
        "A-INV1", "AuthService", "must_not", "store_plaintext_passwords",
        kind="invariant", entity_id="E-AUTH", status="current"
    )

    # Fact
    adapter.semantic.add_assertion(
        "A-F01", "PostgresDB", "max_connections", "100",
        kind="fact", entity_id="E-DB", status="current"
    )

    print("Memory Seeded Successfully!")
    print("Storage Stats:", json.dumps(adapter.semantic.get_stats(), indent=2))

    # 3. Simulate User Turn 1: User asks about AuthService protocol
    print("\n[Step 2] Testing Pre-Turn Context Compilation (UserTurn 1)...")
    prompt1 = "How is user authentication implemented in AuthService?"
    t0 = time.time()
    packet1 = adapter.on_user_prompt_submit(prompt1, session_id="sess-101")
    t1 = time.time()

    print(f"Preparation Latency: {packet1['metrics']['prep_latency_ms']} ms")
    print(f"Round-trip Verified: {packet1['metrics']['is_verified']}")
    print(f"Delivered Token Count: {packet1['token_count']}")
    print("\nInjected Context Packet Preview:")
    print("--------------------------------------------------")
    print(packet1["additionalContext"])
    print("--------------------------------------------------")

    # Check temporal supersession check: A-D01 (SessionTokens) should NOT be in current active context!
    assert "JWT_OAuth2" in packet1["additionalContext"]
    assert "SessionTokens" not in packet1["additionalContext"]
    assert "store_plaintext_passwords" in packet1["additionalContext"]
    print("✅ PASS: Current state active, superseded D01 correctly omitted!")

    # 4. Simulate PostToolUse observation
    print("\n[Step 3] Testing PostToolUse Event Ingestion...")
    adapter.on_post_tool_use("read_file", {"path": "src/auth.py"}, "class AuthService:\n    def login(self): pass", session_id="sess-101")
    events = adapter.events.get_events(session_id="sess-101")
    print(f"Recorded Event Count for session sess-101: {len(events)}")
    assert len(events) >= 2  # UserPromptSubmit + PostToolUse
    print("✅ PASS: PostToolUse event appended losslessly!")

    # 5. Simulate MCP Tool Calls
    print("\n[Step 4] Testing MCP STDIO Server Interface...")
    mcp_resp = mcp.handle_request({
        "jsonrpc": "2.0",
        "id": 42,
        "method": "tools/call",
        "params": {
            "name": "query",
            "arguments": {"query": "PostgresDB", "mode": "search"}
        }
    })
    res_text = mcp_resp["result"]["content"][0]["text"]
    res_data = json.loads(res_text)
    print("MCP Query Result:", json.dumps(res_data, indent=2))
    assert len(res_data) >= 1
    assert res_data[0]["subject"] == "PostgresDB"
    print("✅ PASS: MCP STDIO Server query returned valid assertion!")

    print("\n==================================================")
    print("  ALL E2E INTEGRATION TESTS PASSED SUCCESSFULLY! ")
    print("==================================================")

if __name__ == "__main__":
    run_e2e_scenario()
