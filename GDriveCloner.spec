# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

block_cipher = None
HERE = Path(SPECPATH)

a = Analysis(
    [str(HERE / "main.py")],
    pathex=[str(HERE)],
    binaries=[],
    datas=[
        (str(HERE / "web"), "web"),
        (str(HERE / "auth"), "auth"),
    ],
    hiddenimports=[
        "google.auth",
        "google.auth.transport",
        "google.auth.transport.requests",
        "google.oauth2",
        "google.oauth2.credentials",
        "google_auth_oauthlib",
        "google_auth_oauthlib.flow",
        "googleapiclient",
        "googleapiclient.discovery",
        "googleapiclient.http",
        "httplib2",
        "flask",
        "werkzeug",
        "jinja2",
        "click",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy", "PIL", "scipy", "pandas"],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="GDriveCloner",
    debug=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=True,
)
