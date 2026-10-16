import json
import os
from data.items import ITEM_POOL
from data.achievements import ACHIEVEMENTS
from data.monsters import MONSTER_LOG
from data.stages import STAGE_PALETTES

SAVE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'save_logbook.json')


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

