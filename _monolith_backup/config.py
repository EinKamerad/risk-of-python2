from ursina import *
from types import SimpleNamespace
import json
import os

ctx = SimpleNamespace(game=None)

def rgb(r, g, b, a=255):
    """Перевод цвета 0-255 в диапазон 0.0-1.0 для всех версий Ursina"""
    return Color(r / 255.0, g / 255.0, b / 255.0, a / 255.0)

def is_valid(entity):
    """Безопасная проверка, что сущность жива и её C++ узел не удалён"""
    return (
        entity is not None
        and not getattr(entity, 'is_dead', False)
        and not getattr(entity, 'is_destroyed', False)
        and not entity.is_empty()
        and entity.enabled
    )

def clear_children(entity):
    """Безопасно очищает дочерние 3D-узлы (для превью в лобби и журнале)"""
    if not entity or entity.is_empty():
        return
    for ch in list(entity.children):
        if ch and not ch.is_empty():
            destroy(ch)

# Настройки игры по умолчанию
SETTINGS = {
    'fov': 90,
    'sensitivity': 45,
    'fog_density': 0.006,
    'fullscreen': False,
    'coop_bot': True
}

# ==========================================
# БАЗА ИЗ 37 ПРЕДМЕТОВ (7 БАЗОВЫХ + 30 НОВЫХ)
# ==========================================
ITEM_POOL = {
    'syringe': {
        'name': "Soldier's Syringe", 'short': 'SYR',
        'desc': '+15% скорости атаки',
        'color': rgb(255, 225, 60), 'default_unlocked': True
    },
    'hoof': {
        'name': "Paul's Goat Hoof", 'short': 'HOOF',
        'desc': '+14% скорости бега',
        'color': rgb(70, 235, 255), 'default_unlocked': True
    },
    'bear': {
        'name': 'Tougher Times', 'short': 'BEAR',
        'desc': '+15% шанс блока урона',
        'color': rgb(255, 150, 50), 'default_unlocked': True
    },
    'ukulele': {
        'name': 'Ukulele', 'short': 'UKU',
        'desc': '25% шанс цепной молнии',
        'color': rgb(235, 80, 255), 'default_unlocked': True
    },
    'gasoline': {
        'name': 'Gasoline', 'short': 'GAS',
        'desc': 'Взрыв врагов при смерти (AoE)',
        'color': rgb(255, 65, 65), 'default_unlocked': True
    },
    'lens': {
        'name': "Lens-Maker's Glasses", 'short': 'CRIT',
        'desc': '+10% шанс критического урона (x2)',
        'color': rgb(255, 45, 85), 'default_unlocked': True
    },
    'feather': {
        'name': 'Hopoo Feather', 'short': 'JMP',
        'desc': '+1 прыжок в воздухе',
        'color': rgb(110, 255, 140), 'default_unlocked': True
    },
    'crowbar': {
        'name': 'Crowbar', 'short': 'CROW',
        'desc': '+50% урона врагам с >85% HP',
        'color': rgb(210, 220, 235), 'default_unlocked': True
    },
    'tri_tip': {
        'name': 'Tri-Tip Dagger', 'short': 'BLEED',
        'desc': '+15% шанс вызвать кровотечение',
        'color': rgb(225, 35, 55), 'default_unlocked': True
    },
    'ap_rounds': {
        'name': 'Armor-Piercing Rounds', 'short': 'APR',
        'desc': '+20% урона по Боссам',
        'color': rgb(255, 185, 80), 'default_unlocked': True
    },
    'backup_mag': {
        'name': 'Backup Magazine', 'short': 'MAG',
        'desc': '-12% перезарядки навыка ПКМ (M2)',
        'color': rgb(180, 200, 230), 'default_unlocked': True
    },
    'energy_drink': {
        'name': 'Energy Drink', 'short': 'NRG',
        'desc': '+20% скорости рывка и +8% бега',
        'color': rgb(50, 205, 255), 'default_unlocked': True
    },
    'bison_steak': {
        'name': 'Bison Steak', 'short': 'STEAK',
        'desc': '+25 к максимальному HP',
        'color': rgb(215, 75, 65), 'default_unlocked': True
    },
    'monster_tooth': {
        'name': 'Monster Tooth', 'short': 'TOOTH',
        'desc': 'Лечит +8 HP при убийстве врага',
        'color': rgb(120, 255, 130), 'default_unlocked': True
    },
    'medkit': {
        'name': 'Medkit', 'short': 'MED',
        'desc': 'Лечит +15 HP после получения урона',
        'color': rgb(90, 245, 145), 'default_unlocked': True
    },
    'repulsion_armor': {
        'name': 'Repulsion Armor Plate', 'short': 'PLATE',
        'desc': 'Снижает входящий урон на 4 ед.',
        'color': rgb(155, 175, 205), 'default_unlocked': True
    },
    'topaz_brooch': {
        'name': 'Topaz Brooch', 'short': 'TOPAZ',
        'desc': '+15 временного щита при убийстве',
        'color': rgb(255, 195, 45), 'default_unlocked': True
    },
    'opal': {
        'name': 'Oddly-shaped Opal', 'short': 'OPAL',
        'desc': 'Снижает редкий урон на 30%',
        'color': rgb(175, 135, 255), 'default_unlocked': True
    },
    'focus_crystal': {
        'name': 'Focus Crystal', 'short': 'FOCUS',
        'desc': '+20% урона врагам вблизи (<13м)',
        'color': rgb(255, 70, 145), 'default_unlocked': True
    },
    'sticky_bomb': {
        'name': 'Sticky Bomb', 'short': 'BOMB',
        'desc': '12% шанс прикрепить взрывчатку',
        'color': rgb(255, 125, 40), 'default_unlocked': True
    },
    'stun_grenade': {
        'name': 'Stun Grenade', 'short': 'STUN',
        'desc': '10% шанс оглушить врага на 1.5с',
        'color': rgb(210, 240, 255), 'default_unlocked': True
    },
    'bundle_fireworks': {
        'name': 'Bundle of Fireworks', 'short': 'FIREW',
        'desc': 'Салют ракетами при открытии сундука',
        'color': rgb(255, 95, 205), 'default_unlocked': True
    },
    'atg_missile': {
        'name': 'AtG Missile Mk. 1', 'short': 'ATG',
        'desc': '12% шанс выпустить ракету (250% ур.)',
        'color': rgb(115, 235, 75), 'default_unlocked': True
    },
    'will_o_wisp': {
        'name': "Will-o'-the-wisp", 'short': 'WISP',
        'desc': 'Мощный взрыв лавы при убийстве врага',
        'color': rgb(255, 100, 35), 'default_unlocked': True
    },
    'harvester_scythe': {
        'name': "Harvester's Scythe", 'short': 'SCYTH',
        'desc': '+5% крита и +6 HP при крит. ударе',
        'color': rgb(85, 245, 175), 'default_unlocked': True
    },
    'predatory': {
        'name': 'Predatory Instincts', 'short': 'PRED',
        'desc': 'Криты ускоряют атаку на +12% (3с)',
        'color': rgb(245, 110, 85), 'default_unlocked': True
    },
    'bandolier': {
        'name': 'Bandolier', 'short': 'BAND',
        'desc': 'Убийства сокращают КД всех навыков',
        'color': rgb(225, 190, 95), 'default_unlocked': True
    },
    'kjaro_band': {
        'name': "Kjaro's Band", 'short': 'KJARO',
        'desc': 'Сильные удары создают огненный вихрь',
        'color': rgb(255, 115, 30), 'default_unlocked': True
    },
    'runald_band': {
        'name': "Runald's Band", 'short': 'RNALD',
        'desc': 'Сильные удары замораживают цель',
        'color': rgb(85, 225, 255), 'default_unlocked': True
    },
    'wax_quill': {
        'name': 'Wax Quill', 'short': 'QUILL',
        'desc': 'Прыжок совершает рывок вперёд',
        'color': rgb(255, 215, 120), 'default_unlocked': True
    },
    'rose_buckler': {
        'name': 'Rose Buckler', 'short': 'BUCKL',
        'desc': '-15% урона во время движения',
        'color': rgb(245, 125, 175), 'default_unlocked': True
    },
    'leeching_seed': {
        'name': 'Leeching Seed', 'short': 'SEED',
        'desc': 'Попадания лечат на +1.5 HP',
        'color': rgb(145, 255, 95), 'default_unlocked': True
    },
    'infusion': {
        'name': 'Infusion', 'short': 'INFUS',
        'desc': 'Убийства увеличивают макс. HP (+1)',
        'color': rgb(235, 45, 70), 'default_unlocked': True
    },
    'red_whip': {
        'name': 'Red Whip', 'short': 'WHIP',
        'desc': '+12% к базовой скорости бега',
        'color': rgb(245, 75, 65), 'default_unlocked': True
    },
    'chronobauble': {
        'name': 'Chronobauble', 'short': 'CHRON',
        'desc': 'Атаки замедляют врагов на 35%',
        'color': rgb(195, 120, 255), 'default_unlocked': True
    },
    'behemoth': {
        'name': 'Brilliant Behemoth', 'short': 'BEHEM',
        'desc': 'Все атаки взрываются (+2.5м AoE, +35% ур.)',
        'color': rgb(255, 60, 40), 'default_unlocked': True
    },
    'clover': {
        'name': '57 Leaf Clover', 'short': 'CLOVR',
        'desc': 'Удача: +7% крита и +10% ко всем шансам',
        'color': rgb(75, 255, 135), 'default_unlocked': True
    }
}

