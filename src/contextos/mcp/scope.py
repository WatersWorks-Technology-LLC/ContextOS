"""Resolve MCP requests without a mutable process-wide active workspace."""
from pathlib import Path
import re
from threading import RLock

from ..config import ContextOSConfig
from ..hooks.adapter import HookAdapter
from ..identity import IdentityScope


class ScopeError(ValueError):
    """Invalid or ambiguous request identity; no tool operation is performed."""


class RequestScopes:
    def __init__(self, default_adapter):
        self.default_adapter = default_adapter
        self._adapters = {self._key(default_adapter.config): default_adapter}
        self._sessions = {}
        self._lock = RLock()
        self.has_requests = False

    @staticmethod
    def _key(config):
        return (str(config.workspace_dir.resolve()), config.project_id, config.client_id)

    @staticmethod
    def _text(value, field):
        if not isinstance(value, str) or not value.strip():
            raise ScopeError(f"{field} must be a nonempty string")
        return value

    @classmethod
    def _cwd(cls, value):
        path = Path(cls._text(value, "cwd")).expanduser()
        if not path.is_absolute() or not path.is_dir():
            raise ScopeError("cwd must be an absolute, existing workspace directory")
        return str(path.resolve())

    @classmethod
    def _field(cls, args, payload, field):
        top = args.get(field)
        nested = payload.get(field)
        if field in args:
            cls._text(top, field)
        if field in payload:
            cls._text(nested, f"payload.{field}")
        if top is not None and nested is not None and top != nested:
            raise ScopeError(f"Conflicting {field} in arguments and payload")
        return top if top is not None else nested

    def resolve(self, name, args):
        if not isinstance(args, dict):
            raise ScopeError("Tool arguments must be an object")
        payload = args.get("payload", {}) if name == "record" else {}
        if not isinstance(payload, dict):
            raise ScopeError("record payload must be an object")
        session = self._field(args, payload, "session_id")
        agent = self._field(args, payload, "agent_id") or (args.get("role", "subagent") if name == "subagent_stop" else "main")
        self._text(agent, "agent_id")
        cwd = self._cwd(args["cwd"]) if "cwd" in args else None
        project = args.get("project_id")
        if "project_id" in args:
            self._text(project, "project_id")
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", project):
                raise ScopeError("project_id must be a single safe directory name")

        with self._lock:
            bound = self._sessions.get(session) if session is not None else None
            base = bound or self.default_adapter
            resolved_cwd = cwd or str(base.config.workspace_dir.resolve())
            if bound and (resolved_cwd != str(bound.config.workspace_dir.resolve())
                          or (project is not None and project != bound.config.project_id)):
                raise ScopeError("session_id is already bound to another workspace/project; use a new session_id")
            if session is not None and not bound and cwd is None:
                raise ScopeError("Unknown session_id; call prepare_turn/session_start with cwd first, or supply cwd on this request")

            if bound:
                config = bound.config
            elif resolved_cwd == str(self.default_adapter.config.workspace_dir.resolve()):
                config = self.default_adapter.config.model_copy(deep=True, update={
                    "project_id": project or self.default_adapter.config.project_id})
            else:
                config = ContextOSConfig.load(workspace_dir=Path(resolved_cwd),
                    client_id=self.default_adapter.config.client_id, project_id=project)
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", config.project_id):
                raise ScopeError("Configured project_id must be a single safe directory name")
            key = self._key(config)
            adapter = self._adapters.get(key)
            if adapter is not None:
                config = adapter.config
            identity = IdentityScope.from_config(config, session or "default", agent)
            # Nested identity is a consistency assertion, never an alternative router.
            # In particular payload.project/workspace must not pretend provenance.
            for fields in (args, payload):
                for field in ("runtime_id", "client_id", "producer_runtime", "origin_runtime"):
                    if field in fields and fields[field] != identity.runtime_id:
                        raise ScopeError(f"{field} does not match the server runtime")
                for field in ("project", "project_id"):
                    if field in fields and fields[field] != identity.project_id:
                        raise ScopeError(f"{field} does not match the selected project_id")
                for field in ("workspace", "workspace_id", "cwd"):
                    if field not in fields:
                        continue
                    value = self._text(fields[field], field)
                    if value == identity.workspace_id:
                        continue
                    path = Path(value).expanduser()
                    if not path.is_absolute() or str(path.resolve()) != key[0]:
                        raise ScopeError(f"{field} does not match the selected cwd/workspace identity")
                for field, expected in (("origin_session", identity.session_id), ("origin_agent", identity.agent_id)):
                    if field in fields and fields[field] != expected:
                        raise ScopeError(f"{field} does not match the request identity")
            if adapter is None:
                adapter = HookAdapter(config=config)
                self._adapters[key] = adapter
            if session is not None and name in ("prepare_turn", "session_start"):
                self._sessions[session] = adapter
            self.has_requests = True
            return adapter, identity
