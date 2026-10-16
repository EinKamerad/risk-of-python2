from ursina import *
import math
import random
from config import rgb, ITEM_POOL, SURVIVOR_CLASSES

# ==========================================
# 1. ПРОЦЕДУРНЫЙ КОСМИЧЕСКИЙ СКАЙБОКС (PETRICHOR V)
# ==========================================
def build_skybox(parent_entity, palette):
    """Создает многослойное небо со звездами, расколотой луной, планетой с кольцами и туманностями"""
    sky_root = Entity(parent=parent_entity)
    sky_root.setFogOff()

    random.seed(42)
    for i in range(14):
        ang = (i / 14.0) * math.pi * 2
        dist = random.uniform(165, 195)
        nx = math.cos(ang) * dist
        nz = math.sin(ang) * dist
        ny = random.uniform(12, 48)
        Entity(
            parent=sky_root,
            model='sphere',
            position=(nx, ny, nz),
            scale=(random.uniform(45, 75), random.uniform(14, 26), random.uniform(45, 75)),
            rotation_y=random.uniform(0, 360),
            color=palette['nebula'],
            unlit=True
        )

    for _ in range(140):
        theta = random.uniform(0, math.pi * 2)
        phi = random.uniform(0.12, math.pi * 0.48)
        r = random.uniform(175, 215)
        sx = r * math.cos(phi) * math.cos(theta)
        sy = r * math.sin(phi)
        sz = r * math.cos(phi) * math.sin(theta)
        star_scale = random.uniform(0.9, 2.4)
        star_col = color.white if random.random() > 0.35 else palette['accent']
        Entity(
            parent=sky_root,
            model='diamond',
            position=(sx, sy, sz),
            scale=star_scale,
            color=star_col,
            unlit=True
        )

    # Расколотая Луна Petrichor V с поясом астероидов
    moon_pivot = Entity(parent=sky_root, position=(65, 78, 125), rotation=(-15, -30, 20))
    Entity(parent=moon_pivot, model='sphere', scale=28, color=palette['moon'], unlit=True)
    for i in range(14):
        ang = (i / 14.0) * math.pi * 2
        dist = random.uniform(19, 30)
        Entity(
            parent=moon_pivot,
            model='diamond',
            position=(math.cos(ang) * dist, random.uniform(-5, 7), math.sin(ang) * dist),
            scale=random.uniform(2.5, 5.2),
            rotation=(random.uniform(0, 180), random.uniform(0, 180), 0),
            color=palette['moon'],
            unlit=True
        )
    Entity(parent=moon_pivot, model='diamond', scale=(52, 0.9, 52), color=palette['accent'], unlit=True)

    # Далёкий газовый гигант с двойным кольцом
    planet = Entity(parent=sky_root, position=(-95, 62, -105), rotation=(25, 15, -20))
    Entity(parent=planet, model='sphere', scale=22, color=palette['nebula'], unlit=True)
    Entity(parent=planet, model='diamond', scale=(48, 0.7, 48), color=palette['accent'], unlit=True)
    Entity(parent=planet, model='diamond', scale=(36, 0.5, 36), rotation_y=45, color=palette['moon'], unlit=True)

    random.seed()
    return sky_root


