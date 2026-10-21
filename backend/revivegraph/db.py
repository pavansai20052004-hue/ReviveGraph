import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .recovery_schema import SCHEMA as RECOVERY_SCHEMA


SCHEMA = """
CREATE TABLE IF NOT EXISTS registrations (
 id TEXT PRIMARY KEY, fixture_id TEXT NOT NULL, version INTEGER NOT NULL,
 data TEXT NOT NULL, created_at TEXT NOT NULL, actor TEXT NOT NULL,
 UNIQUE(fixture_id, version)
);
CREATE TABLE IF NOT EXISTS profile_versions (
 profile_id TEXT NOT NULL, version INTEGER NOT NULL, content_hash TEXT NOT NULL,
 PRIMARY KEY(profile_id, version)
);
CREATE TABLE IF NOT EXISTS fleets (
 id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, mode TEXT NOT NULL CHECK(mode IN ('simulation','physical')),
 registration_id TEXT NOT NULL REFERENCES registrations(id), revision INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS batches (
 id TEXT PRIMARY KEY, registration_id TEXT NOT NULL REFERENCES registrations(id),
 fleet_id TEXT NOT NULL, mode TEXT NOT NULL, payload TEXT NOT NULL, report TEXT NOT NULL,
 preview_revision INTEGER NOT NULL, created_at TEXT NOT NULL,
 committed_revision INTEGER, committed_at TEXT, committed_by TEXT
);
CREATE TABLE IF NOT EXISTS assessments (
 id TEXT PRIMARY KEY, subject_type TEXT NOT NULL, subject_id TEXT NOT NULL,
 batch_id TEXT NOT NULL REFERENCES batches(id), data TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS computers (
 id TEXT PRIMARY KEY, fleet_id TEXT NOT NULL REFERENCES fleets(id),
 registration_id TEXT NOT NULL REFERENCES registrations(id), profile_id TEXT NOT NULL,
 batch_id TEXT NOT NULL REFERENCES batches(id), assessment_id TEXT NOT NULL REFERENCES assessments(id),
 data TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS components (
 id TEXT PRIMARY KEY, fleet_id TEXT NOT NULL REFERENCES fleets(id),
 registration_id TEXT NOT NULL REFERENCES registrations(id),
 batch_id TEXT NOT NULL REFERENCES batches(id), assessment_id TEXT NOT NULL REFERENCES assessments(id),
 location_asset_id TEXT REFERENCES computers(id), origin_asset_id TEXT REFERENCES computers(id),
 data TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS commit_keys (
 key TEXT PRIMARY KEY, batch_id TEXT NOT NULL REFERENCES batches(id), request_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_events (
 id INTEGER PRIMARY KEY, action TEXT NOT NULL, entity_id TEXT NOT NULL,
 actor TEXT NOT NULL, occurred_at TEXT NOT NULL, data TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1, 2):
                raise RuntimeError(f"Unsupported database schema {version}; supported versions are 1 and 2")
            # executescript otherwise commits an open transaction implicitly. Keep
            # the whole additive migration and its version pin in one script.
            connection.executescript("BEGIN IMMEDIATE;\n" + SCHEMA + RECOVERY_SCHEMA +
                                     "\nPRAGMA user_version = 2;\nCOMMIT;")

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
