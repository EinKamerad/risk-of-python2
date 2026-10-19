from ursina import *
import math
import random
from config import rgb, ITEM_POOL


def build_item_mesh(parent_entity, item_key):
    root = Entity(parent=parent_entity)
    info = ITEM_POOL.get(item_key, {})
    item_col = info.get('mesh_color', info.get('color', color.yellow))

    if item_key == 'syringe':
        tilt = Entity(parent=root, rotation_z=35)
        Entity(parent=tilt, model='cube', scale=(0.28, 0.75, 0.28), color=rgb(220, 235, 250))
        Entity(parent=tilt, model='cube', scale=(0.22, 0.55, 0.30), color=color.yellow, unlit=True)
        Entity(parent=tilt, model='cube', scale=(0.05, 0.45, 0.05), y=0.55, color=color.light_gray)
        Entity(parent=tilt, model='cube', scale=(0.42, 0.08, 0.42), y=-0.42, color=color.gray)

    elif item_key == 'hoof':
        Entity(parent=root, model='cube', scale=(0.26, 0.65, 0.26), y=0.15, rotation_z=-15, color=rgb(235, 240, 250))
        Entity(parent=root, model='diamond', scale=(0.44, 0.35, 0.55), position=(0.1, -0.22, 0.08), color=color.cyan, unlit=True)

    elif item_key in ('bear', 'safer_spaces'):
        brown = rgb(185, 85, 245) if item_key == 'safer_spaces' else rgb(215, 130, 55)
        Entity(parent=root, model='sphere', scale=0.52, y=-0.12, color=brown)
        head = Entity(parent=root, model='sphere', scale=0.42, y=0.28, color=brown)
        Entity(parent=head, model='sphere', scale=0.38, position=(-0.38, 0.38, 0), color=brown)
        Entity(parent=head, model='sphere', scale=0.38, position=(0.38, 0.38, 0), color=brown)
        Entity(parent=head, model='sphere', scale=0.28, position=(0, -0.05, 0.42), color=rgb(245, 210, 170))
        if item_key == 'safer_spaces':
            Entity(parent=root, model='sphere', scale=0.88, color=rgb(200, 85, 255, 95), unlit=True)

    elif item_key in ('ukulele', 'polylute'):
        tilt = Entity(parent=root, rotation_z=-30)
        body_c = rgb(155, 55, 225) if item_key == 'polylute' else rgb(210, 125, 45)
        Entity(parent=tilt, model='sphere', scale=(0.48, 0.55, 0.18), y=-0.18, color=body_c)
        Entity(parent=tilt, model='sphere', scale=(0.36, 0.40, 0.19), y=0.05, color=body_c)
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

    elif item_key == 'bungus':
        Entity(parent=root, model='cube', scale=(0.24, 0.48, 0.24), y=-0.15, color=rgb(230, 240, 225))
        Entity(parent=root, model='sphere', scale=(0.75, 0.42, 0.75), y=0.18, color=rgb(85, 245, 120), unlit=True)
        for sx, sz in ((-0.18, 0.15), (0.18, -0.15), (0.12, 0.18)):
            Entity(parent=root, model='sphere', scale=0.14, position=(sx, 0.32, sz), color=color.cyan, unlit=True)

    elif item_key == 'tarrasque':
        Entity(parent=root, model='diamond', scale=(0.65, 0.78, 0.55), color=rgb(235, 35, 60), unlit=True)
        Entity(parent=root, model='sphere', scale=(0.45, 0.45, 0.45), position=(-0.14, 0.18, 0), color=rgb(255, 85, 95), unlit=True)
        Entity(parent=root, model='sphere', scale=(0.45, 0.45, 0.45), position=(0.14, 0.18, 0), color=rgb(255, 85, 95), unlit=True)

    elif item_key == 'tesla_coil':
        Entity(parent=root, model='cube', scale=(0.45, 0.22, 0.45), y=-0.25, color=rgb(55, 65, 82))
        Entity(parent=root, model='cube', scale=(0.18, 0.55, 0.18), y=0.05, color=rgb(180, 120, 60))
        Entity(parent=root, model='sphere', scale=(0.48, 0.28, 0.48), y=0.38, color=color.cyan, unlit=True)

    elif item_key == 'aegis':
        Entity(parent=root, model='diamond', scale=(0.68, 0.78, 0.22), color=color.gold, unlit=True)
        Entity(parent=root, model='diamond', scale=(0.42, 0.52, 0.26), color=color.white, unlit=True)

    elif item_key in ('shattering_justice', 'guillotine'):
        tilt = Entity(parent=root, rotation_z=25)
        Entity(parent=tilt, model='cube', scale=(0.12, 0.85, 0.12), color=rgb(80, 85, 95))
        Entity(parent=tilt, model='cube', scale=(0.55, 0.28, 0.28), y=0.35, color=item_col, unlit=True)

    elif item_key == 'crowbar':
        tilt = Entity(parent=root, rotation_z=30)
        Entity(parent=tilt, model='cube', scale=(0.12, 0.85, 0.12), color=rgb(210, 45, 45))
        Entity(parent=tilt, model='cube', scale=(0.32, 0.12, 0.12), position=(0.1, 0.42, 0), color=rgb(200, 210, 225))

    elif item_key in ('tri_tip', 'harvester_scythe', 'ceremonial_dagger'):
        tilt = Entity(parent=root, rotation_z=-35)
        Entity(parent=tilt, model='diamond', scale=(0.28, 0.85, 0.14), y=0.12, color=item_col, unlit=True)
        Entity(parent=tilt, model='cube', scale=(0.12, 0.35, 0.12), y=-0.35, color=rgb(60, 65, 75))

    elif item_key in ('ap_rounds', 'backup_mag', 'bandolier', 'afterburner', 'lysate_cell'):
        Entity(parent=root, model='cube', scale=(0.48, 0.58, 0.28), color=rgb(65, 75, 90))
        for bx in (-0.14, 0.0, 0.14):
            Entity(parent=root, model='diamond', scale=(0.12, 0.45, 0.12), position=(bx, 0.32, 0), color=item_col, unlit=True)

    elif item_key in ('energy_drink', 'will_o_wisp', 'infusion', 'plasma_shrimp'):
        Entity(parent=root, model='cube', scale=(0.38, 0.68, 0.38), color=item_col, unlit=True)
        Entity(parent=root, model='cube', scale=(0.42, 0.12, 0.42), y=0.35, color=color.white)

    elif item_key in ('bison_steak', 'monster_tooth', 'leeching_seed', 'alien_head'):
        Entity(parent=root, model='sphere', scale=(0.62, 0.52, 0.48), color=item_col)
        Entity(parent=root, model='sphere', scale=0.22, position=(-0.12, 0.05, 0.18), color=color.black, unlit=True)
        Entity(parent=root, model='sphere', scale=0.22, position=(0.12, 0.05, 0.18), color=color.black, unlit=True)

    elif item_key in ('medkit', 'repulsion_armor', 'rose_buckler'):
        Entity(parent=root, model='cube', scale=(0.64, 0.52, 0.24), color=rgb(235, 240, 250))
        Entity(parent=root, model='cube', scale=(0.42, 0.14, 0.28), color=item_col, unlit=True)
        Entity(parent=root, model='cube', scale=(0.14, 0.42, 0.28), color=item_col, unlit=True)

    elif item_key in ('topaz_brooch', 'opal', 'focus_crystal', 'chronobauble', 'frost_relic', 'razorwire'):
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
        Entity(parent=root, model='diamond', scale=(0.55, 0.72, 0.55), color=item_col, unlit=True)
        Entity(parent=root, model='sphere', scale=0.38, color=color.white, unlit=True)

    return root