import random
from core.utils import rgb

TIER_INFO = {
    'white': {
        'name': 'ОБЫЧНЫЙ',
        'color': rgb(235, 242, 250),
    },
    'green': {
        'name': 'НЕОБЫЧНЫЙ',
        'color': rgb(85, 235, 95),
    },
    'red': {
        'name': 'ЛЕГЕНДАРНЫЙ',
        'color': rgb(255, 55, 65),
    },
    'void': {
        'name': 'ПУСТОТА',
        'color': rgb(205, 85, 255),
    },
    'lunar': {
        'name': 'ЛУННЫЙ',
        'color': rgb(65, 185, 255),
    }
}

ITEM_POOL = {
    # ==========================================
    # ОБЫЧНЫЕ ПРЕДМЕТЫ (WHITE / COMMON)
    # ==========================================
    'syringe': {
        'name': "Soldier's Syringe", 'short': 'SYR', 'tier': 'white',
        'desc': '+15% скорости атаки',
        'mesh_color': rgb(255, 225, 60), 'default_unlocked': True
    },
    'hoof': {
        'name': "Paul's Goat Hoof", 'short': 'HOOF', 'tier': 'white',
        'desc': '+14% скорости бега',
        'mesh_color': rgb(70, 235, 255), 'default_unlocked': True
    },
    'bear': {
        'name': 'Tougher Times', 'short': 'BEAR', 'tier': 'white',
        'desc': '+15% шанс блока урона',
        'mesh_color': rgb(255, 150, 50), 'default_unlocked': True
    },
    'gasoline': {
        'name': 'Gasoline', 'short': 'GAS', 'tier': 'white',
        'desc': 'Взрыв врагов при смерти (AoE)',
        'mesh_color': rgb(255, 65, 65), 'default_unlocked': True
    },
    'lens': {
        'name': "Lens-Maker's Glasses", 'short': 'CRIT', 'tier': 'white',
        'desc': '+10% шанс критического урона (x2)',
        'mesh_color': rgb(255, 45, 85), 'default_unlocked': True
    },
    'crowbar': {
        'name': 'Crowbar', 'short': 'CROW', 'tier': 'white',
        'desc': '+50% урона врагам с >85% HP',
        'mesh_color': rgb(210, 220, 235), 'default_unlocked': True
    },
    'tri_tip': {
        'name': 'Tri-Tip Dagger', 'short': 'BLEED', 'tier': 'white',
        'desc': '+15% шанс вызвать кровотечение',
        'mesh_color': rgb(225, 35, 55), 'default_unlocked': True
    },
    'ap_rounds': {
        'name': 'Armor-Piercing Rounds', 'short': 'APR', 'tier': 'white',
        'desc': '+20% урона по Боссам',
        'mesh_color': rgb(255, 185, 80), 'default_unlocked': True
    },
    'backup_mag': {
        'name': 'Backup Magazine', 'short': 'MAG', 'tier': 'white',
        'desc': '-12% перезарядки навыка ПКМ (M2)',
        'mesh_color': rgb(180, 200, 230), 'default_unlocked': True
    },
    'energy_drink': {
        'name': 'Energy Drink', 'short': 'NRG', 'tier': 'white',
        'desc': '+20% скорости рывка и +8% бега',
        'mesh_color': rgb(50, 205, 255), 'default_unlocked': True
    },
    'bison_steak': {
        'name': 'Bison Steak', 'short': 'STEAK', 'tier': 'white',
        'desc': '+25 к максимальному HP',
        'mesh_color': rgb(215, 75, 65), 'default_unlocked': True
    },
    'monster_tooth': {
        'name': 'Monster Tooth', 'short': 'TOOTH', 'tier': 'white',
        'desc': 'Лечит +8 HP при убийстве врага',
        'mesh_color': rgb(120, 255, 130), 'default_unlocked': True
    },
    'medkit': {
        'name': 'Medkit', 'short': 'MED', 'tier': 'white',
        'desc': 'Лечит +15 HP после получения урона',
        'mesh_color': rgb(90, 245, 145), 'default_unlocked': True
    },
    'repulsion_armor': {
        'name': 'Repulsion Armor Plate', 'short': 'PLATE', 'tier': 'white',
        'desc': 'Снижает входящий урон на 4 ед.',
        'mesh_color': rgb(155, 175, 205), 'default_unlocked': True
    },
    'topaz_brooch': {
        'name': 'Topaz Brooch', 'short': 'TOPAZ', 'tier': 'white',
        'desc': '+15 временного щита при убийстве',
        'mesh_color': rgb(255, 195, 45), 'default_unlocked': True
    },
    'opal': {
        'name': 'Oddly-shaped Opal', 'short': 'OPAL', 'tier': 'white',
        'desc': 'Снижает редкий урон на 30%',
        'mesh_color': rgb(175, 135, 255), 'default_unlocked': True
    },
    'focus_crystal': {
        'name': 'Focus Crystal', 'short': 'FOCUS', 'tier': 'white',
        'desc': '+20% урона врагам вблизи (<13м)',
        'mesh_color': rgb(255, 70, 145), 'default_unlocked': True
    },
    'sticky_bomb': {
        'name': 'Sticky Bomb', 'short': 'BOMB', 'tier': 'white',
        'desc': '12% шанс прикрепить взрывчатку',
        'mesh_color': rgb(255, 125, 40), 'default_unlocked': True
    },
    'stun_grenade': {
        'name': 'Stun Grenade', 'short': 'STUN', 'tier': 'white',
        'desc': '10% шанс оглушить врага на 1.5с',
        'mesh_color': rgb(210, 240, 255), 'default_unlocked': True
    },
    'bundle_fireworks': {
        'name': 'Bundle of Fireworks', 'short': 'FIREW', 'tier': 'white',
        'desc': 'Салют ракетами при открытии сундука',
        'mesh_color': rgb(255, 95, 205), 'default_unlocked': True
    },
    'bungus': {
        'name': 'Bustling Fungus', 'short': 'BUNG', 'tier': 'white',
        'desc': 'Стоя на месте >1.2с, создаёт зону лечения (4.5% HP/с вам и союзникам)',
        'mesh_color': rgb(95, 255, 125), 'default_unlocked': True
    },

    # ==========================================
    # НЕОБЫЧНЫЕ ПРЕДМЕТЫ (GREEN / UNCOMMON)
    # ==========================================
    'ukulele': {
        'name': 'Ukulele', 'short': 'UKU', 'tier': 'green',
        'desc': '25% шанс цепной молнии',
        'mesh_color': rgb(235, 80, 255), 'default_unlocked': True
    },
    'feather': {
        'name': 'Hopoo Feather', 'short': 'JMP', 'tier': 'green',
        'desc': '+1 прыжок в воздухе',
        'mesh_color': rgb(110, 255, 140), 'default_unlocked': True
    },
    'atg_missile': {
        'name': 'AtG Missile Mk. 1', 'short': 'ATG', 'tier': 'green',
        'desc': '12% шанс выпустить ракету (220% ур.)',
        'mesh_color': rgb(115, 235, 75), 'default_unlocked': True
    },
    'will_o_wisp': {
        'name': "Will-o'-the-wisp", 'short': 'WISP', 'tier': 'green',
        'desc': 'Мощный взрыв лавы при убийстве врага',
        'mesh_color': rgb(255, 100, 35), 'default_unlocked': True
    },
    'harvester_scythe': {
        'name': "Harvester's Scythe", 'short': 'SCYTH', 'tier': 'green',
        'desc': '+5% крита и +6 HP при крит. ударе',
        'mesh_color': rgb(85, 245, 175), 'default_unlocked': True
    },
    'predatory': {
        'name': 'Predatory Instincts', 'short': 'PRED', 'tier': 'green',
        'desc': 'Криты ускоряют атаку на +12% (3с)',
        'mesh_color': rgb(245, 110, 85), 'default_unlocked': True
    },
    'bandolier': {
        'name': 'Bandolier', 'short': 'BAND', 'tier': 'green',
        'desc': 'Убийства сокращают КД всех навыков',
        'mesh_color': rgb(225, 190, 95), 'default_unlocked': True
    },
    'kjaro_band': {
        'name': "Kjaro's Band", 'short': 'KJARO', 'tier': 'green',
        'desc': 'Сильные удары создают огненный вихрь',
        'mesh_color': rgb(255, 115, 30), 'default_unlocked': True
    },
    'runald_band': {
        'name': "Runald's Band", 'short': 'RNALD', 'tier': 'green',
        'desc': 'Сильные удары замораживают цель',
        'mesh_color': rgb(85, 225, 255), 'default_unlocked': True
    },
    'wax_quill': {
        'name': 'Wax Quill', 'short': 'QUILL', 'tier': 'green',
        'desc': 'Прыжок совершает рывок вперёд',
        'mesh_color': rgb(255, 215, 120), 'default_unlocked': True
    },
    'rose_buckler': {
        'name': 'Rose Buckler', 'short': 'BUCKL', 'tier': 'green',
        'desc': '-15% урона во время движения',
        'mesh_color': rgb(245, 125, 175), 'default_unlocked': True
    },
    'leeching_seed': {
        'name': 'Leeching Seed', 'short': 'SEED', 'tier': 'green',
        'desc': 'Попадания лечат на +1.5 HP',
        'mesh_color': rgb(145, 255, 95), 'default_unlocked': True
    },
    'infusion': {
        'name': 'Infusion', 'short': 'INFUS', 'tier': 'green',
        'desc': 'Убийства увеличивают макс. HP (+1)',
        'mesh_color': rgb(235, 45, 70), 'default_unlocked': True
    },
    'red_whip': {
        'name': 'Red Whip', 'short': 'WHIP', 'tier': 'green',
        'desc': '+12% к базовой скорости бега',
        'mesh_color': rgb(245, 75, 65), 'default_unlocked': True
    },
    'chronobauble': {
        'name': 'Chronobauble', 'short': 'CHRON', 'tier': 'green',
        'desc': 'Атаки замедляют врагов на 35%',
        'mesh_color': rgb(195, 120, 255), 'default_unlocked': True
    },
    'razorwire': {
        'name': 'Razorwire', 'short': 'RAZOR', 'tier': 'green',
        'desc': 'При получении урона выпускает шипы в 5 врагов вокруг',
        'mesh_color': rgb(185, 235, 115), 'default_unlocked': True
    },
    'guillotine': {
        'name': 'Old Guillotine', 'short': 'GUILL', 'tier': 'green',
        'desc': 'Мгновенно казнит врагов с HP ниже 13% (за стак)',
        'mesh_color': rgb(210, 225, 245), 'default_unlocked': True
    },

    # ==========================================
    # ЛЕГЕНДАРНЫЕ ПРЕДМЕТЫ (RED / LEGENDARY)
    # ==========================================
    'behemoth': {
        'name': 'Brilliant Behemoth', 'short': 'BEHEM', 'tier': 'red',
        'desc': 'Все атаки взрываются (+2.5м AoE, +25% ур.)',
        'mesh_color': rgb(255, 60, 40), 'default_unlocked': True
    },
    'clover': {
        'name': '57 Leaf Clover', 'short': 'CLOVR', 'tier': 'red',
        'desc': 'Удача: +7% крита и +12% ко всем шансам',
        'mesh_color': rgb(75, 255, 135), 'default_unlocked': True
    },
    'tarrasque': {
        'name': 'Heart of Tarrasque', 'short': 'TARR', 'tier': 'red',
        'desc': '+100 к макс. HP и мощная регенерация (+2.5% макс. HP в секунду)',
        'mesh_color': rgb(245, 55, 75), 'default_unlocked': True
    },
    'aegis': {
        'name': 'Aegis', 'short': 'AEGIS', 'tier': 'red',
        'desc': 'Избыточное лечение сверх максимума превращается во временный щит',
        'mesh_color': rgb(255, 215, 75), 'default_unlocked': True
    },
    'tesla_coil': {
        'name': 'Unstable Tesla Coil', 'short': 'TESLA', 'tier': 'red',
        'desc': 'Каждые 1.2с автоматически бьёт молнией ближайших врагов',
        'mesh_color': rgb(110, 225, 255), 'default_unlocked': True
    },
    'ceremonial_dagger': {
        'name': 'Ceremonial Dagger', 'short': 'DAGGR', 'tier': 'red',
        'desc': 'Убийство врага выпускает 3 самонаводящихся спектральных кинжала',
        'mesh_color': rgb(255, 75, 110), 'default_unlocked': True
    },
    'frost_relic': {
        'name': 'Frost Relic', 'short': 'FROST', 'tier': 'red',
        'desc': 'Убийства создают вокруг вас ледяной вихрь на 4 сек.',
        'mesh_color': rgb(125, 240, 255), 'default_unlocked': True
    },
    'shattering_justice': {
        'name': 'Shattering Justice', 'short': 'JUSTC', 'tier': 'red',
        'desc': 'Атаки раскалывают броню врага, увеличивая урон по нему на +20%',
        'mesh_color': rgb(255, 165, 55), 'default_unlocked': True
    },
    'alien_head': {
        'name': 'Alien Head', 'short': 'ALIEN', 'tier': 'red',
        'desc': '-20% времени перезарядки всех способностей',
        'mesh_color': rgb(140, 255, 165), 'default_unlocked': True
    },
    'afterburner': {
        'name': 'Hardlight Afterburner', 'short': 'BURN', 'tier': 'red',
        'desc': '-30% перезарядки навыка Shift и +35% скорости рывка',
        'mesh_color': rgb(255, 110, 55), 'default_unlocked': True
    }
}

