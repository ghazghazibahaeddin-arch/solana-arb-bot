"""
Ghost Engine - Historical Market Database

Stores real market snapshots for later:
- backtesting
- pattern detection
- learning
- market simulation
"""

import os
import sqlite3
from typing import Optional, Dict, Any


DB_PATH = os.getenv(
    "GHOST_DB_PATH",
    "data/history.db"
)


def connect():
    """Open SQLite database connection."""

    os.makedirs(
        os.path.dirname(DB_PATH) or ".",
        exist_ok=True
    )

    conn = sqlite3.connect(
        DB_PATH,
        timeout=30
    )

    conn.execute(
        "PRAGMA journal_mode=WAL"
    )

    return conn


def create_tables():
    """Create historical market tables."""

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tokens (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            symbol TEXT,

            address TEXT,

            chain_id TEXT,

            dex_id TEXT,

            pair_address TEXT,

            price REAL,

            liquidity REAL,

            volume REAL,

            buys INTEGER DEFAULT 0,

            sells INTEGER DEFAULT 0,

            market_cap REAL DEFAULT 0,

            fdv REAL DEFAULT 0,

            score REAL DEFAULT 0,

            risk REAL DEFAULT 0,

            holders INTEGER DEFAULT 0,

            timestamp REAL NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_tokens_address_timestamp

        ON tokens(address, timestamp)
        """
    )

    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_tokens_timestamp

        ON tokens(timestamp)
        """
    )

    conn.commit()
    conn.close()


def save_snapshot(
    pair: Dict[str, Any],
    score: float = 0,
    risk: float = 0,
    holders: int = 0,
    timestamp: Optional[float] = None
):
    """
    Save one REAL market observation.

    The snapshot is never overwritten.
    Every observation becomes historical data.
    """

    create_tables()

    import time

    if timestamp is None:
        timestamp = time.time()

    base = pair.get(
        "baseToken",
        {}
    )

    liquidity_data = pair.get(
        "liquidity",
        {}
    ) or {}

    volume_data = pair.get(
        "volume",
        {}
    ) or {}

    txns = pair.get(
        "txns",
        {}
    ) or {}

    h24 = txns.get(
        "h24",
        {}
    ) or {}

    price = safe_float(
        pair.get("priceUsd")
    )

    liquidity = safe_float(
        liquidity_data.get("usd")
    )

    volume = safe_float(
        volume_data.get("h24")
    )

    buys = safe_int(
        h24.get("buys")
    )

    sells = safe_int(
        h24.get("sells")
    )

    market_cap = safe_float(
        pair.get("marketCap")
    )

    fdv = safe_float(
        pair.get("fdv")
    )

    conn = connect()

    conn.execute(
        """
        INSERT INTO tokens (
            symbol,
            address,
            chain_id,
            dex_id,
            pair_address,
            price,
            liquidity,
            volume,
            buys,
            sells,
            market_cap,
            fdv,
            score,
            risk,
            holders,
            timestamp
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            base.get("symbol"),
            base.get("address"),
            pair.get("chainId"),
            pair.get("dexId"),
            pair.get("pairAddress"),
            price,
            liquidity,
            volume,
            buys,
            sells,
            market_cap,
            fdv,
            float(score or 0),
            float(risk or 0),
            int(holders or 0),
            timestamp
        )
    )

    conn.commit()
    conn.close()


def get_recent_snapshots(
    address: str,
    limit: int = 100
):
    """Return recent observations for one token."""

    create_tables()

    conn = connect()

    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            symbol,
            address,
            price,
            liquidity,
            volume,
            buys,
            sells,
            score,
            risk,
            holders,
            timestamp

        FROM tokens

        WHERE address = ?

        ORDER BY timestamp DESC

        LIMIT ?
        """,
        (
            address,
            limit
        )
    )

    rows = cur.fetchall()

    conn.close()

    return rows


def count_snapshots():
    """Number of historical observations."""

    create_tables()

    conn = connect()

    cur = conn.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM tokens"
    )

    result = cur.fetchone()[0]

    conn.close()

    return result


def safe_float(value):

    try:
        if value is None:
            return 0.0

        return float(value)

    except (
        TypeError,
        ValueError
    ):
        return 0.0


def safe_int(value):

    try:
        if value is None:
            return 0

        return int(value)

    except (
        TypeError,
        ValueError
    ):
        return 0


create_tables()
