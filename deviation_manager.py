
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent
DB_PATH = BASE / "deviations.sqlite"

STATES = (
    "OPEN",
    "UNDER_INVESTIGATION",
    "CORRECTIVE_ACTION",
    "CLOSED"
)

TRANSITIONS = {
    "OPEN": {"UNDER_INVESTIGATION"},
    "UNDER_INVESTIGATION": {"CORRECTIVE_ACTION"},
    "CORRECTIVE_ACTION": {"CLOSED", "UNDER_INVESTIGATION"},
    "CLOSED": set()
}


def now():
    return datetime.now(timezone.utc).isoformat()


def connect():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS Deviation (
                deviation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                shipment_id TEXT NOT NULL UNIQUE,
                report_id TEXT NOT NULL,
                original_decision TEXT NOT NULL
                    CHECK(original_decision IN ('FAIL','REVIEW')),
                status TEXT NOT NULL DEFAULT 'OPEN'
                    CHECK(status IN (
                        'OPEN',
                        'UNDER_INVESTIGATION',
                        'CORRECTIVE_ACTION',
                        'CLOSED'
                    )),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS DeviationEvent (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                deviation_id INTEGER NOT NULL,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                old_status TEXT,
                new_status TEXT,
                notes TEXT NOT NULL,
                root_cause TEXT,
                corrective_action TEXT,
                owner TEXT,
                due_date TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(deviation_id)
                    REFERENCES Deviation(deviation_id)
            );

            CREATE INDEX IF NOT EXISTS idx_deviation_status
                ON Deviation(status);

            CREATE INDEX IF NOT EXISTS idx_event_deviation
                ON DeviationEvent(deviation_id, event_id);

            CREATE TRIGGER IF NOT EXISTS prevent_event_update
            BEFORE UPDATE ON DeviationEvent
            BEGIN
                SELECT RAISE(ABORT, 'Audit events cannot be updated');
            END;

            CREATE TRIGGER IF NOT EXISTS prevent_event_delete
            BEFORE DELETE ON DeviationEvent
            BEGIN
                SELECT RAISE(ABORT, 'Audit events cannot be deleted');
            END;
        """)


def create_deviation(shipment_id, report_id, decision, actor):
    if decision not in ("FAIL", "REVIEW"):
        raise ValueError("Only FAIL or REVIEW can create deviations")

    timestamp = now()

    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")

        existing = conn.execute(
            "SELECT * FROM Deviation WHERE shipment_id = ?",
            (shipment_id,)
        ).fetchone()

        if existing:
            return dict(existing)

        cursor = conn.execute("""
            INSERT INTO Deviation
            (shipment_id, report_id, original_decision,
             status, created_at, updated_at)
            VALUES (?, ?, ?, 'OPEN', ?, ?)
        """, (shipment_id, report_id, decision,
              timestamp, timestamp))

        deviation_id = cursor.lastrowid

        conn.execute("""
            INSERT INTO DeviationEvent
            (deviation_id, actor, action, old_status,
             new_status, notes, created_at)
            VALUES (?, ?, 'CREATED', NULL, 'OPEN',
                    'Deviation opened from compliance report', ?)
        """, (deviation_id, actor, timestamp))

        return dict(conn.execute(
            "SELECT * FROM Deviation WHERE deviation_id = ?",
            (deviation_id,)
        ).fetchone())


def update_deviation(deviation_id, new_status, actor,
                     notes, root_cause=None,
                     corrective_action=None,
                     owner=None, due_date=None):

    if new_status not in STATES:
        raise ValueError("Invalid deviation status")

    if not actor.strip() or not notes.strip():
        raise ValueError("Actor and notes are required")

    if new_status == "CORRECTIVE_ACTION":
        if not corrective_action or not owner or not due_date:
            raise ValueError(
                "Corrective action, owner and due date are required"
            )
        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Due date must be YYYY-MM-DD")

    if new_status == "CLOSED" and not root_cause:
        raise ValueError("Root cause is required for closure")

    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")

        deviation = conn.execute(
            "SELECT * FROM Deviation WHERE deviation_id = ?",
            (deviation_id,)
        ).fetchone()

        if deviation is None:
            raise LookupError("Deviation not found")

        old_status = deviation["status"]

        if new_status not in TRANSITIONS[old_status]:
            raise ValueError(
                f"Invalid transition: {old_status} -> {new_status}"
            )

        timestamp = now()

        conn.execute("""
            UPDATE Deviation
            SET status = ?, updated_at = ?
            WHERE deviation_id = ?
        """, (new_status, timestamp, deviation_id))

        conn.execute("""
            INSERT INTO DeviationEvent
            (deviation_id, actor, action, old_status,
             new_status, notes, root_cause,
             corrective_action, owner, due_date, created_at)
            VALUES (?, ?, 'STATUS_CHANGE', ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            deviation_id, actor.strip(), old_status,
            new_status, notes.strip(), root_cause,
            corrective_action, owner, due_date, timestamp
        ))

        return dict(conn.execute(
            "SELECT * FROM Deviation WHERE deviation_id = ?",
            (deviation_id,)
        ).fetchone())


def list_deviations():
    with connect() as conn:
        return [
            dict(row) for row in conn.execute("""
                SELECT * FROM Deviation
                ORDER BY updated_at DESC, deviation_id DESC
            """).fetchall()
        ]


def get_deviation(deviation_id):
    with connect() as conn:
        deviation = conn.execute(
            "SELECT * FROM Deviation WHERE deviation_id = ?",
            (deviation_id,)
        ).fetchone()

        if deviation is None:
            return None

        events = conn.execute("""
            SELECT * FROM DeviationEvent
            WHERE deviation_id = ?
            ORDER BY event_id
        """, (deviation_id,)).fetchall()

        return {
            "deviation": dict(deviation),
            "events": [dict(row) for row in events]
        }


if __name__ == "__main__":
    init_db()
    print("Deviation database initialized:", DB_PATH)