# ==========================================
# ПРЕДМЕТЫ ПУСТОТЫ (VOID / PURPLE)
# Спавнятся только на Базаре и в Лунных Бутонах!
# ==========================================
VOID_ITEMS = {
    'plasma_shrimp': {
        'name': 'Plasma Shrimp (Креветка Пустоты)', 'short': 'SHRM', 'tier': 'void',
        'desc': '[ПУСТОТА] Пока есть щит (+20 щита), каждая атака пускает ракету (40% ур.)',
        'mesh_color': rgb(195, 95, 255), 'default_unlocked': True, 'void': True
    },
    'polylute': {
        'name': 'Polylute (Полилютня Бездны)', 'short': 'PLUTE', 'tier': 'void',
        'desc': '[ПУСТОТА] 25% шанс обрушить на цель серию из 3 ударов молнии Бездны',
        'mesh_color': rgb(215, 75, 255), 'default_unlocked': True, 'void': True
    },
    'safer_spaces': {
        'name': 'Safer Spaces (Сфера Бездны)', 'short': 'SPACE', 'tier': 'void',
        'desc': '[ПУСТОТА] Гарантированно блокирует любой удар раз в 12 сек. (-15% КД за стак)',
        'mesh_color': rgb(180, 90, 255), 'default_unlocked': True, 'void': True
    },
    'lysate_cell': {
        'name': 'Lysate Cell (Клетка Бездны)', 'short': 'CELL', 'tier': 'void',
        'desc': '[ПУСТОТА] Сокращает перезарядку Ультимейта [R] на 25% за стак',
        'mesh_color': rgb(225, 110, 255), 'default_unlocked': True, 'void': True
    }
}

