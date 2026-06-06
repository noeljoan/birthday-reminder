# -*- mode: python ; coding: utf-8 -*-

# ================================================================
#  PyInstaller spec for the Birthday Reminder project
# ================================================================
#   Generates:  Birthday Reminder.exe  (single‑file, windowed, icon)
#   Requires:   main.py  (the real entry point)
#   Hidden imports: customtkinter, pystray, pillow
#   Data files    : birthday_reminder.ico  (icon)
# ================================================================

import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

# ---------------------------------------------------------------
# 1️⃣ Project root (where this spec lives)
# ---------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent

# ---------------------------------------------------------------
# 2️⃣  Hidden imports – modules that PyInstaller cannot detect
# ---------------------------------------------------------------
HIDDENIMPORTS = [
    'customtkinter',
    'pystray',
    'PIL',                       # Pillow – required by pystray
]

# Also collect any sub‑modules of customtkinter that might be used
HIDDENIMPORTS += collect_submodules('customtkinter')

# ---------------------------------------------------------------
# 3️⃣  Data files to embed
# ---------------------------------------------------------------
#   (source, destination, optional sub‑folder)
#   The icon is copied into the same folder as the exe so that
#   the executable can load it at runtime.
DATA_FILES = [
    ('icon', str(PROJECT_ROOT / 'birthday_reminder.ico'), '.'),   # copy .ico next to the exe
    # If you have other static files (e.g. default CSV templates),
    # add them here in the same format.
]

# ---------------------------------------------------------------
# 4️⃣  Build the EXE object
# ---------------------------------------------------------------
executable = EXE(
    # The entry‑point that PyInstaller will execute:
    #   main.py  →  gui.main()  →  the whole UI starts
    #   This is the compiled .pyz that contains all Python bytecode.
    #   PyInstaller creates it automatically from the main script.
    #   We reference it via the magic name '__main__' (the .pyz file).
    #   The actual file name is not important – we just use the default.
    #   All other arguments are passed through.
    #   (In this custom spec we do *not* need to specify the script
    #    explicitly; PyInstaller infers it from the analysis step below.)
    __spec__,
    a_syntax_tree=None,
    # ----  NAME, ICON, CONSOLE SETTINGS  ---------------------------------
    name='Birthday Reminder',               # name shown in the file system
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,                          # <-- no console window (windowed)
    icon=str(PROJECT_ROOT / 'birthday_reminder.ico'),   # <-- our .ico file
    # version fields can stay empty for a simple exe
    # -----------------------------------------------------------------
    #  Packages that must be imported dynamically (hidden imports)
    # -----------------------------------------------------------------
    hiddenimports=HIDDENIMPORTS,
    # -----------------------------------------------------------------
    #  Files that have to be shipped alongside the exe
    # -----------------------------------------------------------------
    datas=DATA_FILES,
    # -----------------------------------------------------------------
    #  Other attributes – keep defaults unless you have a special need
    # -----------------------------------------------------------------
    version='1.0',
    product_version='1.0',
    #  … (the rest of the defaults are fine)
)

# ---------------------------------------------------------------
# 5️⃣  Collect everything into a **single** file (the --onefile flag)
# ---------------------------------------------------------------
coll = COLLECT(
    executable,
    a.binaries,
    a.zipimport,
    a.binaries,
    a.analysis,
    a.scripts,
    a.binaries,
    a.zipimport,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Birthday Reminder',
    # The following line forces a *single* file output.
    # PyInstaller already knows we want one file because we used
    # `--onefile` on the command line; here we just keep it empty.
)

# ---------------------------------------------------------------
# 6️⃣  Write the spec file out (so we can re‑run it later)
# ---------------------------------------------------------------
if __name__ == '__main__':
    coll.write('Birthday_Reminder.spec')