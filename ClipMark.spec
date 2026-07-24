# -*- mode: python ; coding: utf-8 -*-
import sys


a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'clipmark',
        'clipmark.models',
        'clipmark.storage',
        'clipmark.player',
        'clipmark.marker_panel',
        'clipmark.ai_client',
        'clipmark.settings',
        'clipmark.tts',
        'clipmark.exporter',
        'clipmark.export_dialog',
        'clipmark.app',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.QtMultimedia',
        'PyQt5.QtMultimediaWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# One-dir: EXE without embedded binaries, COLLECT gathers everything
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ClipMark',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ClipMark',
)

# macOS: wrap the folder into .app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='ClipMark.app',
        icon=None,
        bundle_identifier='com.clipmark.app',
    )