# ==========================================
# ЛУННЫЕ ПРЕДМЕТЫ (LUNAR / BLUE)
# Спавнятся только на Базаре и в Лунных Бутонах!
# ==========================================
LUNAR_ITEMS = {
    'shaped_glass': {
        'name': 'Shaped Glass (Лунное Стекло)', 'short': 'GLASS', 'tier': 'lunar',
        'desc': '[ЛУННЫЙ] Урон x2 (+100%), но макс. HP снижено на 50%',
        'mesh_color': rgb(70, 175, 255), 'default_unlocked': True, 'lunar': True
    },
    'transcendence': {
        'name': 'Transcendence (Жук Превосходства)', 'short': 'TRANS', 'tier': 'lunar',
        'desc': '[ЛУННЫЙ] +50% макс. HP и мощный регенерирующий щит',
        'mesh_color': rgb(65, 195, 255), 'default_unlocked': True, 'lunar': True
    },
    'purity': {
        'name': 'Purity (Чистота)', 'short': 'PURE', 'tier': 'lunar',
        'desc': '[ЛУННЫЙ] Перезарядка всех навыков -2 сек., но удача ниже',
        'mesh_color': rgb(140, 225, 255), 'default_unlocked': True, 'lunar': True
    },
    'lunar_pauldron': {
        'name': 'Stone Flux Pauldron (Каменный Наплечник)', 'short': 'FLUX', 'tier': 'lunar',
        'desc': '[ЛУННЫЙ] Макс. HP +100% (x2), но скорость бега -30%',
        'mesh_color': rgb(90, 160, 255), 'default_unlocked': True, 'lunar': True
    },
    'spinel_tonic': {
        'name': 'Spinel Tonic (Лунный Тоник)', 'short': 'TONIC', 'tier': 'lunar',
        'desc': '[ЛУННЫЙ] Все характеристики (+Урон, +HP, +Атака, +Бег) +25%',
        'mesh_color': rgb(55, 140, 255), 'default_unlocked': True, 'lunar': True
    }
}

