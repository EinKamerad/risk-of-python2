from ursina import *
import math
import random
from config import rgb, SURVIVOR_CLASSES

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

