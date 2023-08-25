# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ["src/main.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("mainwindow.ui", "."),
        ("images/inamata_logo_white_128.png", "images"),
        ("images/icon_512.ico", "images"),
        ("images/icon_512.png", "images"),
        ("images/icon_256.png", "images"),
        ("images/icon_128.png", "images"),
        ("images/icon_64.png", "images"),
        ("images/icon_32.png", "images"),
        ("images/icon_16.png", "images"),
        ("fonts/Lato-Regular.ttf", "fonts"),
        ("littlefs/root_cas.pem", "littlefs"),
    ],
    hiddenimports=["PySide2.QtXml"],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
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
    name="inamata_flasher",
    icon="images/icon_512.ico",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
)