# База достижений (Ачивок)
ACHIEVEMENTS = {
    'ach_slayer': {
        'name': 'Истребитель (Slayer)',
        'desc': 'Уничтожьте 12 монстров за всё время.',
        'unlocks_item': 'lens',
        'reward_text': "Открывает: Lens-Maker's Glasses (Крит x2)"
    },
    'ach_boss': {
        'name': 'Убийца Титанов (Titanfall)',
        'desc': 'Победите Босса Телепорта.',
        'unlocks_item': 'feather',
        'reward_text': 'Открывает: Hopoo Feather (+Прыжок в воздухе)'
    },
    'ach_traveler': {
        'name': 'Исследователь миров',
        'desc': 'Перейдите на 2-й этап через Телепорт.',
        'unlocks_item': None,
        'reward_text': 'Почётная запись в Журнале выжившего'
    },
    'ach_hoarder': {
        'name': 'Коллекционер артефактов',
        'desc': 'Соберите 6 предметов за один забег.',
        'unlocks_item': None,
        'reward_text': 'Почётная запись в Журнале выжившего'
    }
}

# Типы боссов и стоимость спавна врагов для ИИ-Режиссёра
BOSS_TYPES = ['boss', 'vagrant', 'overlord']

BOSS_TITLES = {
    'boss': 'STONE TITAN :: PRIMORDIAL GUARDIAN',
    'vagrant': 'WANDERING VAGRANT :: GENTLE PROTECTOR',
    'overlord': 'IMP OVERLORD :: LORD OF THE RED PLANE'
}

