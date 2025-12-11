"""
Funciones de solo lectura para consultar PostgreSQL.
"""
from contextlib import contextmanager
from typing import Any, Dict, List

import psycopg2
import psycopg2.extras

from agent.config import AdminAgentConfig

_config = AdminAgentConfig()


@contextmanager
def _get_conn():
    conn = psycopg2.connect(
        host=_config.postgres_host,
        port=_config.postgres_port,
        user=_config.postgres_user,
        password=_config.postgres_password,
        dbname=_config.postgres_db,
    )
    try:
        yield conn
    finally:
        conn.close()


def execute_safe_query(query: str) -> List[Dict[str, Any]]:
    """Ejecuta solo SELECT; rechaza cualquier otra sentencia."""
    normalized = query.strip().lower()
    if not normalized.startswith("select"):
        raise ValueError("Solo se permiten consultas SELECT de lectura")
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query)
            rows = cur.fetchall()
            return [dict(row) for row in rows]


def get_slow_queries(limit: int = 10) -> List[Dict[str, Any]]:
    """Obtiene queries más lentas usando pg_stat_statements."""
    query = f"""
    SELECT query, mean_time, calls
    FROM pg_stat_statements
    ORDER BY mean_time DESC
    LIMIT {limit}
    """
    return execute_safe_query(query)


def get_connection_stats() -> List[Dict[str, Any]]:
    """Estadísticas de conexiones."""
    query = """
    SELECT state, count(*) AS total
    FROM pg_stat_activity
    GROUP BY state
    """
    return execute_safe_query(query)


def get_table_sizes(limit: int = 20) -> List[Dict[str, Any]]:
    """Tamaños de tablas."""
    query = f"""
    SELECT
        schemaname,
        relname,
        pg_total_relation_size(relid) AS total_bytes
    FROM pg_catalog.pg_statio_user_tables
    ORDER BY pg_total_relation_size(relid) DESC
    LIMIT {limit}
    """
    return execute_safe_query(query)


