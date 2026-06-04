'''Utility for managing Windows Startup shortcut for the Birthday Reminder app.

Provides three public functions:
- ``enable_startup()``   – creates a shortcut (batch file) in the user's
  Startup folder so the app launches automatically on login.
- ``disable_startup()``  – removes the shortcut if it exists.
- ``is_startup_enabled()`` – returns ``True`` when the shortcut is present.

The implementation deliberately uses a small ``.bat`` wrapper instead of a
``.lnk`` file to avoid the need for ``pywin32``/``winshell`` which are not
standard on all systems. The batch file runs the project's ``main.py`` using
the interpreter that launched this script (``sys.executable``).
'''

import os
import sys
from pathlib import Path

# Name of the startup helper file – using ``.bat`` ensures it works without extra COM deps.
STARTUP_FILENAME = "Birthday Reminder.bat"

def _startup_folder() -> Path:
    """Return the absolute path to the current user’s Startup folder.

    The folder resolves to ``%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup``.
    """
    appdata = os.getenv("APPDATA")
    if not appdata:
        raise RuntimeError("Unable to locate APPDATA environment variable for startup folder.")
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"

def _batch_path() -> Path:
    """Full path to the batch file that will be placed in the Startup folder."""
    return _startup_folder() / STARTUP_FILENAME

def _project_main_path() -> Path:
    """Absolute path to the project's main entry point (``main.py``)."""
    # ``__file__`` is ``startup.py`` – the sibling ``main.py`` resides in the same directory.
    return Path(__file__).with_name("main.py").resolve()

def enable_startup() -> None:
    """Create a batch file in the Windows Startup folder to launch the app.

    The batch file runs the same Python interpreter that executed this
    function (``sys.executable``) with the project's ``main.py``.
    If the startup batch already exists it will be overwritten.
    """
    startup_dir = _startup_folder()
    startup_dir.mkdir(parents=True, exist_ok=True)
    batch_file = _batch_path()
    # Build the command line – quoting paths that may contain spaces.
    python_exe = Path(sys.executable).as_posix()
    main_script = _project_main_path().as_posix()
    # ``/C`` runs the command and exits; ``start`` decouples the process.
    command = f"@echo off\nstart \"\" \"{python_exe}\" \"{main_script}\""
    # Write the batch file (UTF‑8 text). Overwrites any existing file.
    batch_file.write_text(command, encoding="utf-8")

def disable_startup() -> None:
    """Remove the startup batch file if it exists."""
    batch_file = _batch_path()
    try:
        batch_file.unlink()
    except FileNotFoundError:
        pass  # Already disabled – nothing to do.

def is_startup_enabled() -> bool:
    """Return ``True`` when the startup batch file is present in the Startup folder."""
    return _batch_path().exists()

# ---------------------------------------------------------------------------
# Simple manual test – executed only when running this file directly.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Enable/disable Windows startup for Birthday Reminder")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--enable", action="store_true", help="Enable auto‑start on login")
    group.add_argument("--disable", action="store_true", help="Disable auto‑start on login")
    args = parser.parse_args()
    if args.enable:
        enable_startup()
        print("Startup enabled.")
    elif args.disable:
        disable_startup()
        print("Startup disabled.")
    else:
        print(f"Startup enabled: {is_startup_enabled()}")