# База монстров (7 обычных врагов и 3 босса)
MONSTER_LOG = {
    'lemurian': {
        'name': 'Lemurian (Лемуриец)', 'hp': 36, 'damage': 9,
        'desc': 'Быстрый двуногий ящер ближнего боя. Охотится стаями и атакует когтями.'
    },
    'wisp': {
        'name': 'Lesser Wisp (Малый Огонёк)', 'hp': 26, 'damage': 11.5,
        'desc': 'Парящий дух огня в древней железной маске. Атакует сгустками плазмы издалека.'
    },
    'beetle': {
        'name': 'Beetle (Рабочий Жук)', 'hp': 28, 'damage': 7.5,
        'desc': 'Стремительное панцирное насекомое. Таранным рывком сбивает выживших с ног.'
    },
    'jellyfish': {
        'name': 'Jellyfish (Блуждающая Медуза)', 'hp': 24, 'damage': 14.0,
        'desc': 'Парящее биолюминесцентное создание, взрывающееся электрическим импульсом вблизи.'
    },
    'golem': {
        'name': 'Stone Golem (Каменный Голем)', 'hp': 95, 'damage': 18.0,
        'desc': 'Тяжёлый страж руин. Фокусирует смертоносный лазерный луч на цели.'
    },
    'imp': {
        'name': 'Imp (Бес Пустоты)', 'hp': 52, 'damage': 13.5,
        'desc': 'Порождение Красной Плоскости. Мгновенно телепортируется за спину жертвы.'
    },
    'greater_wisp': {
        'name': 'Greater Wisp (Большой Огонёк)', 'hp': 82, 'damage': 16.5,
        'desc': 'Древний дух изумрудного пламени. Выпускает парные взрывные черепа.'
    },
    'boss': {
        'name': 'Stone Titan (Каменный Титан)', 'hp': 450, 'damage': 22,
        'desc': 'Колоссальный страж Телепорта. Выпускает веерные лазерные залпы из рунного ядра.'
    },
    'vagrant': {
        'name': 'Wandering Vagrant (Блуждающий Бродяга)', 'hp': 480, 'damage': 20,
        'desc': 'Гигантская небесная медуза. Обстреливает арену самонаводящимися сферами и сверхновой.'
    },
    'overlord': {
        'name': 'Imp Overlord (Повелитель Бесов)', 'hp': 520, 'damage': 24,
        'desc': 'Владыка демонов Пустоты. Совершает сокрушительные телепорт-прыжки и мечет шипы.'
    }
}

