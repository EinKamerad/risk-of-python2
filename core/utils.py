from ursina import *
from types import SimpleNamespace

ctx = SimpleNamespace(game=None)


def rgb(r, g, b, a=255):
    """Перевод цвета 0-255 в диапазон 0.0-1.0 для всех версий Ursina"""
    return Color(r / 255.0, g / 255.0, b / 255.0, a / 255.0)


def is_valid(entity):
    """Безопасная проверка, что сущность жива и её C++ узел не удалён"""
    return (
        entity is not None
        and not getattr(entity, 'is_dead', False)
        and not getattr(entity, 'is_destroyed', False)
        and not entity.is_empty()
        and entity.enabled
    )


def clear_children(entity):
    """Безопасно очищает дочерние 3D-узлы (для превью в лобби и журнале)"""
    if not entity or entity.is_empty():
        return
    for ch in list(entity.children):
        if ch and not ch.is_empty():
            destroy(ch)


SETTINGS = {
    'fov': 90,
    'sensitivity': 45,
    'fog_density': 0.006,
    'fullscreen': False,
    'monitor': 0,
    'coop_bot': True
}

