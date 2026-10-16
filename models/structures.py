from ursina import *
import math
import random
from config import rgb

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

