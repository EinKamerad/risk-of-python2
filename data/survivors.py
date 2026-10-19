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
        'subtitle': 'Flame of Corruption [БЛИЖНИЙ БОЙ]',
        'icon': 'SOL',
        'hp': 160,
        'speed': 10.6,
        'damage': 30.0,
        'fire_rate': 2.9,
        'proj_speed': 42.0,
        'proj_scale': 0.48,
        'aoe': 3.5,
        'body_color': rgb(210, 35, 45),
        'armor_color': rgb(40, 35, 38),
        'visor_color': rgb(255, 165, 30),
        'skills': {
            'm1': {'name': 'Junkyard Dog Slash', 'cd': 0.34, 'desc': '[ЛКМ - Ближний бой] Широкие рубящие удары огненным мечом перед собой (радиус 5.4м).'},
            'm2': {'name': 'Volcanic Viper & Gun Flame', 'cd': 4.0, 'desc': '[ПКМ] Сокрушительный огненный апперкот мечом в прыжке + волна пламени.'},
            'shift': {'name': 'Fafnir Lunge', 'cd': 3.8, 'desc': '[Shift] Стремительный пробивной рывок с огненным ударом кулака.'},
            'r': {'name': 'DRAGON INSTALL', 'cd': 11.0, 'desc': '[R] Пробуждение силы Гира: взрыв Tyrant Rave + ускорение боя и регенерация на 6 сек.'}
        }
    },
    'gwen': {
        'name': 'GWEN',
        'subtitle': 'Благая Швея [БЛИЖНИЙ БОЙ]',
        'icon': 'GWN',
        'hp': 135,
        'speed': 10.8,
        'damage': 18.5,
        'fire_rate': 4.8,
        'proj_speed': 52.0,
        'proj_scale': 0.30,
        'aoe': 1.8,
        'body_color': rgb(65, 195, 255),
        'armor_color': rgb(32, 28, 46),
        'visor_color': rgb(195, 240, 255),
        'skills': {
            'm1': {'name': 'Snip Snip! (Thousand Cuts)', 'cd': 0.21, 'desc': '[ЛКМ - Ближний бой] Сверхбыстрые разрезы ножницами в конусе перед собой с вампиризмом.'},
            'm2': {'name': 'Center Snip!', 'cd': 3.5, 'desc': '[ПКМ - Ближний бой] Мощный смыкающий разрез гигантскими ножницами (320% чистого урона + лечение).'},
            'shift': {'name': 'Skip \'n Slash & Hallowed Mist', 'cd': 5.2, 'desc': '[Shift] Рывок вперёд и призыв Священного Тумана, лечащего Гвен и бьющего врагов.'},
            'r': {'name': 'Needlework', 'cd': 9.0, 'desc': '[R] Дальний залп веером из 5 гигантских призрачных игл насквозь.'}
        }
    },
    'enforcer': {
        'name': 'ENFORCER',
        'subtitle': 'Тяжёлый Бастион UES (Hollowed Concepts)',
        'icon': 'ENF',
        'hp': 175,
        'speed': 9.0,
        'damage': 15.0,
        'fire_rate': 1.65,
        'proj_speed': 64.0,
        'proj_scale': 0.20,
        'aoe': 0.0,
        'body_color': rgb(55, 115, 195),
        'armor_color': rgb(38, 48, 68),
        'visor_color': rgb(110, 225, 255),
        'skills': {
            'm1': {'name': 'Riot Shotgun', 'cd': 0.60, 'desc': '[ЛКМ] Мощный залп картечью из 6 пробивных дробин (в стойке щита стреляет быстрее и кучнее).'},
            'm2': {'name': 'Shield Bash', 'cd': 4.0, 'desc': '[ПКМ - Ближний бой] Оглушающий удар щитом перед собой (260% урона, отбрасывание + стан 2с и +20 щита).'},
            'shift': {'name': 'Protect and Serve', 'cd': 1.2, 'desc': '[Shift] Переключение Стойки Щита: -65% входящего урона и +45% скорости стрельбы (при снятии — рывок).'},
            'r': {'name': 'Tear Gas Grenade', 'cd': 9.5, 'desc': '[R] Бросает гранату со слезоточивым газом (замедляет врагов на 50% и наносит урон по области 6 сек).'}
        }
    },
    'scout': {
        'name': 'SCOUT (DRG)',
        'subtitle': 'ROCK AND STONE! Разведчик Hoxxes IV',
        'icon': 'SCT',
        'hp': 120,
        'speed': 11.4,
        'damage': 14.5,
        'fire_rate': 6.8,
        'proj_speed': 72.0,
        'proj_scale': 0.22,
        'aoe': 0.0,
        'body_color': rgb(35, 115, 215),
        'armor_color': rgb(55, 65, 82),
        'visor_color': rgb(255, 210, 55),
        'skills': {
            'm1': {'name': 'Deepcore GK2', 'cd': 0.14, 'desc': '[ЛКМ] Скорострельная штурмовая винтовка с высокой кучностью и точностью.'},
            'm2': {'name': 'Boomstick (Special Powder)', 'cd': 3.6, 'desc': '[ПКМ] Мощный дуплет из обреза (8 дробин) + реактивный прыжок от отдачи в воздухе!'},
            'shift': {'name': 'Grappling Hook', 'cd': 3.2, 'desc': '[Shift] Выстреливает крюком-кошкой на 45м и стремительно притягивает Скаута на тросе (+35% бега).'},
            'r': {'name': 'IFG & Flare Grenade', 'cd': 9.0, 'desc': '[R] Бросает гранату ингибиторного поля (IFG): замедляет врагов на 65% и бьёт током по зоне.'}
        }
    },
    'm4a1': {
        'name': 'M4A1 (GFL)',
        'subtitle': 'Лидер AR Team [DUMMY LINK SYSTEM]',
        'icon': 'M4',
        'hp': 110,
        'speed': 10.4,
        'damage': 15.5,
        'fire_rate': 5.8,
        'proj_speed': 68.0,
        'proj_scale': 0.23,
        'aoe': 0.0,
        'body_color': rgb(75, 95, 78),
        'armor_color': rgb(42, 46, 48),
        'visor_color': rgb(95, 255, 135),
        'skills': {
            'm1': {'name': 'M4A1 Assault Carbine', 'cd': 0.17, 'desc': '[ЛКМ] Точный огонь из карабина. Все живые клоны Dummy Link синхронно атакуют цели.'},
            'm2': {'name': 'Jupiter Cannon (MOD3)', 'cd': 4.5, 'desc': '[ПКМ] Раскладывает рельсовую пушку: пробивной энерго-выстрел с огромным взрывом (340% ур.).'},
            'shift': {'name': 'Tactical Evasion', 'cd': 3.6, 'desc': '[Shift] Тактический рывок с получением +25 щита и приказом клонам дать залп.'},
            'r': {'name': 'Dummy Link (До 4 Клонов)', 'cd': 7.5, 'desc': '[R] Спавнит ИИ-клона с вашими предметами (макс 4). При смерти вы переселяетесь в живого клона (КД навыков 12с)!'}
        }
    }
}