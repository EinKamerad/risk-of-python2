from ursina import *
import math
import random
from config import rgb, SURVIVOR_CLASSES


def build_survivor_mesh(parent_entity, char_key):
    cfg = SURVIVOR_CLASSES[char_key]
    root = Entity(parent=parent_entity, y=0)
    parts = {'root': root, 'halo': None, 'bow': None, 'shield': None}

    # Особая 3D-модель парящего Космического Корабля из Mindustry (Gamma Core Unit)
    if char_key == 'mindustry':
        left_hip = Entity(parent=root, position=(-0.36, 0.85, -0.28))
        right_hip = Entity(parent=root, position=(0.36, 0.85, -0.28))
        for hip in (left_hip, right_hip):
            Entity(parent=hip, model='cube', scale=(0.28, 0.26, 0.52), color=cfg['armor_color'])
            Entity(parent=hip, model='cube', scale=(0.32, 0.10, 0.36), y=0.14, color=cfg['body_color'])
            Entity(parent=hip, model='diamond', scale=(0.30, 0.30, 0.62), z=-0.38, color=color.cyan, unlit=True)
            Entity(parent=hip, model='diamond', scale=(0.18, 0.18, 0.82), z=-0.52, color=color.white, unlit=True)
        parts['left_leg'] = left_hip
        parts['right_leg'] = right_hip

        torso = Entity(parent=root, position=(0, 1.35, 0))
        # Многослойный дельта-корпус и бронированный киль
        Entity(parent=torso, model='diamond', scale=(1.35, 0.44, 1.78), color=cfg['body_color'])
        Entity(parent=torso, model='diamond', scale=(0.92, 0.48, 1.95), z=0.10, color=cfg['armor_color'])
        Entity(parent=torso, model='cube', scale=(0.72, 0.38, 1.05), y=0.12, color=cfg['armor_color'])
        Entity(parent=torso, model='cube', scale=(0.52, 0.16, 1.35), y=-0.18, color=rgb(40, 45, 58))
        # Кабина и светящееся ядро строительного луча
        Entity(parent=torso, model='diamond', scale=(0.50, 0.38, 0.78), position=(0, 0.28, 0.16), color=cfg['visor_color'], unlit=True)
        Entity(parent=torso, model='sphere', scale=0.28, position=(0, 0.32, 0.20), color=color.white, unlit=True)
        # Передние спаренные зубцы-излучатели (строительный захват)
        for sx in (-0.22, 0.22):
            Entity(parent=torso, model='diamond', scale=(0.14, 0.16, 0.65), position=(sx, -0.02, 0.92), color=cfg['body_color'])
            Entity(parent=torso, model='sphere', scale=0.12, position=(sx, -0.02, 1.18), color=color.yellow, unlit=True)

        # Крылья-пилоны корабля с закрылками и энергоканалами
        for side in (-1, 1):
            wing = Entity(parent=torso, model='diamond', scale=(1.28, 0.18, 1.05), position=(side * 0.72, -0.02, -0.08), rotation_z=side * -10, color=cfg['body_color'])
            Entity(parent=wing, model='cube', scale=(0.58, 0.14, 0.72), position=(side * 0.14, 0.05, 0.05), color=cfg['armor_color'])
            Entity(parent=wing, model='cube', scale=(0.14, 0.16, 0.92), position=(side * 0.28, 0.02, 0.36), color=cfg['visor_color'], unlit=True)
            Entity(parent=wing, model='diamond', scale=(0.22, 0.42, 0.48), position=(side * 0.46, 0.12, -0.18), rotation_z=side * 22, color=cfg['armor_color'])

        halo = Entity(parent=torso, position=(0, 0.52, -0.18))
        Entity(parent=halo, model='diamond', scale=(1.05, 1.05, 0.08), rotation_x=90, color=color.yellow, unlit=True)
        Entity(parent=halo, model='diamond', scale=(0.75, 0.75, 0.08), rotation=(90, 45, 0), color=color.cyan, unlit=True)
        parts['halo'] = halo
        parts['torso'] = torso

        left_shoulder = Entity(parent=torso, position=(-0.66, 0.06, 0.35))
        right_shoulder = Entity(parent=torso, position=(0.66, 0.06, 0.35))
        for sh in (left_shoulder, right_shoulder):
            Entity(parent=sh, model='cube', scale=(0.28, 0.22, 0.42), color=cfg['body_color'])
            Entity(parent=sh, model='cube', scale=(0.10, 0.12, 0.72), position=(-0.07, 0, 0.32), color=cfg['armor_color'])
            Entity(parent=sh, model='cube', scale=(0.10, 0.12, 0.72), position=(0.07, 0, 0.32), color=cfg['armor_color'])
            Entity(parent=sh, model='sphere', scale=0.22, z=0.68, color=cfg['visor_color'], unlit=True)
        parts['left_arm'] = left_shoulder
        parts['right_arm'] = right_shoulder
        return parts

    left_hip = Entity(parent=root, position=(-0.22, 0.86, 0))
    right_hip = Entity(parent=root, position=(0.22, 0.86, 0))
    for side, hip in ((-1, left_hip), (1, right_hip)):
        # Бедро с боковой бронепластиной
        Entity(parent=hip, model='cube', scale=(0.24, 0.44, 0.25), y=-0.20, color=cfg['armor_color'])
        Entity(parent=hip, model='diamond', scale=(0.12, 0.34, 0.28), position=(side * 0.13, -0.18, 0), color=cfg['body_color'])
        # Секционный наколенник с индикатором
        Entity(parent=hip, model='diamond', scale=(0.29, 0.25, 0.32), position=(0, -0.42, 0.07), color=cfg['body_color'])
        Entity(parent=hip, model='cube', scale=(0.14, 0.08, 0.10), position=(0, -0.42, 0.18), color=cfg['visor_color'], unlit=True)
        # Голень, щиток и бронированный ботинок с подошвой
        Entity(parent=hip, model='cube', scale=(0.20, 0.42, 0.22), y=-0.62, color=rgb(40, 44, 54))
        Entity(parent=hip, model='cube', scale=(0.22, 0.30, 0.12), position=(0, -0.60, 0.10), color=cfg['armor_color'])
        Entity(parent=hip, model='cube', scale=(0.26, 0.16, 0.38), position=(0, -0.80, 0.07), color=cfg['armor_color'])
        Entity(parent=hip, model='cube', scale=(0.28, 0.06, 0.40), position=(0, -0.86, 0.07), color=rgb(28, 30, 38))
        Entity(parent=hip, model='cube', scale=(0.26, 0.06, 0.12), position=(0, -0.75, 0.22), color=cfg['visor_color'], unlit=True)

    parts['left_leg'] = left_hip
    parts['right_leg'] = right_hip

    torso = Entity(parent=root, position=(0, 1.26, 0))
    # Пояс с тактическими подсумками и пряжкой
    Entity(parent=torso, model='cube', scale=(0.60, 0.22, 0.40), y=-0.32, color=rgb(38, 42, 52))
    Entity(parent=torso, model='cube', scale=(0.20, 0.13, 0.44), y=-0.32, color=cfg['visor_color'], unlit=True)
    for px in (-0.31, 0.31):
        Entity(parent=torso, model='cube', scale=(0.10, 0.18, 0.24), position=(px, -0.31, 0.04), color=cfg['armor_color'])
    # Грудная клетка, боковые рёбра брони и воротник-горжет
    Entity(parent=torso, model='cube', scale=(0.68, 0.64, 0.42), y=0.05, color=cfg['body_color'])
    Entity(parent=torso, model='cube', scale=(0.72, 0.28, 0.36), y=0.18, color=cfg['body_color'])
    Entity(parent=torso, model='diamond', scale=(0.60, 0.54, 0.30), position=(0, 0.12, 0.16), color=cfg['armor_color'])
    Entity(parent=torso, model='diamond', scale=(0.24, 0.28, 0.34), position=(0, 0.14, 0.21), color=cfg['visor_color'], unlit=True)
    Entity(parent=torso, model='cube', scale=(0.44, 0.12, 0.40), y=0.39, color=cfg['armor_color'])

    backpack = Entity(parent=torso, position=(0, 0.08, -0.30))
    Entity(parent=backpack, model='cube', scale=(0.50, 0.54, 0.26), color=cfg['armor_color'])
    Entity(parent=backpack, model='cube', scale=(0.36, 0.38, 0.16), z=-0.10, color=rgb(42, 48, 58))
    Entity(parent=backpack, model='cube', scale=(0.14, 0.28, 0.20), z=-0.12, color=cfg['visor_color'], unlit=True)
    for side_x in (-0.17, 0.17):
        thruster = Entity(parent=backpack, model='cube', scale=(0.14, 0.24, 0.14), position=(side_x, -0.18, -0.06), rotation_x=12, color=rgb(45, 50, 60))
        Entity(parent=thruster, model='diamond', scale=(0.75, 1.1, 0.75), y=-0.65, color=cfg['visor_color'], unlit=True)
    parts['torso'] = torso

    head = Entity(parent=torso, position=(0, 0.58, 0))
    if char_key != 'v1':
        Entity(parent=head, model='sphere', scale=(0.54, 0.58, 0.56), color=cfg['armor_color'])

    if char_key == 'commando':
        # Купольный шлем с окантовкой, фильтром и сдвоенной антенной
        Entity(parent=head, model='sphere', scale=(0.50, 0.40, 0.44), position=(0, 0.02, 0.14), color=cfg['visor_color'], unlit=True)
        Entity(parent=head, model='cube', scale=(0.56, 0.08, 0.42), position=(0, 0.20, 0.05), color=cfg['body_color'])
        Entity(parent=head, model='cube', scale=(0.24, 0.14, 0.22), position=(0, -0.18, 0.22), color=rgb(40, 45, 55))
        Entity(parent=head, model='cube', scale=(0.04, 0.36, 0.04), position=(-0.26, 0.28, -0.05), color=cfg['body_color'])
        Entity(parent=head, model='sphere', scale=0.07, position=(-0.26, 0.46, -0.05), color=cfg['visor_color'], unlit=True)
        # Нагрудная перевязь и набедренные кобуры
        Entity(parent=torso, model='cube', scale=(0.66, 0.10, 0.45), position=(0, 0.08, 0.02), rotation_z=26, color=rgb(45, 50, 60))
        for side, hip in ((-1, left_hip), (1, right_hip)):
            Entity(parent=hip, model='cube', scale=(0.14, 0.28, 0.24), position=(side * 0.16, -0.15, 0), color=rgb(35, 38, 45))
            Entity(parent=hip, model='cube', scale=(0.08, 0.14, 0.12), position=(side * 0.16, -0.02, -0.04), color=cfg['body_color'])

    elif char_key == 'artificer':
        # Коронованный шлем техномага, длинная мантия и рунный ореол
        Entity(parent=head, model='cube', scale=(0.46, 0.18, 0.38), position=(0, 0.02, 0.16), color=cfg['visor_color'], unlit=True)
        Entity(parent=head, model='diamond', scale=(0.72, 0.30, 0.72), y=0.22, color=cfg['armor_color'])
        Entity(parent=head, model='diamond', scale=(0.24, 0.45, 0.42), position=(0, 0.36, 0.05), color=cfg['body_color'])
        # Фалды мантии по бокам и сзади
        for sx in (-0.28, 0.28):
            Entity(parent=torso, model='diamond', scale=(0.24, 0.75, 0.44), position=(sx, -0.48, -0.04), rotation_z=sx * -18, color=cfg['body_color'])
            Entity(parent=torso, model='diamond', scale=(0.26, 0.20, 0.46), position=(sx, -0.78, -0.04), color=cfg['armor_color'])
        Entity(parent=torso, model='diamond', scale=(0.56, 0.82, 0.18), position=(0, -0.52, -0.22), rotation_x=10, color=cfg['body_color'])
        halo = Entity(parent=torso, position=(0, 0.38, -0.52))
        Entity(parent=halo, model='diamond', scale=(1.32, 1.32, 0.10), color=color.cyan, unlit=True)
        Entity(parent=halo, model='diamond', scale=(1.32, 1.32, 0.10), rotation_z=45, color=cfg['visor_color'], unlit=True)
        Entity(parent=halo, model='sphere', scale=0.28, color=color.magenta, unlit=True)
        parts['halo'] = halo

    elif char_key == 'huntress':
        # Три вертикальных сенсора визора, капюшон, двойной шарф и колчан со стрелами
        Entity(parent=head, model='diamond', scale=(0.62, 0.56, 0.64), position=(0, 0.06, -0.04), color=cfg['body_color'])
        for vy in (-0.09, 0.03, 0.15):
            Entity(parent=head, model='diamond', scale=(0.14, 0.08, 0.38), position=(0, vy, 0.19), color=cfg['visor_color'], unlit=True)
        scarf = Entity(parent=torso, position=(0, 0.35, -0.20), rotation_x=24)
        Entity(parent=scarf, model='cube', scale=(0.58, 0.18, 0.38), color=cfg['body_color'])
        Entity(parent=scarf, model='diamond', scale=(0.32, 0.92, 0.14), position=(-0.14, -0.48, -0.24), rotation_z=8, color=cfg['body_color'])
        Entity(parent=scarf, model='diamond', scale=(0.28, 0.78, 0.14), position=(0.16, -0.42, -0.22), rotation_z=-10, color=cfg['body_color'])
        quiver = Entity(parent=backpack, position=(0.24, 0.14, -0.08), rotation_z=-20)
        Entity(parent=quiver, model='cube', scale=(0.18, 0.58, 0.18), color=rgb(45, 50, 64))
        for ax in (-0.04, 0.0, 0.04):
            Entity(parent=quiver, model='diamond', scale=(0.05, 0.35, 0.05), position=(ax, 0.36, 0), color=color.cyan, unlit=True)

    elif char_key == 'buzz':
        # Фиолетовый шлем-капюшон, лицо, прозрачный скафандр, грудная панель с кнопками и крылья
        Entity(parent=head, model='sphere', scale=(0.56, 0.58, 0.56), color=rgb(145, 55, 225))
        Entity(parent=head, model='sphere', scale=(0.42, 0.42, 0.38), position=(0, -0.02, 0.12), color=rgb(245, 205, 175))
        Entity(parent=head, model='cube', scale=(0.24, 0.14, 0.20), position=(0, -0.16, 0.22), color=rgb(235, 190, 160))
        Entity(parent=head, model='sphere', scale=(0.76, 0.74, 0.76), color=rgb(190, 240, 255, 75), unlit=True)
        Entity(parent=torso, model='cube', scale=(0.74, 0.38, 0.48), position=(0, 0.16, 0.04), color=rgb(125, 235, 65))
        Entity(parent=torso, model='cube', scale=(0.68, 0.10, 0.50), position=(0, 0.32, 0.04), color=rgb(145, 55, 225))
        Entity(parent=torso, model='sphere', scale=0.09, position=(-0.20, 0.18, 0.29), color=color.red, unlit=True)
        Entity(parent=torso, model='sphere', scale=0.09, position=(-0.08, 0.18, 0.29), color=color.green, unlit=True)
        Entity(parent=torso, model='sphere', scale=0.09, position=(0.04, 0.18, 0.29), color=color.blue, unlit=True)
        Entity(parent=torso, model='sphere', scale=(0.18, 0.14, 0.08), position=(0.20, 0.18, 0.28), color=color.red, unlit=True)
        for side in (-1, 1):
            wing = Entity(parent=backpack, model='cube', scale=(1.22, 0.30, 0.08), position=(side * 0.75, 0.12, -0.06), rotation_z=side * -8, color=rgb(155, 65, 245))
            Entity(parent=wing, model='cube', scale=(0.98, 0.42, 0.12), y=0.35, color=color.white)
            Entity(parent=wing, model='cube', scale=(0.96, 0.22, 0.14), y=0.45, color=color.red, unlit=True)
            Entity(parent=wing, model='sphere', scale=(0.18, 0.72, 0.38), x=side * 0.52, color=color.lime if side > 0 else color.red, unlit=True)

    elif char_key == 'v1':
        # Голова-камера V1 с боковыми сенсорными щитками, ядро и 8 энергетических крыльев
        cam_head = Entity(parent=head, model='cube', scale=(0.34, 0.30, 0.66), position=(0, 0.02, 0.06), color=rgb(45, 115, 235))
        for sx in (-0.20, 0.20):
            Entity(parent=cam_head, model='diamond', scale=(0.12, 0.42, 0.85), position=(sx, 0.04, -0.05), color=rgb(35, 90, 195))
        Entity(parent=cam_head, model='cube', scale=(0.42, 0.42, 0.16), position=(0, 0, 0.48), color=rgb(28, 32, 44))
        Entity(parent=cam_head, model='sphere', scale=(0.38, 0.40, 0.22), position=(0, 0, 0.55), color=rgb(255, 230, 45), unlit=True)
        wing_hub = Entity(parent=torso, position=(0, 0.18, -0.34))
        Entity(parent=wing_hub, model='cube', scale=(0.38, 0.44, 0.20), color=rgb(32, 38, 52))
        for side in (-1, 1):
            for ang in (42, 16, -10, -36):
                w = Entity(parent=wing_hub, rotation_z=side * ang, rotation_y=side * -14)
                Entity(parent=w, model='cube', scale=(0.45, 0.08, 0.14), position=(side * 0.30, 0, 0), color=rgb(45, 115, 235))
                Entity(parent=w, model='diamond', scale=(1.25, 0.15, 0.10), position=(side * 0.78, 0, 0), color=rgb(255, 215, 35), unlit=True)

    elif char_key == 'sol':
        # Повязка с бляхой ROCK YOU, ленты, шипастая шевелюра, воротник и фалды куртки
        Entity(parent=head, model='sphere', scale=(0.48, 0.50, 0.48), color=rgb(245, 200, 170))
        Entity(parent=head, model='cube', scale=(0.55, 0.14, 0.55), y=0.14, color=rgb(215, 30, 40))
        Entity(parent=head, model='cube', scale=(0.24, 0.12, 0.08), position=(0, 0.14, 0.26), color=rgb(190, 198, 210))
        for lx in (-0.12, 0.12):
            Entity(parent=head, model='diamond', scale=(0.12, 0.45, 0.10), position=(lx, 0.02, -0.32), rotation_x=28, color=rgb(215, 30, 40))
        for hx, hy, hz, rx in ((0, 0.32, -0.16, 35), (-0.24, 0.20, -0.20, 30), (0.24, 0.20, -0.20, 30), (0, -0.06, -0.34, 42), (-0.18, 0.28, 0.08, -15), (0.18, 0.28, 0.08, -15)):
            Entity(parent=head, model='diamond', scale=(0.28, 0.54, 0.36), position=(hx, hy, hz), rotation_x=rx, color=rgb(48, 30, 28))
        Entity(parent=torso, model='cube', scale=(0.56, 0.20, 0.44), position=(0, 0.38, -0.04), color=rgb(210, 35, 45))
        Entity(parent=torso, model='cube', scale=(0.26, 0.12, 0.44), position=(0, -0.32, 0.02), color=color.gold, unlit=True)
        Entity(parent=torso, model='cube', scale=(0.76, 0.58, 0.14), position=(0, -0.40, -0.20), rotation_x=12, color=rgb(200, 30, 40))

    elif char_key == 'gwen':
        # Гетерохромные глаза, корона-ободок, спиральные локоны с бантами и пышное платье
        Entity(parent=head, model='sphere', scale=(0.48, 0.50, 0.48), color=rgb(248, 225, 220))
        Entity(parent=head, model='sphere', scale=0.11, position=(-0.12, 0.04, 0.22), color=rgb(90, 220, 255), unlit=True)
        Entity(parent=head, model='sphere', scale=0.11, position=(0.12, 0.04, 0.22), color=rgb(255, 110, 195), unlit=True)
        Entity(parent=head, model='diamond', scale=(0.68, 0.24, 0.30), position=(0, 0.28, 0.05), color=rgb(32, 28, 46))
        Entity(parent=head, model='diamond', scale=(0.22, 0.26, 0.12), position=(0, 0.32, 0.18), color=color.gold, unlit=True)
        for side in (-1, 1):
            drill = Entity(parent=head, position=(side * 0.36, 0.08, -0.10), rotation_z=side * -18)
            Entity(parent=drill, model='diamond', scale=(0.30, 0.18, 0.22), y=0.05, color=rgb(215, 55, 110))
            Entity(parent=drill, model='diamond', scale=(0.36, 0.98, 0.36), y=-0.38, color=rgb(75, 205, 255))
            Entity(parent=drill, model='diamond', scale=(0.42, 0.48, 0.42), y=-0.62, color=rgb(60, 180, 240))
            Entity(parent=drill, model='diamond', scale=(0.26, 0.45, 0.26), y=-0.88, color=rgb(185, 240, 255), unlit=True)
        Entity(parent=torso, model='diamond', scale=(1.15, 0.68, 1.15), position=(0, -0.36, 0), color=rgb(32, 28, 46))
        Entity(parent=torso, model='diamond', scale=(1.22, 0.24, 1.22), position=(0, -0.55, 0), color=rgb(195, 240, 255), unlit=True)
        Entity(parent=torso, model='diamond', scale=(0.65, 0.35, 0.24), position=(0, -0.18, -0.26), color=rgb(75, 205, 255), unlit=True)

    elif char_key == 'enforcer':
        # Тяжёлый шлем с защитным забралом, броневоротником и проблесковыми маячками
        Entity(parent=head, model='cube', scale=(0.62, 0.56, 0.62), color=cfg['armor_color'])
        Entity(parent=head, model='cube', scale=(0.56, 0.18, 0.40), position=(0, 0.04, 0.16), color=cfg['visor_color'], unlit=True)
        Entity(parent=head, model='cube', scale=(0.58, 0.06, 0.42), position=(0, 0.04, 0.17), color=cfg['armor_color'])
        Entity(parent=head, model='cube', scale=(0.66, 0.14, 0.66), y=0.26, color=cfg['body_color'])
        Entity(parent=torso, model='cube', scale=(0.86, 0.28, 0.58), position=(0, 0.34, -0.02), color=cfg['armor_color'])
        Entity(parent=torso, model='sphere', scale=(0.20, 0.14, 0.20), position=(-0.36, 0.50, 0), color=color.cyan, unlit=True)
        Entity(parent=torso, model='sphere', scale=(0.20, 0.14, 0.20), position=(0.36, 0.50, 0), color=color.red, unlit=True)

    elif char_key == 'scout':
        # Шахтёрская каска с козырьком и фонарём, очки, пышная рыжая борода с кольцами и флаеры
        Entity(parent=head, model='sphere', scale=(0.54, 0.48, 0.56), y=0.08, color=rgb(245, 185, 40))
        Entity(parent=head, model='cube', scale=(0.48, 0.08, 0.32), position=(0, 0.16, 0.20), color=rgb(55, 65, 82))
        Entity(parent=head, model='sphere', scale=(0.24, 0.24, 0.22), position=(0, 0.24, 0.28), color=color.white, unlit=True)
        Entity(parent=head, model='cube', scale=(0.50, 0.14, 0.32), position=(0, 0.02, 0.16), color=rgb(60, 225, 255), unlit=True)
        beard = Entity(parent=head, position=(0, -0.22, 0.18))
        Entity(parent=beard, model='diamond', scale=(0.62, 0.70, 0.44), color=rgb(225, 95, 25))
        Entity(parent=beard, model='diamond', scale=(0.40, 0.58, 0.36), position=(-0.20, -0.08, -0.04), color=rgb(205, 80, 20))
        Entity(parent=beard, model='diamond', scale=(0.40, 0.58, 0.36), position=(0.20, -0.08, -0.04), color=rgb(205, 80, 20))
        Entity(parent=beard, model='cube', scale=(0.22, 0.08, 0.22), y=-0.22, color=color.gold, unlit=True)
        for bx in (-0.28, -0.14, 0.14, 0.28):
            Entity(parent=torso, model='cube', scale=(0.09, 0.24, 0.10), position=(bx, -0.26, 0.22), color=color.yellow, unlit=True)

    elif char_key == 'm4a1':
        # Тактическая гарнитура, зелёная прядь, шарф, юбка и рельсовая пушка Jupiter Cannon (MOD3)
        Entity(parent=head, model='sphere', scale=(0.48, 0.50, 0.48), color=rgb(248, 222, 205))
        Entity(parent=head, model='sphere', scale=0.10, position=(-0.12, 0.03, 0.22), color=rgb(75, 245, 130), unlit=True)
        Entity(parent=head, model='sphere', scale=0.10, position=(0.12, 0.03, 0.22), color=rgb(75, 245, 130), unlit=True)
        Entity(parent=head, model='sphere', scale=(0.54, 0.40, 0.54), y=0.14, color=rgb(155, 135, 115))
        Entity(parent=head, model='diamond', scale=(0.14, 0.46, 0.16), position=(-0.14, -0.05, 0.24), rotation_z=12, color=rgb(85, 245, 140), unlit=True)
        Entity(parent=head, model='diamond', scale=(0.26, 0.90, 0.26), position=(0.26, -0.24, -0.16), rotation_x=18, color=rgb(145, 125, 105))
        for side in (-1, 1):
            Entity(parent=head, model='cube', scale=(0.12, 0.26, 0.24), position=(side * 0.27, 0.04, 0.02), color=rgb(40, 44, 52))
            Entity(parent=head, model='sphere', scale=0.08, position=(side * 0.32, 0.04, 0.02), color=rgb(95, 255, 135), unlit=True)
        Entity(parent=torso, model='cube', scale=(0.66, 0.22, 0.48), y=0.32, color=rgb(65, 110, 82))
        Entity(parent=torso, model='diamond', scale=(0.98, 0.72, 0.92), y=-0.38, color=rgb(42, 46, 50))
        jup = Entity(parent=backpack, position=(0.28, 0.32, -0.14), rotation_x=-18)
        Entity(parent=jup, model='cube', scale=(0.26, 1.05, 0.30), y=0.28, color=rgb(48, 54, 62))
        Entity(parent=jup, model='cube', scale=(0.14, 0.96, 0.34), y=0.30, color=rgb(95, 255, 135), unlit=True)

    elif char_key == 'medic':
        # Очки в оправе, причёска, белый медицинский халат с фалдами, красный галстук и ранец Medi-Pack
        Entity(parent=head, model='sphere', scale=(0.48, 0.52, 0.48), color=rgb(245, 205, 180))
        Entity(parent=head, model='cube', scale=(0.50, 0.18, 0.50), y=0.22, color=rgb(35, 30, 32))
        Entity(parent=head, model='diamond', scale=(0.18, 0.22, 0.20), position=(0.08, 0.32, 0.20), rotation_z=-20, color=rgb(35, 30, 32))
        Entity(parent=head, model='cube', scale=(0.44, 0.04, 0.10), position=(0, 0.05, 0.22), color=rgb(40, 40, 45))
        Entity(parent=head, model='sphere', scale=(0.18, 0.16, 0.10), position=(-0.12, 0.04, 0.24), color=color.white, unlit=True)
        Entity(parent=head, model='sphere', scale=(0.18, 0.16, 0.10), position=(0.12, 0.04, 0.24), color=color.white, unlit=True)
        Entity(parent=torso, model='cube', scale=(0.76, 0.66, 0.46), y=-0.38, color=rgb(235, 238, 245))
        Entity(parent=torso, model='diamond', scale=(0.14, 0.44, 0.46), position=(0, 0.10, 0.03), color=color.red, unlit=True)
        Entity(parent=backpack, model='cube', scale=(0.36, 0.68, 0.36), position=(0.18, 0.10, -0.12), color=rgb(220, 45, 45), unlit=True)
        Entity(parent=backpack, model='cube', scale=(0.24, 0.62, 0.28), position=(-0.16, 0.08, -0.12), color=rgb(255, 195, 55), unlit=True)

    elif char_key == 'aigis':
        # Золотая причёска, механические наушники-визор, красная лента-бант и ядро Papillon Heart
        Entity(parent=head, model='sphere', scale=(0.48, 0.50, 0.48), color=rgb(248, 228, 212))
        Entity(parent=head, model='sphere', scale=(0.55, 0.44, 0.55), y=0.10, color=rgb(245, 205, 65))
        Entity(parent=head, model='cube', scale=(0.56, 0.08, 0.54), y=0.16, color=rgb(55, 65, 85))
        Entity(parent=head, model='sphere', scale=0.11, position=(-0.12, 0.02, 0.22), color=color.cyan, unlit=True)
        Entity(parent=head, model='sphere', scale=0.11, position=(0.12, 0.02, 0.22), color=color.cyan, unlit=True)
        for side in (-1, 1):
            Entity(parent=head, model='diamond', scale=(0.18, 0.36, 0.36), position=(side * 0.29, 0.02, 0), color=rgb(225, 230, 240))
            Entity(parent=head, model='sphere', scale=0.12, position=(side * 0.34, 0.02, 0), color=color.cyan, unlit=True)
        Entity(parent=torso, model='diamond', scale=(0.56, 0.22, 0.26), position=(0, 0.34, 0.20), color=rgb(235, 45, 60), unlit=True)
        for side in (-1, 1):
            Entity(parent=backpack, model='diamond', scale=(0.85, 0.24, 0.16), position=(side * 0.48, 0.14, -0.06), rotation_z=side * 18, color=rgb(235, 195, 55))

    elif char_key == 'reimu':
        # Огромный красный бант, боковые пряди в трубках, наряд жрицы мико и сферы Инь-Ян
        Entity(parent=head, model='sphere', scale=(0.48, 0.50, 0.48), color=rgb(248, 225, 215))
        Entity(parent=head, model='sphere', scale=(0.54, 0.42, 0.54), y=0.12, color=rgb(38, 28, 36))
        for side in (-1, 1):
            Entity(parent=head, model='cube', scale=(0.14, 0.38, 0.14), position=(side * 0.28, -0.10, 0.08), color=color.white)
            Entity(parent=head, model='diamond', scale=(0.16, 0.24, 0.16), position=(side * 0.28, -0.32, 0.08), color=rgb(38, 28, 36))
        bow_knot = Entity(parent=head, position=(0, 0.18, -0.26), rotation_x=15)
        Entity(parent=bow_knot, model='diamond', scale=(1.08, 0.46, 0.22), color=rgb(235, 35, 45), unlit=True)
        Entity(parent=bow_knot, model='diamond', scale=(0.42, 0.65, 0.18), y=-0.28, color=rgb(235, 35, 45), unlit=True)
        Entity(parent=torso, model='diamond', scale=(1.10, 0.72, 1.10), y=-0.38, color=rgb(225, 38, 48))
        Entity(parent=torso, model='diamond', scale=(1.14, 0.18, 1.14), y=-0.62, color=color.white, unlit=True)
        Entity(parent=torso, model='cube', scale=(0.54, 0.26, 0.46), y=0.22, color=color.white)
        Entity(parent=torso, model='diamond', scale=(0.38, 0.18, 0.24), position=(0, 0.28, 0.22), color=color.yellow, unlit=True)
        halo = Entity(parent=torso, position=(0, 0.35, -0.36))
        for side, col_orb in ((-1, rgb(235, 40, 50)), (1, color.white)):
            orb = Entity(parent=halo, model='sphere', scale=0.38, position=(side * 0.68, 0, 0), color=col_orb, unlit=True)
            Entity(parent=orb, model='diamond', scale=(1.45, 0.18, 1.45), color=color.gold, unlit=True)
        parts['halo'] = halo

    left_shoulder = Entity(parent=torso, position=(-0.48, 0.25, 0))
    right_shoulder = Entity(parent=torso, position=(0.48, 0.25, 0))

    for idx, sh in enumerate((left_shoulder, right_shoulder)):
        pad_scale = (0.56, 0.50, 0.56) if char_key == 'enforcer' else (0.42, 0.38, 0.42)
        Entity(parent=sh, model='diamond', scale=pad_scale, y=0.08, color=cfg['armor_color'])
        if char_key == 'reimu':
            Entity(parent=sh, model='diamond', scale=(0.36, 0.42, 0.36), position=(0, -0.08, 0.12), color=color.white)
        arm = Entity(parent=sh, model='cube', scale=(0.18, 0.18, 0.56), position=(0, -0.12, 0.22), color=cfg['body_color'])
        Entity(parent=arm, model='cube', scale=(1.12, 1.12, 0.35), z=0.35, color=cfg['armor_color'])

        if char_key == 'commando':
            gun = Entity(parent=arm, model='cube', scale=(0.65, 1.1, 0.95), position=(0, 0.15, 0.58), color=rgb(38, 42, 52))
            Entity(parent=gun, model='cube', scale=(0.44, 0.44, 1.05), position=(0, 0.38, 0.46), color=cfg['visor_color'], unlit=True)
            Entity(parent=gun, model='cube', scale=(0.35, 0.35, 0.45), position=(0, -0.25, 0.55), color=cfg['body_color'])
        elif char_key == 'artificer':
            orb = Entity(parent=arm, model='diamond', scale=(1.45, 1.45, 0.95), position=(0, 0.12, 0.68), color=color.magenta, unlit=True)
            Entity(parent=orb, model='sphere', scale=0.65, color=color.yellow, unlit=True)
            Entity(parent=orb, model='diamond', scale=(1.65, 0.20, 1.65), color=color.cyan, unlit=True)
        elif char_key == 'huntress':
            if idx == 0:
                bow = Entity(parent=sh, position=(0, -0.1, 0.56), rotation_z=15)
                Entity(parent=bow, model='diamond', scale=(0.10, 0.82, 0.24), color=cfg['armor_color'])
                Entity(parent=bow, model='diamond', scale=(0.12, 0.26, 0.28), color=cfg['body_color'])
                Entity(parent=bow, model='cube', scale=(0.03, 0.76, 0.04), z=-0.08, color=cfg['visor_color'], unlit=True)
                Entity(parent=bow, model='diamond', scale=(0.05, 0.05, 0.52), z=0.14, color=color.cyan, unlit=True)
                parts['bow'] = bow
            else:
                glaive = Entity(parent=sh, model='diamond', scale=(0.36, 0.08, 0.36), position=(0.08, -0.10, 0.48), color=color.cyan, unlit=True)
                Entity(parent=glaive, model='sphere', scale=0.45, color=color.white, unlit=True)
        elif char_key == 'buzz' and idx == 1:
            emitter = Entity(parent=sh, model='cube', scale=(0.26, 0.26, 0.32), position=(0, -0.10, 0.38), color=rgb(240, 245, 250))
            Entity(parent=emitter, model='cube', scale=(0.75, 0.35, 0.85), y=0.45, color=rgb(125, 235, 65))
            Entity(parent=emitter, model='sphere', scale=0.48, z=0.52, color=color.red, unlit=True)
        elif char_key == 'v1':
            if idx == 0:
                Entity(parent=sh, model='diamond', scale=(0.18, 0.18, 0.06), position=(0, 0.05, 0.58), color=color.gold, unlit=True)
            else:
                rev = Entity(parent=sh, model='cube', scale=(0.12, 0.20, 0.68), position=(0, -0.08, 0.58), color=rgb(35, 42, 58))
                Entity(parent=rev, model='sphere', scale=(1.25, 0.95, 0.35), position=(0, 0.05, -0.10), color=rgb(70, 80, 100))
                Entity(parent=rev, model='cube', scale=(0.68, 0.40, 0.98), position=(0, 0.36, 0.16), color=color.cyan, unlit=True)
        elif char_key == 'sol' and idx == 1:
            sword = Entity(parent=sh, position=(0, -0.12, 0.52), rotation_x=15)
            Entity(parent=sword, model='cube', scale=(0.20, 0.32, 0.36), z=0.05, color=rgb(60, 65, 75))
            Entity(parent=sword, model='cube', scale=(0.13, 0.26, 1.42), z=0.58, color=rgb(200, 35, 35))
            Entity(parent=sword, model='cube', scale=(0.15, 0.10, 1.38), position=(0, 0.10, 0.58), color=rgb(255, 165, 30), unlit=True)
            Entity(parent=sword, model='diamond', scale=(0.10, 0.16, 1.45), position=(0, -0.10, 0.60), color=rgb(220, 230, 245))
        elif char_key == 'gwen' and idx == 1:
            scis = Entity(parent=sh, position=(0, -0.12, 0.48))
            for sy in (-0.12, 0.14):
                Entity(parent=scis, model='diamond', scale=(0.08, 0.22, 0.24), position=(0, sy, -0.08), color=color.gold, unlit=True)
            Entity(parent=scis, model='diamond', scale=(0.08, 0.20, 1.42), position=(0, 0.11, 0.55), rotation_x=-14, color=rgb(110, 225, 255), unlit=True)
            Entity(parent=scis, model='diamond', scale=(0.08, 0.20, 1.42), position=(0, -0.07, 0.55), rotation_x=14, color=rgb(195, 245, 255), unlit=True)
            Entity(parent=scis, model='sphere', scale=0.26, position=(0, 0.02, 0.05), color=color.gold, unlit=True)
        elif char_key == 'enforcer':
            if idx == 0:
                shield = Entity(parent=sh, position=(-0.28, -0.15, 0.45), rotation_y=-25)
                Entity(parent=shield, model='cube', scale=(1.18, 1.68, 0.14), color=cfg['armor_color'])
                Entity(parent=shield, model='cube', scale=(1.25, 1.75, 0.08), z=-0.02, color=cfg['body_color'])
                Entity(parent=shield, model='cube', scale=(0.84, 0.28, 0.18), y=0.38, color=cfg['visor_color'], unlit=True)
                Entity(parent=shield, model='diamond', scale=(0.48, 0.68, 0.20), y=-0.20, color=cfg['visor_color'], unlit=True)
                for cy in (-0.72, 0.72):
                    Entity(parent=shield, model='cube', scale=(1.28, 0.12, 0.18), y=cy, color=rgb(85, 95, 115))
                aura = Entity(
                    parent=shield, model='cube', scale=(1.68, 1.98, 0.06),
                    z=0.10, color=rgb(70, 210, 255, 110), unlit=True, enabled=False
                )
                parts['shield'] = shield
                parts['shield_aura'] = aura
            else:
                sg = Entity(parent=sh, position=(0, -0.10, 0.55))
                Entity(parent=sg, model='cube', scale=(0.16, 0.22, 0.98), z=0.26, color=rgb(35, 40, 50))
                Entity(parent=sg, model='cube', scale=(0.22, 0.15, 0.56), position=(0, -0.08, 0.36), color=cfg['body_color'])
                Entity(parent=sg, model='cube', scale=(0.12, 0.08, 0.88), position=(0, 0.12, 0.28), color=cfg['visor_color'], unlit=True)
        elif char_key == 'scout':
            if idx == 0:
                grap = Entity(parent=sh, position=(0, -0.10, 0.50))
                Entity(parent=grap, model='cube', scale=(0.16, 0.20, 0.58), z=0.16, color=rgb(235, 175, 40))
                Entity(parent=grap, model='diamond', scale=(0.34, 0.14, 0.34), z=0.48, color=color.cyan, unlit=True)
                Entity(parent=grap, model='diamond', scale=(0.14, 0.34, 0.34), z=0.48, color=color.cyan, unlit=True)
            else:
                gk2 = Entity(parent=sh, position=(0, -0.10, 0.55))
                Entity(parent=gk2, model='cube', scale=(0.14, 0.22, 0.88), z=0.26, color=rgb(45, 52, 68))
                Entity(parent=gk2, model='cube', scale=(0.10, 0.26, 0.18), position=(0, -0.18, 0.22), color=rgb(245, 185, 40))
                Entity(parent=gk2, model='cube', scale=(0.16, 0.09, 0.74), position=(0, 0.11, 0.28), color=rgb(35, 130, 235), unlit=True)
        elif char_key == 'm4a1' and idx == 1:
            rifle = Entity(parent=sh, position=(0, -0.10, 0.55))
            Entity(parent=rifle, model='cube', scale=(0.12, 0.20, 0.96), z=0.28, color=rgb(35, 38, 42))
            Entity(parent=rifle, model='cube', scale=(0.09, 0.26, 0.16), position=(0, -0.18, 0.24), color=rgb(55, 62, 58))
            Entity(parent=rifle, model='cube', scale=(0.14, 0.12, 0.26), position=(0, 0.15, 0.22), color=rgb(95, 255, 135), unlit=True)
        elif char_key == 'medic':
            if idx == 0:
                medigun = Entity(parent=sh, position=(0, -0.12, 0.52))
                Entity(parent=medigun, model='cube', scale=(0.22, 0.24, 0.82), z=0.22, color=rgb(70, 75, 85))
                Entity(parent=medigun, model='cube', scale=(0.26, 0.26, 0.22), z=0.52, color=rgb(185, 195, 210))
                Entity(parent=medigun, model='sphere', scale=0.28, z=0.66, color=color.red, unlit=True)
            else:
                syr_gun = Entity(parent=sh, position=(0, -0.10, 0.52))
                Entity(parent=syr_gun, model='cube', scale=(0.18, 0.20, 0.72), z=0.22, color=rgb(60, 65, 75))
                Entity(parent=syr_gun, model='sphere', scale=(0.26, 0.26, 0.45), position=(0, 0.15, 0.22), color=color.red, unlit=True)
                Entity(parent=syr_gun, model='diamond', scale=(0.06, 0.18, 0.55), position=(0, -0.12, 0.45), color=rgb(220, 230, 245))
        elif char_key == 'aigis':
            if idx == 0:
                cannon = Entity(parent=sh, position=(0, -0.10, 0.50))
                Entity(parent=cannon, model='cube', scale=(0.26, 0.26, 0.76), z=0.22, color=rgb(235, 195, 55))
                Entity(parent=cannon, model='sphere', scale=0.24, z=0.62, color=color.orange, unlit=True)
            else:
                barrel = Entity(parent=sh, position=(0, -0.10, 0.52))
                Entity(parent=barrel, model='cube', scale=(0.24, 0.18, 0.58), z=0.18, color=color.cyan, unlit=True)
                for fx in (-0.08, 0.0, 0.08):
                    Entity(parent=barrel, model='cube', scale=(0.04, 0.06, 0.32), position=(fx, 0, 0.52), color=rgb(235, 195, 55))
        elif char_key == 'reimu':
            if idx == 0:
                for oy in (-0.06, 0.06):
                    Entity(parent=sh, model='cube', scale=(0.18, 0.03, 0.32), position=(0, oy, 0.52), rotation_y=oy * 180, color=rgb(245, 50, 65), unlit=True)
            else:
                gohei = Entity(parent=sh, position=(0, -0.10, 0.55), rotation_x=20)
                Entity(parent=gohei, model='cube', scale=(0.08, 0.08, 1.18), z=0.36, color=rgb(140, 85, 45))
                Entity(parent=gohei, model='diamond', scale=(0.38, 0.48, 0.38), z=0.98, color=color.white, unlit=True)
                Entity(parent=gohei, model='diamond', scale=(0.28, 0.36, 0.28), position=(0, -0.18, 0.88), color=rgb(245, 50, 65), unlit=True)

    parts['left_arm'] = left_shoulder
    parts['right_arm'] = right_shoulder
    return parts