from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2.extras import Json

ROOT = Path(__file__).resolve().parents[3]
RUNTIME_STATE_KEY = "draft_runtime_state"


def _database_url() -> str:
    return (
        os.getenv("DATABASE_URL", "").strip()
        or os.getenv("POSTGRES_URL", "").strip()
        or os.getenv("RENDER_POSTGRES_URL", "").strip()
    )


def _runtime_state_path() -> Path | None:
    raw_path = os.getenv("DRAFT_RUNTIME_STATE_PATH", "").strip()
    if not raw_path:
        return None
    return Path(raw_path).expanduser().resolve()


def get_storage_mode() -> str:
    if _database_url():
        return "database"
    if _runtime_state_path():
        return "file"
    return "repository"


def _connect():
    database_url = _database_url().replace("postgresql+psycopg2://", "postgresql://")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured.")
    return psycopg2.connect(database_url)


def _ensure_database_table() -> None:
    conn = _connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS runtime_state_entries (
                        key TEXT PRIMARY KEY,
                        payload JSONB NOT NULL,
                        source TEXT,
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )
    finally:
        conn.close()


def load_runtime_state() -> dict[str, Any] | None:
    if get_storage_mode() == "database":
        _ensure_database_table()
        conn = _connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT payload FROM runtime_state_entries WHERE key = %s",
                    (RUNTIME_STATE_KEY,),
                )
                row = cur.fetchone()
        finally:
            conn.close()
        return row[0] if row else None

    state_path = _runtime_state_path()
    if state_path and state_path.exists():
        return json.loads(state_path.read_text(encoding="utf-8"))
    return None


def save_runtime_state(payload: dict[str, Any], source: str) -> dict[str, Any]:
    if get_storage_mode() == "database":
        _ensure_database_table()
        conn = _connect()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO runtime_state_entries (key, payload, source)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (key)
                        DO UPDATE SET
                            payload = EXCLUDED.payload,
                            source = EXCLUDED.source,
                            updated_at = NOW()
                        RETURNING updated_at
                        """,
                        (RUNTIME_STATE_KEY, Json(payload), source),
                    )
                    updated_at = cur.fetchone()[0]
        finally:
            conn.close()
        return {
            "storage_mode": "database",
            "source": source,
            "updated_at": updated_at.isoformat(),
        }

    state_path = _runtime_state_path()
    if not state_path:
        raise RuntimeError("Runtime storage is not configured. Set DATABASE_URL or DRAFT_RUNTIME_STATE_PATH.")

    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "storage_mode": "file",
        "source": source,
        "updated_at": payload.get("updated_at"),
        "path": str(state_path),
    }


def describe_runtime_state() -> dict[str, Any]:
    state = load_runtime_state()
    state_path = _runtime_state_path()
    return {
        "storage_mode": get_storage_mode(),
        "has_persisted_state": state is not None,
        "state_path": str(state_path) if state_path else None,
        "database_configured": bool(_database_url()),
    }
