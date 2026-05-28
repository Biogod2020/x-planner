from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Union

PathLike = Union[str, Path]


def connect(path: PathLike) -> sqlite3.Connection:
    db_path = Path(path)
    if db_path.parent and str(db_path.parent) != ".":
        db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS missions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            objective TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            brief TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mission_id INTEGER NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ready',
            next_action TEXT NOT NULL,
            expected_output TEXT NOT NULL,
            evidence_required TEXT NOT NULL,
            failure_count INTEGER NOT NULL DEFAULT 0,
            requires_failure_review INTEGER NOT NULL DEFAULT 0,
            today_mainline_on TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
            description TEXT NOT NULL,
            uri TEXT,
            audit_status TEXT NOT NULL DEFAULT 'pending',
            audit_notes TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            audited_at TEXT
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mission_id INTEGER REFERENCES missions(id) ON DELETE CASCADE,
            task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
            review_type TEXT NOT NULL,
            decision TEXT NOT NULL,
            notes TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CHECK (mission_id IS NOT NULL OR task_id IS NOT NULL)
        );

        CREATE TABLE IF NOT EXISTS risks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mission_id INTEGER REFERENCES missions(id) ON DELETE CASCADE,
            task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            mitigation TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS capacity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT NOT NULL UNIQUE,
            available_minutes INTEGER NOT NULL CHECK (available_minutes >= 0),
            energy_level INTEGER NOT NULL CHECK (energy_level BETWEEN 1 AND 5),
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS commitments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mission_id INTEGER REFERENCES missions(id) ON DELETE CASCADE,
            task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
            description TEXT NOT NULL,
            committed_on TEXT NOT NULL,
            due_on TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    connection.commit()