# ==========================================
# 2. ПРОКАЧАННЫЕ 3D-МОДЕЛИ 7 ВЫЖИВШИХ
# ==========================================
def build_survivor_mesh(parent_entity, char_key):
    cfg = SURVIVOR_CLASSES[char_key]
    root = Entity(parent=parent_entity, y=0)
    parts = {'root': root, 'halo': None, 'bow': None}

    left_hip = Entity(parent=root, position=(-0.22, 0.86, 0))
    right_hip = Entity(parent=root, position=(0.22, 0.86, 0))
    for hip in (left_hip, right_hip):
        Entity(parent=hip, model='cube', scale=(0.24, 0.44, 0.25), y=-0.20, color=cfg['armor_color'])
        Entity(parent=hip, model='diamond', scale=(0.28, 0.24, 0.30), position=(0, -0.42, 0.06), color=cfg['body_color'])
        Entity(parent=hip, model='cube', scale=(0.20, 0.42, 0.22), y=-0.62, color=rgb(40, 44, 54))
        Entity(parent=hip, model='cube', scale=(0.25, 0.16, 0.36), position=(0, -0.80, 0.06), color=cfg['armor_color'])
        Entity(parent=hip, model='cube', scale=(0.26, 0.06, 0.12), position=(0, -0.75, 0.20), color=cfg['visor_color'], unlit=True)

    parts['left_leg'] = left_hip
    parts['right_leg'] = right_hip

    torso = Entity(parent=root, position=(0, 1.26, 0))
    Entity(parent=torso, model='cube', scale=(0.58, 0.22, 0.38), y=-0.32, color=rgb(38, 42, 52))
    Entity(parent=torso, model='cube', scale=(0.18, 0.12, 0.42), y=-0.32, color=cfg['visor_color'], unlit=True)
    Entity(parent=torso, model='cube', scale=(0.68, 0.64, 0.42), y=0.05, color=cfg['body_color'])
    Entity(parent=torso, model='diamond', scale=(0.58, 0.52, 0.28), position=(0, 0.12, 0.16), color=cfg['armor_color'])
    Entity(parent=torso, model='diamond', scale=(0.22, 0.26, 0.32), position=(0, 0.14, 0.20), color=cfg['visor_color'], unlit=True)

    backpack = Entity(parent=torso, model='cube', scale=(0.48, 0.52, 0.28), position=(0, 0.08, -0.30), color=cfg['armor_color'])
    for side_x in (-0.16, 0.16):
        thruster = Entity(parent=backpack, model='cube', scale=(0.22, 0.35, 0.22), position=(side_x, -0.22, -0.05), color=rgb(45, 50, 60))
        Entity(parent=thruster, model='sphere', scale=0.65, y=-0.45, color=cfg['visor_color'], unlit=True)
    parts['torso'] = torso

    head = Entity(parent=torso, position=(0, 0.58, 0))
    if char_key != 'v1':
        Entity(parent=head, model='sphere', scale=(0.54, 0.58, 0.56), color=cfg['armor_color'])

    if char_key == 'commando':
        Entity(parent=head, model='sphere', scale=(0.48, 0.38, 0.42), position=(0, 0.02, 0.14), color=cfg['visor_color'], unlit=True)
        Entity(parent=head, model='cube', scale=(0.05, 0.32, 0.05), position=(-0.25, 0.25, -0.05), color=cfg['body_color'])
        Entity(parent=left_hip, model='cube', scale=(0.14, 0.28, 0.22), position=(-0.16, -0.15, 0), color=rgb(35, 38, 45))
        Entity(parent=right_hip, model='cube', scale=(0.14, 0.28, 0.22), position=(0.16, -0.15, 0), color=rgb(35, 38, 45))

    elif char_key == 'artificer':
        Entity(parent=head, model='cube', scale=(0.44, 0.20, 0.36), position=(0, 0.02, 0.16), color=cfg['visor_color'], unlit=True)
        Entity(parent=head, model='diamond', scale=(0.68, 0.28, 0.68), y=0.22, color=cfg['armor_color'])
        halo = Entity(parent=torso, position=(0, 0.36, -0.52))
        Entity(parent=halo, model='diamond', scale=(1.25, 1.25, 0.12), color=color.cyan, unlit=True)
        Entity(parent=halo, model='diamond', scale=(1.25, 1.25, 0.12), rotation_z=45, color=cfg['visor_color'], unlit=True)
        parts['halo'] = halo

    elif char_key == 'huntress':
        for vy in (-0.08, 0.03, 0.14):
            Entity(parent=head, model='diamond', scale=(0.14, 0.08, 0.35), position=(0, vy, 0.18), color=cfg['visor_color'], unlit=True)
        scarf = Entity(parent=torso, position=(0, 0.35, -0.22), rotation_x=25)
        Entity(parent=scarf, model='cube', scale=(0.55, 0.16, 0.35), color=cfg['body_color'])
        Entity(parent=scarf, model='diamond', scale=(0.38, 0.85, 0.15), position=(0, -0.45, -0.25), color=cfg['body_color'])

    elif char_key == 'buzz':
        Entity(parent=head, model='sphere', scale=(0.56, 0.58, 0.56), color=rgb(145, 55, 225))
        Entity(parent=head, model='sphere', scale=(0.42, 0.42, 0.38), position=(0, -0.02, 0.12), color=rgb(245, 205, 175))
        Entity(parent=head, model='sphere', scale=(0.74, 0.72, 0.74), color=rgb(190, 240, 255, 75), unlit=True)
        Entity(parent=torso, model='cube', scale=(0.72, 0.36, 0.46), position=(0, 0.16, 0.04), color=rgb(125, 235, 65))
        Entity(parent=torso, model='sphere', scale=0.09, position=(-0.18, 0.18, 0.28), color=color.red, unlit=True)
        Entity(parent=torso, model='sphere', scale=0.09, position=(-0.06, 0.18, 0.28), color=color.green, unlit=True)
        Entity(parent=torso, model='sphere', scale=0.09, position=(0.06, 0.18, 0.28), color=color.blue, unlit=True)
        for side in (-1, 1):
            wing = Entity(parent=backpack, model='cube', scale=(1.15, 0.28, 0.08), position=(side * 0.72, 0.12, -0.06), rotation_z=side * -8, color=rgb(155, 65, 245))
            Entity(parent=wing, model='cube', scale=(0.95, 0.42, 0.12), y=0.35, color=color.red, unlit=True)
            Entity(parent=wing, model='sphere', scale=(0.18, 0.65, 0.35), x=side * 0.52, color=color.green if side > 0 else color.red, unlit=True)

    elif char_key == 'v1':
        cam_head = Entity(parent=head, model='cube', scale=(0.36, 0.32, 0.62), position=(0, 0.02, 0.06), color=rgb(45, 115, 235))
        Entity(parent=cam_head, model='sphere', scale=(0.45, 0.48, 0.25), position=(0, 0, 0.52), color=rgb(255, 230, 45), unlit=True)
        wing_hub = Entity(parent=torso, position=(0, 0.18, -0.36))
        for side in (-1, 1):
            for ang in (38, 14, -12, -36):
                w = Entity(parent=wing_hub, rotation_z=side * ang, rotation_y=side * -14)
                Entity(parent=w, model='diamond', scale=(1.15, 0.14, 0.12), position=(side * 0.68, 0, 0), color=rgb(255, 215, 35), unlit=True)

    elif char_key == 'sol':
        Entity(parent=head, model='sphere', scale=(0.48, 0.50, 0.48), color=rgb(245, 200, 170))
        Entity(parent=head, model='cube', scale=(0.54, 0.14, 0.54), y=0.14, color=rgb(215, 30, 40))
        Entity(parent=head, model='cube', scale=(0.24, 0.10, 0.28), position=(0, -0.32, 0.22), color=rgb(255, 185, 50), unlit=True)
        for hx, hy, hz in ((0, 0.30, -0.18), (-0.22, 0.18, -0.22), (0.22, 0.18, -0.22), (0, -0.08, -0.34)):
            Entity(parent=head, model='diamond', scale=(0.28, 0.52, 0.36), position=(hx, hy, hz), rotation_x=35, color=rgb(48, 30, 28))
        Entity(parent=torso, model='cube', scale=(0.74, 0.55, 0.14), position=(0, -0.38, -0.20), rotation_x=12, color=rgb(200, 30, 40))

    elif char_key == 'gwen':
        Entity(parent=head, model='sphere', scale=(0.48, 0.50, 0.48), color=rgb(248, 225, 220))
        Entity(parent=head, model='sphere', scale=0.11, position=(-0.12, 0.04, 0.22), color=rgb(90, 220, 255), unlit=True)
        Entity(parent=head, model='sphere', scale=0.11, position=(0.12, 0.04, 0.22), color=rgb(255, 110, 195), unlit=True)
        Entity(parent=head, model='diamond', scale=(0.65, 0.22, 0.28), position=(0, 0.28, 0.05), color=rgb(32, 28, 46))
        for side in (-1, 1):
            drill = Entity(parent=head, position=(side * 0.36, 0.05, -0.10), rotation_z=side * -18)
            Entity(parent=drill, model='diamond', scale=(0.34, 0.95, 0.34), y=-0.35, color=rgb(75, 205, 255))
            Entity(parent=drill, model='diamond', scale=(0.24, 0.45, 0.24), y=-0.75, color=rgb(185, 240, 255), unlit=True)
        Entity(parent=torso, model='diamond', scale=(1.10, 0.65, 1.10), position=(0, -0.36, 0), color=rgb(32, 28, 46))
        Entity(parent=torso, model='diamond', scale=(1.16, 0.22, 1.16), position=(0, -0.54, 0), color=rgb(195, 240, 255), unlit=True)

    left_shoulder = Entity(parent=torso, position=(-0.48, 0.25, 0))
    right_shoulder = Entity(parent=torso, position=(0.48, 0.25, 0))

    for idx, sh in enumerate((left_shoulder, right_shoulder)):
        Entity(parent=sh, model='diamond', scale=(0.40, 0.38, 0.40), y=0.08, color=cfg['armor_color'])
        arm = Entity(parent=sh, model='cube', scale=(0.18, 0.18, 0.56), position=(0, -0.12, 0.22), color=cfg['body_color'])

        if char_key == 'commando':
            gun = Entity(parent=arm, model='cube', scale=(0.65, 1.1, 0.90), position=(0, 0.15, 0.56), color=rgb(38, 42, 52))
            Entity(parent=gun, model='cube', scale=(0.42, 0.42, 0.95), position=(0, 0.36, 0.45), color=cfg['visor_color'], unlit=True)
        elif char_key == 'artificer':
            orb = Entity(parent=arm, model='diamond', scale=(1.45, 1.45, 0.95), position=(0, 0.12, 0.68), color=color.magenta, unlit=True)
            Entity(parent=orb, model='sphere', scale=0.62, color=color.yellow, unlit=True)
        elif char_key == 'huntress' and idx == 0:
            bow = Entity(parent=sh, position=(0, -0.1, 0.55), rotation_z=15)
            Entity(parent=bow, model='diamond', scale=(0.08, 0.72, 0.22), color=cfg['armor_color'])
            Entity(parent=bow, model='cube', scale=(0.03, 0.68, 0.05), z=-0.06, color=cfg['visor_color'], unlit=True)
            parts['bow'] = bow
        elif char_key == 'buzz' and idx == 1:
            emitter = Entity(parent=sh, model='cube', scale=(0.24, 0.24, 0.28), position=(0, -0.10, 0.38), color=rgb(240, 245, 250))
            Entity(parent=emitter, model='sphere', scale=0.45, z=0.5, color=color.red, unlit=True)
        elif char_key == 'v1' and idx == 1:
            rev = Entity(parent=sh, model='cube', scale=(0.12, 0.18, 0.62), position=(0, -0.08, 0.58), color=rgb(35, 42, 58))
            Entity(parent=rev, model='cube', scale=(0.65, 0.38, 0.95), position=(0, 0.35, 0.15), color=color.cyan, unlit=True)
        elif char_key == 'sol' and idx == 1:
            sword = Entity(parent=sh, position=(0, -0.12, 0.52), rotation_x=15)
            Entity(parent=sword, model='cube', scale=(0.10, 0.22, 1.15), z=0.45, color=rgb(200, 35, 35))
            Entity(parent=sword, model='cube', scale=(0.12, 0.08, 1.10), position=(0, 0.08, 0.45), color=rgb(255, 165, 30), unlit=True)
        elif char_key == 'gwen' and idx == 1:
            scis = Entity(parent=sh, position=(0, -0.12, 0.48))
            Entity(parent=scis, model='diamond', scale=(0.06, 0.16, 1.15), position=(0, 0.10, 0.45), rotation_x=-14, color=rgb(110, 225, 255), unlit=True)
            Entity(parent=scis, model='diamond', scale=(0.06, 0.16, 1.15), position=(0, -0.06, 0.45), rotation_x=14, color=rgb(195, 245, 255), unlit=True)
            Entity(parent=scis, model='sphere', scale=0.22, position=(0, 0.02, 0.05), color=color.gold, unlit=True)

    parts['left_arm'] = left_shoulder
    parts['right_arm'] = right_shoulder
    return parts


