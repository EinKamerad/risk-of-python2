from ursina import *
import math
import random
from config import ctx, rgb, STAGE_PALETTES, PROGRESS
from data.stages import SPECIAL_PALETTES
from data.items import LUNAR_ITEMS
from models.skybox import build_skybox
from models.structures import build_map_structure
from world.interactables import Chest, HealingShrine
from world.teleporter import Teleporter
from world.lunar import (
    NewtAltar, BluePortal, LunarShopBud, LunarCauldron,
    MoonPillar, LunarJumpPad, LunarBouncePad, COLOSSEUM_Y, COLOSSEUM_RADIUS
)


def _spawn_parkour_disc(entities_list, sky_platforms, pos, radius, thickness=1.2, col=None, accent=None):
    """Создаёт парящую лунную платформу и регистрирует её поверхность в физике"""
    c_main = col or rgb(200, 212, 232)
    c_acc = accent or rgb(75, 215, 255)
    plat = Entity(position=Vec3(*pos))
    Entity(
        parent=plat, model='cylinder' if False else 'sphere',
        scale=(radius * 2.0, thickness, radius * 2.0),
        y=-thickness * 0.45, color=c_main, collider='box'
    )
    Entity(
        parent=plat, model='diamond',
        scale=(radius * 2.05, 0.22, radius * 2.05),
        y=0.0, color=c_acc, unlit=True
    )
    entities_list.append(plat)
    sky_platforms.append((pos[0], pos[2], radius, pos[1]))
    return plat


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

    ground_size = 240 if special_mode == 'moon' else 126
    ground = Entity(
        model='cube', scale=(ground_size, 2, ground_size),
        y=-1.0, color=palette['ground'], collider='box'
    )
    entities_list.append(ground)

    if ctx.game is not None:
        ctx.game.world_bound = 112.0 if special_mode == 'moon' else 58.0

    # ==========================================================
    # РЕЖИМ 1: БАЗАР МЕЖДУ ВРЕМЕНЕМ (BAZAAR BETWEEN TIME)
    # ==========================================================
    if special_mode == 'bazaar':
        if ctx.game is not None:
            ctx.game.sky_platforms = []

        newt = Entity(position=(0, 0, 22))
        Entity(parent=newt, model='sphere', scale=(6.5, 5.2, 7.5), y=2.6, color=rgb(45, 95, 165))
        Entity(parent=newt, model='sphere', scale=(4.2, 3.8, 4.8), position=(0, 5.0, 2.8), color=rgb(55, 115, 195))
        for ex in (-1.2, 1.2):
            Entity(parent=newt, model='sphere', scale=0.65, position=(ex, 5.6, 4.8), color=color.cyan, unlit=True)
        entities_list.append(newt)

        lunar_keys = list(LUNAR_ITEMS.keys())
        random.shuffle(lunar_keys)
        for i in range(4):
            bx = -12.0 + i * 8.0
            entities_list.append(LunarShopBud(Vec3(bx, 0, 8.0), lunar_keys[i % len(lunar_keys)], cost=2))

        entities_list.append(LunarCauldron(Vec3(-10, 0, -6), 'atg_missile', req_count=3))
        entities_list.append(LunarCauldron(Vec3(10, 0, -6), 'clover', req_count=5))

        exit_portal = BluePortal(Vec3(0, 0, -18), target_mode='next_stage')
        entities_list.append(exit_portal)
        random.seed()
        return entities_list, obstacles_list, None, palette['name']

    # ==========================================================
    # РЕЖИМ 2: COMMENCEMENT — ЛУНА И НЕБЕСНЫЙ КОЛИЗЕЙ МИТРИКСА
    # ==========================================================
    if special_mode == 'moon':
        # 1. Центральный Гравитационный Лифт к Митриксу на (0, 0, 0)
        jump_pad = LunarJumpPad(Vec3(0, 0, 0))
        entities_list.append(jump_pad)

        # Кольцо древних монолитов вокруг центральной площади
        for angle_deg in range(0, 360, 45):
            if angle_deg in (45, 135, 225, 315):
                continue
            rad = math.radians(angle_deg)
            ax, az = math.cos(rad) * 26.0, math.sin(rad) * 26.0
            s_ent, local_obs = build_map_structure(scene, 'arch', palette, Vec3(ax, 0, az), angle_deg)
            entities_list.append(s_ent)
            obstacles_list.extend(local_obs)

        # 2. Четыре возвышенных Бастиона Столпов Луны + паркур-маршруты к ним
        bastion_configs = [
            # (dir_x, dir_z, p_type, bastion_height, accent_col)
            (-1, -1, 'mass', 12.0, rgb(75, 210, 255)),
            (1, -1, 'design', 15.0, rgb(110, 180, 255)),
            (-1, 1, 'blood', 11.0, rgb(245, 65, 85)),
            (1, 1, 'soul', 16.5, rgb(165, 110, 255)),
        ]

        chest_cost = int(25 * (1.25 ** max(0, stage_num - 1)))
        chest_id_counter = 200

        for dx, dz, p_type, b_height, b_col in bastion_configs:
            norm_x = dx * 0.7071
            norm_z = dz * 0.7071

            # Светящаяся энергетическая дорожка на земле в сторону бастиона
            for step_d in (16.0, 28.0):
                rx, rz = norm_x * step_d, norm_z * step_d
                rune = Entity(
                    model='cube', scale=(2.4, 0.08, 6.0),
                    position=(rx, 0.04, rz),
                    rotation_y=math.degrees(math.atan2(norm_x, norm_z)),
                    color=b_col, unlit=True
                )
                entities_list.append(rune)

            # Цепочка из 5 парящих паркур-платформ с плавным подъёмом к бастиону
            num_steps = 5
            for s_idx in range(1, num_steps + 1):
                frac = s_idx / float(num_steps + 1)
                dist = 24.0 + frac * 54.0
                lateral = math.sin(s_idx * 1.4) * 6.5
                px = norm_x * dist - norm_z * lateral
                pz = norm_z * dist + norm_x * lateral
                py = round(b_height * frac, 2)
                _spawn_parkour_disc(
                    entities_list, sky_platforms,
                    (px, py, pz), radius=4.8, thickness=1.0,
                    col=rgb(175, 190, 215), accent=b_col
                )

                # На 2-й платформе каждого маршрута ставим сундук с лутом
                if s_idx == 2:
                    ch = Chest(Vec3(px, py, pz), chest_cost, chest_id=chest_id_counter)
                    chest_id_counter += 1
                    entities_list.append(ch)

            # Дополнительный скоростной трамплин (Bounce Pad) у подножия маршрута
            bpad_pos = Vec3(norm_x * 32.0 + norm_z * 9.0, 0.0, norm_z * 32.0 - norm_x * 9.0)
            entities_list.append(LunarBouncePad(bpad_pos, jump_vel=21.5, boost_forward=14.0))

            # Главная парящая платформа Бастиона (радиус 16.5м), где стоит Столп Луны
            bx, bz = norm_x * 84.0, norm_z * 84.0
            _spawn_parkour_disc(
                entities_list, sky_platforms,
                (bx, b_height, bz), radius=16.5, thickness=2.2,
                col=rgb(210, 222, 240), accent=b_col
            )

            # Сам Столп Луны в центре Бастиона
            pillar = MoonPillar(Vec3(bx, b_height, bz), p_type)
            entities_list.append(pillar)
            obstacles_list.append((bx, bz, 1.6, b_height + 5.5, b_height))

            # 4 декоративных обелиска по краям Бастиона
            for c_ang in (0, 90, 180, 270):
                cr = math.radians(c_ang)
                ox, oz = bx + math.cos(cr) * 13.5, bz + math.sin(cr) * 13.5
                col_ent = Entity(
                    model='cube', scale=(1.5, 5.5, 1.5),
                    position=(ox, b_height + 2.75, oz), color=rgb(55, 68, 92)
                )
                Entity(
                    parent=col_ent, model='diamond', scale=(0.9, 0.5, 0.9),
                    y=0.65, color=b_col, unlit=True
                )
                entities_list.append(col_ent)
                obstacles_list.append((ox, oz, 1.1, b_height + 5.5, b_height))

        # 3. Боковые паркур-острова с Алтарями Лечения и Сундуками (Север, Юг, Запад, Восток)
        cardinal_islands = [
            (0.0, 68.0, 8.5),
            (0.0, -68.0, 8.5),
            (-68.0, 0.0, 8.5),
            (68.0, 0.0, 8.5),
        ]
        for ix, iz, iy in cardinal_islands:
            # Трамплин с земли на боковой остров
            ux = ix * 0.68
            uz = iz * 0.68
            entities_list.append(LunarBouncePad(Vec3(ux, 0.0, uz), jump_vel=18.5, boost_forward=10.0))
            _spawn_parkour_disc(
                entities_list, sky_platforms,
                (ix, iy, iz), radius=9.5, thickness=1.5,
                col=rgb(190, 205, 228), accent=rgb(90, 235, 195)
            )
            shrine = HealingShrine(Vec3(ix - 2.5, iy, iz), int(chest_cost * 0.75))
            entities_list.append(shrine)
            ch = Chest(Vec3(ix + 2.8, iy, iz), chest_cost, chest_id=chest_id_counter)
            chest_id_counter += 1
            entities_list.append(ch)

        # Пограничные мега-монолиты на дальнем кольце нижнего плато (R = 104м)
        for angle_deg in range(0, 360, 30):
            rad = math.radians(angle_deg)
            ax, az = math.cos(rad) * 104.0, math.sin(rad) * 104.0
            s_ent, local_obs = build_map_structure(scene, 'monolith', palette, Vec3(ax, 0, az), angle_deg)
            entities_list.append(s_ent)
            obstacles_list.extend(local_obs)

        # ==========================================================
        # 4. НЕБЕСНЫЙ КОЛИЗЕЙ МИТРИКСА НА ВЫСОТЕ Y = 120.0 (РАДИУС 56м)
        # ==========================================================
        colosseum = Entity(position=(0, COLOSSEUM_Y, 0))
        # Массивное многослойное основание Колизея с твёрдым коллайдером
        Entity(
            parent=colosseum, model='cube',
            scale=(COLOSSEUM_RADIUS * 1.85, 3.0, COLOSSEUM_RADIUS * 1.85),
            y=-1.5, color=rgb(195, 208, 228), collider='box'
        )
        Entity(
            parent=colosseum, model='sphere',
            scale=(COLOSSEUM_RADIUS * 2.0, 2.2, COLOSSEUM_RADIUS * 2.0),
            y=-1.0, color=rgb(220, 230, 246)
        )
        Entity(
            parent=colosseum, model='diamond',
            scale=(COLOSSEUM_RADIUS * 2.04, 0.35, COLOSSEUM_RADIUS * 2.04),
            y=-0.02, color=rgb(70, 205, 255), unlit=True
        )
        # Центральное рунное кольцо дуэли
        Entity(
            parent=colosseum, model='diamond',
            scale=(24.0, 0.12, 24.0),
            y=0.04, color=rgb(55, 165, 245), unlit=True
        )

        # 16 гигантских внешних пилонов по периметру Колизея
        for i in range(16):
            ang = (i / 16.0) * math.pi * 2
            cx = math.cos(ang) * (COLOSSEUM_RADIUS - 2.0)
            cz = math.sin(ang) * (COLOSSEUM_RADIUS - 2.0)
            Entity(
                parent=colosseum, model='cube',
                scale=(2.6, 15.0, 2.6), position=(cx, 7.5, cz),
                color=rgb(50, 62, 86)
            )
            Entity(
                parent=colosseum, model='diamond',
                scale=(1.8, 3.2, 1.8), position=(cx, 16.5, cz),
                color=rgb(80, 225, 255), unlit=True
            )
            obstacles_list.append((cx, cz, 1.6, COLOSSEUM_Y + 15.0, COLOSSEUM_Y))

        # 4 внутренние массивные колонны-укрытия на радиусе 22м (чтобы прятаться от залпов Митрикса)
        for c_ang in (45, 135, 225, 315):
            rad = math.radians(c_ang)
            ix, iz = math.cos(rad) * 22.0, math.sin(rad) * 22.0
            Entity(
                parent=colosseum, model='cube',
                scale=(3.4, 11.0, 3.4), position=(ix, 5.5, iz),
                color=rgb(60, 75, 102)
            )
            Entity(
                parent=colosseum, model='cube',
                scale=(3.6, 0.4, 3.6), position=(ix, 2.2, iz),
                color=rgb(75, 215, 255), unlit=True
            )
            obstacles_list.append((ix, iz, 2.1, COLOSSEUM_Y + 11.0, COLOSSEUM_Y))

        entities_list.append(colosseum)
        sky_platforms.append((0.0, 0.0, COLOSSEUM_RADIUS + 1.0, COLOSSEUM_Y))

        # Внутренние паркур-платформы и трамплины на самой арене Митрикса (для ухода от ударных волн и «Пиццы»)
        for i in range(4):
            ang1 = math.radians(i * 90)
            p1x, p1z = math.cos(ang1) * 33.0, math.sin(ang1) * 33.0
            _spawn_parkour_disc(
                entities_list, sky_platforms,
                (p1x, COLOSSEUM_Y + 3.2, p1z), radius=5.2, thickness=0.9,
                col=rgb(190, 205, 230), accent=color.cyan
            )
            # Второй ярус паркур-платформ в Колизее (Y = 126.5)
            ang2 = math.radians(i * 90 + 28)
            p2x, p2z = math.cos(ang2) * 36.0, math.sin(ang2) * 36.0
            _spawn_parkour_disc(
                entities_list, sky_platforms,
                (p2x, COLOSSEUM_Y + 6.5, p2z), radius=4.5, thickness=0.9,
                col=rgb(175, 195, 225), accent=rgb(120, 240, 255)
            )
            # Прыжковый трамплин на арене Колизея
            ang_pad = math.radians(i * 90 + 45)
            pad_x, pad_z = math.cos(ang_pad) * 38.0, math.sin(ang_pad) * 38.0
            entities_list.append(LunarBouncePad(Vec3(pad_x, COLOSSEUM_Y, pad_z), jump_vel=19.0, boost_forward=0.0))

        if ctx.game is not None:
            ctx.game.sky_platforms = sky_platforms

        random.seed()
        return entities_list, obstacles_list, jump_pad, palette['name']

    # ==========================================================
    # РЕЖИМ 3: ОБЫЧНЫЕ ЭТАПЫ PETRICHOR V
    # ==========================================================
    if ctx.game is not None:
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