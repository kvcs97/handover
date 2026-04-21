# -*- mode: python ; coding: utf-8 -*-
import glob, os

# GTK3/Pango-DLLs für WeasyPrint bundeln.
# Lokal: C:\Program Files\GTK3-Runtime Win64\bin
# CI (MSYS2): C:\msys64\mingw64\bin  (nach: pacman -S mingw-w64-x86_64-pango)
_GTK_CANDIDATES = [
    r"C:\Program Files\GTK3-Runtime Win64\bin",
    r"C:\msys64\mingw64\bin",
]
_GTK_BIN = next(
    (p for p in _GTK_CANDIDATES
     if os.path.isdir(p) and any("gobject" in f.lower() for f in os.listdir(p))),
    None,
)

if _GTK_BIN and "msys64" in _GTK_BIN.lower():
    # Nur relevante Pango/Cairo-DLLs aus MSYS2 – nicht den gesamten 1000-DLL-Katalog
    _KEEP = (
        "libglib-", "libgobject-", "libgio-", "libgmodule-",
        "libpango-", "libpangocairo-", "libpangoft2-", "libpangowin32-",
        "libcairo-", "libcairo-g", "libpixman-",
        "libharfbuzz-", "libfontconfig-", "libfreetype-", "libfribidi-",
        "libpng", "libbz2", "libbrotli", "zlib1",
        "libexpat-", "libintl-", "libiconv-", "libwinpthread-",
        "libgraphite", "libunistring-", "libpcre2-8",
    )
    gtk_dlls = [
        (f, ".")
        for f in glob.glob(os.path.join(_GTK_BIN, "*.dll"))
        if os.path.basename(f).lower().startswith(_KEEP)
    ]
else:
    gtk_dlls = [(f, ".") for f in glob.glob(os.path.join(_GTK_BIN or "", "*.dll"))]

a = Analysis(
    ['main.py'],
    pathex=[_GTK_BIN] if _GTK_BIN else [],
    binaries=gtk_dlls,
    datas=[
        ('templates', 'templates'),
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.loops.asyncio',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'uvicorn.main',
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.orm',
        'msal',
        'msal.authority',
        'msal.application',
        'pypdf',
        'reportlab.pdfgen',
        'reportlab.lib.pagesizes',
        'reportlab.lib.utils',
        'email.mime.multipart',
        'email.mime.text',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='handover-backend',
    debug=False,
    strip=False,
    upx=False,
    console=True,
    onefile=True,
)
