# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ["main.py"],
    pathex=["/home/moritz/Sandbox/ds-flasher"],
    binaries=[],
    datas=[
        ("mainwindow.ui", "."),
        ("./images/logo_white_960.png", "./images"),
        ("./images/ofai_logo_128.png", "./images"),
        ("./images/protohaus_makerspace_logo_128.png", "./images"),
        ("./images/icon_512.png", "./images"),
        ("./images/icon_256.png", "./images"),
        ("./images/icon_128.png", "./images"),
        ("./images/icon_64.png", "./images"),
        ("./images/icon_32.png", "./images"),
        ("./images/icon_16.png", "./images"),
        ("esp-idf/gen_esp32part.py", "./esp-idf"),
        ("esp-idf/spiffsgen.py", "./esp-idf"),
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
    name="togayo_flasher",
    icon="./images/icon_512.png",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
)
