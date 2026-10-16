from ursina import *
import math
import random
from config import rgb

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