# 7 Классов выживших с 4 способностями у каждого
SURVIVOR_CLASSES = {
    'commando': {
        'name': 'COMMANDO',
        'icon': 'CMD',
        'subtitle': 'Универсальный боец UES',
        'hp': 115,
        'speed': 9.6,
        'damage': 12.0,
        'fire_rate': 6.5,
        'proj_speed': 62.0,
        'proj_scale': 0.22,
        'aoe': 0.0,
        'body_color': rgb(235, 130, 35),
        'armor_color': rgb(70, 78, 95),
        'visor_color': rgb(60, 245, 255),
        'skills': {
            'm1': {'name': 'Double Tap', 'cd': 0.15, 'desc': '[ЛКМ] Скорострельная стрельба из двух пистолетов.'},
            'm2': {'name': 'Phase Round', 'cd': 3.2, 'desc': '[ПКМ] Мощный плазменный заряд (300% урона), прошивающий врагов насквозь.'},
            'shift': {'name': 'Tactical Dive', 'cd': 4.0, 'desc': '[Shift] Стремительный тактический рывок вперёд.'},
            'r': {'name': 'Suppressive Fire', 'cd': 8.0, 'desc': '[R] Шквальная очередь из 8 выстрелов повышенной точности.'}
        }
    },
    'artificer': {
        'name': 'ARTIFICER',
        'subtitle': 'Высокотехнологичный Архимаг',
        'icon': 'ART',
        'hp': 100,
        'speed': 8.5,
        'damage': 34.0,
        'fire_rate': 1.9,
        'proj_speed': 36.0,
        'proj_scale': 0.52,
        'aoe': 4.2,
        'body_color': rgb(155, 55, 230),
        'armor_color': rgb(225, 195, 105),
        'visor_color': rgb(255, 235, 65),
        'skills': {
            'm1': {'name': 'Plasma Bolt', 'cd': 0.52, 'desc': '[ЛКМ] Взрывные плазменные сферы, наносящие урон по площади.'},
            'm2': {'name': 'Charged Nano-Bomb', 'cd': 5.0, 'desc': '[ПКМ] Сверхтяжёлая грави-сфера (280% урона в огромном радиусе).'},
            'shift': {'name': 'Snapfreeze Surge', 'cd': 4.5, 'desc': '[Shift] Реактивный взлёт вверх с ледяным взрывом под ногами.'},
            'r': {'name': 'Orbital Ion Strike', 'cd': 10.0, 'desc': '[R] Обрушивает 5 орбитальных ионных лучей на ближайших врагов.'}
        }
    },
    'huntress': {
        'name': 'HUNTRESS',
        'subtitle': 'Стремительный Снайпер',
        'icon': 'HNT',
        'hp': 95,
        'speed': 10.8,
        'damage': 18.0,
        'fire_rate': 3.4,
        'proj_speed': 54.0,
        'proj_scale': 0.28,
        'aoe': 0.0,
        'body_color': rgb(215, 45, 70),
        'armor_color': rgb(45, 50, 64),
        'visor_color': rgb(255, 240, 90),
        'skills': {
            'm1': {'name': 'Strafe Bow', 'cd': 0.29, 'desc': '[ЛКМ] Выпускает энергетические стрелы с автонаведением.'},
            'm2': {'name': 'Laser Glaive', 'cd': 5.5, 'desc': '[ПКМ] Бросает лазерную глефу, рикошетящую до 5 раз между врагами!'},
            'shift': {'name': 'Phase Blink', 'cd': 3.5, 'desc': '[Shift] Мгновенная телепортация в направлении взгляда.'},
            'r': {'name': 'Arrow Rain', 'cd': 9.5, 'desc': '[R] Прыжок в небо и обстрел зоны градом энергетических стрел.'}
        }
    },
    'buzz': {
        'name': 'BUZZ LIGHTYEAR',
        'subtitle': 'Космический Рейнджер Star Command',
        'icon': 'BUZ',
        'hp': 135,
        'speed': 9.8,
        'damage': 16.0,
        'fire_rate': 4.8,
        'proj_speed': 66.0,
        'proj_scale': 0.25,
        'aoe': 1.2,
        'body_color': rgb(125, 235, 65),
        'armor_color': rgb(240, 245, 250),
        'visor_color': rgb(155, 65, 245),
        'skills': {
            'm1': {'name': 'Wrist Laser', 'cd': 0.21, 'desc': '[ЛКМ] Скорострельный наручный лазер Звёздного Командования.'},
            'm2': {'name': 'Hyper-Beam', 'cd': 4.0, 'desc': '[ПКМ] Пробивной луч полной мощности с взрывным импульсом.'},
            'shift': {'name': 'To Infinity & Beyond!', 'cd': 4.5, 'desc': '[Shift] Раскрывает крылья и взмывает в воздух на реактивном ранце.'},
            'r': {'name': 'Star Command Salvo', 'cd': 9.0, 'desc': '[R] Залп из 6 самонаводящихся фотонных ракет по врагам.'}
        }
    },
    'v1': {
        'name': 'V1 (ULTRAKILL)',
        'subtitle': 'MANKIND IS DEAD. BLOOD IS FUEL.',
        'icon': 'V1',
        'hp': 95,
        'speed': 12.2,
        'damage': 19.0,
        'fire_rate': 5.2,
        'proj_speed': 78.0,
        'proj_scale': 0.22,
        'aoe': 0.0,
        'body_color': rgb(45, 115, 235),
        'armor_color': rgb(32, 38, 52),
        'visor_color': rgb(255, 225, 40),
        'skills': {
            'm1': {'name': 'Piercer Revolver', 'cd': 0.19, 'desc': '[ЛКМ] Высокоточные выстрелы из револьвера.'},
            'm2': {'name': 'Marksman Ricoshot', 'cd': 4.2, 'desc': '[ПКМ] Бросок монеты: рикошет по 4 врагам + лечение кровью!'},
            'shift': {'name': 'Slam Dash', 'cd': 3.0, 'desc': '[Shift] Сверхзвуковой рывок сквозь врагов с выкачиванием HP.'},
            'r': {'name': 'Electric Railcannon', 'cd': 8.5, 'desc': '[R] Разряд рельсотрона, поражающий всех врагов цепной молнией.'}
        }
    },
    'sol': {
        'name': 'SOL BADGUY',
        'subtitle': 'Flame of Corruption (Guilty Gear)',
        'icon': 'SOL',
        'hp': 145,
        'speed': 10.2,
        'damage': 28.0,
        'fire_rate': 2.8,
        'proj_speed': 42.0,
        'proj_scale': 0.48,
        'aoe': 3.5,
        'body_color': rgb(210, 35, 45),
        'armor_color': rgb(40, 35, 38),
        'visor_color': rgb(255, 165, 30),
        'skills': {
            'm1': {'name': 'Gun Flame', 'cd': 0.35, 'desc': '[ЛКМ] Взмах мечом Junkyard Dog, пускающий пробивную волну пламени.'},
            'm2': {'name': 'Volcanic Viper', 'cd': 4.2, 'desc': '[ПКМ] Сокрушительный огненный апперкот в прыжке с AoE-взрывом.'},
            'shift': {'name': 'Fafnir Lunge', 'cd': 3.8, 'desc': '[Shift] Стремительный пробивной удар вперёд, сжигающий врагов на пути.'},
            'r': {'name': 'DRAGON INSTALL', 'cd': 11.0, 'desc': '[R] Пробуждение силы Гира: взрыв Tyrant Rave + ускорение боя на 6 сек.'}
        }
    },
    'gwen': {
        'name': 'GWEN',
        'subtitle': 'Благая Швея (League of Legends)',
        'icon': 'GWN',
        'hp': 115,
        'speed': 10.5,
        'damage': 16.5,
        'fire_rate': 4.6,
        'proj_speed': 52.0,
        'proj_scale': 0.30,
        'aoe': 1.8,
        'body_color': rgb(65, 195, 255),
        'armor_color': rgb(32, 28, 46),
        'visor_color': rgb(195, 240, 255),
        'skills': {
            'm1': {'name': 'Snip Snip!', 'cd': 0.22, 'desc': '[ЛКМ] Быстрые разрезы ножницами, исцеляющие Гвен при попадании.'},
            'm2': {'name': 'Center Snip', 'cd': 3.8, 'desc': '[ПКМ] Мощный финальный разрез по центру (пробивает броню и врагов).'},
            'shift': {'name': 'Hallowed Mist', 'cd': 5.5, 'desc': '[Shift] Рывок и призыв Священного Тумана, лечащего Гвен и бьющего врагов.'},
            'r': {'name': 'Needlework', 'cd': 9.0, 'desc': '[R] Выпускает веер из 5 гигантских призрачных игл насквозь.'}
        }
    }
}

