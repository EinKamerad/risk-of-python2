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
        armor_col = rgb(82, 42, 38)

        l_leg = Entity(parent=root, position=(-0.26, 0.75, 0))
        r_leg = Entity(parent=root, position=(0.26, 0.75, 0))
        for leg in (l_leg, r_leg):
            Entity(parent=leg, model='cube', scale=(0.24, 0.75, 0.28), y=-0.35, color=skin_col)
            Entity(parent=leg, model='diamond', scale=(0.28, 0.24, 0.32), position=(0, -0.35, 0.08), color=armor_col)
            Entity(parent=leg, model='diamond', scale=(0.30, 0.20, 0.46), position=(0, -0.70, 0.14), color=spine_col)
        parts['left_leg'] = l_leg
        parts['right_leg'] = r_leg

        torso = Entity(parent=root, position=(0, 1.15, 0), rotation_x=18)
        Entity(parent=torso, model='cube', scale=(0.72, 0.98, 0.56), color=skin_col)
        Entity(parent=torso, model='cube', scale=(0.54, 0.86, 0.18), z=0.23, color=belly_col)
        Entity(parent=torso, model='diamond', scale=(1.05, 0.38, 0.58), y=0.34, color=armor_col)
        for i in range(5):
            Entity(parent=torso, model='diamond', scale=(0.15, 0.42, 0.28), position=(0, 0.38 - i * 0.22, -0.32), rotation_x=-35, color=spine_col)

        tail = Entity(parent=torso, position=(0, -0.4, -0.25))
        Entity(parent=tail, model='diamond', scale=(0.32, 0.28, 1.25), position=(0, -0.1, -0.52), rotation_x=-25, color=skin_col)
        Entity(parent=tail, model='diamond', scale=(0.20, 0.32, 0.45), position=(0, -0.32, -1.05), rotation_x=-15, color=spine_col)
        parts['tail'] = tail
        parts['torso'] = torso

        head = Entity(parent=torso, position=(0, 0.64, 0.18), rotation_x=-18)
        Entity(parent=head, model='diamond', scale=(0.72, 0.54, 1.02), color=skin_col)
        Entity(parent=head, model='cube', scale=(0.48, 0.16, 0.72), position=(0, -0.20, 0.16), color=belly_col)
        for tx in (-0.16, 0.0, 0.16):
            Entity(parent=head, model='diamond', scale=(0.07, 0.14, 0.07), position=(tx, -0.12, 0.42), color=spine_col)
        Entity(parent=head, model='diamond', scale=(0.20, 0.72, 0.20), position=(-0.26, 0.38, -0.22), rotation=(-30, 0, -20), color=spine_col)
        Entity(parent=head, model='diamond', scale=(0.20, 0.72, 0.20), position=(0.26, 0.38, -0.22), rotation=(-30, 0, 20), color=spine_col)
        Entity(parent=head, model='sphere', scale=0.16, position=(-0.21, 0.09, 0.27), color=color.yellow, unlit=True)
        Entity(parent=head, model='sphere', scale=0.16, position=(0.21, 0.09, 0.27), color=color.yellow, unlit=True)

        l_arm = Entity(parent=torso, position=(-0.46, 0.22, 0.1))
        r_arm = Entity(parent=torso, position=(0.46, 0.22, 0.1))
        for arm in (l_arm, r_arm):
            Entity(parent=arm, model='cube', scale=(0.19, 0.58, 0.19), position=(0, -0.2, 0.2), rotation_x=-45, color=skin_col)
            Entity(parent=arm, model='diamond', scale=(0.22, 0.28, 0.18), position=(0, -0.44, 0.42), rotation_x=-65, color=spine_col)
        parts['left_arm'] = l_arm
        parts['right_arm'] = r_arm

    elif enemy_type == 'wisp':
        core = Entity(parent=root, position=(0, 2.3, 0))
        Entity(parent=core, model='sphere', scale=0.90, color=rgb(255, 135, 20), unlit=True)
        Entity(parent=core, model='diamond', scale=(0.60, 1.55, 0.60), y=0.40, color=color.yellow, unlit=True)
        Entity(parent=core, model='diamond', scale=(0.38, 1.85, 0.38), y=0.58, color=color.white, unlit=True)

        mask = Entity(parent=core, position=(0, 0, 0.40))
        Entity(parent=mask, model='cube', scale=(0.80, 0.90, 0.22), color=rgb(55, 60, 72))
        Entity(parent=mask, model='diamond', scale=(0.65, 0.35, 0.26), y=-0.38, color=rgb(42, 46, 56))
        Entity(parent=mask, model='cube', scale=(0.26, 0.13, 0.28), position=(-0.18, 0.12, 0.02), color=color.yellow, unlit=True)
        Entity(parent=mask, model='cube', scale=(0.26, 0.13, 0.28), position=(0.18, 0.12, 0.02), color=color.yellow, unlit=True)
        Entity(parent=mask, model='diamond', scale=(0.26, 0.88, 0.26), position=(-0.45, 0.48, -0.1), rotation_z=-25, color=rgb(95, 100, 115))
        Entity(parent=mask, model='diamond', scale=(0.26, 0.88, 0.26), position=(0.45, 0.48, -0.1), rotation_z=25, color=rgb(95, 100, 115))

        ring1 = Entity(parent=core, model='diamond', scale=(1.85, 0.18, 1.85), color=rgb(70, 75, 88))
        ring2 = Entity(parent=core, model='diamond', scale=(0.18, 1.85, 1.85), color=rgb(115, 120, 135))
        parts['core'] = core
        parts['ring1'] = ring1
        parts['ring2'] = ring2

    elif enemy_type == 'beetle':
        shell_col = rgb(95, 62, 42)
        plate_col = rgb(135, 88, 55)
        horn_col = rgb(225, 175, 85)
        torso = Entity(parent=root, position=(0, 0.65, 0))
        Entity(parent=torso, model='sphere', scale=(1.18, 0.74, 1.48), color=shell_col)
        Entity(parent=torso, model='diamond', scale=(0.92, 0.38, 1.22), y=0.28, color=plate_col)
        Entity(parent=torso, model='cube', scale=(0.06, 0.42, 1.15), y=0.29, color=rgb(55, 35, 22))
        horn = Entity(parent=torso, model='diamond', scale=(0.26, 0.82, 0.38), position=(0, 0.24, 0.78), rotation_x=55, color=horn_col)
        for mx in (-0.24, 0.24):
            Entity(parent=torso, model='diamond', scale=(0.14, 0.14, 0.45), position=(mx, -0.05, 0.75), rotation_y=mx * -35, color=horn_col)
        Entity(parent=torso, model='sphere', scale=0.16, position=(-0.27, 0.13, 0.64), color=color.orange, unlit=True)
        Entity(parent=torso, model='sphere', scale=0.16, position=(0.27, 0.13, 0.64), color=color.orange, unlit=True)

        l_leg = Entity(parent=root, position=(-0.55, 0.45, 0))
        r_leg = Entity(parent=root, position=(0.55, 0.45, 0))
        for side, leg in ((-1, l_leg), (1, r_leg)):
            for z_off in (-0.36, 0.0, 0.36):
                Entity(parent=leg, model='diamond', scale=(0.22, 0.60, 0.22), position=(side * 0.12, -0.2, z_off), rotation_z=side * 28, color=shell_col)
        parts['torso'] = torso
        parts['horn'] = horn
        parts['left_leg'] = l_leg
        parts['right_leg'] = r_leg

    elif enemy_type == 'jellyfish':
        core = Entity(parent=root, position=(0, 2.2, 0))
        Entity(parent=core, model='sphere', scale=(1.40, 1.08, 1.40), color=rgb(75, 225, 255, 185), unlit=True)
        Entity(parent=core, model='diamond', scale=(1.55, 0.28, 1.55), y=-0.22, color=rgb(135, 245, 255, 160), unlit=True)
        Entity(parent=core, model='sphere', scale=0.68, y=-0.05, color=rgb(245, 110, 255), unlit=True)
        tentacles = Entity(parent=core, y=-0.35)
        for i in range(8):
            ang = (i / 8.0) * math.pi * 2
            tx, tz = math.cos(ang) * 0.38, math.sin(ang) * 0.38
            t_col = color.cyan if i % 2 == 0 else rgb(235, 120, 255)
            Entity(parent=tentacles, model='diamond', scale=(0.13, 1.35, 0.13), position=(tx, -0.55, tz), color=t_col, unlit=True)
        parts['core'] = core
        parts['tentacles'] = tentacles

    elif enemy_type == 'golem':
        st_col = rgb(78, 86, 98)
        st_dark = rgb(52, 58, 68)
        rune_col = rgb(255, 70, 55)
        l_leg = Entity(parent=root, position=(-0.46, 1.0, 0))
        r_leg = Entity(parent=root, position=(0.46, 1.0, 0))
        for leg in (l_leg, r_leg):
            Entity(parent=leg, model='cube', scale=(0.48, 1.0, 0.52), y=-0.5, color=st_dark)
            Entity(parent=leg, model='cube', scale=(0.56, 0.28, 0.64), position=(0, -0.88, 0.08), color=st_col)
        parts['left_leg'] = l_leg
        parts['right_leg'] = r_leg

        torso = Entity(parent=root, position=(0, 1.85, 0))
        Entity(parent=torso, model='cube', scale=(1.48, 1.38, 0.95), color=st_col)
        Entity(parent=torso, model='diamond', scale=(1.65, 0.45, 1.05), y=0.45, color=st_dark)
        Entity(parent=torso, model='diamond', scale=(0.32, 0.78, 1.02), color=rune_col, unlit=True)
        head = Entity(parent=torso, model='cube', scale=(0.78, 0.62, 0.74), y=0.95, color=st_dark)
        Entity(parent=head, model='cube', scale=(0.68, 0.16, 0.78), y=0.05, color=rune_col, unlit=True)
        eye = Entity(parent=head, model='sphere', scale=0.36, position=(0, 0.05, 0.46), color=color.red, unlit=True)

        l_arm = Entity(parent=torso, position=(-1.02, 0.35, 0))
        r_arm = Entity(parent=torso, position=(1.02, 0.35, 0))
        for arm in (l_arm, r_arm):
            Entity(parent=arm, model='diamond', scale=(0.62, 0.55, 0.62), y=0.12, color=st_dark)
            Entity(parent=arm, model='cube', scale=(0.44, 1.25, 0.44), y=-0.55, color=st_col)
            Entity(parent=arm, model='cube', scale=(0.56, 0.48, 0.56), y=-1.15, color=st_dark)
        parts['torso'] = torso
        parts['eye'] = eye
        parts['left_arm'] = l_arm
        parts['right_arm'] = r_arm

    elif enemy_type == 'imp':
        imp_col = rgb(45, 22, 48)
        crimson = rgb(245, 35, 70)
        l_leg = Entity(parent=root, position=(-0.24, 0.78, 0))
        r_leg = Entity(parent=root, position=(0.24, 0.78, 0))
        for leg in (l_leg, r_leg):
            Entity(parent=leg, model='diamond', scale=(0.25, 0.84, 0.25), y=-0.4, color=imp_col)
            Entity(parent=leg, model='diamond', scale=(0.18, 0.18, 0.38), position=(0, -0.75, 0.12), color=crimson, unlit=True)
        parts['left_leg'] = l_leg
        parts['right_leg'] = r_leg

        torso = Entity(parent=root, position=(0, 1.28, 0))
        Entity(parent=torso, model='diamond', scale=(0.86, 1.18, 0.60), color=imp_col)
        Entity(parent=torso, model='diamond', scale=(0.22, 0.72, 0.28), z=0.24, color=crimson, unlit=True)
        Entity(parent=torso, model='sphere', scale=0.18, z=0.30, color=color.white, unlit=True)
        for side in (-1, 1):
            Entity(parent=torso, model='diamond', scale=(0.18, 0.68, 0.18), position=(side * 0.30, 0.68, 0), rotation_z=side * -24, color=crimson, unlit=True)
            Entity(parent=torso, model='diamond', scale=(0.14, 0.42, 0.24), position=(side * 0.24, 0.25, -0.24), rotation_x=-30, color=crimson, unlit=True)

        l_arm = Entity(parent=torso, position=(-0.54, 0.22, 0))
        r_arm = Entity(parent=torso, position=(0.54, 0.22, 0))
        for arm in (l_arm, r_arm):
            Entity(parent=arm, model='diamond', scale=(0.24, 0.78, 0.24), position=(0, -0.25, 0.22), rotation_x=-50, color=imp_col)
            for cx in (-0.06, 0.06):
                Entity(parent=arm, model='diamond', scale=(0.10, 0.48, 0.14), position=(cx, -0.54, 0.44), rotation_x=-70, color=crimson, unlit=True)
        parts['torso'] = torso
        parts['left_arm'] = l_arm
        parts['right_arm'] = r_arm

    elif enemy_type == 'greater_wisp':
        core = Entity(parent=root, position=(0, 2.7, 0))
        Entity(parent=core, model='sphere', scale=1.28, color=rgb(65, 245, 110), unlit=True)
        Entity(parent=core, model='diamond', scale=(0.90, 2.25, 0.90), y=0.52, color=rgb(175, 255, 120), unlit=True)

        mask = Entity(parent=core, position=(0, 0, 0.54))
        Entity(parent=mask, model='diamond', scale=(1.42, 1.65, 0.36), color=rgb(48, 54, 64))
        Entity(parent=mask, model='diamond', scale=(0.38, 0.24, 0.40), position=(-0.28, 0.16, 0.05), color=color.lime, unlit=True)
        Entity(parent=mask, model='diamond', scale=(0.38, 0.24, 0.40), position=(0.28, 0.16, 0.05), color=color.lime, unlit=True)
        for side in (-1, 1):
            Entity(parent=mask, model='diamond', scale=(0.30, 0.95, 0.28), position=(side * 0.58, 0.58, -0.05), rotation_z=side * -22, color=rgb(78, 86, 100))

        ring1 = Entity(parent=core, model='diamond', scale=(2.6, 0.24, 2.6), color=rgb(65, 72, 85))
        l_orb = Entity(parent=core, model='sphere', scale=0.52, position=(-1.38, -0.1, 0.35), color=color.lime, unlit=True)
        r_orb = Entity(parent=core, model='sphere', scale=0.52, position=(1.38, -0.1, 0.35), color=color.lime, unlit=True)
        for orb in (l_orb, r_orb):
            Entity(parent=orb, model='diamond', scale=(1.45, 0.45, 1.45), y=-0.35, color=rgb(55, 62, 74))
        parts['core'] = core
        parts['ring1'] = ring1
        parts['l_orb'] = l_orb
        parts['r_orb'] = r_orb
    else:
        return build_boss_mesh(parent_entity, enemy_type)

    return parts
