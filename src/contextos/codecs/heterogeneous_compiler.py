import hashlib
from typing import List, Dict, Any, Tuple
from .ncc_vcl import NCCVCLCodec
import json

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
        include_visual_summary: bool = False,
        section_codecs: Dict[str, str] = None
    ) -> Tuple[str, str]:
        lines = ["CTX/2.1-HYBRID-BLOCK"]
        selected = section_codecs or {}

        def encode_section(section: str, rows: List[Dict[str, Any]]) -> List[str]:
            codec = selected.get(section)
            if codec in ("ncc_vcl", "csc_vcl", "structured_text", "json_schema"):
                if codec == "ncc_vcl":
                    return [NCCVCLCodec.encode_assertion(row) for row in rows]
                if codec == "csc_vcl":
                    return [f"{r.get('subject')} 关 {r.get('predicate')} 联 {r.get('object')}" for r in rows]
                if codec == "json_schema":
                    return [json.dumps(rows, ensure_ascii=False, separators=(",", ":"))]
                return [f"- {r.get('subject')} {r.get('predicate')} {r.get('object')}" for r in rows]
            if codec == "native_graph":
                return [f"({r.get('subject')})-[{r.get('predicate')}]->({r.get('object')})" for r in rows]
            if codec == "columnar":
                return ["SUBJ | PRED | OBJ"] + [f"{r.get('subject')} | {r.get('predicate')} | {r.get('object')}" for r in rows]
            return [NCCVCLCodec.encode_assertion(row) for row in rows]

        # 1. @INV -> NCC-VCL
        if invariants:
            inv_codec = selected.get("@INV", "ncc_vcl")
            lines.append(f"@INV ({'NCC-VCL' if inv_codec == 'ncc_vcl' else inv_codec.upper()})")
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
            dec_codec = selected.get("@DEC", "ncc_vcl")
            lines.append(f"@DEC ({'NCC-VCL' if dec_codec == 'ncc_vcl' else dec_codec.upper()})")
            lines.extend(encode_section("@DEC", decisions))

        # 4. @STATE -> Columnar Tabular
        if facts:
            state_codec = selected.get("@STATE", "columnar")
            lines.append(f"@STATE ({state_codec.upper()})")
            lines.extend(encode_section("@STATE", facts))

        # 5. @DEP -> Graph Topology
        if graph_edges:
            dep_codec = selected.get("@DEP")
            lines.append(f"@DEP ({dep_codec.upper() if dep_codec else 'GRAPH'})")
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
