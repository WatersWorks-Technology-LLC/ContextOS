import hashlib
import re
from typing import List, Dict, Any, Tuple

class NCCVCLCodec:
    """
    Neanderthal Context Compression (NCC-VCL) Codec.
    Compacts assertions and state into normalized telegraphic syntax with VCL relation codes.
    Example:
    [CURR:FACT] DB.timeout=30s | SRC:S1
    [CURR:DECISION] Auth.protocol->OAuth2 | REPL:D03 | SRC:S2
    """

    RELATION_MAP = {
        "depends_on": "->",
        "implements": "=>",
        "supersedes": ">>",
        "conflicts_with": "!==",
        "constrained_by": "!!"
    }

    INV_RELATION_MAP = {v: k for k, v in RELATION_MAP.items()}

    @classmethod
    def encode_assertion(cls, assertion: Dict[str, Any]) -> str:
        kind = assertion.get("kind", "fact").upper()
        status = assertion.get("status", "current").upper()[:4]
        subj = assertion.get("subject", "")
        pred = assertion.get("predicate", "")
        obj = assertion.get("object", "")
        source = assertion.get("source_ref", "")

        rel_code = cls.RELATION_MAP.get(pred, f":{pred}:")
        line = f"[{status}:{kind}] {subj} {rel_code} {obj}"
        if source:
            line += f" | SRC:{source}"
        return line

    @classmethod
    def encode_packet(cls, assertions: List[Dict[str, Any]], invariants: List[str] = None) -> Tuple[str, str]:
        lines = []
        if invariants:
            lines.append("=== PINNED INVARIANTS ===")
            for inv in invariants:
                lines.append(f"[MUST] {inv}")

        lines.append("=== CURRENT WORKING STATE (NCC-VCL) ===")
        for a in assertions:
            lines.append(cls.encode_assertion(a))

        encoded_text = "\n".join(lines)
        checksum = hashlib.sha256(encoded_text.encode("utf-8")).hexdigest()[:8]
        return encoded_text, checksum

    @classmethod
    def decode_line(cls, line: str) -> Dict[str, Any]:
        pattern = r"\[(\w+):(\w+)\]\s+(.*?)\s+(->|=>|>>|!==|!!|:\w+:)\s+(.*?)(\s+\|\s+SRC:(.*))?$"
        match = re.match(pattern, line.strip())
        if not match:
            return {"raw": line, "valid": False}

        status, kind, subj, rel_code, obj, _, source = match.groups()
        pred = cls.INV_RELATION_MAP.get(rel_code, rel_code.strip(":"))

        return {
            "status": "current" if status == "CURR" else status.lower(),
            "kind": kind.lower(),
            "subject": subj,
            "predicate": pred,
            "object": obj,
            "source_ref": source or None,
            "valid": True
        }
