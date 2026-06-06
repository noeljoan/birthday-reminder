"""Database layer for Birthday Reminder application.

This module handles the SQLite database that stores birthday information.
It automatically creates ``birthdays.db`` and the required ``birthdays``
 table if they do not already exist.

All functions use type hints and include inline comments for clarity.
"""

import csv
import datetime
import sqlite3
from pathlib import Path
from typing import List, Tuple, Optional

# Path to the SQLite database file (created in the project root)
DB_PATH = Path(__file__).with_name("birthdays.db")
print("DATABASE:", DB_PATH.resolve())

# SQL statements used throughout the module
_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS birthdays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    birthday TEXT NOT NULL,          -- stored as ISO date string YYYY-MM-DD
    email TEXT,
    notes TEXT,
    category TEXT,
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
    """Create the database file and the ``birthdays`` table if necessary.

    The original implementation dropped the ``birthdays`` table on each import,
    which erased all persisted records. The fix now only creates the table if it
    does not already exist, preserving data across restarts.
    """
    conn = _get_connection()
    try:
        # Create the table with the correct schema if it does not exist
        conn.executescript(_CREATE_TABLE_SQL)
    finally:
        conn.close()

# Call initializer at import time so the DB is ready for any function call
_initialize_db()

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def add_birthday(
    first_name: str,
    last_name: str,
    birthday: datetime.date,
    email: Optional[str] = None,
    notes: Optional[str] = None,
    category: Optional[str] = None,
) -> int:
    """Insert a new birthday record.

    Args:
        first_name: Person's first name.
        last_name: Person's last name.
        birthday: Date of birth (datetime.date).
        email: Optional email address.
        notes: Optional free-form notes.
        category: Optional category (e.g., "family", "friend").

    Returns:
        The integer ``id`` of the newly inserted row.
    """
    conn = _get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO birthdays
               (first_name, last_name, birthday, email, notes, category, month, day)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                first_name,
                last_name,
                birthday.isoformat(),
                email,
                notes,
                category,
                birthday.month,
                birthday.day,
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_birthday(
    birthday_id: int,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    birthday: Optional[datetime.date] = None,
    email: Optional[str] = None,
    notes: Optional[str] = None,
    category: Optional[str] = None,
) -> bool:
    """Update fields of an existing birthday.

    Only supplied arguments are updated. Returns ``True`` if a row was updated.
    """
    # Build dynamic SET clause based on provided arguments
    fields: List[str] = []
    values: List[object] = []
    if first_name is not None:
        fields.append("first_name = ?")
        values.append(first_name)
    if last_name is not None:
        fields.append("last_name = ?")
        values.append(last_name)
    if birthday is not None:
        fields.append("birthday = ?")
        values.append(birthday.isoformat())
        fields.append("month = ?")
        values.append(birthday.month)
        fields.append("day = ?")
        values.append(birthday.day)
    if email is not None:
        fields.append("email = ?")
        values.append(email)
    if notes is not None:
        fields.append("notes = ?")
        values.append(notes)
    if category is not None:
        fields.append("category = ?")
        values.append(category)
    if not fields:
        return False
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


def get_all_birthdays() -> List[Tuple[int, str, str, datetime.date, Optional[str], Optional[str], Optional[str], int, int]]:
    """Fetch all birthday records ordered by month and day.

    Returns:
        A list of tuples ``(id, first_name, last_name, birthday_date, email, notes, category, month, day)``.
    """
    conn = _get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, first_name, last_name, birthday, email, notes, category, month, day
            FROM birthdays
            ORDER BY month, day
            """
        ).fetchall()
        result: List[Tuple[int, str, str, datetime.date, Optional[str], Optional[str], Optional[str], int, int]] = []
        for row in rows:
            bdate = datetime.date.fromisoformat(row["birthday"]) if row["birthday"] else None
            result.append((row["id"], row["first_name"], row["last_name"], bdate, row["email"], row["notes"], row["category"], row["month"], row["day"]))
        return result
    finally:
        conn.close()


def get_upcoming_birthdays(limit: int = 10) -> List[Tuple[int, str, str, datetime.date, Optional[str], Optional[str], Optional[str], int, int]]:
    """Return the next ``limit`` birthdays from today forward.

    The query calculates an ordinal day of year for each record and
    compares it to today's ordinal day. It then orders by that distance
    to provide the upcoming birthdays regardless of year.
    """
    from datetime import date
    today = date.today()
    today_ordinal = today.timetuple().tm_yday
    conn = _get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, first_name, last_name, birthday, email, notes, category, month, day
            FROM birthdays
            """
        ).fetchall()
        upcoming = sorted(
            rows,
            key=lambda r: ((r["month"] - 1) * 31 + r["day"] - today_ordinal) % 366,
        )
        result: List[Tuple[int, str, str, datetime.date, Optional[str], Optional[str], Optional[str], int, int]] = []
        for row in upcoming[:limit]:
            bdate = datetime.date.fromisoformat(row["birthday"]) if row["birthday"] else None
            result.append((row["id"], row["first_name"], row["last_name"], bdate, row["email"], row["notes"], row["category"], row["month"], row["day"]))
        return result
    finally:
        conn.close()

