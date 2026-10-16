# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = ['config', 'network', 'core', 'core.utils', 'core.progress', 'core.physics', 'data', 'data.items', 'data.survivors', 'data.monsters', 'data.stages', 'data.achievements', 'models', 'models.skybox', 'models.survivors', 'models.enemies', 'models.bosses', 'models.items', 'models.structures', 'entities', 'entities.fx', 'entities.projectile', 'entities.survivor', 'entities.survivor_skills', 'entities.remote_player', 'entities.enemy', 'entities.boss_ai', 'world', 'world.item_drop', 'world.interactables', 'world.teleporter', 'world.stage_builder', 'world.lunar', 'net', 'net.network_manager', 'ui', 'ui.diorama', 'ui.setup_screens', 'ui.lobby', 'ui.net_handler', 'ui.game_manager', 'ursina', 'panda3d.core', 'direct', 'screeninfo']
tmp_ret = collect_all('ursina')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('panda3d')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('direct')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('screeninfo')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name='RiskOfPython2',
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
    name='RiskOfPython2',
)
