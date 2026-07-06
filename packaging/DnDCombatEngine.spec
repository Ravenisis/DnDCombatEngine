# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Windows desktop application."""

from pathlib import Path


project_root = Path(SPECPATH).parent
src_root = project_root / "src"

a = Analysis(
    [str(src_root / "dnd_combat_engine" / "gui_app.py")],
    pathex=[str(src_root)],
    binaries=[],
    datas=[
        (str(src_root / "dnd_combat_engine" / "data"), "dnd_combat_engine/data"),
        (str(project_root / "LICENSE"), "."),
    ],
    hiddenimports=[
        "pypdf",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtSvg",
        "PySide6.QtWidgets",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DnDCombatEngine",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="DnDCombatEngine",
)
