'''Windows 11 toast notification utilities for Birthday Reminder.

This module uses the *winotify* package (available on Windows) to display
native toast notifications. If *winotify* is unavailable the fallback is
*plyer* which works cross‑platform but provides fewer styling options.

Two public functions are provided:
- ``notify_birthdays_today()`` – shows a notification for any birthdays that
  occur today.
- ``notify_upcoming_birthdays()`` – shows a notification listing birthdays
  occurring in the next 10 days (including today).

Both functions retrieve data from ``database.py`` and calculate ages using
``calculate_age`` so the notifications include the person's current age.
'''

import datetime
from typing import List, Tuple

# Import the data‑layer functions we need
from . import database

# ---------------------------------------------------------------------------
# Helper: create and display a Windows toast using winotify (fallback to plyer)
# ---------------------------------------------------------------------------
try:
    from winotify import Notification  # type: ignore
except Exception:  # pragma: no cover – winotify may not be installed in test env
    Notification = None  # type: ignore
    try:
        from plyer import notification  # type: ignore
    except Exception:  # pragma: no cover – plyer may also be missing
        notification = None  # type: ignore

APP_ID = "Birthday Reminder"


def _show_toast(title: str, msg: str) -> None:
    """Display a Windows toast notification.

    Tries *winotify* first (preferred on Windows), falling back to *plyer*
    if the former is unavailable. The function silently does nothing if both
    libraries cannot be imported – this keeps the module importable on any
    platform.
    """
    if Notification is not None:
        # winotify creates a native toast with an optional sound.
        toast = Notification(app_id=APP_ID, title=title, msg=msg)
        # Use the default notification sound.
        toast.set_audio(audio="default", loop=False)
        toast.show()
    elif notification is not None:
        # plyer offers a very simple cross‑platform API.
        notification.notify(title=title, message=msg, app_name=APP_ID)
    else:
        # No notification backend available – fail silently.
        pass

# ---------------------------------------------------------------------------
# Formatting helpers – turn raw DB rows into human‑readable strings.
# ---------------------------------------------------------------------------
def _format_birthday(record: Tuple) -> str:
    """Return a short, readable string for a birthday ``record``.

    ``record`` layout matches ``database.get_all_birthdays`` –
    ``(id, first_name, last_name, birthday_date, email, notes, category, month, day)``.
    The function calculates the current age and returns something like:
    ``"John Doe – 32 (Apr 12)"``.
    """
    _, first, last, bdate, _email, _notes, _cat, _m, _d = record
    if not isinstance(bdate, datetime.date):
        # Defensive: if the DB returns a string, parse it.
        bdate = datetime.date.fromisoformat(str(bdate))
    age = database.calculate_age(bdate)
    return f"{first} {last} – {age} ({bdate:%b %d})"

# ---------------------------------------------------------------------------
# Public notification functions
# ---------------------------------------------------------------------------
def notify_birthdays_today() -> None:
    """Show a toast for birthdays that fall on the current date.

    If there are no birthdays today the function does nothing.
    """
    today_birthdays = database.birthdays_today()
    if not today_birthdays:
        return
    # Build a bullet‑list string – winotify renders newlines correctly.
    lines = ["Today's birthdays:"] + [_format_birthday(r) for r in today_birthdays]
    message = "\n".join(lines)
    _show_toast("Birthday Reminder – Today", message)


def notify_upcoming_birthdays() -> None:
    """Show a toast for birthdays occurring in the next 10 days.

    The notification lists each upcoming birthday on its own line. If no
    upcoming birthdays are found, nothing is shown.
    """
    upcoming = database.birthdays_next_10_days()
    if not upcoming:
        return
    lines = ["Upcoming birthdays (next 10 days):"] + [_format_birthday(r) for r in upcoming]
    message = "\n".join(lines)
    _show_toast("Birthday Reminder – Upcoming", message)

# ---------------------------------------------------------------------------
# Convenience wrapper – useful for a scheduled task that wants both.
# ---------------------------------------------------------------------------
def send_all_notifications() -> None:
    """Send both today and upcoming birthday notifications.

    This helper can be invoked from a background scheduler (e.g. via the
    ``/loop`` or ``CronCreate`` skill) to keep the user informed.
    """
    notify_birthdays_today()
    notify_upcoming_birthdays()

# ---------------------------------------------------------------------------
# When run as a script, fire the notifications immediately – handy for
# manual testing.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    send_all_notifications()
