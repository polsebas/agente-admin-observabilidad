"""Storage ligero de alertas usando SQLite (read-only para los agentes)."""

import datetime
import json
import sqlite3
from typing import Any, Dict, List, Optional

from agent.config import AdminAgentConfig

_config = AdminAgentConfig()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_config.agno_db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Crea la tabla si no existe."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id TEXT PRIMARY KEY,
                fingerprint TEXT,
                status TEXT,
                labels TEXT,
                annotations TEXT,
                received_at TEXT,
                analysis_report TEXT,
                is_duplicate INTEGER DEFAULT 0
            )
            """
        )
        conn.commit()


def save_alert(
    alert_id: str,
    fingerprint: str,
    status: str,
    labels: Dict[str, Any],
    annotations: Dict[str, Any],
    received_at: datetime.datetime,
    analysis_report: Optional[str] = None,
    is_duplicate: bool = False,
) -> None:
    """Persiste una alerta analizada."""
    init_db()
    with _connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO alerts (
                id, fingerprint, status, labels, annotations, received_at, analysis_report, is_duplicate
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                alert_id,
                fingerprint,
                status,
                json.dumps(labels or {}, ensure_ascii=False),
                json.dumps(annotations or {}, ensure_ascii=False),
                received_at.isoformat(),
                analysis_report or "",
                1 if is_duplicate else 0,
            ),
        )
        conn.commit()


def get_recent_by_fingerprint(fingerprint: str, window_minutes: int) -> List[Dict[str, Any]]:
    """Devuelve alertas recientes con el mismo fingerprint."""
    init_db()
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=window_minutes)
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM alerts
            WHERE fingerprint = ? AND received_at >= ?
            ORDER BY received_at DESC
            """,
            (fingerprint, cutoff.isoformat()),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_alert(alert_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene una alerta por ID."""
    init_db()
    with _connect() as conn:
        row = conn.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,)).fetchone()
    return _row_to_dict(row) if row else None


def list_alerts(limit: int = 50) -> List[Dict[str, Any]]:
    """Lista alertas recientes."""
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM alerts ORDER BY received_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    if not row:
        return {}
    return {
        "id": row["id"],
        "fingerprint": row["fingerprint"],
        "status": row["status"],
        "labels": _safe_json_loads(row["labels"]),
        "annotations": _safe_json_loads(row["annotations"]),
        "received_at": row["received_at"],
        "analysis_report": row["analysis_report"],
        "is_duplicate": bool(row["is_duplicate"]),
    }


def _safe_json_loads(value: str) -> Dict[str, Any]:
    try:
        return json.loads(value) if value else {}
    except Exception:
        return {}


