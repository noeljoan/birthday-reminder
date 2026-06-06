@echo off
rem ==============================================================
rem  Build the Birthday Reminder project into a single Windows exe
rem  (PyInstaller + hidden‑imports + icon + one‑file)
rem ==============================================================

rem ---- 1️⃣  Use the interpreter that is currently active ----------
rem (If you are inside a virtual‑env this will be that interpreter)
set "PYTHON_EXE=%~dp0venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=python"
)

rem ---- 2️⃣  Run PyInstaller ---------------------------------------
"%PYTHON_EXE%" -m PyInstaller --onefile --windowed --icon=birthday_reminder.ico --clean --noconfirm --hidden-import=customtkinter --hidden-import=pystray --hidden-import=pillow --collect-all=customtkinter --add-data="birthday_reminder.ico;." Birthday_Reminder.spec

rem ---- 3️⃣  (optional) clean up temporary folders -------------------
rem rmdir /s /q build
rem rmdir /s /q __pycache__

echo.
echo ------------------------------------------------------------
echo   Build finished!  Executable is:
echo   %cd%\dist\Birthday Reminder.exe
echo ------------------------------------------------------------
pause