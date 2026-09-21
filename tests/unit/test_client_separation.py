import pytest
import tempfile
from pathlib import Path
from contextos.config import ContextOSConfig
from contextos.hooks.adapter import HookAdapter

def test_client_id_directory_separation():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        
        # Load configs for Codex, Antigravity, and Claude Code
        cfg_codex = ContextOSConfig.load(workspace_dir=ws, client_id="codex")
        cfg_antigravity = ContextOSConfig.load(workspace_dir=ws, client_id="antigravity")
        cfg_claude = ContextOSConfig.load(workspace_dir=ws, client_id="claude_code")
        
        dir_codex = cfg_codex.ensure_directories()
        dir_antigravity = cfg_antigravity.ensure_directories()
        dir_claude = cfg_claude.ensure_directories()
        
        assert str(dir_codex).endswith(".contextos/clients/codex")
        assert str(dir_antigravity).endswith(".contextos/clients/antigravity")
        assert str(dir_claude).endswith(".contextos/clients/claude_code")
        
        # Initialize separate HookAdapters
        adapter_codex = HookAdapter(config=cfg_codex)
        adapter_antigravity = HookAdapter(config=cfg_antigravity)
        
        # Set goal in Codex
        adapter_codex.goals.set_active_goal("Codex Goal", session_id="sess-1")
        
        # Verify Antigravity sees NO goal from Codex
        assert adapter_antigravity.goals.get_active_goal(session_id="sess-1") is None
        assert adapter_codex.goals.get_active_goal(session_id="sess-1")["description"] == "Codex Goal"

def test_five_part_identity_key_and_subagent_isolation():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        cfg_codex = ContextOSConfig.load(workspace_dir=ws, client_id="codex")
        adapter_codex = HookAdapter(config=cfg_codex)
        
        # Identity 1: main agent
        key_main = adapter_codex.goals._get_identity_key("codex", "ws1", "proj1", "sess1", "main")
        # Identity 2: subagent research
        key_sub = adapter_codex.goals._get_identity_key("codex", "ws1", "proj1", "sess1", "subagent-research")
        
        assert key_main == "codex:ws1:proj1:sess1:main"
        assert key_sub == "codex:ws1:proj1:sess1:subagent-research"
        assert key_main != key_sub
        
        # Active goal set on main agent key
        adapter_codex.goals.set_active_goal("Main Goal", session_id="sess1", runtime_id="codex", workspace_id="ws1", project_id="proj1", agent_id="main")
        
        # Register subagent inheriting parent goal
        adapter_codex.goals.register_subagent(session_id="sess1", subagent_id="subagent-research", runtime_id="codex", workspace_id="ws1", project_id="proj1", parent_agent_id="main")
        
        sub_goal = adapter_codex.goals.get_active_goal(session_id="sess1", runtime_id="codex", workspace_id="ws1", project_id="proj1", agent_id="subagent-research")
        assert sub_goal is not None
        assert sub_goal["description"] == "Main Goal"

def test_multi_runtime_shared_knowledge_and_transient_isolation():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        cfg_codex = ContextOSConfig.load(workspace_dir=ws, client_id="codex")
        cfg_antigravity = ContextOSConfig.load(workspace_dir=ws, client_id="antigravity")
        cfg_claude = ContextOSConfig.load(workspace_dir=ws, client_id="claude_code")
        
        adapter_codex = HookAdapter(config=cfg_codex)
        adapter_antigravity = HookAdapter(config=cfg_antigravity)
        adapter_claude = HookAdapter(config=cfg_claude)
        
        # 1. Add shared project fact directly to shared store
        adapter_codex.shared_semantic.add_assertion(
            assertion_id="AST-SHARED-1",
            subject="DatabaseSchema",
            predicate="uses",
            object_val="PostgreSQL 16",
            scope="project",
            producer_runtime="codex"
        )
        
        # 2. Add local transient/session assertion to Codex store
        adapter_codex.semantic.add_assertion(
            assertion_id="AST-CODEX-LOCAL-1",
            subject="CodexScratchpad",
            predicate="status",
            object_val="running_tests",
            scope="session",
            runtime_id="codex"
        )
        
        # Codex retrieval queries both shared and local
        res_codex = adapter_codex.retrieval.retrieve("DatabaseSchema CodexScratchpad", runtime_id="codex")
        codex_ast_ids = {a["assertion_id"] for a in res_codex["assertions"]}
        assert "AST-SHARED-1" in codex_ast_ids
        assert "AST-CODEX-LOCAL-1" in codex_ast_ids
        
        # Antigravity retrieval sees shared truth, but NOT Codex local transient state
        res_anti = adapter_antigravity.retrieval.retrieve("DatabaseSchema PostgreSQL", runtime_id="antigravity")
        anti_ast_ids = {a["assertion_id"] for a in res_anti["assertions"]}
        assert "AST-SHARED-1" in anti_ast_ids
        assert "AST-CODEX-LOCAL-1" not in anti_ast_ids

def test_assertion_promotion_and_supersession():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        cfg = ContextOSConfig.load(workspace_dir=ws, client_id="codex")
        adapter = HookAdapter(config=cfg)
        
        # 1. Local session assertion
        ast_id = adapter.semantic.add_assertion(
            assertion_id="AST-LOCAL-FACT",
            subject="APIEndpoint",
            predicate="status",
            object_val="v1_deprecated",
            scope="session",
            runtime_id="codex"
        )
        
        # 2. Promote to project scope in shared semantic store
        promoted_id = adapter.shared_semantic.add_assertion(
            assertion_id="AST-PROJECT-FACT-1",
            subject="APIEndpoint",
            predicate="status",
            object_val="v2_active",
            scope="project",
            producer_runtime="codex",
            origin_assertion_id=ast_id
        )
        
        # 3. Supersede old fact
        adapter.shared_semantic.supersede_assertion(old_assertion_id=ast_id, new_assertion_id=promoted_id)
        
        current_shared = adapter.shared_semantic.query_current_state()
        shared_ids = [a["assertion_id"] for a in current_shared]
        assert promoted_id in shared_ids
        assert ast_id not in shared_ids