# ---------------------------------------------------------------------------
# Birthday calculation utilities
# ---------------------------------------------------------------------------

def _is_leap(year: int) -> bool:
    """Return ``True`` if *year* is a leap year in the Gregorian calendar."""
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def calculate_age(birth: datetime.date, as_of: datetime.date = None) -> int:
    """Calculate the age for *birth* relative to *as_of* (defaults to today).

    Handles leap-year birthdays correctly – if the birthdate is February 29
    and the comparison year is not a leap year, the anniversary is treated
    as March 1 for the purpose of "has the birthday occurred yet?".

    Args:
        birth: The birth ``datetime.date``.
        as_of: The date to calculate the age against; if ``None``, today's
               date is used.

    Returns:
        Age in full years (int).
    """
    if as_of is None:
        as_of = datetime.date.today()
    years = as_of.year - birth.year
    birthday_month = birth.month
    birthday_day = birth.day
    current_year = as_of.year
    if birthday_month == 2 and birthday_day == 29 and not _is_leap(current_year):
        anniversary_month = 3
        anniversary_day = 1
    else:
        anniversary_month = birthday_month
        anniversary_day = birthday_day
    if (as_of.month, as_of.day) < (anniversary_month, anniversary_day):
        years -= 1
    return years


def birthdays_today() -> List[Tuple[int, str, str, datetime.date, Optional[str], Optional[str], Optional[str], int, int]]:
    """Return all records whose birthday matches today's month and day.

    Leap-year handling: if today is Feb 29 and a stored birthday is
    Feb 28 (or vice-versa), it will *not* be considered a match; the
    stored ``month``/``day`` values are used directly.
    """
    today = datetime.date.today()
    return [rec for rec in get_all_birthdays() if rec[7] == today.month and rec[8] == today.day]


def birthdays_next_10_days() -> List[Tuple[int, str, str, datetime.date, Optional[str], Optional[str], Optional[str], int, int]]:
    """Return birthdays occurring within the next 10 days, including today.

    The function respects leap-year boundaries when computing the distance
    to each birthday, so a Feb 28 birthday will still be found on Feb 28
    even in a non-leap year.
    """
    today = datetime.date.today()
    today_ordinal = today.timetuple().tm_yday
    limit_days = 10
    conn = _get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, first_name, last_name, birthday, email, notes, category, month, day
            FROM birthdays
            """
        ).fetchall()
        def distance(month: int, day: int) -> int:
            target_ordinal = (month - 1) * 31 + day
            diff = target_ordinal - today_ordinal
            return diff if diff >= 0 else diff + 366
        upcoming = sorted(rows, key=lambda r: distance(r["month"], r["day"]))
        result: List[Tuple[int, str, str, datetime.date, Optional[str], Optional[str], Optional[str], int, int]] = []
        for row in upcoming:
            dist = distance(row["month"], row["day"])
            if dist > limit_days:
                break
            bdate = datetime.date.fromisoformat(row["birthday"]) if row["birthday"] else None
            result.append((row["id"], row["first_name"], row["last_name"], bdate, row["email"], row["notes"], row["category"], row["month"], row["day"]))
        return result
    finally:
        conn.close()

# ---------------------------------------------------------------------------
# CSV import / export utilities
# ---------------------------------------------------------------------------

def import_csv(file_path: str) -> int:
    """Import birthday records from a CSV file.

    Expected CSV columns (no header required):
    ``FirstName,LastName,Birthday,Email,Notes,Category``

    ``Birthday`` must be in ``YYYY-MM-DD`` format. Rows that cannot be parsed
    are skipped. Duplicate entries (same first name, last name, and birthday) are ignored.
    The function returns the number of newly imported records.
    """
    count = 0
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) < 6:
                continue  # malformed line
            first, last, bdate_str, email, notes, category = [c.strip() for c in row]
            try:
                bdate = datetime.datetime.strptime(bdate_str, "%Y-%m-%d").date()
            except Exception:
                continue  # skip invalid date
            # Check for duplicate
            existing = conn = _get_connection()
            try:
                dup = conn.execute(
                    "SELECT 1 FROM birthdays WHERE first_name = ? AND last_name = ? AND birthday = ?",
                    (first, last, bdate.isoformat()),
                ).fetchone()
            finally:
                conn.close()
            if dup:
                continue
            add_birthday(first, last, bdate, email or None, notes or None, category or None)
            count += 1
    return count


def export_csv(file_path: str) -> int:
    """Export all birthday records to a CSV file.

    The output uses the same column order as the import format. Returns the
    number of rows written.
    """
    records = get_all_birthdays()
    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for rec in records:
            _, first, last, bdate, email, notes, category, _, _ = rec
            writer.writerow([first, last, bdate.isoformat(), email or "", notes or "", category or ""])
    return len(records)