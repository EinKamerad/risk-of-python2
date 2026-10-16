import os
import sys
import subprocess
import tarfile
from setuptools import setup

APP_NAME = "RiskOfPython2"
TARGET_PLATFORM = "manylinux2014_x86_64"

SETUP_CODE = f"""
from setuptools import setup

setup(
    name="{APP_NAME}",
    version="1.0.0",
    options={{
        "build_apps": {{
            "gui_apps": {{
                "{APP_NAME}": "main.py",
            }},
            "include_patterns": [
                "core/**/*.py",
                "data/**/*.py",
                "models/**/*.py",
                "entities/**/*.py",
                "world/**/*.py",
                "net/**/*.py",
                "ui/**/*.py",
                "config.py",
                "network.py",
                "**/*.bam",
                "**/*.obj",
                "**/*.mtl",
                "**/*.png",
                "**/*.jpg",
                "**/*.ttf",
                "**/*.glsl",
                "**/*.vert",
                "**/*.frag",
            ],
            "plugins": [
                "pandagl",
                "p3openal_audio",
            ],
            "platforms": [
                "{TARGET_PLATFORM}",
            ],
        }}
    }}
)
"""


def set_linux_exec_permissions(tarinfo):
    """Прописывает права запуска (chmod +x) для Linux-бинарника прямо из Windows"""
    if tarinfo.name.endswith(f"/{APP_NAME}") or tarinfo.name.endswith(".so") or ".so." in tarinfo.name:
        tarinfo.mode = 0o755
    return tarinfo


def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    setup_path = os.path.join(root_dir, "_temp_setup.py")

    with open(setup_path, "w", encoding="utf-8") as f:
        f.write(SETUP_CODE.strip())

    print("=== 1. Кросс-сборка Linux-версии (Debian / Ubuntu x86_64) на Windows ===")
    try:
        subprocess.check_call([sys.executable, "_temp_setup.py", "build_apps"])
    finally:
        if os.path.exists(setup_path):
            os.remove(setup_path)

    build_dir = os.path.join(root_dir, "build", TARGET_PLATFORM)
    dist_dir = os.path.join(root_dir, "dist")
    os.makedirs(dist_dir, exist_ok=True)
    archive_path = os.path.join(dist_dir, f"{APP_NAME}_debian_linux_x64.tar.gz")

    if os.path.exists(build_dir):
        print("=== 2. Упаковка в .tar.gz с установкой Linux-прав (chmod 755) ===")
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(build_dir, arcname=APP_NAME, filter=set_linux_exec_permissions)
        print(f"\n[ГОТОВО] Архив для Debian Linux создан: {archive_path}")
        print(f"Распакуй его на Debian и запускай ./{APP_NAME}")


if __name__ == "__main__":
    main()