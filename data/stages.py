from core.utils import rgb

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

SPECIAL_PALETTES = {
    'bazaar': {
        'id': 'bazaar',
        'name': 'Bazaar Between Time',
        'desc': 'Тайное святилище Тритона вне пространства и времени.',
        'ground': rgb(20, 26, 46),
        'ruins': rgb(38, 52, 88),
        'accent': rgb(65, 195, 255),
        'sky': rgb(10, 14, 28),
        'nebula': rgb(35, 95, 185),
        'moon': rgb(140, 215, 255)
    },
    'moon': {
        'id': 'moon',
        'name': 'Commencement (The Moon)',
        'desc': 'Расколотая цитадель Митрикса на орбите Petrichor V.',
        'ground': rgb(185, 198, 218),
        'ruins': rgb(55, 68, 92),
        'accent': rgb(75, 215, 255),
        'sky': rgb(8, 12, 24),
        'nebula': rgb(40, 110, 195),
        'moon': rgb(90, 210, 255)
    }
}

