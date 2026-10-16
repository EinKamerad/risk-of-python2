from ursina import *
import math
import random
from config import rgb
from models.bosses import build_boss_mesh

def build_enemy_mesh(parent_entity, enemy_type):
    root = Entity(parent=parent_entity)
    parts = {'root': root}

    if enemy_type == 'lemurian':
        skin_col = rgb(190, 58, 46)
        belly_col = rgb(230, 140, 75)
        spine_col = rgb(245, 235, 200)

        l_leg = Entity(parent=root, position=(-0.26, 0.75, 0))
        r_leg = Entity(parent=root, position=(0.26, 0.75, 0))
        for leg in (l_leg, r_leg):
            Entity(parent=leg, model='cube', scale=(0.24, 0.75, 0.28), y=-0.35, color=skin_col)
            Entity(parent=leg, model='diamond', scale=(0.30, 0.20, 0.44), position=(0, -0.70, 0.12), color=spine_col)
        parts['left_leg'] = l_leg
        parts['right_leg'] = r_leg

        torso = Entity(parent=root, position=(0, 1.15, 0), rotation_x=18)
        Entity(parent=torso, model='cube', scale=(0.70, 0.96, 0.54), color=skin_col)
        Entity(parent=torso, model='cube', scale=(0.52, 0.84, 0.16), z=0.22, color=belly_col)
        Entity(parent=torso, model='diamond', scale=(0.95, 0.35, 0.55), y=0.32, color=rgb(90, 40, 35))
        for i in range(4):
            Entity(parent=torso, model='diamond', scale=(0.15, 0.38, 0.26), position=(0, 0.36 - i * 0.25, -0.32), rotation_x=-35, color=spine_col)

        tail = Entity(parent=torso, position=(0, -0.4, -0.25))
        Entity(parent=tail, model='diamond', scale=(0.30, 0.26, 1.2), position=(0, -0.1, -0.50), rotation_x=-25, color=skin_col)
        parts['tail'] = tail
        parts['torso'] = torso

        head = Entity(parent=torso, position=(0, 0.64, 0.18), rotation_x=-18)
        Entity(parent=head, model='diamond', scale=(0.70, 0.52, 0.98), color=skin_col)
        Entity(parent=head, model='cube', scale=(0.46, 0.15, 0.68), position=(0, -0.20, 0.14), color=belly_col)
        Entity(parent=head, model='diamond', scale=(0.18, 0.68, 0.18), position=(-0.26, 0.36, -0.22), rotation=(-30, 0, -20), color=spine_col)
        Entity(parent=head, model='diamond', scale=(0.18, 0.68, 0.18), position=(0.26, 0.36, -0.22), rotation=(-30, 0, 20), color=spine_col)
        Entity(parent=head, model='sphere', scale=0.16, position=(-0.20, 0.08, 0.26), color=color.yellow, unlit=True)
        Entity(parent=head, model='sphere', scale=0.16, position=(0.20, 0.08, 0.26), color=color.yellow, unlit=True)

        l_arm = Entity(parent=torso, position=(-0.46, 0.22, 0.1))
        r_arm = Entity(parent=torso, position=(0.46, 0.22, 0.1))
        for arm in (l_arm, r_arm):
            Entity(parent=arm, model='cube', scale=(0.18, 0.56, 0.18), position=(0, -0.2, 0.2), rotation_x=-45, color=skin_col)
        parts['left_arm'] = l_arm
        parts['right_arm'] = r_arm

    elif enemy_type == 'wisp':
        core = Entity(parent=root, position=(0, 2.3, 0))
        Entity(parent=core, model='sphere', scale=0.88, color=rgb(255, 135, 20), unlit=True)
        Entity(parent=core, model='diamond', scale=(0.55, 1.45, 0.55), y=0.38, color=color.yellow, unlit=True)

        mask = Entity(parent=core, position=(0, 0, 0.40))
        Entity(parent=mask, model='cube', scale=(0.78, 0.88, 0.22), color=rgb(55, 60, 72))
        Entity(parent=mask, model='cube', scale=(0.25, 0.12, 0.26), position=(-0.18, 0.12, 0.02), color=color.yellow, unlit=True)
        Entity(parent=mask, model='cube', scale=(0.25, 0.12, 0.26), position=(0.18, 0.12, 0.02), color=color.yellow, unlit=True)
        Entity(parent=mask, model='diamond', scale=(0.24, 0.82, 0.24), position=(-0.44, 0.46, -0.1), rotation_z=-25, color=rgb(95, 100, 115))
        Entity(parent=mask, model='diamond', scale=(0.24, 0.82, 0.24), position=(0.44, 0.46, -0.1), rotation_z=25, color=rgb(95, 100, 115))

        ring1 = Entity(parent=core, model='diamond', scale=(1.8, 0.18, 1.8), color=rgb(70, 75, 88))
        ring2 = Entity(parent=core, model='diamond', scale=(0.18, 1.8, 1.8), color=rgb(115, 120, 135))
        parts['core'] = core
        parts['ring1'] = ring1
        parts['ring2'] = ring2

    elif enemy_type == 'beetle':
        # Панцирный жук с рогом и лапками
        shell_col = rgb(95, 62, 42)
        horn_col = rgb(225, 175, 85)
        torso = Entity(parent=root, position=(0, 0.65, 0))
        Entity(parent=torso, model='sphere', scale=(1.15, 0.72, 1.45), color=shell_col)
        Entity(parent=torso, model='diamond', scale=(0.85, 0.35, 1.15), y=0.28, color=rgb(135, 88, 55))
        horn = Entity(parent=torso, model='diamond', scale=(0.24, 0.75, 0.35), position=(0, 0.22, 0.75), rotation_x=55, color=horn_col)
        Entity(parent=torso, model='sphere', scale=0.15, position=(-0.26, 0.12, 0.62), color=color.orange, unlit=True)
        Entity(parent=torso, model='sphere', scale=0.15, position=(0.26, 0.12, 0.62), color=color.orange, unlit=True)

        l_leg = Entity(parent=root, position=(-0.55, 0.45, 0))
        r_leg = Entity(parent=root, position=(0.55, 0.45, 0))
        for side, leg in ((-1, l_leg), (1, r_leg)):
            for z_off in (-0.32, 0.32):
                Entity(parent=leg, model='diamond', scale=(0.22, 0.58, 0.22), position=(side * 0.1, -0.2, z_off), rotation_z=side * 25, color=shell_col)
        parts['torso'] = torso
        parts['horn'] = horn
        parts['left_leg'] = l_leg
        parts['right_leg'] = r_leg

    elif enemy_type == 'jellyfish':
        # Парящая биолюминесцентная медуза
        core = Entity(parent=root, position=(0, 2.2, 0))
        Entity(parent=core, model='sphere', scale=(1.35, 1.05, 1.35), color=rgb(75, 225, 255, 185), unlit=True)
        Entity(parent=core, model='sphere', scale=0.65, y=-0.05, color=rgb(245, 110, 255), unlit=True)
        tentacles = Entity(parent=core, y=-0.35)
        for i in range(6):
            ang = (i / 6.0) * math.pi * 2
            tx, tz = math.cos(ang) * 0.35, math.sin(ang) * 0.35
            Entity(parent=tentacles, model='diamond', scale=(0.12, 1.25, 0.12), position=(tx, -0.5, tz), color=color.cyan, unlit=True)
        parts['core'] = core
        parts['tentacles'] = tentacles

    elif enemy_type == 'golem':
        # Тяжёлый Каменный Голем с лазерным глазом
        st_col = rgb(78, 86, 98)
        st_dark = rgb(52, 58, 68)
        l_leg = Entity(parent=root, position=(-0.45, 1.0, 0))
        r_leg = Entity(parent=root, position=(0.45, 1.0, 0))
        for leg in (l_leg, r_leg):
            Entity(parent=leg, model='cube', scale=(0.46, 1.0, 0.50), y=-0.5, color=st_dark)
        parts['left_leg'] = l_leg
        parts['right_leg'] = r_leg

        torso = Entity(parent=root, position=(0, 1.85, 0))
        Entity(parent=torso, model='cube', scale=(1.45, 1.35, 0.92), color=st_col)
        head = Entity(parent=torso, model='cube', scale=(0.75, 0.58, 0.72), y=0.92, color=st_dark)
        eye = Entity(parent=head, model='sphere', scale=0.35, position=(0, 0, 0.45), color=color.red, unlit=True)

        l_arm = Entity(parent=torso, position=(-0.98, 0.35, 0))
        r_arm = Entity(parent=torso, position=(0.98, 0.35, 0))
        for arm in (l_arm, r_arm):
            Entity(parent=arm, model='cube', scale=(0.42, 1.25, 0.42), y=-0.55, color=st_col)
        parts['torso'] = torso
        parts['eye'] = eye
        parts['left_arm'] = l_arm
        parts['right_arm'] = r_arm

    elif enemy_type == 'imp':
        # Демонический Бес Пустоты
        imp_col = rgb(45, 22, 48)
        crimson = rgb(245, 35, 70)
        l_leg = Entity(parent=root, position=(-0.24, 0.78, 0))
        r_leg = Entity(parent=root, position=(0.24, 0.78, 0))
        for leg in (l_leg, r_leg):
            Entity(parent=leg, model='diamond', scale=(0.24, 0.82, 0.24), y=-0.4, color=imp_col)
        parts['left_leg'] = l_leg
        parts['right_leg'] = r_leg

        torso = Entity(parent=root, position=(0, 1.28, 0))
        Entity(parent=torso, model='diamond', scale=(0.82, 1.15, 0.58), color=imp_col)
        # Вертикальный багровый глаз-разрез на груди
        Entity(parent=torso, model='diamond', scale=(0.18, 0.65, 0.25), z=0.22, color=crimson, unlit=True)
        for side in (-1, 1):
            Entity(parent=torso, model='diamond', scale=(0.16, 0.62, 0.16), position=(side * 0.28, 0.65, 0), rotation_z=side * -22, color=crimson, unlit=True)

        l_arm = Entity(parent=torso, position=(-0.52, 0.22, 0))
        r_arm = Entity(parent=torso, position=(0.52, 0.22, 0))
        for arm in (l_arm, r_arm):
            Entity(parent=arm, model='diamond', scale=(0.22, 0.75, 0.22), position=(0, -0.25, 0.22), rotation_x=-50, color=imp_col)
            Entity(parent=arm, model='diamond', scale=(0.14, 0.42, 0.14), position=(0, -0.52, 0.42), rotation_x=-70, color=crimson, unlit=True)
        parts['torso'] = torso
        parts['left_arm'] = l_arm
        parts['right_arm'] = r_arm

    elif enemy_type == 'greater_wisp':
        # Большой Огонёк с изумрудным пламенем и двумя руками-жаровнями
        core = Entity(parent=root, position=(0, 2.7, 0))
        Entity(parent=core, model='sphere', scale=1.25, color=rgb(65, 245, 110), unlit=True)
        Entity(parent=core, model='diamond', scale=(0.85, 2.1, 0.85), y=0.5, color=rgb(175, 255, 120), unlit=True)

        mask = Entity(parent=core, position=(0, 0, 0.52))
        Entity(parent=mask, model='diamond', scale=(1.35, 1.55, 0.35), color=rgb(48, 54, 64))
        Entity(parent=mask, model='diamond', scale=(0.35, 0.22, 0.38), position=(-0.26, 0.15, 0.05), color=color.lime, unlit=True)
        Entity(parent=mask, model='diamond', scale=(0.35, 0.22, 0.38), position=(0.26, 0.15, 0.05), color=color.lime, unlit=True)

        ring1 = Entity(parent=core, model='diamond', scale=(2.5, 0.22, 2.5), color=rgb(65, 72, 85))
        l_orb = Entity(parent=core, model='sphere', scale=0.48, position=(-1.35, -0.1, 0.35), color=color.lime, unlit=True)
        r_orb = Entity(parent=core, model='sphere', scale=0.48, position=(1.35, -0.1, 0.35), color=color.lime, unlit=True)
        parts['core'] = core
        parts['ring1'] = ring1
        parts['l_orb'] = l_orb
        parts['r_orb'] = r_orb
    else:
        return build_boss_mesh(parent_entity, enemy_type)

    return parts
