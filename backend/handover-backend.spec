# -*- mode: python ; coding: utf-8 -*-
import glob
import os

GTK_BIN = r"C:\Program Files\GTK3-Runtime Win64\bin"
gtk_dlls = [(dll, ".") for dll in glob.glob(os.path.join(GTK_BIN, "*.dll"))]

a = Analysis(
    ['main.py'],
    pathex=[GTK_BIN],
    binaries=gtk_dlls,
    datas=[],
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name='handover-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
