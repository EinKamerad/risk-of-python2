from _monolith_backup.config import ctx
from ursina import *
import math
import random
from config import rgb, STAGE_PALETTES, PROGRESS
from data.stages import SPECIAL_PALETTES
from data.items import LUNAR_ITEMS
from models.skybox import build_skybox
from models.structures import build_map_structure
from world.interactables import Chest, HealingShrine
from world.teleporter import Teleporter
from world.lunar import NewtAltar, BluePortal, LunarShopBud, LunarCauldron, MoonPillar, LunarJumpPad


def build_stage_world(stage_num, seed=None, special_mode=None):
    entities_list = []
    obstacles_list = []
    sky_platforms = []

    if special_mode == 'bazaar':
        palette = SPECIAL_PALETTES['bazaar']
    elif special_mode == 'moon':
        palette = SPECIAL_PALETTES['moon']
    else:
        palette = STAGE_PALETTES[(stage_num - 1) % len(STAGE_PALETTES)]

    if palette['id'] not in PROGRESS.discovered_stages:
        PROGRESS.discovered_stages.append(palette['id'])
        PROGRESS.save()

    window.color = palette['sky']
    scene.fog_color = palette['sky']
    sky_ent = build_skybox(scene, palette)
    entities_list.append(sky_ent)

    if seed is not None:
        random.seed(seed)

    ground = Entity(model='cube', scale=(126, 1, 126), y=-0.5, color=palette['ground'], collider='box')
    entities_list.append(ground)

    # ==========================================================
    # РЕЖИМ 1: БАЗАР МЕЖДУ ВРЕМЕНЕМ (BAZAAR BETWEEN TIME)
    # ==========================================================
    if special_mode == 'bazaar':
        # Статуя гигантского Смотрителя Тритона (Newt)
        newt = Entity(position=(0, 0, 22))
        Entity(parent=newt, model='sphere', scale=(6.5, 5.2, 7.5), y=2.6, color=rgb(45, 95, 165))
        Entity(parent=newt, model='sphere', scale=(4.2, 3.8, 4.8), position=(0, 5.0, 2.8), color=rgb(55, 115, 195))
        for ex in (-1.2, 1.2):
            Entity(parent=newt, model='sphere', scale=0.65, position=(ex, 5.6, 4.8), color=color.cyan, unlit=True)
        entities_list.append(newt)

        # 4 витрины с Лунными предметами
        lunar_keys = list(LUNAR_ITEMS.keys())
        random.shuffle(lunar_keys)
        for i in range(4):
            bx = -12.0 + i * 8.0
            entities_list.append(LunarShopBud(Vec3(bx, 0, 8.0), lunar_keys[i % len(lunar_keys)], cost=2))

        # 2 Котла обмена (Зелёный и Красный легендарный)
        entities_list.append(LunarCauldron(Vec3(-10, 0, -6), 'atg_missile', req_count=3))
        entities_list.append(LunarCauldron(Vec3(10, 0, -6), 'clover', req_count=5))

        # Выходной портал обратно на трассу этапов
        exit_portal = BluePortal(Vec3(0, 0, -18), target_mode='next_stage')
        entities_list.append(exit_portal)
        random.seed()
        return entities_list, obstacles_list, None, palette['name']

    # ==========================================================
    # РЕЖИМ 2: COMMENCEMENT — ЛУНА И КОЛИЗЕЙ МИТРИКСА
    # ==========================================================
    if special_mode == 'moon':
        # 4 Столпа Луны по углам нижнего плато
        pillar_defs = [
            (Vec3(-34, 0, -34), 'mass'),
            (Vec3(34, 0, -34), 'design'),
            (Vec3(-34, 0, 34), 'blood'),
            (Vec3(34, 0, 34), 'soul'),
        ]
        for p_pos, p_type in pillar_defs:
            entities_list.append(MoonPillar(p_pos, p_type))
            obstacles_list.append((p_pos.x, p_pos.z, 1.6, 5.0))

        # Лунные арки и колонны на нижнем плато
        for angle_deg in range(0, 360, 45):
            rad = math.radians(angle_deg)
            ax, az = math.cos(rad) * 46.0, math.sin(rad) * 46.0
            s_ent, local_obs = build_map_structure(scene, 'monolith', palette, Vec3(ax, 0, az), angle_deg)
            entities_list.append(s_ent)
            obstacles_list.extend(local_obs)

        # Гравитационный лифт в центре нижнего плато
        jump_pad = LunarJumpPad(Vec3(0, 0, -24))
        entities_list.append(jump_pad)

        # ПАРЯЩИЙ НЕБЕСНЫЙ КОЛИЗЕЙ МИТРИКСА НА ВЫСОТЕ Y = 22.0
        colosseum = Entity(position=(0, 22.0, 0))
        Entity(parent=colosseum, model='sphere', scale=(54.0, 1.2, 54.0), y=-0.5, color=rgb(215, 225, 242))
        Entity(parent=colosseum, model='diamond', scale=(56.0, 0.35, 56.0), y=0.0, color=rgb(70, 200, 255), unlit=True)
        # 12 величественных белых колонн по периметру арены Митрикса
        for i in range(12):
            ang = (i / 12.0) * math.pi * 2
            cx, cz = math.cos(ang) * 25.5, math.sin(ang) * 25.5
            Entity(parent=colosseum, model='cube', scale=(1.8, 9.5, 1.8), position=(cx, 4.75, cz), color=rgb(55, 68, 92))
            Entity(parent=colosseum, model='diamond', scale=(1.2, 2.2, 1.2), position=(cx, 10.5, cz), color=rgb(80, 225, 255), unlit=True)
        entities_list.append(colosseum)

        # Регистрируем парящую платформу арены Митрикса в физике
        sky_platforms.append((0.0, 0.0, 27.5, 22.0))
        if hasattr(ctx.game, 'sky_platforms'):
            ctx.game.sky_platforms = sky_platforms

        random.seed()
        return entities_list, obstacles_list, jump_pad, palette['name']

    # ==========================================================
    # РЕЖИМ 3: ОБЫЧНЫЕ ЭТАПЫ PETRICHOR V
    # ==========================================================
    if hasattr(ctx.game, 'sky_platforms'):
        ctx.game.sky_platforms = []

    struct_types = ['arch', 'monolith', 'crystals', 'platform']
    for _ in range(28):
        px = random.uniform(-50, 50)
        pz = random.uniform(-50, 50)
        if abs(px) < 10 and abs(pz) < 10:
            continue
        st = random.choice(struct_types)
        rot_y = random.uniform(0, 360)
        s_ent, local_obs = build_map_structure(scene, st, palette, Vec3(px, 0, pz), rot_y)
        entities_list.append(s_ent)
        obstacles_list.extend(local_obs)

    chest_cost = int(25 * (1.25 ** (stage_num - 1)))
    for idx in range(13):
        cx = random.uniform(-46, 46)
        cz = random.uniform(-46, 46)
        if abs(cx) < 6 and abs(cz) < 6:
            continue
        chest = Chest(Vec3(cx, 0, cz), chest_cost, chest_id=idx)
        entities_list.append(chest)
        obstacles_list.append((cx, cz, 0.9, 1.0))

    for _ in range(2):
        sx = random.uniform(-36, 36)
        sz = random.uniform(-36, 36)
        shrine = HealingShrine(Vec3(sx, 0, sz), int(chest_cost * 0.8))
        entities_list.append(shrine)
        obstacles_list.append((sx, sz, 1.1, 3.2))

    # Алтарь Тритона для открытия Синего портала на Базар
    nx, nz = random.uniform(-34, 34), random.uniform(-34, 34)
    entities_list.append(NewtAltar(Vec3(nx, 0, nz)))

    angle = random.uniform(0, math.pi * 2)
    tp_pos = Vec3(math.cos(angle) * 35, 0, math.sin(angle) * 35)
    tp = Teleporter(tp_pos)
    entities_list.append(tp)
    for a in (0, 90, 180, 270):
        r = math.radians(a)
        obstacles_list.append((tp_pos.x + math.cos(r) * 2.2, tp_pos.z + math.sin(r) * 2.2, 0.65, 3.2))

    random.seed()
    return entities_list, obstacles_list, tp, palette['name']