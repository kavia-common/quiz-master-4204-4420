"""
Database connection utilities for the Quiz backend.

This module provides:
- Lazy MySQL connection pool initialization using environment variables
- Functions to acquire/release connections
- FastAPI lifecycle helpers for startup and shutdown
"""

import os
import logging
from typing import Optional

from mysql.connector import pooling, Error as MySQLError

# Module-level variables for the connection pool
_pool: Optional[pooling.MySQLConnectionPool] = None

# Environment variable names (must be provided via .env by the orchestrator)
ENV_MYSQL_HOST = "MYSQL_HOST"
ENV_MYSQL_PORT = "MYSQL_PORT"
ENV_MYSQL_DB = "MYSQL_DB"
ENV_MYSQL_USER = "MYSQL_USER"
ENV_MYSQL_PASSWORD = "MYSQL_PASSWORD"


def _get_db_config() -> dict:
    """
    Read DB configuration from environment variables and return a dict suitable
    for mysql-connector-python connection creation.
    """
    host = os.getenv(ENV_MYSQL_HOST)
    port = os.getenv(ENV_MYSQL_PORT)
    database = os.getenv(ENV_MYSQL_DB)
    user = os.getenv(ENV_MYSQL_USER)
    password = os.getenv(ENV_MYSQL_PASSWORD)

    missing = [name for name, val in [
        (ENV_MYSQL_HOST, host),
        (ENV_MYSQL_PORT, port),
        (ENV_MYSQL_DB, database),
        (ENV_MYSQL_USER, user),
        (ENV_MYSQL_PASSWORD, password),
    ] if not val]

    if missing:
        raise RuntimeError(
            f"Missing required DB environment variables: {', '.join(missing)}. "
            "These must be set in the container .env by the orchestrator."
        )

    try:
        port_int = int(port)
    except ValueError as exc:
        raise RuntimeError(f"Invalid {ENV_MYSQL_PORT} value: {port}") from exc

    return {
        "host": host,
        "port": port_int,
        "database": database,
        "user": user,
        "password": password,
        "charset": "utf8mb4",
        "collation": "utf8mb4_unicode_ci",
        "autocommit": True,
    }


# PUBLIC_INTERFACE
def init_pool(min_size: int = 1, max_size: int = 5) -> None:
    """Initialize a global MySQL connection pool.

    This should be called on FastAPI startup.

    Raises:
        RuntimeError: if environment variables are missing or pool creation fails.
    """
    global _pool
    if _pool is not None:
        return

    cfg = _get_db_config()
    try:
        _pool = pooling.MySQLConnectionPool(
            pool_name="quiz_backend_pool",
            pool_size=max_size,
            **cfg,
        )
        # sanity check: get and return a connection
        conn = _pool.get_connection()
        conn.close()
        logging.info("MySQL connection pool initialized.")
    except MySQLError as exc:
        raise RuntimeError(f"Failed to initialize MySQL connection pool: {exc}") from exc


# PUBLIC_INTERFACE
def get_connection():
    """Acquire a connection from the global pool.

    Returns:
        mysql.connector.connection.MySQLConnection: a pooled connection

    Raises:
        RuntimeError: if the pool has not been initialized
    """
    if _pool is None:
        raise RuntimeError("DB pool not initialized. Call init_pool() on app startup.")
    try:
        return _pool.get_connection()
    except MySQLError as exc:
        raise RuntimeError(f"Failed to get DB connection: {exc}") from exc


# PUBLIC_INTERFACE
def close_pool() -> None:
    """Close the pool if supported by the driver.

    mysql-connector-python does not expose an explicit close on the pool,
    but we can attempt to clean up references and log shutdown.
    """
    global _pool
    _pool = None
    logging.info("MySQL connection pool reference cleared on shutdown.")
