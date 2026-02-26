# -*- mode: python ; coding: utf-8 -*-
# Build: pyinstaller RoomPingPro.spec
# Output: dist/RoomPingPro (or .exe on Windows, .app on macOS)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('Web', 'Web'), ('version.txt', '.')],
    hiddenimports=['pywebview'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'test', 'unittest', 'doctest', 'pydoc', 'pdb',
        'pytest', 'IPython', 'matplotlib', 'numpy', 'PIL', 'pandas', 'scipy', 'cv2',
    ],
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
    name='RoomPingPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# macOS .app bundle (ignored on Windows/Linux)
app = BUNDLE(
    exe,
    name='RoomPingPro.app',
    icon=None,
    bundle_identifier='com.roompingpro.app',
)