# ==========================================
# 3. МОДЕЛИ 7 ОБЫЧНЫХ ВРАГОВ И 3 БОССОВ
# ==========================================
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

    elif enemy_type == 'boss':
        stone_dark = rgb(68, 74, 86)
        stone_light = rgb(98, 106, 120)

        l_leg = Entity(parent=root, position=(-0.85, 1.6, 0))
        r_leg = Entity(parent=root, position=(0.85, 1.6, 0))
        for leg in (l_leg, r_leg):
            Entity(parent=leg, model='cube', scale=(0.88, 1.6, 0.95), y=-0.8, color=stone_dark)
            Entity(parent=leg, model='cube', scale=(1.05, 0.42, 1.25), position=(0, -1.5, 0.15), color=stone_light)
        parts['left_leg'] = l_leg
        parts['right_leg'] = r_leg

        torso = Entity(parent=root, position=(0, 3.2, 0))
        Entity(parent=torso, model='cube', scale=(2.6, 2.8, 1.8), color=stone_light)
        core = Entity(parent=torso, model='sphere', scale=(0.98, 0.98, 0.58), position=(0, 0.25, 0.82), color=color.red, unlit=True)
        Entity(parent=core, model='diamond', scale=(0.55, 0.55, 0.85), z=0.2, color=color.yellow, unlit=True)
        Entity(parent=torso, model='cube', scale=(0.22, 2.2, 1.86), position=(-0.85, 0, 0), color=color.red, unlit=True)
        Entity(parent=torso, model='cube', scale=(0.22, 2.2, 1.86), position=(0.85, 0, 0), color=color.red, unlit=True)

        l_arm = Entity(parent=torso, position=(-1.85, 0.6, 0))
        r_arm = Entity(parent=torso, position=(1.85, 0.6, 0))
        for arm in (l_arm, r_arm):
            Entity(parent=arm, model='diamond', scale=(1.0, 1.15, 1.0), y=0.3, color=stone_dark)
            Entity(parent=arm, model='cube', scale=(0.78, 2.0, 0.78), y=-0.9, color=stone_dark)
            Entity(parent=arm, model='cube', scale=(1.0, 0.88, 1.0), y=-1.9, color=stone_light)
        parts['left_arm'] = l_arm
        parts['right_arm'] = r_arm

        crown = Entity(parent=torso, position=(0, 2.1, 0))
        Entity(parent=crown, model='diamond', scale=(1.55, 0.85, 1.55), color=color.red, unlit=True)
        Entity(parent=crown, model='diamond', scale=(1.95, 0.25, 1.95), rotation_y=45, color=stone_dark)
        parts['crown'] = crown
        parts['core'] = core
        parts['torso'] = torso

    elif enemy_type == 'vagrant':
        # БОСС 2: Wandering Vagrant (Гигантская небесная медуза)
        bell = Entity(parent=root, position=(0, 4.2, 0))
        Entity(parent=bell, model='sphere', scale=(4.2, 2.8, 4.2), color=rgb(55, 205, 255, 185), unlit=True)
        Entity(parent=bell, model='diamond', scale=(4.6, 0.45, 4.6), y=-0.5, color=rgb(120, 245, 255), unlit=True)
        core = Entity(parent=bell, model='sphere', scale=1.8, y=-0.3, color=rgb(255, 230, 80), unlit=True)

        tentacles = Entity(parent=bell, y=-1.0)
        for i in range(8):
            ang = (i / 8.0) * math.pi * 2
            tx, tz = math.cos(ang) * 1.35, math.sin(ang) * 1.35
            Entity(
                parent=tentacles, model='diamond',
                scale=(0.38, 3.2, 0.38), position=(tx, -1.4, tz),
                color=rgb(80, 235, 255), unlit=True
            )
        parts['bell'] = bell
        parts['core'] = core
        parts['tentacles'] = tentacles

    elif enemy_type == 'overlord':
        # БОСС 3: Imp Overlord (Повелитель Бесов)
        void_dark = rgb(36, 18, 42)
        crimson = rgb(245, 30, 65)

        l_leg = Entity(parent=root, position=(-0.85, 1.5, 0))
        r_leg = Entity(parent=root, position=(0.85, 1.5, 0))
        for leg in (l_leg, r_leg):
            Entity(parent=leg, model='diamond', scale=(0.85, 1.7, 0.85), y=-0.8, color=void_dark)
        parts['left_leg'] = l_leg
        parts['right_leg'] = r_leg

        torso = Entity(parent=root, position=(0, 3.1, 0))
        Entity(parent=torso, model='diamond', scale=(2.8, 3.1, 1.9), color=void_dark)
        # Огромный багровый глаз Пустоты в груди
        Entity(parent=torso, model='diamond', scale=(0.65, 1.95, 0.65), z=0.78, color=crimson, unlit=True)
        for side in (-1, 1):
            Entity(parent=torso, model='diamond', scale=(0.45, 1.8, 0.45), position=(side * 0.95, 1.65, 0), rotation_z=side * -25, color=crimson, unlit=True)

        l_arm = Entity(parent=torso, position=(-1.85, 0.55, 0))
        r_arm = Entity(parent=torso, position=(1.85, 0.55, 0))
        for arm in (l_arm, r_arm):
            Entity(parent=arm, model='diamond', scale=(0.85, 2.2, 0.85), y=-0.85, color=void_dark)
            Entity(parent=arm, model='diamond', scale=(0.55, 1.2, 0.55), position=(0, -1.75, 0.35), rotation_x=-40, color=crimson, unlit=True)
        parts['left_arm'] = l_arm
        parts['right_arm'] = r_arm

        crown = Entity(parent=torso, position=(0, 2.0, 0))
        Entity(parent=crown, model='diamond', scale=(2.1, 0.35, 2.1), color=crimson, unlit=True)
        parts['crown'] = crown
        parts['torso'] = torso

    return parts


