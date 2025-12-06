# src/db.py
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any

from .config import DB_PATH


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they don't exist."""
    conn = get_connection()
    cur = conn.cursor()

    # Each event_id appears once in events
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY,
            start_time TEXT NOT NULL,
            home_team TEXT,
            away_team TEXT
        );
        """
    )

    # odds: one row per (event_id, market_type, selection)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS odds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            market_type TEXT NOT NULL,
            selection TEXT NOT NULL,
            price REAL NOT NULL,
            scraped_at TEXT NOT NULL,
            UNIQUE(event_id, market_type, selection),
            FOREIGN KEY (event_id) REFERENCES events(event_id)
        );
        """
    )

    conn.commit()
    conn.close()


def save_odds(event: Dict[str, Any], parsed: Dict[str, Any]) -> None:
    """
    Save odds for a single event into the odds table.
    If a row for (event_id, market_type, selection) already exists,
    update the price and scraped_at instead of inserting a duplicate.
    """
    conn = get_connection()
    cur = conn.cursor()

    scraped_at = datetime.now(timezone.utc).isoformat()
    event_id = event["event_id"]

    # Ensure the event exists (ignore if already there)
    cur.execute(
        """
        INSERT OR IGNORE INTO events (event_id, start_time, home_team, away_team)
        VALUES (?, ?, ?, ?);
        """,
        (
            event_id,
            event["start_time"],
            event.get("home_team"),
            event.get("away_team"),
        ),
    )

    # MATCH_RESULT
    for mr in parsed.get("match_result", []):
        cur.execute(
            """
            INSERT INTO odds (event_id, market_type, selection, price, scraped_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(event_id, market_type, selection)
            DO UPDATE SET
                price = excluded.price,
                scraped_at = excluded.scraped_at;
            """,
            (
                event_id,
                "MATCH_RESULT",
                mr["team"],
                float(mr["price"]),
                scraped_at,
            ),
        )

    # TOTAL_GOALS_OVER/UNDER (2.5)
    for ou in parsed.get("over_under_2_5", []):
        cur.execute(
            """
            INSERT INTO odds (event_id, market_type, selection, price, scraped_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(event_id, market_type, selection)
            DO UPDATE SET
                price = excluded.price,
                scraped_at = excluded.scraped_at;
            """,
            (
                event_id,
                "TOTAL_GOALS_OVER_UNDER_2_5",
                ou["outcome"],
                float(ou["price"]),
                scraped_at,
            ),
        )

    conn.commit()
    conn.close()
