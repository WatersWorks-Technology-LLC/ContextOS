import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from ..storage.versioning import ContextVersionStore
from ..codecs.structured_text import StructuredTextCodec
from ..codecs.ncc_vcl import NCCVCLCodec

logger = logging.getLogger("ContextOS.SelfHealing")

class SelfHealingEngine:
    """
    Self-Healing & Break Detection Engine.
    Monitors context packet generation, detects semantic corruption or errors,
    executes automatic rollbacks, and degrades gracefully to safe baselines.
    """
    FALLBACK_CASCADE = ["ncc_vcl", "structured_text", "raw_excerpts"]

    def __init__(self, version_store: ContextVersionStore):
        self.version_store = version_store
        self.incident_log: List[Dict[str, Any]] = []

    def record_incident(self, error_type: str, details: str, strategy: str) -> Dict[str, Any]:
        incident = {
            "incident_id": f"INC-{int(time.time()*1000)}",
            "timestamp": time.time(),
            "error_type": error_type,
            "details": details,
            "failed_strategy": strategy,
            "action_taken": "automatic_fallback"
        }
        self.incident_log.append(incident)
        logger.warning(f"[SelfHealing] Incident recorded: {error_type} on strategy {strategy}")
        return incident

    def attempt_recovery_compile(
        self,
        assertions: list,
        invariants: list,
        attempted_codec: str,
        session_id: str = "default",
        parent_commit: Optional[str] = None
    ) -> Tuple[str, str, str, Dict[str, Any]]:
        """
        Attempts to compile context with the requested codec.
        If a break occurs, automatically degrades down the fallback cascade and rolls back to a stable commit.
        """
        try:
            if attempted_codec == "ncc_vcl":
                text, checksum = NCCVCLCodec.encode_packet(assertions, invariants)
                # Verify round trip decoding sanity
                lines = text.splitlines()
                valid_lines = sum(1 for line in lines if line.startswith("[") and NCCVCLCodec.decode_line(line).get("valid"))
                if len(assertions) > 0 and valid_lines == 0:
                    raise ValueError("NCC-VCL round-trip verification failed: zero valid lines decoded.")
            elif attempted_codec == "structured_text":
                text, checksum = StructuredTextCodec.encode_packet(assertions, invariants)
            else:
                raise ValueError(f"Unknown or unsupported codec strategy: {attempted_codec}")

            # Create commit keyframe
            commit = self.version_store.create_commit(text, assertions, invariants, attempted_codec, session_id, parent_commit)
            return text, checksum, attempted_codec, commit

        except Exception as e:
            # Self-healing break detection triggered!
            incident = self.record_incident("CodecBreakException", str(e), attempted_codec)

            # Fallback to Structured Text baseline
            fallback_codec = "structured_text"
            text, checksum = StructuredTextCodec.encode_packet(assertions, invariants)
            
            # Rollback to stable parent keyframe if available
            rollback_commit = self.version_store.rollback(parent_commit) if parent_commit else None
            commit = self.version_store.create_commit(text, assertions, invariants, fallback_codec, session_id, parent_commit)

            commit["incident"] = incident
            commit["rollback"] = rollback_commit
            return text, checksum, fallback_codec, commit