# ==========================================
# 4. 3D-МОДЕЛИ ВСЕХ 37 ПРЕДМЕТОВ
# ==========================================
def build_item_mesh(parent_entity, item_key):
    root = Entity(parent=parent_entity)
    item_col = ITEM_POOL.get(item_key, {}).get('color', color.yellow)

    if item_key == 'syringe':
        tilt = Entity(parent=root, rotation_z=35)
        Entity(parent=tilt, model='cube', scale=(0.28, 0.75, 0.28), color=rgb(220, 235, 250))
        Entity(parent=tilt, model='cube', scale=(0.22, 0.55, 0.30), color=color.yellow, unlit=True)
        Entity(parent=tilt, model='cube', scale=(0.05, 0.45, 0.05), y=0.55, color=color.light_gray)
        Entity(parent=tilt, model='cube', scale=(0.42, 0.08, 0.42), y=-0.42, color=color.gray)

    elif item_key == 'hoof':
        Entity(parent=root, model='cube', scale=(0.26, 0.65, 0.26), y=0.15, rotation_z=-15, color=rgb(235, 240, 250))
        Entity(parent=root, model='diamond', scale=(0.44, 0.35, 0.55), position=(0.1, -0.22, 0.08), color=color.cyan, unlit=True)

    elif item_key == 'bear':
        brown = rgb(215, 130, 55)
        Entity(parent=root, model='sphere', scale=0.52, y=-0.12, color=brown)
        head = Entity(parent=root, model='sphere', scale=0.42, y=0.28, color=brown)
        Entity(parent=head, model='sphere', scale=0.38, position=(-0.38, 0.38, 0), color=brown)
        Entity(parent=head, model='sphere', scale=0.38, position=(0.38, 0.38, 0), color=brown)
        Entity(parent=head, model='sphere', scale=0.28, position=(0, -0.05, 0.42), color=rgb(245, 210, 170))

    elif item_key == 'ukulele':
        tilt = Entity(parent=root, rotation_z=-30)
        Entity(parent=tilt, model='sphere', scale=(0.48, 0.55, 0.18), y=-0.18, color=rgb(210, 125, 45))
        Entity(parent=tilt, model='sphere', scale=(0.36, 0.40, 0.19), y=0.05, color=rgb(210, 125, 45))
        Entity(parent=tilt, model='sphere', scale=(0.18, 0.18, 0.22), y=-0.05, color=color.magenta, unlit=True)
        Entity(parent=tilt, model='cube', scale=(0.10, 0.65, 0.08), y=0.42, color=rgb(110, 65, 25))

    elif item_key == 'gasoline':
        Entity(parent=root, model='cube', scale=(0.52, 0.65, 0.32), y=-0.05, color=color.red)
        Entity(parent=root, model='cube', scale=(0.32, 0.14, 0.16), y=0.34, color=rgb(180, 30, 30))
        Entity(parent=root, model='cube', scale=(0.10, 0.28, 0.10), position=(0.18, 0.38, 0), rotation_z=-35, color=color.yellow, unlit=True)

    elif item_key == 'lens':
        Entity(parent=root, model='cube', scale=(0.75, 0.08, 0.10), y=0.10, color=rgb(40, 45, 55))
        Entity(parent=root, model='sphere', scale=(0.32, 0.28, 0.14), position=(-0.20, 0.04, 0.04), color=rgb(255, 35, 75), unlit=True)
        Entity(parent=root, model='sphere', scale=(0.32, 0.28, 0.14), position=(0.20, 0.04, 0.04), color=rgb(255, 35, 75), unlit=True)

    elif item_key == 'feather':
        tilt = Entity(parent=root, rotation_z=25)
        Entity(parent=tilt, model='cube', scale=(0.06, 0.85, 0.06), color=color.gold, unlit=True)
        Entity(parent=tilt, model='diamond', scale=(0.38, 0.68, 0.12), y=0.12, color=rgb(90, 255, 150), unlit=True)

    elif item_key == 'crowbar':
        tilt = Entity(parent=root, rotation_z=30)
        Entity(parent=tilt, model='cube', scale=(0.12, 0.85, 0.12), color=rgb(210, 45, 45))
        Entity(parent=tilt, model='cube', scale=(0.32, 0.12, 0.12), position=(0.1, 0.42, 0), color=rgb(200, 210, 225))

    elif item_key in ('tri_tip', 'harvester_scythe'):
        tilt = Entity(parent=root, rotation_z=-35)
        Entity(parent=tilt, model='diamond', scale=(0.28, 0.85, 0.14), y=0.12, color=item_col, unlit=True)
        Entity(parent=tilt, model='cube', scale=(0.12, 0.35, 0.12), y=-0.35, color=rgb(60, 65, 75))

    elif item_key in ('ap_rounds', 'backup_mag', 'bandolier'):
        Entity(parent=root, model='cube', scale=(0.48, 0.58, 0.28), color=rgb(65, 75, 90))
        for bx in (-0.14, 0.0, 0.14):
            Entity(parent=root, model='diamond', scale=(0.12, 0.45, 0.12), position=(bx, 0.32, 0), color=item_col, unlit=True)

    elif item_key in ('energy_drink', 'will_o_wisp', 'infusion'):
        Entity(parent=root, model='cube', scale=(0.38, 0.68, 0.38), color=item_col, unlit=True)
        Entity(parent=root, model='cube', scale=(0.42, 0.12, 0.42), y=0.35, color=color.white)

    elif item_key in ('bison_steak', 'monster_tooth', 'leeching_seed'):
        Entity(parent=root, model='sphere', scale=(0.62, 0.42, 0.48), color=item_col)
        Entity(parent=root, model='sphere', scale=0.24, position=(0.12, 0.05, 0.18), color=color.white, unlit=True)

    elif item_key in ('medkit', 'repulsion_armor', 'rose_buckler'):
        Entity(parent=root, model='cube', scale=(0.64, 0.52, 0.24), color=rgb(235, 240, 250))
        Entity(parent=root, model='cube', scale=(0.42, 0.14, 0.28), color=item_col, unlit=True)
        Entity(parent=root, model='cube', scale=(0.14, 0.42, 0.28), color=item_col, unlit=True)

    elif item_key in ('topaz_brooch', 'opal', 'focus_crystal', 'chronobauble'):
        Entity(parent=root, model='diamond', scale=(0.58, 0.78, 0.58), color=item_col, unlit=True)
        Entity(parent=root, model='diamond', scale=(0.82, 0.16, 0.82), color=color.gold, unlit=True)

    elif item_key in ('kjaro_band', 'runald_band'):
        Entity(parent=root, model='diamond', scale=(0.72, 0.22, 0.72), color=item_col, unlit=True)
        Entity(parent=root, model='sphere', scale=0.32, y=0.22, color=color.white, unlit=True)

    elif item_key in ('atg_missile', 'bundle_fireworks', 'behemoth', 'sticky_bomb', 'stun_grenade'):
        tilt = Entity(parent=root, rotation_z=25)
        Entity(parent=tilt, model='cube', scale=(0.32, 0.72, 0.32), color=item_col, unlit=True)
        Entity(parent=tilt, model='diamond', scale=(0.42, 0.42, 0.42), y=0.45, color=color.yellow, unlit=True)

    else:
        # Клевер, кнут, восковое перо, хищные инстинкты и др.
        Entity(parent=root, model='diamond', scale=(0.55, 0.72, 0.55), color=item_col, unlit=True)
        Entity(parent=root, model='sphere', scale=0.38, color=color.white, unlit=True)

    return root


