from ursina import *
import math
import random
from config import ctx, rgb, is_valid, SETTINGS, ITEM_POOL, ACHIEVEMENTS, SURVIVOR_CLASSES, PROGRESS
from models import build_survivor_mesh
from entities import Survivor, RemotePlayer, Enemy, Projectile
from world import ItemDrop, Chest, build_stage_world
from network import NetworkManager


class GameManager(Entity):
    def __init__(self):
        super().__init__()
        ctx.game = self
        self.settings = dict(SETTINGS)
        self.net = NetworkManager()

        self.running = False
        self.stage = 1
        self.stage_seed = 1001
        self.stage_name = ''
        self.elapsed_time = 0.0
        self.director_credits = 0.0
        self.spawn_timer = 1.5
        self.active_boss = None

        self.player = None
        self.remote_players = {}
        self.enemies = []
        self.stage_entities = []
        self.obstacles = []
        self.teleporter = None

        # Состояние ввода кода комнаты в меню
        self.typing_code = False
        self.room_code_input = ""

        self.setup_lighting()
        self.setup_menu_diorama()
        self.setup_ui()

    def setup_lighting(self):
        DirectionalLight(y=12, z=6, rotation=(45, -35, 0), shadows=False)
        AmbientLight(color=rgb(145, 150, 180, 255))

    def setup_menu_diorama(self):
        self.diorama_root = Entity(position=(0, 0, 0))
        Entity(parent=self.diorama_root, model='cube', scale=(13.5, 0.4, 7), y=-0.2, color=rgb(34, 42, 58))
        Entity(parent=self.diorama_root, model='cube', scale=(12.0, 0.15, 5.5), y=0.05, color=rgb(50, 62, 84))

        self.menu_crystal = Entity(
            parent=self.diorama_root, model='diamond',
            scale=(1.0, 2.2, 1.0), position=(0, 2.4, 2.2),
            color=rgb(60, 215, 255), unlit=True
        )

        self.preview_commando = Entity(parent=self.diorama_root, position=(-2.8, 0.12, -0.2), rotation_y=22)
        self.commando_parts = build_survivor_mesh(self.preview_commando, 'commando')

        self.preview_artificer = Entity(parent=self.diorama_root, position=(0.0, 0.12, -0.4), rotation_y=0)
        self.artificer_parts = build_survivor_mesh(self.preview_artificer, 'artificer')

        self.preview_huntress = Entity(parent=self.diorama_root, position=(2.8, 0.12, -0.2), rotation_y=-22)
        self.huntress_parts = build_survivor_mesh(self.preview_huntress, 'huntress')

        self.reset_menu_camera()

    def reset_menu_camera(self):
        camera.parent = scene
        camera.position = (0, 2.25, -10.8)
        camera.rotation = (6, 0, 0)

    # ==========================================
    # ФИЗИКА ПОВЕРХНОСТЕЙ И КОЛЛИЗИЙ
    # ==========================================
    def get_surface_height(self, x, z, current_y):
        max_h = 0.0
        for ox, oz, rad, h in self.obstacles:
            if math.hypot(x - ox, z - oz) <= rad + 0.35:
                if current_y >= h - 0.55:
                    max_h = max(max_h, h)
        return max_h

    def resolve_horizontal_collision(self, pos, radius=0.7, entity_y=0.0):
        rx, rz = pos.x, pos.z
        for ox, oz, o_rad, o_h in self.obstacles:
            if entity_y >= o_h - 0.35:
                continue
            dx = rx - ox
            dz = rz - oz
            dist = math.hypot(dx, dz)
            min_d = radius + o_rad
            if dist < min_d:
                if dist < 0.001:
                    rx += min_d
                else:
                    push = (min_d - dist) / dist
                    rx += dx * push
                    rz += dz * push
        return Vec3(rx, pos.y, rz)

    def is_inside_solid_obstacle(self, pos, radius=0.2):
        for ox, oz, o_rad, o_h in self.obstacles:
            if 0.0 <= pos.y <= o_h:
                if math.hypot(pos.x - ox, pos.z - oz) <= (o_rad + radius):
                    return True
        return False

    def unlock_achievement(self, ach_key):
        if ach_key in ACHIEVEMENTS and ach_key not in PROGRESS.unlocked_achievements:
            PROGRESS.unlocked_achievements.append(ach_key)
            ach = ACHIEVEMENTS[ach_key]
            item_k = ach.get('unlocks_item')
            if item_k and item_k not in PROGRESS.unlocked_items:
                PROGRESS.unlocked_items.append(item_k)
            PROGRESS.save()
            self.show_banner(f"ДОСТИЖЕНИЕ: {ach['name']} ({ach['reward_text']})", color.gold, 4.0)

    def setup_ui(self):
        # 1. ГЛАВНОЕ МЕНЮ
        self.menu_panel = Entity(parent=camera.ui)

        Entity(parent=self.menu_panel, model='quad', scale=(2.0, 0.16), y=0.42, z=0.02, color=rgb(12, 16, 26, 230))
        Entity(parent=self.menu_panel, model='quad', scale=(2.0, 0.005), y=0.34, z=-0.01, color=rgb(255, 165, 50))

        Text(
            text='RISK OF PYTHON 2 : LAN & CO-OP',
            parent=self.menu_panel, y=0.445, z=-0.02, scale=2.0,
            origin=(0, 0), color=rgb(255, 185, 60)
        )
        Text(
            text='ВЫБЕРИТЕ ВЫЖИВШЕГО [1 / 2 / 3] ИЛИ ПОДКЛЮЧИТЕСЬ К КОМНАТЕ ДРУГА НИЖЕ',
            parent=self.menu_panel, y=0.375, z=-0.02, scale=0.88,
            origin=(0, 0), color=rgb(150, 225, 255)
        )

        # --- ПАНЕЛЬ МУЛЬТИПЛЕЕРА (LAN И КОД КОМНАТЫ) ---
        Entity(parent=self.menu_panel, model='quad', scale=(1.56, 0.12), y=0.255, z=0.02, color=rgb(16, 22, 36, 235))

        self.btn_host = Button(
            text='СОЗДАТЬ КОМНАТУ (HOST)',
            parent=self.menu_panel, scale=(0.34, 0.055), position=(-0.56, 0.272), z=-0.01,
            color=rgb(35, 95, 65), highlight_color=rgb(50, 140, 90)
        )
        self.btn_host.on_click = self.action_host_room

        self.btn_code_box = Button(
            text='КОД: [ НАЖМИТЕ ДЛЯ ВВОДА ]',
            parent=self.menu_panel, scale=(0.40, 0.055), position=(-0.15, 0.272), z=-0.01,
            color=rgb(28, 36, 54), highlight_color=rgb(45, 60, 88)
        )
        self.btn_code_box.on_click = self.toggle_code_typing

        self.btn_join_code = Button(
            text='ВОЙТИ ПО КОДУ',
            parent=self.menu_panel, scale=(0.25, 0.055), position=(0.21, 0.272), z=-0.01,
            color=rgb(40, 85, 145), highlight_color=rgb(60, 120, 200)
        )
        self.btn_join_code.on_click = self.action_join_by_code

        self.btn_join_lan = Button(
            text='НАЙТИ В LAN (АВТО)',
            parent=self.menu_panel, scale=(0.32, 0.055), position=(0.53, 0.272), z=-0.01,
            color=rgb(95, 55, 145), highlight_color=rgb(130, 80, 195)
        )
        self.btn_join_lan.on_click = self.action_join_lan

        self.net_status_text = Text(
            text=f'Статус сети: Одиночный режим (Ваш LAN IP: {self.net.host_ip})',
            parent=self.menu_panel, position=(0, 0.215), z=-0.02,
            origin=(0, 0), scale=0.82, color=color.cyan
        )

        # --- КАРТОЧКИ 3 ПЕРСОНАЖЕЙ ---
        cards = [
            ('commando', -0.48, rgb(235, 125, 35), "[1] COMMANDO\nHP: 115 | SPD: 9.6\nM1: Double Tap | M2: Phase\nShift: Dive | R: Barrage"),
            ('artificer', 0.0, rgb(165, 65, 235), "[2] ARTIFICER\nHP: 100 | SPD: 8.5\nM1: Plasma | M2: Nano-Bomb\nShift: Surge | R: Ion Strike"),
            ('huntress', 0.48, rgb(225, 50, 80), "[3] HUNTRESS\nHP: 95 | SPD: 10.8\nM1: Homing Bow | M2: Glaive\nShift: Blink | R: Arrow Rain")
        ]
        for key, cx, col, label in cards:
            Entity(parent=self.menu_panel, model='quad', scale=(0.43, 0.23), position=(cx, -0.29), z=0.01, color=col)
            btn = Button(
                text=label, parent=self.menu_panel, scale=(0.415, 0.215),
                position=(cx, -0.29), z=-0.01, color=rgb(24, 30, 44, 245), highlight_color=col
            )
            btn.on_click = lambda k=key: self.start_run(k)

        Entity(parent=self.menu_panel, model='quad', scale=(1.5, 0.045), y=-0.46, z=0.02, color=rgb(12, 16, 26, 210))
        Text(
            text='Управление: [WASD] Ходьба | [Space] Прыжок | [ЛКМ/ПКМ/Shift/R] Навыки | [E] Действие | [Tab] Статистика',
            parent=self.menu_panel, y=-0.46, z=-0.02, origin=(0, 0), scale=0.76, color=rgb(200, 210, 230)
        )

        # 2. БОЕВОЙ ИНТЕРФЕЙС (HUD)
        self.hud_panel = Entity(parent=camera.ui, enabled=False)
        self.crosshair = Text(text='+', parent=self.hud_panel, origin=(0, 0), z=-0.02, scale=1.6, color=color.cyan)

        self.top_bar_bg = Entity(
            parent=self.hud_panel, model='quad', scale=(0.98, 0.105),
            position=(-0.27, 0.43), z=0.02, color=rgb(14, 18, 28, 210)
        )
        self.hud_room_label = Text(
            text='INVENTORY  [HOLD TAB FOR DETAILS]',
            parent=self.hud_panel, position=(-0.74, 0.472), z=-0.02,
            scale=0.72, color=rgb(175, 195, 225)
        )

        self.item_slots = {}
        for idx, (k, info) in enumerate(ITEM_POOL.items()):
            slot_x = -0.68 + idx * 0.135
            slot_y = 0.415
            slot_bg = Entity(
                parent=self.hud_panel, model='quad', scale=(0.12, 0.068),
                position=(slot_x, slot_y), z=0.01, color=rgb(28, 34, 48, 225)
            )
            Entity(
                parent=self.hud_panel, model='quad', scale=(0.12, 0.010),
                position=(slot_x, slot_y + 0.029), z=-0.01, color=info['color']
            )
            lbl_name = Text(
                text=info['short'], parent=self.hud_panel,
                position=(slot_x, slot_y + 0.008), z=-0.02, origin=(0, 0),
                scale=0.78, color=info['color']
            )
            lbl_count = Text(
                text='x0', parent=self.hud_panel,
                position=(slot_x, slot_y - 0.016), z=-0.02, origin=(0, 0),
                scale=0.86, color=rgb(125, 130, 145)
            )
            self.item_slots[k] = {'bg': slot_bg, 'name_txt': lbl_name, 'count_txt': lbl_count}

        Entity(
            parent=self.hud_panel, model='quad', scale=(0.46, 0.12),
            position=(0.61, 0.425), z=0.02, color=rgb(14, 18, 28, 210)
        )
        self.diff_badge = Entity(
            parent=self.hud_panel, model='quad', scale=(0.46, 0.010),
            position=(0.61, 0.48), z=-0.01, color=rgb(80, 225, 100)
        )
        self.diff_text = Text(
            text='', parent=self.hud_panel, position=(0.40, 0.465),
            z=-0.02, scale=0.80, color=color.white
        )

        # Полоска здоровья и золота
        Entity(
            parent=self.hud_panel, model='quad', scale=(0.48, 0.125),
            position=(-0.60, -0.41), z=0.02, color=rgb(14, 18, 28, 215)
        )
        self.gold_text = Text(
            text='$0', parent=self.hud_panel, position=(-0.82, -0.362),
            z=-0.02, scale=1.0, color=color.gold
        )
        self.hp_bar_bg = Entity(
            parent=self.hud_panel, model='quad', scale=(0.44, 0.038),
            position=(-0.82, -0.43), origin=(-0.5, 0), z=0.01, color=rgb(50, 20, 22)
        )
        self.hp_bar_fill = Entity(
            parent=self.hp_bar_bg, model='quad', scale=(1, 1),
            origin=(-0.5, 0), z=-0.01, color=rgb(85, 225, 95)
        )
        self.hp_text = Text(
            text='110 / 110 HP', parent=self.hud_panel, position=(-0.60, -0.43),
            z=-0.02, origin=(0, 0), scale=0.90, color=color.white
        )

        # Иконки 4 способностей (M1, M2, Shift, R)
        self.skill_boxes = {}
        skill_defs = [
            ('m1', 'M1', 0.42, color.yellow),
            ('m2', 'M2', 0.52, color.orange),
            ('shift', 'SHIFT', 0.62, color.cyan),
            ('r', 'ULT [R]', 0.72, color.magenta)
        ]
        for sk_key, title, sx, col in skill_defs:
            box = Entity(
                parent=self.hud_panel, model='quad', scale=(0.088, 0.085),
                position=(sx, -0.415), z=0.01, color=rgb(35, 45, 65, 230)
            )
            Text(text=title, parent=self.hud_panel, position=(sx, -0.39), z=-0.02, origin=(0, 0), scale=0.72, color=col)
            cd_lbl = Text(text='READY', parent=self.hud_panel, position=(sx, -0.43), z=-0.02, origin=(0, 0), scale=0.68, color=color.white)
            self.skill_boxes[sk_key] = (box, cd_lbl, col)

        # Полоска здоровья Босса
        self.boss_hud = Entity(parent=self.hud_panel, enabled=False)
        self.boss_title = Text(
            text='STONE TITAN :: PRIMORDIAL GUARDIAN',
            parent=self.boss_hud, position=(0, 0.31), z=-0.02,
            origin=(0, 0), scale=1.05, color=color.red
        )
        self.boss_bar_bg = Entity(
            parent=self.boss_hud, model='quad', scale=(0.76, 0.026),
            position=(-0.38, 0.27), origin=(-0.5, 0), z=0.01, color=rgb(45, 15, 15, 230)
        )
        self.boss_bar_fill = Entity(
            parent=self.boss_bar_bg, model='quad', scale=(1, 1),
            origin=(-0.5, 0), z=-0.01, color=color.red
        )

        # Панель [TAB]
        self.tab_panel = Entity(parent=self.hud_panel, enabled=False)
        Entity(parent=self.tab_panel, model='quad', scale=(0.88, 0.56), position=(0, 0), z=0.01, color=rgb(12, 16, 26, 240))
        self.tab_text = Text(text='', parent=self.tab_panel, position=(-0.39, 0.22), z=-0.02, scale=0.90, color=color.white)

        # Баннер уведомлений
        self.banner_text = Text(text='', parent=self.hud_panel, position=(0, 0.19), z=-0.02, origin=(0, 0), scale=1.15, color=color.yellow)
        self.banner_timer = 0.0

    # ==========================================
    # ДЕЙСТВИЯ МУЛЬТИПЛЕЕРА В МЕНЮ
    # ==========================================
    def toggle_code_typing(self):
        self.typing_code = not self.typing_code
        self.refresh_code_button()

    def refresh_code_button(self):
        if self.typing_code:
            shown = self.room_code_input if self.room_code_input else "ВВЕДИТЕ КОД..."
            self.btn_code_box.text = f"КОД: > {shown}_ <"
            self.btn_code_box.color = rgb(55, 75, 115)
        else:
            shown = self.room_code_input if self.room_code_input else "НАЖМИТЕ ДЛЯ ВВОДА"
            self.btn_code_box.text = f"КОД: [ {shown} ]"
            self.btn_code_box.color = rgb(28, 36, 54)

    def handle_menu_key(self, key):
        if not self.typing_code:
            return False
        if key == 'backspace':
            self.room_code_input = self.room_code_input[:-1]
            self.refresh_code_button()
            return True
        elif key in ('enter', 'return'):
            self.typing_code = False
            self.refresh_code_button()
            self.action_join_by_code()
            return True
        elif key == 'escape':
            self.typing_code = False
            self.refresh_code_button()
            return True
        elif key in ('space', '-'):
            self.room_code_input += '-'
            self.refresh_code_button()
            return True
        elif len(key) == 1 and (key.isalnum() or key in ('.', ':')):
            if len(self.room_code_input) < 21:
                self.room_code_input += key.upper()
                self.refresh_code_button()
            return True
        return False

    def action_host_room(self):
        self.typing_code = False
        self.refresh_code_button()
        ok, info = self.net.host_room()
        if ok:
            self.net_status_text.text = f"КОМНАТА СОЗДАНА! КОД КОМНАТЫ: {info}  (IP: {self.net.host_ip}:{self.net.port}) — Выберите персонажа!"
            self.net_status_text.color = color.lime
        else:
            self.net_status_text.text = f"Ошибка создания комнаты: {info}"
            self.net_status_text.color = color.red

    def action_join_by_code(self):
        self.typing_code = False
        self.refresh_code_button()
        if not self.room_code_input.strip():
            self.net_status_text.text = "Сначала нажмите на поле 'КОД' и введите код комнаты друга!"
            self.net_status_text.color = color.orange
            return
        ok, info = self.net.join_by_code(self.room_code_input)
        if ok:
            self.net_status_text.text = f"ПОДКЛЮЧЕНО К КОМНАТЕ [{info}]! Выберите выжившего [1 / 2 / 3] для входа в бой!"
            self.net_status_text.color = color.lime
        else:
            self.net_status_text.text = info
            self.net_status_text.color = color.red

    def action_join_lan(self):
        self.typing_code = False
        self.refresh_code_button()
        ok, info = self.net.join_lan_auto()
        if ok:
            self.room_code_input = info
            self.refresh_code_button()
            self.net_status_text.text = f"НАЙДЕНА LAN-КОМНАТА [{info}]! Выберите выжившего [1 / 2 / 3]!"
            self.net_status_text.color = color.lime
        else:
            self.net_status_text.text = f"Активные комнаты в LAN не найдены ({info})"
            self.net_status_text.color = color.orange

    @property
    def difficulty_coeff(self):
        minutes = self.elapsed_time / 60.0
        player_bonus = 1.0 + 0.3 * len(self.remote_players)
        return (1.0 + 0.18 * minutes) * (1.15 ** (self.stage - 1)) * player_bonus

    def get_difficulty_info(self):
        c = self.difficulty_coeff
        if c < 1.3:
            return 'EASY', rgb(80, 225, 100)
        elif c < 1.8:
            return 'MEDIUM', rgb(255, 210, 60)
        elif c < 2.5:
            return 'HARD', rgb(255, 130, 40)
        elif c < 3.5:
            return 'VERY HARD', rgb(245, 55, 55)
        return 'HAHAHA (INSANE)', rgb(210, 50, 255)

    def start_run(self, char_key):
        self.typing_code = False
        self.menu_panel.enabled = False
        self.diorama_root.enabled = False
        self.hud_panel.enabled = True
        mouse.locked = True

        if is_valid(self.player):
            destroy(self.player)
        if self.net.mode != 'client':
            self.stage = 1
            self.stage_seed = random.randint(1000, 999999)
        self.elapsed_time = 0.0
        self.player = Survivor(char_key)
        self.generate_stage(seed=self.stage_seed)
        self.running = True

        if self.net.connected and self.net.mode == 'host':
            self.net.broadcast({'type': 'stage_sync', 'stage': self.stage, 'seed': self.stage_seed})

    def generate_stage(self, seed=None):
        if seed is None:
            seed = random.randint(1000, 999999)
        self.stage_seed = seed

        for e in list(self.enemies):
            if is_valid(e):
                e.is_dead = True
                destroy(e)
        self.enemies.clear()

        for obj in list(self.stage_entities):
            if obj and not obj.is_empty():
                destroy(obj)
        self.stage_entities.clear()
        self.obstacles.clear()
        self.active_boss = None

        res = build_stage_world(self.stage, seed=self.stage_seed)
        self.stage_entities, self.obstacles, self.teleporter, stage_info = res
        self.stage_name = stage_info['name'] if isinstance(stage_info, dict) else str(stage_info)

        if is_valid(self.player):
            self.player.position = Vec3(0, 1, 0)
        self.director_credits = 26.0 * self.difficulty_coeff
        self.show_banner(f'STAGE {self.stage}: {self.stage_name.upper()}', color.yellow, 3.0)

        if self.stage >= 2:
            self.unlock_achievement('ach_traveler')

    def next_stage(self, from_network=False):
        self.stage += 1
        new_seed = random.randint(1000, 999999) if not from_network else self.stage_seed
        self.generate_stage(seed=new_seed)
        if not from_network and self.net.connected:
            self.net.broadcast({'type': 'stage_sync', 'stage': self.stage, 'seed': self.stage_seed})

    def spawn_boss(self, pos, net_id=None, from_network=False):
        boss = Enemy(pos, 'boss', self.difficulty_coeff, net_id=net_id)
        self.active_boss = boss
        self.enemies.append(boss)
        if not from_network and self.net.connected and self.net.mode == 'host':
            self.net.broadcast({
                'type': 'enemy_spawn',
                'net_id': boss.net_id,
                'enemy_type': 'boss',
                'pos': [round(pos.x, 2), round(pos.y, 2), round(pos.z, 2)],
                'coeff': round(self.difficulty_coeff, 2)
            })

    def spawn_item_drop(self, pos, item_key=None, broadcast=True):
        key = item_key if item_key in ITEM_POOL else random.choice(list(ITEM_POOL.keys()))
        drop = ItemDrop(pos, key)
        self.stage_entities.append(drop)
        if broadcast and self.net.connected:
            self.net.broadcast({
                'type': 'item_drop',
                'item_key': key,
                'pos': [round(pos.x, 2), round(pos.y, 2), round(pos.z, 2)]
            })

    def collect_item(self, key):
        self.player.items[key] += 1
        info = ITEM_POOL[key]
        self.show_banner(f"ПОДОБРАНО: {info['name']} ({info['desc']})", info['color'], 3.2)
        if sum(self.player.items.values()) >= 6:
            self.unlock_achievement('ach_hoarder')

    def show_banner(self, msg, col=color.yellow, duration=2.5):
        self.banner_text.text = msg
        self.banner_text.color = col
        self.banner_timer = duration

    def on_player_death(self):
        self.running = False
        mouse.locked = False
        self.tab_panel.enabled = False
        if is_valid(self.player):
            destroy(self.player)
        self.player = None
        for rp in list(self.remote_players.values()):
            if is_valid(rp):
                destroy(rp)
        self.remote_players.clear()

        self.diorama_root.enabled = True
        self.reset_menu_camera()
        self.menu_panel.enabled = True
        self.show_banner('ВЫ ПОГИБЛИ! ВЫБЕРИТЕ ВЫЖИВШЕГО ДЛЯ НОВОГО ЗАБЕГА', color.red, 999.0)

    # ==========================================
    # ОБРАБОТКА СЕТЕВЫХ ПАКЕТОВ
    # ==========================================
    def process_network(self):
        for msg in self.net.poll_messages():
            mtype = msg.get('type')

            if mtype == 'welcome':
                self.net.my_id = msg.get('player_id', 'p2')
                self.net.room_code = msg.get('room_code', self.net.room_code)
                self.show_banner(f"ПОДКЛЮЧЕНО К КОМНАТЕ {self.net.room_code}!", color.lime, 3.0)

            elif mtype == 'client_joined':
                pid = msg.get('player_id')
                self.show_banner(f"ИГРОК [{pid.upper()}] ПОДКЛЮЧИЛСЯ К КОМНАТЕ!", color.cyan, 3.0)
                if self.running and self.net.mode == 'host':
                    self.net.broadcast({'type': 'stage_sync', 'stage': self.stage, 'seed': self.stage_seed})

            elif mtype == 'player_left':
                pid = msg.get('player_id')
                if pid in self.remote_players:
                    destroy(self.remote_players.pop(pid))
                self.show_banner(f"ИГРОК [{str(pid).upper()}] ПОКИНУЛ ИГРУ", color.orange, 2.5)

            elif mtype == 'player_state':
                pid = msg.get('player_id')
                if not pid or pid == self.net.my_id:
                    continue
                if not self.running:
                    continue
                if pid not in self.remote_players or not is_valid(self.remote_players[pid]):
                    self.remote_players[pid] = RemotePlayer(pid, msg.get('char_key', 'commando'))
                self.remote_players[pid].apply_net_state(msg)

            elif mtype == 'player_shoot':
                pid = msg.get('player_id')
                if not self.running or pid == self.net.my_id:
                    continue
                col_tag = msg.get('col', 'cyan')
                p_col = color.cyan if col_tag == 'cyan' else (
                    color.yellow if col_tag == 'commando' else (
                        color.magenta if col_tag == 'artificer' else rgb(255, 80, 100)
                    )
                )
                Projectile(
                    pos=msg['pos'], direction=msg['dir'], speed=msg['speed'],
                    damage=0, scale_val=msg['scale'], proj_color=p_col,
                    is_player=True, aoe=msg.get('aoe', 0.0), pierce=msg.get('pierce', False),
                    bounces=msg.get('bounces', 0), homing=msg.get('homing', False), is_remote=True
                )

            elif mtype == 'stage_sync':
                new_stage = msg.get('stage', 1)
                new_seed = msg.get('seed', 1001)
                if self.stage != new_stage or self.stage_seed != new_seed:
                    self.stage = new_stage
                    self.stage_seed = new_seed
                    if self.running:
                        self.generate_stage(seed=self.stage_seed)

            elif mtype == 'enemy_spawn':
                if self.running and self.net.mode == 'client':
                    etype = msg['enemy_type']
                    pos = Vec3(*msg['pos'])
                    if etype == 'boss':
                        self.spawn_boss(pos, net_id=msg['net_id'], from_network=True)
                    else:
                        e = Enemy(pos, etype, msg.get('coeff', self.difficulty_coeff), net_id=msg['net_id'])
                        self.enemies.append(e)

            elif mtype == 'enemy_damage':
                if self.running:
                    nid = msg.get('net_id')
                    amt = msg.get('amount', 0)
                    for e in list(self.enemies):
                        if is_valid(e) and e.net_id == nid:
                            e.take_damage(amt, from_network=True)
                            break

            elif mtype == 'chest_open':
                if self.running:
                    cid = msg.get('chest_id')
                    ikey = msg.get('item_key')
                    for obj in self.stage_entities:
                        if isinstance(obj, Chest) and obj.chest_id == cid:
                            obj.open_visual(ikey)
                            break

            elif mtype == 'item_drop':
                if self.running:
                    self.spawn_item_drop(Vec3(*msg['pos']), item_key=msg.get('item_key'), broadcast=False)

            elif mtype == 'tp_activate':
                if self.running and self.teleporter:
                    self.teleporter.activate_teleporter(from_network=True)

    def update(self):
        self.process_network()

        if not self.running:
            t = time.time()
            self.preview_commando.rotation_y += 24 * time.dt
            self.preview_artificer.rotation_y -= 24 * time.dt
            self.preview_huntress.rotation_y += 24 * time.dt
            self.menu_crystal.rotation_y += 55 * time.dt
            self.menu_crystal.y = 2.4 + math.sin(t * 2.5) * 0.2
            if self.artificer_parts.get('halo'):
                self.artificer_parts['halo'].rotation_z += 90 * time.dt
            return

        if not is_valid(self.player):
            return

        self.elapsed_time += time.dt
        coeff = self.difficulty_coeff
        self.enemies = [e for e in self.enemies if is_valid(e)]

        # ИИ-Режиссер спавнит врагов (в мультиплеере — на стороне хоста и рассылает клиентам)
        if self.net.mode != 'client':
            tp_mult = 1.8 if (self.teleporter and self.teleporter.state == 'charging') else 1.0
            self.director_credits += (3.8 * coeff * tp_mult) * time.dt
            self.spawn_timer -= time.dt

            if self.spawn_timer <= 0 and len(self.enemies) < 24:
                self.spawn_timer = random.uniform(1.8, 3.4)
                if self.director_credits >= 12.0:
                    enemy_type = 'wisp' if (self.director_credits >= 18.0 and random.random() < 0.42) else 'lemurian'
                    cost = 18.0 if enemy_type == 'wisp' else 12.0
                    self.director_credits -= cost

                    ang = random.uniform(0, math.pi * 2)
                    dist = random.uniform(16.0, 28.0)
                    p_pos = Vec3(*self.player.position)
                    spawn_pos = p_pos + Vec3(math.cos(ang) * dist, 0, math.sin(ang) * dist)
                    spawn_pos.x = clamp(spawn_pos.x, -54, 54)
                    spawn_pos.z = clamp(spawn_pos.z, -54, 54)
                    spawn_pos.y = 0
                    new_enemy = Enemy(spawn_pos, enemy_type, coeff)
                    self.enemies.append(new_enemy)

                    if self.net.connected and self.net.mode == 'host':
                        self.net.broadcast({
                            'type': 'enemy_spawn',
                            'net_id': new_enemy.net_id,
                            'enemy_type': enemy_type,
                            'pos': [round(spawn_pos.x, 2), 0, round(spawn_pos.z, 2)],
                            'coeff': round(coeff, 2)
                        })

        if self.banner_timer > 0:
            self.banner_timer -= time.dt
            if self.banner_timer <= 0:
                self.banner_text.text = ''

        p = self.player
        if self.net.connected:
            players_online = 1 + len(self.remote_players)
            self.hud_room_label.text = f"КОД КОМНАТЫ: {self.net.room_code}  |  ИГРОКОВ В СЕТИ: {players_online}  |  [TAB] ИНФО"
            self.hud_room_label.color = color.lime
        else:
            self.hud_room_label.text = "INVENTORY  [HOLD TAB FOR DETAILS]"
            self.hud_room_label.color = rgb(175, 195, 225)

        for k, slot in self.item_slots.items():
            cnt = p.items[k]
            slot['count_txt'].text = f"x{cnt}"
            if cnt > 0:
                slot['count_txt'].color = color.white
                slot['bg'].color = rgb(48, 58, 82, 240)
            else:
                slot['count_txt'].color = rgb(125, 130, 145)
                slot['bg'].color = rgb(24, 28, 40, 180)

        self.gold_text.text = f"${p.gold}   |   {SURVIVOR_CLASSES[p.char_key]['name']}"
        hp_ratio = clamp(p.hp / p.max_hp, 0.0, 1.0)
        self.hp_bar_fill.scale_x = max(0.001, hp_ratio)
        self.hp_bar_fill.color = rgb(85, 225, 95) if hp_ratio > 0.35 else rgb(245, 70, 60)
        self.hp_text.text = f"{int(p.hp)} / {p.max_hp} HP"

        # Обновление индикаторов всех 4 способностей
        cds = {'m1': p.m1_cd, 'm2': p.m2_cd, 'shift': p.shift_cd, 'r': p.r_cd}
        for sk_key, (box, cd_lbl, col) in self.skill_boxes.items():
            rem = cds[sk_key]
            if rem <= 0:
                cd_lbl.text = 'READY'
                cd_lbl.color = col
                box.color = rgb(35, 55, 75, 235)
            else:
                cd_lbl.text = f"{rem:.1f}s"
                cd_lbl.color = color.red
                box.color = rgb(22, 24, 32, 235)

        if is_valid(self.active_boss):
            self.boss_hud.enabled = True
            b_ratio = clamp(self.active_boss.hp / self.active_boss.max_hp, 0.0, 1.0)
            self.boss_bar_fill.scale_x = max(0.001, b_ratio)
        else:
            self.boss_hud.enabled = False

        mins = int(self.elapsed_time // 60)
        secs = int(self.elapsed_time % 60)
        diff_label, diff_col = self.get_difficulty_info()
        self.diff_badge.color = diff_col
        self.diff_text.text = (
            f"STAGE {self.stage}: {self.stage_name}\n"
            f"TIME: {mins:02d}:{secs:02d}  |  {diff_label} (x{coeff:.2f})\n"
            f"MONSTERS: {len(self.enemies)}  |  CO-OP: {1 + len(self.remote_players)}P"
        )

        self.tab_panel.enabled = bool(held_keys['tab'])
        if self.tab_panel.enabled:
            atk_bonus = p.items['syringe'] * 15
            spd_bonus = p.items['hoof'] * 14
            blk_pct = p.block_chance * 100.0
            net_line = f"Сеть: Комната {self.net.room_code} ({1 + len(self.remote_players)} игр.)" if self.net.connected else "Сеть: Одиночная игра"
            lines = [
                f"=== SURVIVOR OVERVIEW: {SURVIVOR_CLASSES[p.char_key]['name']} | {net_line} ===",
                f"Base Damage: {p.base_damage:.1f}   |   Attack Speed: +{atk_bonus}% ({p.fire_rate:.1f} shots/s)",
                f"Move Speed: +{spd_bonus}% ({p.move_speed:.1f})   |   Block Chance: {blk_pct:.1f}%   |   Crit: {p.crit_chance*100:.0f}%",
                "",
                "=== COLLECTED ITEMS & STACKS ==="
            ]
            for k, info in ITEM_POOL.items():
                lines.append(f" - {info['name']} [x{p.items[k]}]: {info['desc']}")
            self.tab_text.text = '\n'.join(lines)