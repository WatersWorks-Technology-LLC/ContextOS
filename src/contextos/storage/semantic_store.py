import sqlite3
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..identity import IdentityScope

class SemanticStore:
    """
    SQLite-backed store for entities, assertions, constraints, decisions, decision rationale,
    closed branch conditions, and temporal validity (observed_at, valid_from, valid_until, superseded_at).
    """
    def __init__(self, data_dir: Path, db_filename: str = "semantic.db"):
        self.db_path = data_dir / db_filename
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS entities (
                    entity_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    attributes TEXT,
                    created_at REAL
                );

                CREATE TABLE IF NOT EXISTS assertions (
                    assertion_id TEXT PRIMARY KEY,
                    entity_id TEXT,
                    kind TEXT NOT NULL, -- fact, decision, constraint, question, invariant, conflict
                    subject TEXT NOT NULL,
                    predicate TEXT NOT NULL,
                    object TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'current', -- current, superseded, proposed, rejected, conflict
                    scope TEXT NOT NULL DEFAULT 'project', -- ephemeral, session, runtime, project, workspace, global
                    runtime_id TEXT DEFAULT 'codex',
                    workspace_id TEXT DEFAULT 'default',
                    project_id TEXT DEFAULT 'default',
                    producer_runtime TEXT DEFAULT 'codex',
                    origin_runtime TEXT DEFAULT 'codex',
                    origin_session TEXT DEFAULT 'default',
                    origin_agent TEXT DEFAULT 'main',
                    origin_turn TEXT,
                    identity_confidence TEXT DEFAULT 'observed',
                    origin_assertion_id TEXT,
                    confidence REAL DEFAULT 1.0,
                    source_ref TEXT,
                    decision_rationale TEXT,
                    closed_branch_condition TEXT,
                    observed_at REAL,
                    valid_from REAL,
                    valid_until REAL,
                    superseded_at REAL,
                    superseded_by TEXT,
                    created_at REAL,
                    FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
                );

                CREATE INDEX IF NOT EXISTS idx_assertions_entity ON assertions(entity_id);
                CREATE INDEX IF NOT EXISTS idx_assertions_status ON assertions(status);
                CREATE INDEX IF NOT EXISTS idx_assertions_kind ON assertions(kind);
            """)

            # Graceful column migrations for existing databases
            for col, col_type in [
                ("scope", "TEXT DEFAULT 'project'"),
                ("runtime_id", "TEXT DEFAULT 'codex'"),
                ("workspace_id", "TEXT DEFAULT 'default'"),
                ("project_id", "TEXT DEFAULT 'default'"),
                ("producer_runtime", "TEXT DEFAULT 'codex'"),
                ("origin_runtime", "TEXT DEFAULT 'codex'"),
                ("origin_session", "TEXT DEFAULT 'default'"),
                ("origin_agent", "TEXT DEFAULT 'main'"),
                ("origin_turn", "TEXT"),
                ("identity_confidence", "TEXT DEFAULT 'legacy'"),
                ("origin_assertion_id", "TEXT"),
                ("decision_rationale", "TEXT"),
                ("closed_branch_condition", "TEXT"),
                ("observed_at", "REAL"),
                ("valid_from", "REAL"),
                ("valid_until", "REAL"),
                ("superseded_at", "REAL")
            ]:
                try:
                    conn.execute(f"ALTER TABLE assertions ADD COLUMN {col} {col_type}")
                except Exception:
                    pass

            conn.executescript("""
                CREATE INDEX IF NOT EXISTS idx_assertions_scope ON assertions(scope);
                CREATE INDEX IF NOT EXISTS idx_assertions_runtime ON assertions(runtime_id);
            """)


    def add_entity(self, entity_id: str, name: str, category: str, attributes: Optional[Dict[str, Any]] = None) -> str:
        with self._get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO entities (entity_id, name, category, attributes, created_at) VALUES (?, ?, ?, ?, ?)",
                (entity_id, name, category, json.dumps(attributes or {}), time.time())
            )
        return entity_id

    def add_assertion(
        self,
        assertion_id: str,
        subject: str,
        predicate: str,
        object_val: str,
        kind: str = "fact",
        entity_id: Optional[str] = None,
        status: str = "current",
        scope: str = "project",
        runtime_id: str = "codex",
        workspace_id: str = "default",
        project_id: str = "default",
        producer_runtime: str = "codex",
        origin_session: str = "default",
        origin_agent: str = "main",
        origin_assertion_id: Optional[str] = None,
        confidence: float = 1.0,
        source_ref: Optional[str] = None,
        decision_rationale: Optional[str] = None,
        closed_branch_condition: Optional[str] = None,
        valid_from: Optional[float] = None,
        valid_until: Optional[float] = None,
        origin_turn: Optional[str] = None,
        identity_confidence: str = "observed"
    ) -> str:
        now = time.time()
        with self._get_conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO assertions 
                   (assertion_id, entity_id, kind, subject, predicate, object, status, scope, runtime_id, workspace_id, project_id, producer_runtime,
                    origin_runtime, origin_session, origin_agent, origin_turn, origin_assertion_id,
                    identity_confidence,
                    confidence, source_ref, decision_rationale, closed_branch_condition, observed_at, valid_from, valid_until, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    assertion_id, entity_id, kind, subject, predicate, object_val, status, scope, runtime_id, workspace_id, project_id, producer_runtime,
                    producer_runtime, origin_session, origin_agent, origin_turn, origin_assertion_id,
                    identity_confidence,
                    confidence, source_ref, decision_rationale, closed_branch_condition, now, valid_from or now, valid_until, now
                )
            )
        return assertion_id

    def promote_assertion(self, assertion_id: str, target_scope: str, promotion_reason: str = "verified_fact") -> Optional[str]:
        """
        Promotes an assertion to a higher scope (ephemeral -> session -> runtime -> project -> workspace -> global).
        Creates a new promoted record with origin reference to preserve execution provenance.
        """
        valid_scopes = ["ephemeral", "session", "runtime", "project", "workspace", "global"]
        if target_scope not in valid_scopes:
            return None

        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM assertions WHERE assertion_id = ?", (assertion_id,)).fetchone()
            if not row:
                return None
            a = dict(row)
            
            promoted_id = f"AST-PROM-{uuid.uuid4().hex[:8]}"
            now = time.time()
            conn.execute(
                """INSERT INTO assertions 
                   (assertion_id, entity_id, kind, subject, predicate, object, status, scope, runtime_id, workspace_id, project_id, producer_runtime,
                    origin_runtime, origin_session, origin_agent, origin_assertion_id,
                    confidence, source_ref, decision_rationale, closed_branch_condition, observed_at, valid_from, valid_until, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, 'current', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    promoted_id, a.get("entity_id"), a.get("kind"), a.get("subject"), a.get("predicate"), a.get("object"),
                    target_scope, a.get("runtime_id"), a.get("workspace_id"), a.get("project_id"), a.get("producer_runtime"),
                    a.get("producer_runtime"), a.get("origin_session"), a.get("origin_agent"), assertion_id,
                    a.get("confidence", 1.0), a.get("source_ref"), f"Promoted ({promotion_reason}): {a.get('decision_rationale') or ''}",
                    a.get("closed_branch_condition"), now, now, None, now
                )
            )
            return promoted_id



    def supersede_assertion(self, old_assertion_id: str, new_assertion_id: str):
        now = time.time()
        with self._get_conn() as conn:
            conn.execute(
                """UPDATE assertions 
                   SET status = 'superseded', valid_until = ?, superseded_at = ?, superseded_by = ? 
                   WHERE assertion_id = ?""",
                (now, now, new_assertion_id, old_assertion_id)
            )

    def record_closed_branch(self, decision_id: str, rejected_option: str, rationale: str, condition_to_reopen: str):
        now = time.time()
        aid = f"REJ-{decision_id}"
        with self._get_conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO assertions 
                   (assertion_id, kind, subject, predicate, object, status, confidence, decision_rationale, closed_branch_condition, observed_at, created_at)
                   VALUES (?, 'decision', ?, 'rejected_option', ?, 'rejected', 1.0, ?, ?, ?, ?)""",
                (aid, decision_id, rejected_option, rationale, condition_to_reopen, now, now)
            )
        return aid

    @staticmethod
    def _identity_filter(identity: Optional[IdentityScope]):
        if identity is None:
            return "1 = 1", []
        # Client-local MCP reads never widen to another workspace or runtime.
        # Durable project assertions may be reused across sessions; transient
        # session/ephemeral assertions remain private to their originating agent.
        return (
            "runtime_id = ? AND workspace_id = ? AND project_id = ? "
            "AND (scope NOT IN ('session', 'ephemeral') OR (origin_session = ? AND origin_agent = ?))",
            [identity.runtime_id, identity.workspace_id, identity.project_id,
             identity.session_id, identity.agent_id],
        )

    def query_current_state(self, kind: Optional[str] = None, entity_id: Optional[str] = None,
                            runtime_id: Optional[str] = "codex", workspace_id: Optional[str] = None,
                            project_id: Optional[str] = None,
                            identity: Optional[IdentityScope] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM assertions WHERE status = 'current'"
        params = []
        if identity is not None:
            clause, params = self._identity_filter(identity)
            query += " AND " + clause
        elif runtime_id:
            query += " AND (runtime_id = ? OR scope IN ('workspace', 'global'))"
            params.append(runtime_id)
        if workspace_id:
            query += " AND ((scope = 'global') OR workspace_id = ?)"
            params.append(workspace_id)
        if project_id:
            query += " AND (scope IN ('workspace', 'global') OR project_id = ?)"
            params.append(project_id)
        if kind:
            query += " AND kind = ?"
            params.append(kind)
        if entity_id:
            query += " AND entity_id = ?"
            params.append(entity_id)
        
        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]


    def query_conflicts_and_closed_branches(self, identity: Optional[IdentityScope] = None) -> Dict[str, List[Dict[str, Any]]]:
        clause, params = self._identity_filter(identity)
        with self._get_conn() as conn:
            conflicts = [dict(r) for r in conn.execute(
                "SELECT * FROM assertions WHERE status IN ('conflict', 'proposed') AND " + clause, params).fetchall()]
            closed = [dict(r) for r in conn.execute(
                "SELECT * FROM assertions WHERE status = 'rejected' AND " + clause, params).fetchall()]
        return {"conflicts": conflicts, "closed_branches": closed}

    def search_assertions(self, keyword: str, limit: int = 20,
                          identity: Optional[IdentityScope] = None) -> List[Dict[str, Any]]:
        pattern = f"%{keyword}%"
        clause, params = self._identity_filter(identity)
        query = """SELECT * FROM assertions
                   WHERE (assertion_id = ? OR subject LIKE ? OR predicate LIKE ? OR object LIKE ? OR decision_rationale LIKE ?)
                   AND """ + clause + " ORDER BY created_at DESC LIMIT ?"
        with self._get_conn() as conn:
            rows = conn.execute(query, [keyword, pattern, pattern, pattern, pattern, *params, limit]).fetchall()
            return [dict(r) for r in rows]

    def get_stats(self, identity: Optional[IdentityScope] = None) -> Dict[str, int]:
        clause, params = self._identity_filter(identity)
        with self._get_conn() as conn:
            if identity is None:
                entity_count = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
            else:
                entity_count = conn.execute(
                    "SELECT COUNT(DISTINCT entity_id) FROM assertions WHERE " + clause, params).fetchone()[0]
            assertion_count = conn.execute("SELECT COUNT(*) FROM assertions WHERE " + clause, params).fetchone()[0]
            current_count = conn.execute("SELECT COUNT(*) FROM assertions WHERE status = 'current' AND " + clause, params).fetchone()[0]
            conflict_count = conn.execute("SELECT COUNT(*) FROM assertions WHERE status IN ('proposed', 'conflict', 'rejected') AND " + clause, params).fetchone()[0]
        return {
            "entities": entity_count,
            "total_assertions": assertion_count,
            "current_assertions": current_count,
            "conflicts_or_closed_branches": conflict_count
        }
