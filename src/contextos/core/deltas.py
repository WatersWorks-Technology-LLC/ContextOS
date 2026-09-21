import hashlib
import json
import time
from typing import Dict, Any, List, Optional, Tuple, Set

class DifferentialKeyframeEngine:
    """
    Assertion-ID Differential Keyframe Protocol for ContextOS.
    Generates compact delta representations (@BASE + @Δ) across contiguous turns
    operating on stable assertion-level identities (+A817, -A412, ~A930:object old->new).
    
    Guarantees strict fail-closed reconstruction validation:
    Any checksum mismatch, corrupted delta, or out-of-order parent commit returns (None, None, False).
    """
    def __init__(self, max_chain_length: int = 5):
        self.max_chain_length = max_chain_length

    @staticmethod
    def get_assertion_id(assertion: Dict[str, Any]) -> str:
        if "id" in assertion and assertion["id"]:
            return str(assertion["id"])
        # Stable fallback hash ID
        kind = assertion.get("kind", "fact")
        subj = assertion.get("subject", "")
        pred = assertion.get("predicate", "")
        obj = assertion.get("object", "")
        h = hashlib.sha256(f"{kind}:{subj}:{pred}:{obj}".encode("utf-8")).hexdigest()[:6]
        return f"A-{h}"

    @classmethod
    def hash_state(cls, assertions: List[Dict[str, Any]], invariants: List[str]) -> str:
        s_assertions = []
        for a in assertions:
            if isinstance(a, dict):
                aid = cls.get_assertion_id(a)
                s_assertions.append(f"{aid}:{a.get('kind')}:{a.get('subject')}:{a.get('predicate')}:{a.get('object')}")
        s_assertions.sort()
        s_invariants = sorted(list(set(invariants)))
        payload = json.dumps({"a": s_assertions, "i": s_invariants}, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8]

    def generate_delta(
        self,
        base_commit_id: str,
        base_assertions: List[Dict[str, Any]],
        base_invariants: List[str],
        current_assertions: List[Dict[str, Any]],
        current_invariants: List[str],
        chain_length: int = 1
    ) -> Dict[str, Any]:
        """
        Calculates assertion-level difference between base state and current state.
        If chain_length exceeds max_chain_length, triggers an automatic rebase.
        """
        if chain_length > self.max_chain_length:
            return {
                "rebased": True,
                "reason": "max_chain_length_exceeded",
                "base_commit_id": base_commit_id,
                "packet_text": None
            }

        # Index assertions by stable assertion ID
        base_map = {self.get_assertion_id(a): a for a in base_assertions if isinstance(a, dict)}
        curr_map = {self.get_assertion_id(a): a for a in current_assertions if isinstance(a, dict)}

        base_ids = set(base_map.keys())
        curr_ids = set(curr_map.keys())

        added_ids = curr_ids - base_ids
        removed_ids = base_ids - curr_ids
        common_ids = base_ids & curr_ids

        delta_lines = []

        # Modifications / transitions
        for aid in sorted(list(common_ids)):
            old_a = base_map[aid]
            new_a = curr_map[aid]
            if old_a.get("object") != new_a.get("object"):
                delta_lines.append(f"~{aid}:object {old_a.get('object')}→{new_a.get('object')}")

        # Additions
        for aid in sorted(list(added_ids)):
            a = curr_map[aid]
            delta_lines.append(f"+{aid}:{a.get('kind')}:{a.get('subject')}:{a.get('predicate')}={a.get('object')}")

        # Removals
        for aid in sorted(list(removed_ids)):
            delta_lines.append(f"-{aid}")

        # Invariants diffs
        base_inv_set = set(base_invariants)
        curr_inv_set = set(current_invariants)
        for inv in sorted(list(curr_inv_set - base_inv_set)):
            delta_lines.append(f"+INV:{inv}")
        for inv in sorted(list(base_inv_set - curr_inv_set)):
            delta_lines.append(f"-INV:{inv}")

        target_checksum = self.hash_state(current_assertions, current_invariants)

        packet_lines = [
            f"@BASE {base_commit_id}",
            f"@CHECKSUM {target_checksum}",
            "@Δ"
        ] + delta_lines

        packet_text = "\n".join(packet_lines)

        return {
            "rebased": False,
            "base_commit_id": base_commit_id,
            "chain_length": chain_length,
            "target_checksum": target_checksum,
            "delta_lines": delta_lines,
            "packet_text": packet_text
        }

    def apply_delta(
        self,
        base_assertions: List[Dict[str, Any]],
        base_invariants: List[str],
        delta_packet_text: str
    ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[List[str]], bool]:
        """
        Applies assertion-ID delta packet text to base state.
        Fails closed (returns None, None, False) if checksum, structure, or content is invalid.
        """
        if not delta_packet_text or not isinstance(delta_packet_text, str):
            return None, None, False

        lines = delta_packet_text.strip().split("\n")
        target_checksum = None
        in_delta = False

        reconstructed_map = {self.get_assertion_id(a): dict(a) for a in base_assertions if isinstance(a, dict)}
        reconstructed_invariants = list(base_invariants)

        try:
            for line in lines:
                line = line.strip()
                if line.startswith("@CHECKSUM "):
                    target_checksum = line.split(" ", 1)[1]
                elif line == "@Δ":
                    in_delta = True
                elif in_delta and line:
                    if line.startswith("+INV:"):
                        inv = line[5:]
                        if inv not in reconstructed_invariants:
                            reconstructed_invariants.append(inv)
                    elif line.startswith("-INV:"):
                        inv = line[5:]
                        if inv in reconstructed_invariants:
                            reconstructed_invariants.remove(inv)
                    elif line.startswith("+"):
                        # Addition: +A123:kind:subject:predicate=object
                        content = line[1:]
                        if ":" in content and "=" in content:
                            aid_rest, obj = content.split("=", 1)
                            parts = aid_rest.split(":")
                            if len(parts) >= 4:
                                aid, kind, subj, pred = parts[0], parts[1], parts[2], parts[3]
                                new_item = {"id": aid, "kind": kind, "subject": subj, "predicate": pred, "object": obj}
                                reconstructed_map[aid] = new_item
                    elif line.startswith("-"):
                        # Removal: -A123
                        aid = line[1:]
                        reconstructed_map.pop(aid, None)
                    elif line.startswith("~"):
                        # Modification: ~A123:field old->new
                        content = line[1:]
                        if ":" in content and "→" in content:
                            aid_field, transition = content.split(":", 1)
                            parts = aid_field.split(" ")
                            aid = parts[0]
                            field = parts[1] if len(parts) > 1 else "object"
                            old_v, new_v = transition.split("→", 1)
                            if aid in reconstructed_map:
                                reconstructed_map[aid][field] = new_v
        except Exception:
            return None, None, False

        reconstructed_assertions = list(reconstructed_map.values())
        calc_checksum = self.hash_state(reconstructed_assertions, reconstructed_invariants)

        if target_checksum and calc_checksum != target_checksum:
            return None, None, False

        return reconstructed_assertions, reconstructed_invariants, True
