"""Single-node SQLite ledger, durable recalculation queue and notification log."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

from app.domain import Event, EventAdapter, State, baseline, replay


class Conflict(ValueError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as conn:
            if conn.execute("PRAGMA user_version").fetchone()[0] not in (0, 1):
                raise ValueError("Unsupported database schema version; preserve the database and migrate explicitly")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS generations (
                    id INTEGER PRIMARY KEY, initial TEXT NOT NULL, state TEXT NOT NULL,
                    request TEXT, demo_cursor INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT, generation INTEGER NOT NULL,
                    event_id TEXT NOT NULL, effective TEXT NOT NULL, payload TEXT NOT NULL,
                    UNIQUE(generation, event_id)
                );
                CREATE TABLE IF NOT EXISTS evaluations (
                    id TEXT PRIMARY KEY, generation INTEGER NOT NULL, version INTEGER NOT NULL,
                    request TEXT NOT NULL, result TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS jobs (
                    generation INTEGER PRIMARY KEY, version INTEGER NOT NULL, request TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS notifications (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT, generation INTEGER NOT NULL,
                    version INTEGER NOT NULL, kind TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT, generation INTEGER NOT NULL,
                    kind TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL
                );
                PRAGMA user_version=1;
                CREATE INDEX IF NOT EXISTS events_identity ON events(event_id);
            """)
        with self.transaction() as conn:
            if conn.execute("SELECT value FROM settings WHERE key='active'").fetchone() is None:
                self._new_generation(conn, 1)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self.connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def _active(self, conn: sqlite3.Connection) -> int:
        return int(conn.execute("SELECT value FROM settings WHERE key='active'").fetchone()[0])

    def _state(self, conn: sqlite3.Connection) -> State:
        row = conn.execute("SELECT state FROM generations WHERE id=?", (self._active(conn),)).fetchone()
        return State.model_validate_json(row[0])

    def state(self) -> State:
        with self.connection() as conn:
            return self._state(conn)

    def analysis_snapshot(self, expected_version: int | None = None, expected_generation: int | None = None) -> State:
        with self.connection() as conn:
            conn.execute('BEGIN')
            state = self._state(conn)
            self._guard(state, expected_version, expected_generation)
            return state

    def overview_snapshot(self) -> tuple[State, dict[str, Any] | None, bool, int]:
        """All overview facts come from one SQLite read snapshot."""
        with self.connection() as conn:
            conn.execute('BEGIN')
            state = self._state(conn)
            rows = conn.execute("SELECT result FROM evaluations WHERE generation=? AND COALESCE(json_extract(result,'$.scope'),'live')='live' "
                                'ORDER BY (version=?) DESC, created_at DESC, rowid DESC LIMIT 1',
                                (state.generation, state.version)).fetchone()
            pending = conn.execute('SELECT 1 FROM jobs WHERE generation=?', (state.generation,)).fetchone()
            cursor = conn.execute('SELECT COALESCE(MAX(seq),0) FROM notifications').fetchone()[0]
            return state, json.loads(rows[0]) if rows else None, bool(pending), cursor

    def _new_generation(self, conn: sqlite3.Connection, generation: int) -> State:
        state = baseline(generation)
        conn.execute("INSERT INTO generations(id,initial,state,created_at) VALUES(?,?,?,?)",
                     (generation, state.model_dump_json(), state.model_dump_json(), now()))
        conn.execute("INSERT OR REPLACE INTO settings VALUES('active',?)", (generation,))
        return state

    def _notify(self, conn: sqlite3.Connection, state: State, kind: str, detail: dict[str, Any]) -> None:
        conn.execute("INSERT INTO notifications(generation,version,kind,detail,created_at) VALUES(?,?,?,?,?)",
                     (state.generation, state.version, kind, json.dumps(detail), now()))
        conn.execute("INSERT INTO audit(generation,kind,detail,created_at) VALUES(?,?,?,?)",
                     (state.generation, kind, json.dumps(detail), now()))

    @staticmethod
    def _guard(state: State, expected_version: int | None, expected_generation: int | None) -> None:
        if ((expected_version is not None and state.version != expected_version) or
                (expected_generation is not None and state.generation != expected_generation)):
            raise Conflict("Financial state changed; refresh and retry")

    def _accept(self, conn: sqlite3.Connection, event: Event,
                expected_version: int | None = None, expected_generation: int | None = None) -> dict[str, Any]:
        state = self._state(conn)
        payload = event.model_dump_json()
        existing = conn.execute("SELECT seq,generation,payload FROM events WHERE event_id=? ORDER BY seq",
                                (event.event_id,)).fetchall()
        if existing:
            matched = next((row for row in existing if row['payload'] == payload), None)
            if matched is None:
                raise Conflict("Event ID already accepted with different content")
            version = conn.execute("SELECT COUNT(*) FROM events WHERE generation=? AND seq<=?",
                                   (matched['generation'], matched['seq'])).fetchone()[0]
            return dict(duplicate=True, event_id=event.event_id, generation=matched['generation'],
                        state_version=version)
        self._guard(state, expected_version, expected_generation)
        conn.execute("INSERT INTO events(generation,event_id,effective,payload) VALUES(?,?,?,?)",
                     (state.generation, event.event_id, event.timestamp.isoformat(), payload))
        row = conn.execute("SELECT initial, request FROM generations WHERE id=?", (state.generation,)).fetchone()
        events = [EventAdapter.validate_json(item[0]) for item in conn.execute(
            "SELECT payload FROM events WHERE generation=? ORDER BY seq", (state.generation,))]
        updated = replay(State.model_validate_json(row[0]), events)
        conn.execute("UPDATE generations SET state=? WHERE id=?", (updated.model_dump_json(), state.generation))
        if row[1] and json.loads(row[1]).get("proposal_id", "proposal") in updated.proposals:
            conn.execute("INSERT OR REPLACE INTO jobs VALUES(?,?,?)",
                         (state.generation, updated.version, row[1]))
        else:
            conn.execute("DELETE FROM jobs WHERE generation=?", (state.generation,))
        affected = [item[0] for item in conn.execute(
            "SELECT id FROM evaluations WHERE generation=? AND coalesce(json_extract(result,'$.scope'),'live')='live' ORDER BY rowid",
            (updated.generation,))]
        self._notify(conn, updated, "EVENT_ACCEPTED", {"event_id": event.event_id, "type": event.type,
            'affected_evaluation_ids': affected, 'state_version': updated.version,
            'recalculation_scheduled': conn.execute('SELECT 1 FROM jobs WHERE generation=?', (updated.generation,)).fetchone() is not None})
        return dict(duplicate=False, event_id=event.event_id, generation=updated.generation,
                    state_version=updated.version)

    def accept(self, event: Event, expected_version: int | None = None,
               expected_generation: int | None = None) -> dict[str, Any]:
        with self.transaction() as conn:
            return self._accept(conn, event, expected_version, expected_generation)

    def reset(self, expected_version: int | None = None, expected_generation: int | None = None) -> State:
        with self.transaction() as conn:
            self._guard(self._state(conn), expected_version, expected_generation)
            old = self._active(conn)
            state = self._new_generation(conn, old + 1)
            conn.execute("DELETE FROM jobs WHERE generation=?", (old,))
            self._notify(conn, state, "DEMO_RESET", {"previous_generation": old})
            return state

    def scenario(self, initial: State, expected_version: int | None = None,
                 expected_generation: int | None = None) -> State:
        with self.transaction() as conn:
            self._guard(self._state(conn), expected_version, expected_generation)
            old = self._active(conn)
            state = initial.model_copy(update={"generation": old+1, "version": 0}, deep=True)
            conn.execute("INSERT INTO generations(id,initial,state,created_at) VALUES(?,?,?,?)",
                         (state.generation, state.model_dump_json(), state.model_dump_json(), now()))
            conn.execute("UPDATE settings SET value=? WHERE key='active'", (state.generation,))
            conn.execute("DELETE FROM jobs WHERE generation=?", (old,))
            self._notify(conn, state, "SCENARIO_CREATED", {"previous_generation": old, "initial_state": state.model_dump(mode="json")})
            return state

    def events(self, limit: int = 50, before: int | None = None,
               generation: int | None = None) -> list[dict[str, Any]]:
        with self.connection() as conn:
            selected = generation or self._active(conn)
            rows = conn.execute("SELECT seq,payload FROM events WHERE generation=? AND seq<? ORDER BY seq DESC LIMIT ?",
                                (selected, before or 2**63-1, min(limit, 100)))
            return [{"seq": row[0], "event": json.loads(row[1])} for row in rows]

    def notifications(self, after: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute("SELECT * FROM notifications WHERE seq>? ORDER BY seq LIMIT ?", (after, limit))
            return [{**dict(row), "detail": json.loads(row["detail"])} for row in rows]

    def audit(self, limit: int = 50, before: int | None = None) -> list[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute("SELECT * FROM audit WHERE seq<? ORDER BY seq DESC LIMIT ?",
                                (before or 2**63-1, min(limit, 100)))
            return [{**dict(row), "detail": json.loads(row["detail"])} for row in rows]

    def schedule(self, request: dict[str, Any], expected_version: int | None = None,
                 expected_generation: int | None = None) -> State:
        with self.transaction() as conn:
            state = self._state(conn)
            self._guard(state, expected_version, expected_generation)
            if request.get('proposal_id', 'proposal') not in state.proposals:
                raise ValueError("Unknown payment proposal")
            encoded = json.dumps(request, sort_keys=True)
            conn.execute("UPDATE generations SET request=? WHERE id=?", (encoded, state.generation))
            conn.execute("INSERT OR REPLACE INTO jobs VALUES(?,?,?)", (state.generation, state.version, encoded))
            return state

    def pending(self) -> tuple[State, dict[str, Any]] | None:
        with self.connection() as conn:
            conn.execute("BEGIN")
            state = self._state(conn)
            row = conn.execute("SELECT request FROM jobs WHERE generation=?", (state.generation,)).fetchone()
            return (state, json.loads(row[0])) if row else None

    def save_evaluation(self, result: dict[str, Any], request: dict[str, Any]) -> None:
        with self.transaction() as conn:
            self._save_evaluation(conn, result, request)

    def save_experiment(self, result: dict[str, Any], request: dict[str, Any]) -> None:
        with self.transaction() as conn:
            if result.get('scope') != 'experiment':
                raise ValueError('Explicit experiment scope required')
            self._guard(self._state(conn), result['state_version'], result['generation'])
            self._save_evaluation(conn, result, request)

    def _save_evaluation(self, conn: sqlite3.Connection, result: dict[str, Any], request: dict[str, Any]) -> None:
        conn.execute("INSERT INTO evaluations VALUES(?,?,?,?,?,?)", (
            result["id"], result["generation"], result["state_version"],
            json.dumps(request), json.dumps(result), now()))
        experiment = result.get('scope') == 'experiment'
        if not experiment:
            conn.execute("DELETE FROM jobs WHERE generation=? AND version=? AND request=?", (
                result["generation"], result["state_version"], json.dumps(request, sort_keys=True)))
        state = self._state(conn)
        # Snapshot metadata, not the current state, identifies this immutable result.
        historical = state.model_copy(update={"generation": result["generation"],
                                               "version": result["state_version"]})
        self._notify(conn, historical, 'EXPERIMENT_SAVED' if experiment else "EVALUATION_COMPLETED", {
            "evaluation_id": result["id"], 'scope': result.get('scope', 'live'),
            'recommendation': result.get('recommendation'), 'state_version': result['state_version'],
            'policy': (result.get('decision_evidence') or {}).get('primary_policy', 'legacy')})


    def recalculate(self, expected_version: int | None = None, expected_generation: int | None = None) -> State:
        with self.transaction() as conn:
            state = self._state(conn)
            self._guard(state, expected_version, expected_generation)
            row = conn.execute('SELECT request FROM generations WHERE id=?', (state.generation,)).fetchone()
            if row[0] is None:
                raise ValueError('Evaluate a payment first to establish calculation settings')
            conn.execute('INSERT OR REPLACE INTO jobs VALUES(?,?,?)', (state.generation, state.version, row[0]))
            return state

    def decisions(self, limit: int = 30, before: str | None = None,
                  generation: int | None = None) -> list[dict[str, Any]]:
        with self.connection() as conn:
            selected = generation or self._active(conn)
            stamp, separator, rowid = (before or '9999').partition('|')
            if separator and (not rowid.isdigit() or not 0 < int(rowid) <= 2**63-1):
                raise ValueError('Invalid decision cursor')
            rows = conn.execute("SELECT result FROM evaluations WHERE generation=? AND "
                                "(created_at<? OR (created_at=? AND rowid<?)) "
                                "ORDER BY created_at DESC, rowid DESC LIMIT ?",
                                (selected, stamp, stamp, int(rowid) if separator else 0, min(limit, 100)))
            return [json.loads(row[0]) for row in rows]

    def decision_cursor(self, identifier: str) -> str:
        with self.connection() as conn:
            row = conn.execute('SELECT created_at,rowid FROM evaluations WHERE id=?', (identifier,)).fetchone()
            return f'{row[0]}|{row[1]}'

    def decision(self, identifier: str) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = conn.execute("SELECT result FROM evaluations WHERE id=?", (identifier,)).fetchone()
            return json.loads(row[0]) if row else None

    def next_demo(self, expected_version: int | None = None,
                  expected_generation: int | None = None) -> dict[str, Any]:
        with self.transaction() as conn:
            state = self._state(conn)
            self._guard(state, expected_version, expected_generation)
            cursor = conn.execute("SELECT demo_cursor FROM generations WHERE id=?", (state.generation,)).fetchone()[0]
            if cursor >= 3:
                return {"completed": True, "accepted": None}
            base = dict(event_id=f"feed-{state.generation}-{cursor}", business_id="demo", timestamp=now())
            payload: dict[str, Any]
            if cursor == 0:
                payload = dict(type="RECEIVABLE_DELAYED", receivable_id="customer",
                               expected_date=(state.receivables["customer"].expected_date + timedelta(days=3)).isoformat())
            elif cursor == 1:
                payload = dict(type="EXPENSE_RECORDED", obligation=dict(
                    id=f"feed-repair-{state.generation}", label="Equipment repair", amount_paise=800000,
                    due_date=(state.base_date + timedelta(days=2)).isoformat(), mandatory=True))
            else:
                receivable = state.receivables["customer"]
                remaining = receivable.amount_paise - receivable.received_paise
                if not remaining:
                    conn.execute("UPDATE generations SET demo_cursor=3 WHERE id=?", (state.generation,))
                    return {"completed": True, "accepted": None}
                payload = dict(type="RECEIVABLE_RECEIVED", receivable_id="customer", amount_paise=min(2000000, remaining))
            accepted = self._accept(conn, EventAdapter.validate_python({**base, **payload}))
            conn.execute("UPDATE generations SET demo_cursor=? WHERE id=?", (cursor + 1, state.generation))
            return {"completed": False, "accepted": accepted}
