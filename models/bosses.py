from ursina import *
import math
from config import rgb


def build_boss_mesh(parent_entity, enemy_type):
    root = Entity(parent=parent_entity)
    parts = {'root': root}

    if enemy_type == 'boss':
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

    elif enemy_type == 'lunar_chimera':
        # Лунная Химера — парящее кольцо-конструкт из белого мрамора и синей плазмы
        marble = rgb(225, 235, 248)
        slate = rgb(45, 58, 82)
        cyan_glow = rgb(70, 225, 255)

        core = Entity(parent=root, position=(0, 2.5, 0))
        Entity(parent=core, model='sphere', scale=0.95, color=cyan_glow, unlit=True)
        Entity(parent=core, model='diamond', scale=(1.6, 0.5, 2.2), color=marble)
        ring1 = Entity(parent=core, model='diamond', scale=(2.6, 0.22, 2.6), color=slate)
        ring2 = Entity(parent=core, model='diamond', scale=(0.22, 2.6, 2.6), color=cyan_glow, unlit=True)
        for side in (-1, 1):
            wing = Entity(parent=core, model='cube', scale=(1.2, 0.18, 0.65), position=(side * 1.4, 0, -0.2), rotation_z=side * 15, color=marble)
            Entity(parent=wing, model='cube', scale=(0.9, 0.08, 0.8), z=0.4, color=cyan_glow, unlit=True)
        parts['core'] = core
        parts['ring1'] = ring1
        parts['ring2'] = ring2

    elif enemy_type == 'mithrix':
        # ==========================================================
        # МИТРИКС, КОРОЛЬ НИЧЕГО (MITHRIX, KING OF NOTHING)
        # ==========================================================
        lunar_white = rgb(230, 238, 250)
        lunar_silver = rgb(165, 182, 208)
        obsidian = rgb(32, 38, 54)
        cobalt = rgb(40, 95, 205)
        cyan_fire = rgb(75, 235, 255)

        # 1. СОСТАВНЫЕ НОГИ С НАКОЛЕННИКАМИ И ПОНОЖАМИ
        l_leg = Entity(parent=root, position=(-0.55, 1.95, 0))
        r_leg = Entity(parent=root, position=(0.55, 1.95, 0))
        for side, leg in ((-1, l_leg), (1, r_leg)):
            # Бедро и боковая бронепластина (тассет)
            Entity(parent=leg, model='cube', scale=(0.46, 0.95, 0.48), y=-0.45, color=obsidian)
            Entity(parent=leg, model='diamond', scale=(0.22, 0.85, 0.62), position=(side * 0.28, -0.35, 0), rotation_z=side * -12, color=lunar_white)
            # Светящийся наколенник
            Entity(parent=leg, model='diamond', scale=(0.54, 0.45, 0.58), position=(0, -0.95, 0.14), color=lunar_white)
            Entity(parent=leg, model='diamond', scale=(0.24, 0.32, 0.62), position=(0, -0.95, 0.18), color=cyan_fire, unlit=True)
            # Голень и сабатон
            Entity(parent=leg, model='cube', scale=(0.40, 0.92, 0.44), y=-1.40, color=lunar_silver)
            Entity(parent=leg, model='diamond', scale=(0.52, 0.32, 0.85), position=(0, -1.85, 0.16), color=lunar_white)
        parts['left_leg'] = l_leg
        parts['right_leg'] = r_leg

        # 2. АТЛЕТИЧНЫЙ ТОРС, ПОЯС И ЛУННОЕ ЯДРО
        torso = Entity(parent=root, position=(0, 2.85, 0))
        # Талия и пояс с кобальтовой тканью
        Entity(parent=torso, model='cube', scale=(1.05, 0.55, 0.68), y=-0.65, color=obsidian)
        Entity(parent=torso, model='diamond', scale=(1.25, 0.32, 0.78), y=-0.45, color=cobalt)
        Entity(parent=torso, model='diamond', scale=(0.42, 1.25, 0.16), position=(0, -1.15, 0.36), color=cobalt)

        # Грудная клетка из белого лунного сплава
        Entity(parent=torso, model='diamond', scale=(1.75, 1.55, 1.05), y=0.20, color=lunar_white)
        Entity(parent=torso, model='cube', scale=(1.25, 1.10, 0.82), y=0.15, color=obsidian)
        # V-образные нагрудные пластины
        Entity(parent=torso, model='cube', scale=(0.55, 1.15, 0.92), position=(-0.32, 0.22, 0.05), rotation_z=18, color=lunar_white)
        Entity(parent=torso, model='cube', scale=(0.55, 1.15, 0.92), position=(0.32, 0.22, 0.05), rotation_z=-18, color=lunar_white)
        # Центральное ядро Митрикса
        core = Entity(parent=torso, model='diamond', scale=(0.48, 0.78, 0.45), position=(0, 0.25, 0.42), color=cyan_fire, unlit=True)
        parts['core'] = core
        parts['torso'] = torso

        # 3. РАЗВЕВАЮЩИЙСЯ КОРОЛЕВСКИЙ ПЛАЩ (CAPE)
        cape = Entity(parent=torso, position=(-0.25, 0.75, -0.45), rotation_x=14)
        Entity(parent=cape, model='cube', scale=(1.45, 0.28, 0.35), color=cobalt)
        Entity(parent=cape, model='diamond', scale=(1.65, 2.65, 0.18), position=(0, -1.35, -0.15), color=cobalt)
        Entity(parent=cape, model='diamond', scale=(0.85, 2.45, 0.20), position=(0, -1.35, -0.17), color=cyan_fire, unlit=True)
        parts['cape'] = cape

        # 4. ШЛЕМ-КОРОНА МИТРИКСА (CRESTED CYCLOPS CROWN)
        head = Entity(parent=torso, position=(0, 1.18, 0.05))
        Entity(parent=head, model='sphere', scale=(0.68, 0.78, 0.72), color=lunar_white)
        # Лицевая панель с вертикальным светящимся разрезом и глазом-циклопом
        Entity(parent=head, model='diamond', scale=(0.58, 0.75, 0.55), position=(0, 0.02, 0.18), color=obsidian)
        Entity(parent=head, model='cube', scale=(0.10, 0.62, 0.35), position=(0, 0.06, 0.30), color=cyan_fire, unlit=True)
        eye = Entity(parent=head, model='sphere', scale=(0.24, 0.24, 0.28), position=(0, 0.08, 0.38), color=color.white, unlit=True)
        parts['eye'] = eye

        # Двойные восходящие рога-гребни короны (Tuning-Fork Crown)
        for side in (-1, 1):
            crest = Entity(parent=head, position=(side * 0.22, 0.38, -0.02), rotation_z=side * -14)
            Entity(parent=crest, model='diamond', scale=(0.18, 1.15, 0.42), y=0.45, color=lunar_white)
            Entity(parent=crest, model='diamond', scale=(0.12, 0.95, 0.22), position=(side * -0.05, 0.52, 0.08), color=cyan_fire, unlit=True)
        # Задний нимб короны
        crown = Entity(parent=head, model='diamond', scale=(1.35, 1.35, 0.12), position=(0, 0.35, -0.32), color=cyan_fire, unlit=True)
        parts['crown'] = crown

        # 5. АСИММЕТРИЧНЫЕ ПЛЕЧИ И РУКИ
        l_arm = Entity(parent=torso, position=(-1.05, 0.62, 0))
        # Массивный трёхслойный лунный наплечник на левом плече
        Entity(parent=l_arm, model='diamond', scale=(0.95, 0.65, 0.95), position=(-0.15, 0.28, 0), rotation_z=25, color=lunar_white)
        Entity(parent=l_arm, model='diamond', scale=(0.75, 0.95, 0.55), position=(-0.32, 0.55, 0), rotation_z=35, color=cyan_fire, unlit=True)
        Entity(parent=l_arm, model='cube', scale=(0.38, 1.35, 0.38), y=-0.55, color=obsidian)
        Entity(parent=l_arm, model='cube', scale=(0.44, 0.65, 0.44), y=-1.15, color=lunar_white)
        parts['left_arm'] = l_arm

        r_arm = Entity(parent=torso, position=(1.05, 0.62, 0))
        Entity(parent=r_arm, model='diamond', scale=(0.72, 0.55, 0.72), y=0.20, color=lunar_silver)
        Entity(parent=r_arm, model='cube', scale=(0.40, 1.35, 0.40), y=-0.55, color=obsidian)
        Entity(parent=r_arm, model='cube', scale=(0.46, 0.65, 0.46), y=-1.15, color=lunar_white)
        parts['right_arm'] = r_arm

        # 6. КОЛОССАЛЬНЫЙ ЛУННЫЙ МОЛОТ (LUNAR HAMMER) В ПРАВОЙ РУКЕ
        hammer = Entity(parent=r_arm, position=(0, -1.25, 0.35), rotation_x=65)
        # Рукоять молота длиной 4.6м с рунными кольцами
        Entity(parent=hammer, model='cube', scale=(0.18, 4.6, 0.18), y=1.4, color=obsidian)
        for ry in (0.2, 1.2, 2.2, 3.0):
            Entity(parent=hammer, model='cube', scale=(0.24, 0.12, 0.24), y=ry, color=cyan_fire, unlit=True)
        # Навершие рукояти
        Entity(parent=hammer, model='diamond', scale=(0.42, 0.55, 0.42), y=-0.95, color=lunar_white)

        # Гигантский ударный блок молота
        head_block = Entity(parent=hammer, position=(0, 3.65, 0))
        Entity(parent=head_block, model='cube', scale=(1.35, 0.95, 2.45), color=obsidian)
        Entity(parent=head_block, model='cube', scale=(1.42, 0.65, 1.85), color=lunar_white)
        # Ударные бойки спереди и сзади
        Entity(parent=head_block, model='diamond', scale=(1.25, 0.85, 0.95), z=1.35, color=lunar_white)
        Entity(parent=head_block, model='diamond', scale=(0.95, 0.75, 1.15), z=-1.35, color=lunar_silver)
        # Светящиеся рунные полосы и реактивная аура молота
        hammer_aura = Entity(parent=head_block, model='cube', scale=(1.48, 0.28, 2.55), color=cyan_fire, unlit=True)
        Entity(parent=head_block, model='diamond', scale=(1.75, 0.18, 1.75), color=cyan_fire, unlit=True)

        parts['hammer'] = hammer
        parts['hammer_aura'] = hammer_aura

        # Аура 3-й и 4-й фазы вокруг торса
        phase_ring = Entity(
            parent=torso, model='diamond', scale=(3.6, 0.15, 3.6),
            y=-0.2, color=cyan_fire, unlit=True, enabled=False
        )
        parts['phase_ring'] = phase_ring

    return parts