# ==========================================
# 5. СТРУКТУРЫ КАРТЫ С ТОЧНЫМИ ДАННЫМИ КОЛЛИЗИЙ
# ==========================================
def build_map_structure(parent_entity, struct_type, palette, pos, rot_y):
    root = Entity(parent=parent_entity, position=pos, rotation_y=rot_y)
    ruin_col = palette['ruins']
    accent_col = palette['accent']
    obstacles = []
    rad_y = math.radians(rot_y)
    cos_y, sin_y = math.cos(rad_y), math.sin(rad_y)

    def to_world(lx, lz):
        wx = pos.x + lx * cos_y + lz * sin_y
        wz = pos.z - lx * sin_y + lz * cos_y
        return wx, wz

    if struct_type == 'arch':
        h = random.uniform(7.5, 11.5)
        w = random.uniform(6.5, 9.0)
        Entity(parent=root, model='cube', scale=(1.8, h, 1.8), position=(-w / 2, h / 2, 0), color=ruin_col, collider='box')
        Entity(parent=root, model='cube', scale=(1.8, h, 1.8), position=(w / 2, h / 2, 0), color=ruin_col, collider='box')
        Entity(parent=root, model='cube', scale=(w + 2.8, 1.6, 2.2), position=(0, h + 0.5, 0), color=ruin_col)
        Entity(parent=root, model='diamond', scale=(1.3, 2.3, 1.3), position=(0, h - 1.5, 0), color=accent_col, unlit=True)

        wx1, wz1 = to_world(-w / 2, 0)
        wx2, wz2 = to_world(w / 2, 0)
        obstacles.append((wx1, wz1, 1.15, h))
        obstacles.append((wx2, wz2, 1.15, h))

    elif struct_type == 'monolith':
        h = random.uniform(7.0, 14.0)
        Entity(parent=root, model='cube', scale=(3.8, 1.6, 3.8), y=0.8, color=ruin_col, collider='box')
        Entity(parent=root, model='cube', scale=(2.5, h, 2.5), y=h / 2 + 1.0, color=ruin_col, collider='box')
        Entity(parent=root, model='cube', scale=(0.45, h * 0.72, 2.6), y=h / 2 + 1.0, color=accent_col, unlit=True)
        Entity(parent=root, model='diamond', scale=(2.6, 2.6, 2.6), y=h + 1.6, color=ruin_col)
        obstacles.append((pos.x, pos.z, 1.95, h + 1.5))

    elif struct_type == 'crystals':
        Entity(parent=root, model='sphere', scale=(3.6, 2.2, 3.4), y=0.7, color=ruin_col, collider='box')
        for _ in range(3):
            ang = random.uniform(-25, 25)
            ch = random.uniform(2.5, 4.8)
            Entity(
                parent=root,
                model='diamond',
                scale=(0.95, ch, 0.95),
                position=(random.uniform(-1.0, 1.0), ch * 0.4, random.uniform(-1.0, 1.0)),
                rotation=(ang, random.uniform(0, 360), ang),
                color=accent_col,
                unlit=True
            )
        obstacles.append((pos.x, pos.z, 1.85, 2.2))

    elif struct_type == 'platform':
        Entity(parent=root, model='cube', scale=(5.2, 1.8, 5.2), y=0.9, color=ruin_col, collider='box')
        Entity(parent=root, model='cube', scale=(5.3, 0.2, 5.3), y=1.7, color=accent_col, unlit=True)
        obstacles.append((pos.x, pos.z, 2.75, 1.8))

    return root, obstacles