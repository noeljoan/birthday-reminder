
  # Birthday Reminder

  [![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue?logo=python)](https://www.python.org/)
  [![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
</div>

A modern desktop application for tracking birthdays with a clean CustomTkinter interface, automatic Windows toast notifications, system-tray integration, and CSV import/export support.

## Screenshot

![Dashboard](screenshot.png)

---

## Features

- **Dashboard View**: Shows upcoming birthdays (today, next 10 days), total contacts, and the next birthday with days remaining and age
- **Birthday List**: Table view with all contacts, including a "Days Remaining" countdown column
- **CRUD Operations**: Add, edit, delete, and refresh birthday entries
- **Search**: Live filtering by first name, last name, or email
- **CSV Import/Export**: Backup and restore your data in standard CSV format
- **Windows Toast Notifications**: Automatic notifications for today's birthdays and upcoming birthdays
- **System Tray**: Minimize to tray for background operation
- **Auto-Start**: Optional Windows startup integration

---

## Installation

### Requirements

- Python 3.9+
- Windows 10/11 (for toast notifications and system tray)

### Install Dependencies

```bash
# Clone the repository
git clone https://github.com/yourusername/birthday_reminder.git
cd birthday_reminder

# Create virtual environment (recommended)
python -m venv venv
.\venv\Scripts\activate  # On Windows

# Install requirements
pip install -r requirements.txt
```

### Run the Application

```bash
python main.py
```

---

## Building a Standalone EXE

A `build.bat` script is provided for easy compilation with PyInstaller.

### Quick Build

```bash
# Activate virtual environment
.\venv\Scripts\activate

# Run the build script
.\build.bat
```

The compiled executable will be available at:
```
dist\Birthday Reminder.exe
```

### Manual PyInstaller Command

```bash
pyinstaller --onefile --windowed --icon=birthday_reminder.ico main.py
```

---

## Project Structure

```
birthday_reminder/
├── main.py              # Application entry point
├── gui.py               # CustomTkinter MVC GUI implementation
├── database.py          # SQLite database layer
├── notifications.py     # Windows toast notifications
├── tray.py              # System tray integration
├── startup.py           # Windows startup utility
├── build.bat            # PyInstaller build script
├── Birthday_Reminder.spec  # PyInstaller specification
├── requirements.txt     # Python dependencies
└── README.md
```

---

## Module Overview

### `main.py`
Simple entry point that launches the GUI.

### `gui.py`
Implements an MVC architecture with:
- **Model**: Thin wrapper around database operations
- **View**: CustomTkinter UI with toolbar, table view, and dashboard cards
- **Controller**: Binds UI events to model actions, handles search, CSV import/export, and dashboard updates

### `database.py`
SQLite persistence layer providing:
- `add_birthday()` - Insert new records
- `update_birthday()` - Modify existing records
- `delete_birthday()` - Remove records
- `get_all_birthdays()` - Retrieve all entries
- `birthdays_today()` - Get today's birthdays
- `birthdays_next_10_days()` - Get upcoming birthdays
- `calculate_age()` - Age calculation with leap-year handling
- `import_csv()` / `export_csv()` - CSV import/export with duplicate detection

### `notifications.py`
Windows toast notification utilities:
- `notify_birthdays_today()` - Shows notification for today's birthdays
- `notify_upcoming_birthdays()` - Shows notification for upcoming birthdays (next 10 days)
- `send_all_notifications()` - Sends both notifications
- `start_tray_if_needed()` - Initializes system tray on Windows

### `tray.py`
System tray icon using `pystray` with:
- **Open Birthday Reminder**: Launches the main GUI
- **Check Birthdays Now**: Triggers toast notifications
- **Exit**: Closes the application

### `startup.py`
Windows startup integration:
- `enable_startup()` - Creates a .bat file in the user's startup folder
- `disable_startup()` - Removes the startup file
- `is_startup_enabled()` - Checks if auto-start is enabled

---

## CSV Format

The application expects CSV files with the following columns (in order):

```csv
FirstName,LastName,Birthday,Email,Notes,Category
John,Doe,1990-03-15,john@example.com,School friend,friend
```

- Birthday must be in `YYYY-MM-DD` format
- Duplicate entries (same first name, last name, and birthday) are ignored during import

---

## Usage

### Adding Birthdays
1. Click **"Add"** in the toolbar
2. Fill in the form (first name, last name, birthday required)
3. Click **"OK"** to save

### Searching
Type in the **Search** field to filter the birthday table by first name, last name, or email (case-insensitive).

### Dashboard
Click **"Dashboard"** to view:
- Birthdays today (names and count)
- Upcoming birthdays in the next 10 days (names and dates)
- Next birthday with date, days remaining, and upcoming age

### Import/Export
- **Import CSV**: Loads birthdays from a CSV file, skipping duplicates
- **Export CSV**: Saves all entries to a CSV file

---

## Development

### Code Style
- Type hints throughout all modules
- Inline comments explaining complex logic
- MVC separation in the GUI layer

### Testing
Run the notification module standalone for manual testing:
```bash
python notifications.py
```

---

## License

MIT License - See [LICENSE](https://github.com/noeljoan/weight-and-balance/blob/main/LICENSE) file for details.

---

## Acknowledgments

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - Modern tkinter widgets
- [pystray](https://github.com/ikonst/pystray) - System tray support
- [winotify](https://github.com/obsidianmd/winotify) - Windows toast notifications
