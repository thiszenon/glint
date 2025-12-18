# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src\\glint\\cli\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('D:\\ALLProgrammes\\glint\\src\\glint/web/templates', 'glint/web/templates'), ('D:\\ALLProgrammes\\glint\\src\\glint/web/static', 'glint/web/static'), ('D:\\ALLProgrammes\\glint\\src\\glint/assets', 'glint/assets')],
    hiddenimports=['sqlmodel', 'sqlalchemy', 'typer', 'rich', 'flask', 'plyer', 'requests', 'urllib3', 'questionary', 'customtkinter'],
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
    name='glint',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
