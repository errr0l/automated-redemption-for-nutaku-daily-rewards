# -*- mode: python ; coding: utf-8 -*-
import shutil
import os
import platform

current_dir = os.getcwd()
system_name = platform.system()
_split = "\\" if system_name == 'Windows' else '/'

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Automated-Redemption',
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

#shutil.copyfile(current_dir + '/src/config.txt', '{0}/config.txt'.format(DISTPATH))
path = ['', 'src', 'config.txt']
shutil.copyfile(current_dir + _split.join(path), '{0}{1}{2}'.format(DISTPATH, _split, path[2]))
