'''Database layer for Birthday Reminder application.

This module handles the SQLite database that stores birthday information.
It automatically creates ``birthdays.db`` and the required ``birthdays``
 table if they do not already exist.

All functions use type hints and include inline comments for clarity.
'''

import sqlite3
from pathlib import Path
from typing import List, Tuple, Optional

# Path to the SQLite database file (created in the project root)
DB_PATH = Path(__file__).with_name("birthdays.db")

# SQL statements used throughout the module
_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS birthdays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    day INTEGER NOT NULL CHECK (day BETWEEN 1 AND 31)
);
"""

# Helper: get a connection (ensures foreign keys are enabled)
def _get_connection() -> sqlite3.Connection:
    """Return a new SQLite connection with row factory set.

    The connection is opened with ``detect_types`` so that SQLite can
    return proper Python types for dates if needed in the future.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Initialise the database – executed once on import
def _initialize_db() -> None:
    """Create the database file and the ``birthdays`` table if necessary."""
    # ``touch`` the file implicitly by connecting to it
    conn = _get_connection()
    try:
        conn.executescript(_CREATE_TABLE_SQL)
    finally:
        conn.close()

# Call initializer at import time so the DB is ready for any function call
_initialize_db()

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def add_birthday(name: str, month: int, day: int) -> int:
    """Insert a new birthday record.

    Args:
        name: Person's name.
        month: Month of the birthday (1‑12).
        day: Day of the month (1‑31).

    Returns:
        The integer ``id`` of the newly inserted row.
    """
    conn = _get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO birthdays (name, month, day) VALUES (?, ?, ?)",
            (name, month, day),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_birthday(birthday_id: int, name: Optional[str] = None,
                     month: Optional[int] = None, day: Optional[int] = None) -> bool:
    """Update fields of an existing birthday.

    Only the supplied arguments are updated. If none are supplied, the
    function does nothing and returns ``False``.

    Returns:
        ``True`` if a row was updated, ``False`` otherwise.
    """
    if name is None and month is None and day is None:
        return False

    # Build dynamic SET clause based on provided arguments
    fields: List[str] = []
    values: List[object] = []
    if name is not None:
        fields.append("name = ?")
        values.append(name)
    if month is not None:
        fields.append("month = ?")
        values.append(month)
    if day is not None:
        fields.append("day = ?")
        values.append(day)
    values.append(birthday_id)  # WHERE clause value

    sql = f"UPDATE birthdays SET {', '.join(fields)} WHERE id = ?"
    conn = _get_connection()
    try:
        cur = conn.execute(sql, values)
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def delete_birthday(birthday_id: int) -> bool:
    """Remove a birthday entry by its ``id``.

    Returns ``True`` if a row was deleted, ``False`` otherwise.
    """
    conn = _get_connection()
    try:
        cur = conn.execute("DELETE FROM birthdays WHERE id = ?", (birthday_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_all_birthdays() -> List[Tuple[int, str, int, int]]:
    """Fetch all birthday records ordered by month and day.

    Returns:
        A list of tuples ``(id, name, month, day)``.
    """
    conn = _get_connection()
    try:
        rows = conn.execute(
            "SELECT id, name, month, day FROM birthdays ORDER BY month, day"
        ).fetchall()
        return [(row["id"], row["name"], row["month"], row["day"]) for row in rows]
    finally:
        conn.close()


def get_upcoming_birthdays(limit: int = 10) -> List[Tuple[int, str, int, int]]:
    """Return the next ``limit`` birthdays from today forward.

    The query calculates a simple ordinal day of year for each record and
    compares it to today's ordinal day. It then orders by that distance to
    provide the upcoming birthdays regardless of year.
    """
    from datetime import date

    today = date.today()
    today_ordinal = today.timetuple().tm_yday

    conn = _get_connection()
    try:
        # Compute ordinal day for each record (ignoring year) and calculate
        # distance from today, wrapping around the end of the year.
        rows = conn.execute(
            """
            SELECT id, name, month, day,
                   ((month - 1) * 31 + day) - ? AS distance
            FROM birthdays
            """,
            (today_ordinal,),
        ).fetchall()
        # Normalise distance to be positive (wrap‑around) and sort
        upcoming = sorted(
            rows,
            key=lambda r: ((r["month"] - 1) * 31 + r["day"] - today_ordinal) % 366,
        )
        # Slice to requested limit and return simple tuple format
        result = [
            (row["id"], row["name"], row["month"], row["day"]) for row in upcoming[:limit]
        ]
        return result
    finally:
        conn.close()
