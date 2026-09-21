import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from ..codecs.heterogeneous_compiler import HeterogeneousPacketCompiler
from ..codecs.ncc_vcl import NCCVCLCodec
from ..codecs.structured_text import StructuredTextCodec

class ShadowTester:
    """
    Background Shadow Testing & Counterfactual Replay Engine.
    Delivers production packet A synchronously to Codex, while evaluating
    shadow candidates B, C, D asynchronously in the background.
    """
    SHADOW_CANDIDATES = ["hybrid_packet", "ncc_vcl", "structured_text", "json_schema"]

    def __init__(self, data_dir: Path, filename: str = "shadow_results.jsonl"):
        self.file_path = data_dir / filename
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def run_shadow_eval(
        self,
        turn_id: str,
        prompt: str,
        assertions: List[Dict[str, Any]],
        invariants: List[str],
        production_strategy: str,
        production_token_count: int
    ) -> List[Dict[str, Any]]:
        shadow_records = []

        for candidate in self.SHADOW_CANDIDATES:
            if candidate == production_strategy:
                continue

            t0 = time.time()
            if candidate == "hybrid_packet":
                text, checksum = HeterogeneousPacketCompiler.compile_packet(assertions, invariants)
            elif candidate == "ncc_vcl":
                text, checksum = NCCVCLCodec.encode_packet(assertions, invariants)
            else:
                text, checksum = StructuredTextCodec.encode_packet(assertions, invariants)
            t1 = time.time()

            shadow_tokens = max(1, len(text) // 4)
            prep_ms = round((t1 - t0) * 1000, 2)
            token_diff = production_token_count - shadow_tokens

            record = {
                "turn_id": turn_id,
                "timestamp": time.time(),
                "production_strategy": production_strategy,
                "shadow_candidate": candidate,
                "shadow_tokens": shadow_tokens,
                "token_diff_vs_prod": token_diff,
                "shadow_prep_ms": prep_ms,
                "checksum": checksum
            }

            shadow_records.append(record)
            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")

        return shadow_records

class CounterfactualReplayEngine:
    """
    Counterfactual Replay Engine.
    Saves real interaction turns and replays them asynchronously during idle compute periods.
    """
    def __init__(self, data_dir: Path, filename: str = "episodes.jsonl"):
        self.file_path = data_dir / filename
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def record_episode(self, turn_id: str, prompt: str, assertions: list, invariants: list, result: str):
        episode = {
            "turn_id": turn_id,
            "timestamp": time.time(),
            "prompt": prompt,
            "assertion_count": len(assertions),
            "invariant_count": len(invariants),
            "codex_result_summary": result[:200]
        }
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(episode) + "\n")

    def replay_episodes(self, shadow_tester: ShadowTester, limit: int = 10) -> int:
        if not self.file_path.exists():
            return 0

        replayed_count = 0
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    ep = json.loads(line)
                    shadow_tester.run_shadow_eval(
                        turn_id=f"REPLAY-{ep['turn_id']}",
                        prompt=ep["prompt"],
                        assertions=[],
                        invariants=[],
                        production_strategy="hybrid_packet",
                        production_token_count=100
                    )
                    replayed_count += 1
                    if replayed_count >= limit:
                        break
                except Exception:
                    continue
        return replayed_count
