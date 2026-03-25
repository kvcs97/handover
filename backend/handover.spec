# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
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