ITEM_POOL.update(VOID_ITEMS)
ITEM_POOL.update(LUNAR_ITEMS)

# Автоматически назначаем каждому предмету его каноничный цвет редкости из TIER_INFO
for _k, _info in ITEM_POOL.items():
    _t = _info.get('tier', 'white')
    _info['color'] = TIER_INFO[_t]['color']
    _info['tier_name'] = TIER_INFO[_t]['name']

ITEMS_BY_TIER = {
    t: [k for k, v in ITEM_POOL.items() if v.get('tier') == t]
    for t in TIER_INFO.keys()
}


def roll_item_from_pool(pool_type='small_chest'):
    """
    Выбирает предмет из соответствующего пула RoR2.
    Синие (Lunar) и Фиолетовые (Void) предметы НИКОГДА не падают из обычных сундуков и боссов.
    """
    r = random.random()
    if pool_type == 'small_chest':
        # Малый сундук: 79% White, 20% Green, 1% Red
        tier = 'white' if r < 0.79 else ('green' if r < 0.99 else 'red')
    elif pool_type == 'large_chest':
        # Большой сундук: 80% Green, 20% Red
        tier = 'green' if r < 0.80 else 'red'
    elif pool_type == 'legendary_chest':
        # Легендарный сундук: 100% Red
        tier = 'red'
    elif pool_type == 'boss':
        # Награда Босса Телепорта: 75% Green, 25% Red
        tier = 'green' if r < 0.75 else 'red'
    elif pool_type in ('lunar_pod', 'bazaar'):
        # Лунный Бутон / Базар: 55% Lunar, 45% Void
        tier = 'lunar' if r < 0.55 else 'void'
    elif pool_type in ITEMS_BY_TIER:
        tier = pool_type
    else:
        tier = 'white'

    candidates = ITEMS_BY_TIER.get(tier) or ITEMS_BY_TIER['white']
    return random.choice(candidates)