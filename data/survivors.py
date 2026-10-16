from core.utils import rgb

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