# Палитры локаций и космоса
STAGE_PALETTES = [
    {
        'id': 'roost',
        'name': 'Distant Roost',
        'desc': 'Туманные утёсы и руины древних храмов на краю океана Petrichor V.',
        'ground': rgb(36, 52, 66),
        'ruins': rgb(62, 78, 96),
        'accent': rgb(75, 225, 255),
        'sky': rgb(14, 22, 36),
        'nebula': rgb(45, 110, 165),
        'moon': rgb(210, 230, 255)
    },
    {
        'id': 'acres',
        'name': 'Scorched Acres',
        'desc': 'Выжженные солнцем террасы с раскалёнными обелисками и пеплом.',
        'ground': rgb(74, 46, 36),
        'ruins': rgb(102, 68, 54),
        'accent': rgb(255, 150, 45),
        'sky': rgb(34, 18, 16),
        'nebula': rgb(165, 70, 40),
        'moon': rgb(255, 200, 140)
    },
    {
        'id': 'depths',
        'name': 'Abyssal Depths',
        'desc': 'Глубокий тектонический разлом, озарённый кристаллами магмы.',
        'ground': rgb(42, 30, 62),
        'ruins': rgb(70, 52, 98),
        'accent': rgb(240, 65, 195),
        'sky': rgb(20, 12, 34),
        'nebula': rgb(135, 40, 145),
        'moon': rgb(245, 160, 255)
    },
    {
        'id': 'siren',
        'name': "Siren's Call",
        'desc': 'Кладбище разбившихся кораблей среди изумрудных скал.',
        'ground': rgb(30, 60, 56),
        'ruins': rgb(54, 90, 84),
        'accent': rgb(90, 255, 165),
        'sky': rgb(12, 28, 28),
        'nebula': rgb(40, 140, 115),
        'moon': rgb(180, 255, 220)
    }
]

