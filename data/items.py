from core.utils import rgb

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

LUNAR_ITEMS = {
    'shaped_glass': {
        'name': 'Shaped Glass (Лунное Стекло)', 'short': 'GLASS',
        'desc': '[ЛУННЫЙ] Урон x2 (+100%), но макс. HP снижено на 50%',
        'color': rgb(70, 175, 255), 'default_unlocked': True, 'lunar': True
    },
    'transcendence': {
        'name': 'Transcendence (Жук Превосходства)', 'short': 'TRANS',
        'desc': '[ЛУННЫЙ] +50% макс. HP и мощный регенерирующий щит',
        'color': rgb(65, 195, 255), 'default_unlocked': True, 'lunar': True
    },
    'purity': {
        'name': 'Purity (Чистота)', 'short': 'PURE',
        'desc': '[ЛУННЫЙ] Перезарядка всех навыков -2 сек., но удача ниже',
        'color': rgb(140, 225, 255), 'default_unlocked': True, 'lunar': True
    },
    'lunar_pauldron': {
        'name': 'Stone Flux Pauldron (Каменный Наплечник)', 'short': 'FLUX',
        'desc': '[ЛУННЫЙ] Макс. HP +100% (x2), но скорость бега -30%',
        'color': rgb(90, 160, 255), 'default_unlocked': True, 'lunar': True
    },
    'spinel_tonic': {
        'name': 'Spinel Tonic (Лунный Тоник)', 'short': 'TONIC',
        'desc': '[ЛУННЫЙ] Все характеристики (+Урон, +HP, +Атака, +Бег) +25%',
        'color': rgb(55, 140, 255), 'default_unlocked': True, 'lunar': True
    }
}

ITEM_POOL.update(LUNAR_ITEMS)

