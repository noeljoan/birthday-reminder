"""System tray integration for Birthday Reminder using pystray.

The tray icon provides quick access to the application without needing the
main window to be open all the time. It offers three menu actions:

- **Open Birthday Reminder** – launches the main GUI (``gui.main``).
- **Check Birthdays Now**      – triggers the toast notifications for today
  and upcoming birthdays.
- **Exit**                     – shuts down the tray icon and terminates the
  process.

The implementation uses a tiny generated PNG as the icon to avoid external
image files. All heavy imports (pystray, PIL) are performed lazily inside the
``start_tray`` function so the module can be imported on systems without a
display (e.g., during automated tests).
"""

import sys
import threading
from pathlib import Path

# Local imports – we reuse existing functionality.
import gui  # ``gui.main`` starts the application UI
import notifications  # toast helpers


def _create_icon_image() -> "PIL.Image.Image":
    """Generate a simple 64×64 icon for the tray.

    The icon is a solid teal square with a small white "B" letter; this
    avoids having to ship a separate image file. ``pystray`` expects a
    ``PIL.Image`` instance.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont  # type: ignore
    except Exception as exc:  # pragma: no cover – Pillow should be present in the env
        raise RuntimeError("Pillow is required for the system-tray icon") from exc

    size = (64, 64)
    img = Image.new("RGBA", size, (0, 112, 192, 255))  # teal background
    draw = ImageDraw.Draw(img)
    # Draw a white "B" – using a generic font.
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except Exception:
        font = ImageFont.load_default()
    w, h = draw.textsize("B", font=font)
    draw.text(((size[0] - w) / 2, (size[1] - h) / 2 - 4), "B", fill="white", font=font)
    return img


def _open_app() -> None:
    """Launch the main GUI in a new thread.

    ``gui.main`` creates its own ``CTk`` instance and runs ``mainloop``. To
    keep the tray responsive we start the GUI in a separate daemon thread.
    """
    threading.Thread(target=gui.main, daemon=True).start()


def _check_birthdays() -> None:
    """Trigger toast notifications for today and upcoming birthdays."""
    notifications.send_all_notifications()


def _exit(icon) -> None:
    """Callback for the *Exit* menu item – stops the tray icon."""
    icon.stop()
    # ``sys.exit`` is safe here because the tray is the only non-daemon thread.
    sys.exit(0)


def start_tray() -> None:
    """Create and run the pystray system-tray icon.

    This function blocks until the user selects *Exit*. It should be called
    from the main entry point of the application (e.g., ``if __name__ == '__main__'``).
    """
    try:
        import pystray  # type: ignore
    except Exception as exc:  # pragma: no cover – pystray may be missing in CI
        raise RuntimeError("pystray is required for system-tray support") from exc

    # Build the menu – each item receives the ``icon`` instance as the first
    # argument, which we ignore for the simple callbacks.
    menu = pystray.Menu(
        pystray.MenuItem("Open Birthday Reminder", lambda icon: _open_app()),
        pystray.MenuItem("Check Birthdays Now", lambda icon: _check_birthdays()),
        pystray.MenuItem("Exit", lambda icon: _exit(icon)),
    )

    icon = pystray.Icon("birthday_reminder", _create_icon_image(), "Birthday Reminder", menu)
    # Run the icon event loop – this call blocks until ``icon.stop()`` is
    # invoked (via the *Exit* menu item).
    icon.run()


# ---------------------------------------------------------------------------
# When executed directly, start the tray.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    start_tray()