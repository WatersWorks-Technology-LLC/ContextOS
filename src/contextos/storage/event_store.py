import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any
from ..identity import IdentityScope

class EventStore:
    """
    Immutable append-only event log.
    Design Law #1: Raw history is immutable evidence.
    """
    def __init__(self, data_dir: Path, filename: str = "events.jsonl"):
        self.file_path = data_dir / filename
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def append_event(self, event_type: str, payload: Dict[str, Any], session_id: str = None,
                     identity: IdentityScope = None, turn_id: str = None) -> Dict[str, Any]:
        if identity is None:
            raise ValueError("IdentityScope is required for new events")
        identity_data = identity.as_dict()
        event = {
            "event_id": f"EVT-{uuid.uuid4().hex[:8]}",
            "timestamp": time.time(),
            "iso_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            **identity_data,
            "session_id": identity.session_id,
            "identity_confidence": "observed",
            "turn_id": turn_id,
            "type": event_type,
            "payload": payload
        }
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
        return event

    def get_events(self, limit: int = 100, session_id: str = None,
                   identity: IdentityScope = None) -> List[Dict[str, Any]]:
        import collections
        if not self.file_path.exists():
            return []
        events = collections.deque(maxlen=limit)
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    evt = json.loads(line)
                    if identity and any(evt.get(k) != v for k, v in identity.as_dict().items()):
                        continue
                    if session_id and evt.get("session_id") != session_id:
                        continue
                    events.append(evt)
                except Exception:
                    continue
        return list(events)
