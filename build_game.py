import os
import sys
import shutil
import platform
import PyInstaller.__main__

# Принудительно включаем UTF-8 для вывода в консоль на любых серверах
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

APP_NAME = 'RiskOfPython2'
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

HIDDEN_IMPORTS = [
    'config', 'network',
    'core', 'core.utils', 'core.progress', 'core.physics',
    'data', 'data.items', 'data.survivors', 'data.monsters', 'data.stages', 'data.achievements',
    'models', 'models.skybox', 'models.survivors', 'models.enemies', 'models.bosses', 'models.items', 'models.structures',
    'entities', 'entities.fx', 'entities.projectile', 'entities.survivor', 'entities.survivor_skills',
    'entities.remote_player', 'entities.enemy', 'entities.boss_ai',
    'world', 'world.item_drop', 'world.interactables', 'world.teleporter', 'world.stage_builder', 'world.lunar',
    'net', 'net.network_manager',
    'ui', 'ui.diorama', 'ui.setup_screens', 'ui.lobby', 'ui.net_handler', 'ui.game_manager',
    'ursina', 'panda3d.core', 'direct', 'screeninfo', 'PIL', 'pyperclip'
]


def build():
    os_name = platform.system().lower()
    print(f"=== Building {APP_NAME} for platform: {os_name.upper()} ===")

    args = [
        'main.py',
        f'--name={APP_NAME}',
        '--noconfirm',
        '--clean',
        '--onedir',
        '--windowed',
        '--collect-all=ursina',
        '--collect-all=panda3d',
        '--collect-all=direct',
        '--collect-all=screeninfo',
        '--collect-all=panda3d_gltf',
        '--collect-all=simplepbr',
    ]

    for mod in HIDDEN_IMPORTS:
        args.append(f'--hidden-import={mod}')

    PyInstaller.__main__.run(args)

    dist_folder = os.path.join(ROOT_DIR, 'dist', APP_NAME)
    if os.path.exists(dist_folder):
        archive_format = 'gztar' if os_name == 'linux' else 'zip'
        archive_base = os.path.join(ROOT_DIR, 'dist', f'{APP_NAME}_{os_name}_x64')
        out_file = shutil.make_archive(archive_base, archive_format, os.path.join(ROOT_DIR, 'dist'), APP_NAME)
        print(f"\n[DONE] Executable folder: {dist_folder}")
        print(f"[ARCHIVE] Created release archive: {out_file}")


if __name__ == '__main__':
    build()