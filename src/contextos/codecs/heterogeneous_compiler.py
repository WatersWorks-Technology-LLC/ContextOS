import hashlib
from typing import List, Dict, Any, Tuple
from .ncc_vcl import NCCVCLCodec

class HeterogeneousPacketCompiler:
    """
    Per-Section Adaptive Hybrid Representation Compiler.
    Allows each semantic block to independently choose its optimal, cheapest trustworthy representation:
    - @INV    -> NCC-VCL
    - @STATE  -> Columnar tabular
    - @DEP    -> Graph topology
    - @TIME   -> Timeline syntax
    - @FLAGS  -> Bitset / compact boolean
    - @DEC    -> NCC-VCL
    - @EXACT  -> Raw text
    - @SRC    -> Handles
    - @VISUAL -> VCL-A SVG
    """
    @classmethod
    def compile_packet(
        cls,
        assertions: List[Dict[str, Any]],
        invariants: List[str],
        graph_edges: List[Dict[str, Any]] = None,
        timeline_events: List[Dict[str, Any]] = None,
        include_visual_summary: bool = False
    ) -> Tuple[str, str]:
        lines = ["CTX/2.1-HYBRID-BLOCK"]

        # 1. @INV -> NCC-VCL
        if invariants:
            lines.append("@INV (NCC-VCL)")
            for inv in invariants:
                lines.append(f"[MUST] {inv}")

        # Group assertions by kind
        decisions = [a for a in assertions if a.get("kind") == "decision"]
        facts = [a for a in assertions if a.get("kind") in ("fact", "state")]
        flags = [a for a in assertions if a.get("kind") == "flag"]
        exacts = [a for a in assertions if a.get("kind") in ("hash", "exact", "path")]
        sources = [a.get("source_ref") for a in assertions if a.get("source_ref")]

        # 2. @FLAGS -> Bitset / Compact Boolean
        if flags:
            lines.append("@FLAGS (BITSET)")
            flag_str = " ".join([f"{f.get('subject')}={1 if f.get('object') in ('true', '1', 'True') else 0}" for f in flags])
            lines.append(flag_str)

        # 3. @DEC -> NCC-VCL
        if decisions:
            lines.append("@DEC (NCC-VCL)")
            for d in decisions:
                lines.append(NCCVCLCodec.encode_assertion(d))

        # 4. @STATE -> Columnar Tabular
        if facts:
            lines.append("@STATE (COLUMNAR)")
            lines.append("SUBJ | PRED | OBJ")
            for f in facts:
                lines.append(f"{f.get('subject')} | {f.get('predicate')} | {f.get('object')}")

        # 5. @DEP -> Graph Topology
        if graph_edges:
            lines.append("@DEP (GRAPH)")
            for e in graph_edges:
                lines.append(f"{e.get('source')} -> {e.get('target')} [{e.get('relation', 'rel')}]")

        # 6. @TIME -> Timeline Syntax
        if timeline_events:
            lines.append("@TIME (TIMELINE)")
            for te in timeline_events:
                lines.append(f"T[{te.get('iso_time', 'N/A')}] : {te.get('event', '')}")

        # 7. @EXACT -> Raw Text
        if exacts:
            lines.append("@EXACT (RAW)")
            for ex in exacts:
                lines.append(f"{ex.get('subject')}={ex.get('object')}")

        # 8. @SRC -> Provenance Source Handles
        if sources:
            lines.append("@SRC (HANDLES)")
            unique_srcs = sorted(list(set(sources)))
            lines.append(f"Pointers: {', '.join(unique_srcs)}")

        # 9. @VISUAL -> VCL-A Summary handle
        if include_visual_summary:
            lines.append("@VISUAL (VCL-A)")
            lines.append("MAP: topology_vcl_a_atlas.svg [Z2]")

        text = "\n".join(lines)
        checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]
        return text, checksum
