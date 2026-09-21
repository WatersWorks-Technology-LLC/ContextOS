import json
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any

class EventStore:
    """
    Immutable append-only event log.
    Design Law #1: Raw history is immutable evidence.
    """
    def __init__(self, data_dir: Path, filename: str = "events.jsonl"):
        self.file_path = data_dir / filename
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def append_event(self, event_type: str, payload: Dict[str, Any], session_id: str = None) -> Dict[str, Any]:
        event = {
            "event_id": f"EVT-{uuid.uuid4().hex[:8]}",
            "timestamp": time.time(),
            "iso_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "session_id": session_id or "default-session",
            "type": event_type,
            "payload": payload
        }
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
        return event

    def get_events(self, limit: int = 100, session_id: str = None) -> List[Dict[str, Any]]:
        if not self.file_path.exists():
            return []
        events = []
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    evt = json.loads(line)
                    if session_id and evt.get("session_id") != session_id:
                        continue
                    events.append(evt)
                except Exception:
                    continue
        return events[-limit:]
