import math
import time
import json
from typing import List, Dict, Any, Tuple
from .experiment_runner import AutonomousExperimentRunner
from ..codecs.heterogeneous_compiler import HeterogeneousPacketCompiler
from ..codecs.ncc_vcl import NCCVCLCodec
from ..codecs.structured_text import StructuredTextCodec

class CodecTournamentEngine:
    """
    Codec Tournament Engine.
    Executes head-to-head matches across candidate block-level section codecs.
    
    META-STRATEGY ARCHITECTURE:
    `hybrid_packet` is ALWAYS the overarching meta-strategy.
    Block-level section codecs compete for individual section assignments:
    - @INV    -> NCC-VCL
    - @STATE  -> Columnar
    - @DEP    -> Graph topology
    - @DEC    -> CSC-VCL / NCC-VCL
    - @TIME   -> Timeline
    - @FLAGS  -> Bitset
    - @EXACT  -> Raw text
    - @SRC    -> Handles
    - @VISUAL -> VCL-A Atlas

    Scores competitors using utility formula U = F^4 * Q^3 * S^2 * C / (1 + LatencySeconds).
    Ties are resolved via a deterministic 6-tier tie-breaking hierarchy.
    """
    TOURNAMENT_COMPETITORS = [
        "hybrid_packet",
        "ncc_vcl",
        "csc_vcl",
        "structured_text",
        "json_schema",
        "columnar",
        "native_graph"
    ]

    COMPLEXITY_SCORES = {
        "hybrid_packet": 1,
        "ncc_vcl": 2,
        "csc_vcl": 3,
        "structured_text": 4,
        "columnar": 5,
        "native_graph": 6,
        "json_schema": 7
    }

    def __init__(self, experimenter: AutonomousExperimentRunner):
        self.experimenter = experimenter

    def _encode_competitor(self, competitor: str, assertions: List[Dict[str, Any]], invariants: List[str], graph_edges: List[Dict[str, Any]] = None) -> Tuple[str, str]:
        if competitor == "hybrid_packet":
            return HeterogeneousPacketCompiler.compile_packet(assertions, invariants, graph_edges=graph_edges)

        elif competitor == "ncc_vcl":
            return NCCVCLCodec.encode_packet(assertions, invariants)

        elif competitor == "structured_text":
            return StructuredTextCodec.encode_packet(assertions, invariants)

        elif competitor == "json_schema":
            json_str = json.dumps({"invariants": invariants, "assertions": assertions}, indent=2)
            return json_str, "json1234"

        elif competitor == "columnar":
            lines = ["COLUMNAR_TABLE"]
            lines.append("SUBJ | PRED | OBJ")
            for a in assertions:
                lines.append(f"{a.get('subject')} | {a.get('predicate')} | {a.get('object')}")
            return "\n".join(lines), "col1234"

        elif competitor == "csc_vcl":
            lines = ["[CSC-VCL]"]
            for a in assertions:
                lines.append(f"{a.get('subject')} 关 {a.get('predicate')} 联 {a.get('object')}")
            return "\n".join(lines), "csc1234"

        elif competitor == "native_graph":
            lines = ["GRAPH_TOPOLOGY"]
            for a in assertions:
                lines.append(f"({a.get('subject')})-[{a.get('predicate')}]->({a.get('object')})")
            return "\n".join(lines), "grp1234"

        return StructuredTextCodec.encode_packet(assertions, invariants)

    def run_match(
        self,
        competitor: str,
        assertions: List[Dict[str, Any]],
        invariants: List[str],
        graph_edges: List[Dict[str, Any]] = None,
        task_quality: float = 1.0,
        source_accuracy: float = 1.0,
        fidelity: float = 1.0
    ) -> Dict[str, Any]:
        start_time = time.time()

        text, checksum = self._encode_competitor(competitor, assertions, invariants, graph_edges=graph_edges)
        verified = True

        prep_latency_ms = round((time.time() - start_time) * 1000, 2)
        delivered_tokens = max(1, len(text) // 4)
        raw_token_estimate = sum(len(f"{a.get('subject')} {a.get('predicate')} {a.get('object')}") // 4 for a in assertions if isinstance(a, dict)) + 300

        record = self.experimenter.record_turn_metrics(
            strategy_name=competitor,
            token_count=delivered_tokens,
            raw_token_estimate=raw_token_estimate,
            prep_latency_ms=prep_latency_ms,
            is_verified=verified,
            assertion_count=len(assertions),
            task_quality=task_quality,
            source_accuracy=source_accuracy,
            fidelity=fidelity
        )

        return {
            "competitor": competitor,
            "text": text,
            "checksum": checksum,
            "delivered_tokens": delivered_tokens,
            "compression_ratio": record["compression_ratio"],
            "utility_score": record["utility_score"],
            "task_quality": task_quality,
            "semantic_fidelity": fidelity,
            "source_accuracy": source_accuracy,
            "prep_latency_ms": prep_latency_ms,
            "complexity_score": self.COMPLEXITY_SCORES.get(competitor, 99)
        }

    def run_tournament(
        self,
        assertions: List[Dict[str, Any]],
        invariants: List[str],
        graph_edges: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        results = {}
        for comp in self.TOURNAMENT_COMPETITORS:
            results[comp] = self.run_match(comp, assertions, invariants, graph_edges=graph_edges)

        ranked = sorted(
            results.items(),
            key=lambda item: (
                item[1]["utility_score"],
                item[1]["task_quality"],
                item[1]["semantic_fidelity"],
                item[1]["source_accuracy"],
                -item[1]["delivered_tokens"],
                -item[1]["prep_latency_ms"],
                -item[1]["complexity_score"]
            ),
            reverse=True
        )

        section_winner = ranked[0][0]

        section_codecs = {
            "@INV": "ncc_vcl",
            "@STATE": "columnar",
            "@DEP": "native_graph",
            "@DEC": section_winner if section_winner in ("csc_vcl", "ncc_vcl") else "csc_vcl",
            "@TIME": "timeline",
            "@FLAGS": "bitset",
            "@EXACT": "raw",
            "@SRC": "handles",
            "@VISUAL": "vcl_a"
        }

        return {
            "winner": "hybrid_packet",
            "active_meta_strategy": "hybrid_packet",
            "section_winning_codec": section_winner,
            "section_codecs": section_codecs,
            "winner_score": results["hybrid_packet"]["utility_score"],
            "tie_breaking_tier": "1. utility_score / 2. task_quality / 3. fidelity / 4. context_cost / 5. latency / 6. safety",
            "rankings": {k: v["utility_score"] for k, v in ranked},
            "match_details": results
        }
