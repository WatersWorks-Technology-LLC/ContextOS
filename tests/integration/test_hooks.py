import pytest
import time
import tempfile
from pathlib import Path
from contextos.config import ContextOSConfig
from contextos.hooks.adapter import HookAdapter

@pytest.fixture
def tmp_config():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        cfg = ContextOSConfig(workspace_dir=Path(td))
        yield cfg
        import gc
        gc.collect()

def test_integration_hook_prompt_submit(tmp_config):
    adapter = HookAdapter(config=tmp_config)
    adapter.semantic.add_assertion("A1", "DB", "timeout", "30s", kind="constraint")

    res = adapter.on_user_prompt_submit("How is DB timeout configured?")
    assert "additionalContext" in res
    assert "telemetry" in res
    assert res["metrics"]["is_verified"] is True

def test_integration_hook_post_tool_use(tmp_config):
    adapter = HookAdapter(config=tmp_config)
    adapter.on_post_tool_use("git_status", {}, "On branch main. Nothing to commit.")
    time.sleep(0.05)  # Wait for async background worker queue to complete

    events = adapter.events.get_events()
    assert len(events) == 1
    assert events[0]["type"] == "PostToolUse"
