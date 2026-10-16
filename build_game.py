import os
import sys
import shutil
import platform
import PyInstaller.__main__

APP_NAME = 'RiskOfPython2'
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Все модули нашей новой структуры проекта
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
    'ursina', 'panda3d.core', 'direct', 'screeninfo'
]


def build():
    os_name = platform.system().lower()
    print(f"=== Сборка {APP_NAME} для платформы: {os_name.upper()} ===")

    args = [
        'main.py',
        f'--name={APP_NAME}',
        '--noconfirm',
        '--clean',
        '--onedir',               # Папка запускается мгновенно (без распаковки 150 МБ во временный каталог)
        '--windowed',             # Без лишнего окна консоли на Windows
        '--collect-all=ursina',   # Включает 3D-примитивы (cube, sphere, diamond), шейдеры и шрифты
        '--collect-all=panda3d',  # Включает движок Panda3D и OpenGL-пайплайны (glx / wgl)
        '--collect-all=direct',
        '--collect-all=screeninfo',
    ]

    for mod in HIDDEN_IMPORTS:
        args.append(f'--hidden-import={mod}')

    PyInstaller.__main__.run(args)

    # Упаковываем готовую сборку в удобный архив для распространения
    dist_folder = os.path.join(ROOT_DIR, 'dist', APP_NAME)
    if os.path.exists(dist_folder):
        archive_format = 'gztar' if os_name == 'linux' else 'zip'
        archive_base = os.path.join(ROOT_DIR, 'dist', f'{APP_NAME}_{os_name}_x64')
        out_file = shutil.make_archive(archive_base, archive_format, os.path.join(ROOT_DIR, 'dist'), APP_NAME)
        print(f"\n[ГОТОВО] Исполняемый билд: {dist_folder}")
        print(f"[АРХИВ]  Готовый архив для отправки: {out_file}")


if __name__ == '__main__':
    build()