# Система сохранения прогресса и Журнала
SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'save_logbook.json')

class ProgressData:
    def __init__(self):
        self.kills = 0
        self.boss_kills = 0
        self.max_stage = 1
        self.unlocked_items = [k for k, v in ITEM_POOL.items() if v['default_unlocked']]
        self.unlocked_achievements = []
        self.discovered_stages = ['roost']
        self.discovered_monsters = list(MONSTER_LOG.keys())
        self.load()

    def load(self):
        if os.path.exists(SAVE_PATH):
            try:
                with open(SAVE_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.kills = data.get('kills', 0)
                self.boss_kills = data.get('boss_kills', 0)
                self.max_stage = data.get('max_stage', 1)
                for it in data.get('unlocked_items', []):
                    if it not in self.unlocked_items:
                        self.unlocked_items.append(it)
                self.unlocked_achievements = data.get('unlocked_achievements', [])
                self.discovered_stages = data.get('discovered_stages', ['roost'])
            except Exception:
                pass

    def save(self):
        try:
            with open(SAVE_PATH, 'w', encoding='utf-8') as f:
                json.dump({
                    'kills': self.kills,
                    'boss_kills': self.boss_kills,
                    'max_stage': self.max_stage,
                    'unlocked_items': self.unlocked_items,
                    'unlocked_achievements': self.unlocked_achievements,
                    'discovered_stages': self.discovered_stages
                }, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def unlock_all(self):
        self.unlocked_items = list(ITEM_POOL.keys())
        self.unlocked_achievements = list(ACHIEVEMENTS.keys())
        self.discovered_stages = [p['id'] for p in STAGE_PALETTES]
        self.save()

PROGRESS = ProgressData()