from typing import List, Dict, Any, Tuple
import hashlib

class StructuredTextCodec:
    """
    Structured English representation compiler.
    """
    @classmethod
    def encode_packet(cls, assertions: List[Dict[str, Any]], invariants: List[str] = None) -> Tuple[str, str]:
        lines = []
        if invariants:
            lines.append("## Critical Invariants & Rules")
            for inv in invariants:
                lines.append(f"- ALWAYS RESPECT: {inv}")
            lines.append("")

        lines.append("## Active Working Memory & State")
        for a in assertions:
            kind = a.get("kind", "fact").capitalize()
            subj = a.get("subject", "")
            pred = a.get("predicate", "")
            obj = a.get("object", "")
            src = a.get("source_ref", "")
            src_str = f" (Source: {src})" if src else ""
            lines.append(f"- **[{kind}]** {subj} {pred} {obj}{src_str}")

        text = "\n".join(lines)
        checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]
        return text, checksum
