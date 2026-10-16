from ursina import *
import math
import random
import textwrap
from config import ctx, rgb, is_valid, clear_children, SETTINGS, ITEM_POOL, ACHIEVEMENTS, SURVIVOR_CLASSES, PROGRESS
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
        self.menu_state = 'main'  # 'main', 'mp_connect', 'settings', 'lobby', 'in_game'
        self.selected_char = 'commando'

        # Состояние лобби и голосования
        self.my_ready = False
        self.lobby_players = {}  # pid -> {'char_key': str, 'ready': bool}
        self.lobby_countdown_active = False
        self.lobby_countdown = 60.0
        self.lobby_sync_timer = 0.0

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

        # Состояние ввода кода комнаты
        self.typing_code = False
        self.room_code_input = ""

        self.setup_lighting()
        self.setup_menu_diorama()
        self.setup_ui()
        self.show_screen('main')

    def setup_lighting(self):
        DirectionalLight(y=12, z=6, rotation=(45, -35, 0), shadows=False)
        AmbientLight(color=rgb(145, 150, 180, 255))

    # ==========================================
    # 3D-СЦЕНА ЛОББИ (ЦЕНТРАЛЬНЫЙ ГЕРОЙ + СОЮЗНИКИ СЗАДИ)
    # ==========================================
    def setup_menu_diorama(self):
        self.diorama_root = Entity(position=(0, 0, 0))

        # Главный подиум в центре (смещён вправо, чтобы не перекрываться левой панелью описания)
        self.main_pedestal = Entity(parent=self.diorama_root, position=(1.15, 0, -1.0))
        Entity(parent=self.main_pedestal, model='cube', scale=(3.4, 0.35, 3.4), y=-0.18, color=rgb(34, 42, 58))
        Entity(parent=self.main_pedestal, model='cube', scale=(2.8, 0.14, 2.8), y=0.04, color=rgb(55, 70, 96))
        Entity(parent=self.main_pedestal, model='cube', scale=(2.9, 0.05, 2.9), y=0.10, color=color.cyan, unlit=True)

        self.local_preview_actor = Entity(parent=self.main_pedestal, position=(0, 0.12, 0), rotation_y=15)
        self.local_preview_parts = build_survivor_mesh(self.local_preview_actor, self.selected_char)

        # Задние постаменты для союзников в мультиплеере
        self.remote_pedestals = []
        back_coords = [
            (-0.95, 0.35, 2.3, 18),
            (1.15, 0.35, 2.8, 0),
            (3.25, 0.35, 2.3, -18)
        ]
        for bx, by, bz, rot_y in back_coords:
            ped = Entity(parent=self.diorama_root, position=(bx, by, bz), enabled=False)
            Entity(parent=ped, model='cube', scale=(2.2, 0.3, 2.2), y=-0.15, color=rgb(28, 34, 48))
            ring = Entity(parent=ped, model='cube', scale=(1.9, 0.06, 1.9), y=0.03, color=rgb(80, 180, 255), unlit=True)
            actor = Entity(parent=ped, position=(0, 0.06, 0), rotation_y=rot_y)
            lbl = Text(
                text='', parent=ped, y=2.95, scale=8.5,
                origin=(0, 0), color=color.cyan, billboard=True
            )
            self.remote_pedestals.append({
                'pedestal': ped,
                'ring': ring,
                'actor': actor,
                'label': lbl,
                'char_key': None,
                'parts': None
            })

        self.menu_crystal = Entity(
            parent=self.diorama_root, model='diamond',
            scale=(0.85, 1.85, 0.85), position=(1.15, 3.3, 2.2),
            color=rgb(60, 215, 255), unlit=True
        )

        self.reset_menu_camera()

    def reset_menu_camera(self):
        camera.parent = scene
        camera.position = (0, 2.15, -8.6)
        camera.rotation = (5, 0, 0)
        camera.fov = self.settings.get('fov', 90)

    def rebuild_local_lobby_model(self):
        clear_children(self.local_preview_actor)
        self.local_preview_parts = build_survivor_mesh(self.local_preview_actor, self.selected_char)

    def refresh_remote_lobby_models(self):
        if not self.net.connected or self.menu_state != 'lobby':
            for slot in self.remote_pedestals:
                slot['pedestal'].enabled = False
            return

        peers = sorted(self.lobby_players.items(), key=lambda x: x[0])
        for idx, slot in enumerate(self.remote_pedestals):
            if idx < len(peers):
                pid, info = peers[idx]
                ckey = info.get('char_key', 'commando')
                if ckey not in SURVIVOR_CLASSES:
                    ckey = 'commando'
                is_rdy = info.get('ready', False)

                slot['pedestal'].enabled = True
                if slot['char_key'] != ckey:
                    clear_children(slot['actor'])
                    slot['parts'] = build_survivor_mesh(slot['actor'], ckey)
                    slot['char_key'] = ckey

                rdy_str = "ГОТОВ ✓" if is_rdy else "ВЫБИРАЕТ..."
                slot['label'].text = f"[{pid.upper()}] {SURVIVOR_CLASSES[ckey]['name']}\n[{rdy_str}]"
                slot['label'].color = color.lime if is_rdy else color.yellow
                slot['ring'].color = color.lime if is_rdy else rgb(80, 180, 255)
            else:
                slot['pedestal'].enabled = False

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

    # ==========================================
    # ПОСТРОЕНИЕ ВСЕХ ЭКРАНОВ ИНТЕРФЕЙСА
    # ==========================================
    def setup_ui(self):
        # Общая верхняя шапка для меню
        self.header_panel = Entity(parent=camera.ui)
        Entity(parent=self.header_panel, model='quad', scale=(2.0, 0.12), y=0.44, z=0.02, color=rgb(12, 16, 26, 235))
        Entity(parent=self.header_panel, model='quad', scale=(2.0, 0.004), y=0.38, z=-0.01, color=rgb(255, 165, 50))
        self.header_title = Text(
            text='RISK OF PYTHON 2 : LAN & CO-OP',
            parent=self.header_panel, y=0.445, z=-0.02, scale=1.75,
            origin=(0, 0), color=rgb(255, 185, 60)
        )

        # ------------------------------------------
        # 1. ГЛАВНОЕ МЕНЮ (MAIN MENU)
        # ------------------------------------------
        self.main_menu_panel = Entity(parent=camera.ui)
        Entity(parent=self.main_menu_panel, model='quad', scale=(0.62, 0.58), position=(-0.46, -0.04), z=0.02, color=rgb(14, 18, 30, 235))
        Entity(parent=self.main_menu_panel, model='quad', scale=(0.62, 0.006), position=(-0.46, 0.25), z=-0.01, color=color.cyan)

        Text(
            text='ГЛАВНОЕ МЕНЮ',
            parent=self.main_menu_panel, position=(-0.46, 0.20), z=-0.02,
            origin=(0, 0), scale=1.25, color=color.white
        )

        menu_Actions = [
            ('ОДИНОЧНАЯ ИГРА', 0.09, rgb(38, 105, 70), rgb(55, 150, 95), self.open_singleplayer_lobby),
            ('СЕТЕВАЯ ИГРА (CO-OP)', -0.02, rgb(40, 85, 145), rgb(60, 125, 205), lambda: self.show_screen('mp_connect')),
            ('НАСТРОЙКИ', -0.13, rgb(65, 72, 95), rgb(95, 105, 135), lambda: self.show_screen('settings')),
            ('ВЫХОД ИЗ ИГРЫ', -0.24, rgb(135, 40, 45), rgb(185, 60, 65), application.quit),
        ]
        for label, by, col, hcol, action in menu_Actions:
            btn = Button(
                text=label, parent=self.main_menu_panel,
                scale=(0.50, 0.08), position=(-0.46, by), z=-0.01,
                color=col, highlight_color=hcol
            )
            btn.on_click = action

        # ------------------------------------------
        # 2. МЕНЮ ПОДКЛЮЧЕНИЯ К СЕТИ (MP CONNECT)
        # ------------------------------------------
        self.mp_panel = Entity(parent=camera.ui, enabled=False)
        Entity(parent=self.mp_panel, model='quad', scale=(0.76, 0.64), position=(-0.42, -0.04), z=0.02, color=rgb(14, 18, 30, 240))
        Entity(parent=self.mp_panel, model='quad', scale=(0.76, 0.006), position=(-0.42, 0.28), z=-0.01, color=color.cyan)

        Text(
            text='СЕТЕВАЯ ИГРА (LAN / КОД КОМНАТЫ)',
            parent=self.mp_panel, position=(-0.42, 0.23), z=-0.02,
            origin=(0, 0), scale=1.1, color=rgb(150, 225, 255)
        )

        self.btn_host = Button(
            text='СОЗДАТЬ КОМНАТУ (HOST)',
            parent=self.mp_panel, scale=(0.64, 0.075), position=(-0.42, 0.13), z=-0.01,
            color=rgb(35, 100, 68), highlight_color=rgb(50, 145, 95)
        )
        self.btn_host.on_click = self.action_host_room

        self.btn_code_box = Button(
            text='КОД: [ НАЖМИТЕ ДЛЯ ВВОДА ]',
            parent=self.mp_panel, scale=(0.64, 0.07), position=(-0.42, 0.03), z=-0.01,
            color=rgb(28, 36, 54), highlight_color=rgb(45, 60, 88)
        )
        self.btn_code_box.on_click = self.toggle_code_typing

        self.btn_join_code = Button(
            text='ПОДКЛЮЧИТЬСЯ ПО КОДУ',
            parent=self.mp_panel, scale=(0.31, 0.07), position=(-0.585, -0.065), z=-0.01,
            color=rgb(40, 85, 145), highlight_color=rgb(60, 120, 200)
        )
        self.btn_join_code.on_click = self.action_join_by_code

        self.btn_join_lan = Button(
            text='НАЙТИ В LAN (АВТО)',
            parent=self.mp_panel, scale=(0.31, 0.07), position=(-0.255, -0.065), z=-0.01,
            color=rgb(95, 55, 145), highlight_color=rgb(130, 80, 195)
        )
        self.btn_join_lan.on_click = self.action_join_lan

        self.net_status_text = Text(
            text=f'Ваш локальный IP: {self.net.host_ip}',
            parent=self.mp_panel, position=(-0.42, -0.16), z=-0.02,
            origin=(0, 0), scale=0.82, color=color.cyan
        )

        btn_mp_back = Button(
            text='<- НАЗАД В ГЛАВНОЕ МЕНЮ',
            parent=self.mp_panel, scale=(0.46, 0.065), position=(-0.42, -0.26), z=-0.01,
            color=rgb(60, 65, 82), highlight_color=rgb(85, 92, 115)
        )
        btn_mp_back.on_click = lambda: self.show_screen('main')

        # ------------------------------------------
        # 3. МЕНЮ НАСТРОЕК (SETTINGS)
        # ------------------------------------------
        self.settings_panel = Entity(parent=camera.ui, enabled=False)
        Entity(parent=self.settings_panel, model='quad', scale=(0.76, 0.64), position=(-0.42, -0.04), z=0.02, color=rgb(14, 18, 30, 240))
        Entity(parent=self.settings_panel, model='quad', scale=(0.76, 0.006), position=(-0.42, 0.28), z=-0.01, color=color.gold)

        Text(
            text='НАСТРОЙКИ ИГРЫ',
            parent=self.settings_panel, position=(-0.42, 0.23), z=-0.02,
            origin=(0, 0), scale=1.15, color=color.gold
        )

        self.lbl_sens = Text(text='', parent=self.settings_panel, position=(-0.74, 0.13), z=-0.02, scale=0.88, color=color.white)
        b_s_minus = Button(text='-', parent=self.settings_panel, scale=(0.07, 0.055), position=(-0.22, 0.12), z=-0.01, color=rgb(45, 55, 75))
        b_s_plus = Button(text='+', parent=self.settings_panel, scale=(0.07, 0.055), position=(-0.12, 0.12), z=-0.01, color=rgb(45, 55, 75))
        b_s_minus.on_click = lambda: self.change_setting('sensitivity', -5)
        b_s_plus.on_click = lambda: self.change_setting('sensitivity', 5)

        self.lbl_fov = Text(text='', parent=self.settings_panel, position=(-0.74, 0.03), z=-0.02, scale=0.88, color=color.white)
        b_f_minus = Button(text='-', parent=self.settings_panel, scale=(0.07, 0.055), position=(-0.22, 0.02), z=-0.01, color=rgb(45, 55, 75))
        b_f_plus = Button(text='+', parent=self.settings_panel, scale=(0.07, 0.055), position=(-0.12, 0.02), z=-0.01, color=rgb(45, 55, 75))
        b_f_minus.on_click = lambda: self.change_setting('fov', -5)
        b_f_plus.on_click = lambda: self.change_setting('fov', 5)

        self.lbl_fog = Text(text='', parent=self.settings_panel, position=(-0.74, -0.07), z=-0.02, scale=0.88, color=color.white)
        b_g_minus = Button(text='-', parent=self.settings_panel, scale=(0.07, 0.055), position=(-0.22, -0.08), z=-0.01, color=rgb(45, 55, 75))
        b_g_plus = Button(text='+', parent=self.settings_panel, scale=(0.07, 0.055), position=(-0.12, -0.08), z=-0.01, color=rgb(45, 55, 75))
        b_g_minus.on_click = lambda: self.change_setting('fog', -0.002)
        b_g_plus.on_click = lambda: self.change_setting('fog', 0.002)

        self.btn_fullscreen = Button(
            text='ПОЛНЫЙ ЭКРАН: ВЫКЛ',
            parent=self.settings_panel, scale=(0.48, 0.065), position=(-0.42, -0.17), z=-0.01,
            color=rgb(45, 65, 95), highlight_color=rgb(65, 95, 135)
        )
        self.btn_fullscreen.on_click = lambda: self.change_setting('fullscreen', 0)

        btn_set_back = Button(
            text='<- НАЗАД В ГЛАВНОЕ МЕНЮ',
            parent=self.settings_panel, scale=(0.46, 0.065), position=(-0.42, -0.27), z=-0.01,
            color=rgb(60, 65, 82), highlight_color=rgb(85, 92, 115)
        )
        btn_set_back.on_click = lambda: self.show_screen('main')
        self.refresh_settings_labels()

        # ------------------------------------------
        # 4. ЛОББИ ВЫБОРА ПЕРСОНАЖА (SINGLE & CO-OP)
        # ------------------------------------------
        self.lobby_panel = Entity(parent=camera.ui, enabled=False)

        # Иконки персонажей слева сверху (7 кнопок в ряд)
        Text(
            text='ВЫБЕРИТЕ ПЕРСОНАЖА [Клавиши 1 - 7]:',
            parent=self.lobby_panel, position=(-0.84, 0.355), z=-0.02,
            scale=0.82, color=rgb(170, 220, 255)
        )

        self.char_icon_Widgets = {}
        char_order = [
            ('commando', '1', 'CMD', rgb(235, 130, 35)),
            ('artificer', '2', 'ART', rgb(165, 65, 235)),
            ('huntress', '3', 'HNT', rgb(225, 50, 80)),
            ('buzz', '4', 'BUZ', rgb(115, 225, 65)),
            ('v1', '5', 'V1', rgb(55, 130, 245)),
            ('sol', '6', 'SOL', rgb(225, 45, 45)),
            ('gwen', '7', 'GWN', rgb(70, 200, 255)),
        ]
        for idx, (ckey, num_str, short_code, col) in enumerate(char_order):
            ix = -0.79 + idx * 0.106
            iy = 0.285
            border = Entity(
                parent=self.lobby_panel, model='quad',
                scale=(0.098, 0.082), position=(ix, iy), z=0.01, color=col
            )
            btn = Button(
                text='', parent=self.lobby_panel,
                scale=(0.088, 0.072), position=(ix, iy), z=-0.01,
                color=rgb(22, 28, 42, 245), highlight_color=col
            )
            btn.on_click = lambda k=ckey: self.select_lobby_character(k)
            # Отдельный Text на панели, чтобы шрифт всегда был идеально чётким
            lbl = Text(
                text=f"[{num_str}]\n{short_code}",
                parent=self.lobby_panel, position=(ix, iy), z=-0.03,
                origin=(0, 0), scale=0.78, color=color.white
            )
            self.char_icon_Widgets[ckey] = {'border': border, 'btn': btn, 'lbl': lbl, 'base_col': col}

        # Левая панель с описанием персонажа и его 4 навыков
        Entity(
            parent=self.lobby_panel, model='quad',
            scale=(0.76, 0.64), position=(-0.47, -0.095), z=0.02,
            color=rgb(12, 16, 28, 238)
        )
        self.lobby_char_line = Entity(
            parent=self.lobby_panel, model='quad',
            scale=(0.76, 0.006), position=(-0.47, 0.225), z=-0.01,
            color=color.orange
        )

        self.lobby_char_title = Text(
            text='', parent=self.lobby_panel, position=(-0.82, 0.20),
            z=-0.02, scale=1.25, color=color.orange
        )
        self.lobby_char_subtitle = Text(
            text='', parent=self.lobby_panel, position=(-0.82, 0.155),
            z=-0.02, scale=0.80, color=rgb(175, 210, 245)
        )
        self.lobby_char_stats = Text(
            text='', parent=self.lobby_panel, position=(-0.82, 0.11),
            z=-0.02, scale=0.78, color=color.gold
        )
        self.lobby_skills_text = Text(
            text='', parent=self.lobby_panel, position=(-0.82, 0.055),
            z=-0.02, scale=0.74, color=color.white
        )

        # Правая панель лобби (статус комнаты, список игроков, таймер и кнопка Старт/Готов)
        Entity(
            parent=self.lobby_panel, model='quad',
            scale=(0.54, 0.28), position=(0.58, 0.20), z=0.02,
            color=rgb(12, 16, 28, 225)
        )
        self.lobby_room_info = Text(
            text='РЕЖИМ: ОДИНОЧНАЯ ИГРА',
            parent=self.lobby_panel, position=(0.33, 0.315), z=-0.02,
            scale=0.82, color=color.lime
        )
        self.lobby_players_list = Text(
            text='', parent=self.lobby_panel, position=(0.33, 0.255),
            z=-0.02, scale=0.76, color=color.white
        )

        self.lobby_timer_text = Text(
            text='', parent=self.lobby_panel, position=(0.58, -0.25),
            z=-0.02, origin=(0, 0), scale=1.05, color=color.yellow
        )

        self.btn_lobby_ready = Button(
            text='НАЧАТЬ ЗАБЕГ (СТАРТ)',
            parent=self.lobby_panel, scale=(0.48, 0.085), position=(0.58, -0.34), z=-0.01,
            color=rgb(38, 120, 70), highlight_color=rgb(55, 165, 95)
        )
        self.btn_lobby_ready.on_click = self.action_lobby_ready

        self.btn_lobby_leave = Button(
            text='<- ПОКИНУТЬ ЛОББИ',
            parent=self.lobby_panel, scale=(0.32, 0.055), position=(0.58, -0.43), z=-0.01,
            color=rgb(85, 40, 48), highlight_color=rgb(125, 55, 65)
        )
        self.btn_lobby_leave.on_click = self.leave_lobby_to_main

        # ------------------------------------------
        # 5. БОЕВОЙ ИНТЕРФЕЙС (HUD)
        # ------------------------------------------
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
        self.banner_text = Text(text='', parent=camera.ui, position=(0, 0.19), z=-0.04, origin=(0, 0), scale=1.15, color=color.yellow)
        self.banner_timer = 0.0

        self.select_lobby_character(self.selected_char)

    # ==========================================
    # НАВИГАЦИЯ ПО ЭКРАНАМ МЕНЮ И НАСТРОЙКАМ
    # ==========================================
    def show_screen(self, screen_name):
        self.typing_code = False
        self.menu_state = screen_name
        self.header_panel.enabled = (screen_name != 'in_game')
        self.main_menu_panel.enabled = (screen_name == 'main')
        self.mp_panel.enabled = (screen_name == 'mp_connect')
        self.settings_panel.enabled = (screen_name == 'settings')
        self.lobby_panel.enabled = (screen_name == 'lobby')
        self.hud_panel.enabled = (screen_name == 'in_game')
        self.diorama_root.enabled = (screen_name != 'in_game')

        if screen_name != 'in_game':
            mouse.locked = False
            window.color = rgb(18, 20, 32)
            scene.fog_color = rgb(18, 20, 32)
            self.reset_menu_camera()
            self.refresh_remote_lobby_models()
            if screen_name == 'lobby':
                self.update_lobby_ui()

    def change_setting(self, key, delta):
        if key == 'sensitivity':
            self.settings['sensitivity'] = clamp(self.settings['sensitivity'] + delta, 10, 120)
        elif key == 'fov':
            self.settings['fov'] = clamp(self.settings['fov'] + delta, 65, 115)
            camera.fov = self.settings['fov']
        elif key == 'fog':
            self.settings['fog_density'] = clamp(round(self.settings['fog_density'] + delta, 3), 0.0, 0.025)
            scene.fog_density = self.settings['fog_density']
        elif key == 'fullscreen':
            self.settings['fullscreen'] = not self.settings['fullscreen']
            window.fullscreen = self.settings['fullscreen']
        self.refresh_settings_labels()

    def refresh_settings_labels(self):
        self.lbl_sens.text = f"Чувствительность мыши: {self.settings['sensitivity']}"
        self.lbl_fov.text = f"Угол обзора камеры (FOV): {self.settings['fov']}"
        self.lbl_fog.text = f"Плотность тумана: {self.settings['fog_density']:.3f}"
        fs_txt = "ВКЛ" if self.settings['fullscreen'] else "ВЫКЛ"
        self.btn_fullscreen.text = f"ПОЛНЫЙ ЭКРАН: {fs_txt}"

    # ==========================================
    # ЛОГИКА ЛОББИ, ВЫБОРА ГЕРОЯ И ТАЙМЕРА ГОТОВНОСТИ
    # ==========================================
    def open_singleplayer_lobby(self):
        self.net.stop_session()
        self.lobby_players.clear()
        self.my_ready = False
        self.lobby_countdown_active = False
        self.lobby_countdown = 60.0
        self.show_screen('lobby')

    def open_multiplayer_lobby(self):
        self.my_ready = False
        self.lobby_countdown_active = False
        self.lobby_countdown = 60.0
        self.show_screen('lobby')
        self.broadcast_lobby_state()

    def leave_lobby_to_main(self):
        self.net.stop_session()
        self.lobby_players.clear()
        self.my_ready = False
        self.lobby_countdown_active = False
        self.show_screen('main')

    def select_lobby_character(self, char_key):
        if char_key not in SURVIVOR_CLASSES:
            return
        self.selected_char = char_key
        cfg = SURVIVOR_CLASSES[char_key]

        # Подсветка выбранной иконки
        for k, w in self.char_icon_Widgets.items():
            if k == char_key:
                w['border'].color = color.white
                w['border'].scale = (0.104, 0.088)
                w['lbl'].color = color.yellow
            else:
                w['border'].color = w['base_col']
                w['border'].scale = (0.096, 0.080)
                w['lbl'].color = color.white

        # Обновление текста описания слева с аккуратным переносом строк
        self.lobby_char_line.color = cfg['body_color']
        self.lobby_char_title.text = cfg['name']
        self.lobby_char_title.color = cfg['body_color']
        self.lobby_char_subtitle.text = cfg['subtitle']
        self.lobby_char_stats.text = (
            f"HP: {cfg['hp']}   |   Скорость: {cfg['speed']}   |   "
            f"Урон: {cfg['damage']}   |   Атака: {cfg['fire_rate']}/с"
        )

        skill_blocks = []
        for sk_id in ('m1', 'm2', 'shift', 'r'):
            sk = cfg['skills'][sk_id]
            wrapped_desc = textwrap.fill(sk['desc'], width=46)
            skill_blocks.append(f"* {sk['name']} (КД: {sk['cd']}с)\n  {wrapped_desc}")
        self.lobby_skills_text.text = '\n\n'.join(skill_blocks)

        self.rebuild_local_lobby_model()
        self.broadcast_lobby_state()
        self.update_lobby_ui()

    def broadcast_lobby_state(self):
        if self.net.connected:
            self.net.broadcast({
                'type': 'lobby_state',
                'player_id': self.net.my_id,
                'char_key': self.selected_char,
                'ready': self.my_ready
            })

    def action_lobby_ready(self):
        # В одиночной игре стартуем мгновенно
        if not self.net.connected:
            self.start_run(self.selected_char)
            return

        # В мультиплеере голос "Готов" отменить нельзя!
        if self.my_ready:
            return

        self.my_ready = True
        self.broadcast_lobby_state()
        self.evaluate_lobby_countdown()
        self.update_lobby_ui()

    def evaluate_lobby_countdown(self):
        if not self.net.connected:
            return
        total_p = 1 + len(self.lobby_players)
        ready_p = (1 if self.my_ready else 0) + sum(1 for info in self.lobby_players.values() if info.get('ready'))

        if ready_p >= 1 and not self.lobby_countdown_active:
            self.lobby_countdown_active = True
            self.lobby_countdown = 60.0

        if ready_p >= total_p and self.lobby_countdown_active:
            self.lobby_countdown = min(self.lobby_countdown, 3.0)

    def update_lobby_ui(self):
        if self.menu_state != 'lobby':
            return

        if not self.net.connected:
            self.lobby_room_info.text = "РЕЖИМ: ОДИНОЧНАЯ ИГРА"
            self.lobby_room_info.color = color.cyan
            self.lobby_players_list.text = (
                f"Выживший: {SURVIVOR_CLASSES[self.selected_char]['name']}\n"
                f"Нажмите кнопку ниже для старта забега."
            )
            self.lobby_timer_text.text = ""
            self.btn_lobby_ready.text = "НАЧАТЬ ЗАБЕГ (СТАРТ)"
            self.btn_lobby_ready.color = rgb(38, 120, 70)
        else:
            role_str = "HOST" if self.net.mode == 'host' else "CLIENT"
            self.lobby_room_info.text = f"КОМНАТА: {self.net.room_code}  ({role_str})"
            self.lobby_room_info.color = color.lime

            lines = []
            my_rdy_str = "ГОТОВ ✓" if self.my_ready else "НЕ ГОТОВ"
            lines.append(f"• ВЫ [{self.net.my_id.upper()}]: {SURVIVOR_CLASSES[self.selected_char]['name']} — [{my_rdy_str}]")
            for pid, info in sorted(self.lobby_players.items()):
                ck = info.get('char_key', 'commando')
                cname = SURVIVOR_CLASSES.get(ck, SURVIVOR_CLASSES['commando'])['name']
                r_str = "ГОТОВ ✓" if info.get('ready') else "НЕ ГОТОВ"
                lines.append(f"• ИГРОК [{pid.upper()}]: {cname} — [{r_str}]")
            self.lobby_players_list.text = '\n'.join(lines)

            total_p = 1 + len(self.lobby_players)
            ready_p = (1 if self.my_ready else 0) + sum(1 for info in self.lobby_players.values() if info.get('ready'))

            if self.lobby_countdown_active:
                if ready_p >= total_p:
                    self.lobby_timer_text.text = f"ВСЕ ГОТОВЫ! СТАРТ ЧЕРЕЗ: {max(0.0, self.lobby_countdown):.1f} СЕК."
                    self.lobby_timer_text.color = color.lime
                else:
                    self.lobby_timer_text.text = f"ДО СТАРТА: {max(0.0, self.lobby_countdown):.1f} СЕК.  (Готовы: {ready_p}/{total_p})"
                    self.lobby_timer_text.color = color.yellow
            else:
                self.lobby_timer_text.text = f"Ожидание первого голоса «Готов» ({ready_p}/{total_p})"
                self.lobby_timer_text.color = rgb(180, 200, 230)

            if self.my_ready:
                self.btn_lobby_ready.text = "ВЫ ГОТОВЫ ✓ (ГОЛОС ПРИНЯТ)"
                self.btn_lobby_ready.color = rgb(55, 85, 65)
                self.btn_lobby_ready.highlight_color = rgb(55, 85, 65)
            else:
                self.btn_lobby_ready.text = "ГОТОВ К БОЮ! [ГОЛОСОВАТЬ]"
                self.btn_lobby_ready.color = rgb(38, 120, 70)
                self.btn_lobby_ready.highlight_color = rgb(55, 165, 95)

    # ==========================================
    # ДЕЙСТВИЯ ПОДКЛЮЧЕНИЯ К СЕТИ
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
        self.lobby_players.clear()
        ok, info = self.net.host_room()
        if ok:
            self.open_multiplayer_lobby()
            self.show_banner(f"КОМНАТА СОЗДАНА! КОД: {info}", color.lime, 3.5)
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
        self.lobby_players.clear()
        ok, info = self.net.join_by_code(self.room_code_input)
        if ok:
            self.open_multiplayer_lobby()
        else:
            self.net_status_text.text = info
            self.net_status_text.color = color.red

    def action_join_lan(self):
        self.typing_code = False
        self.refresh_code_button()
        self.lobby_players.clear()
        ok, info = self.net.join_lan_auto()
        if ok:
            self.room_code_input = info
            self.refresh_code_button()
            self.open_multiplayer_lobby()
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

    # ==========================================
    # СТАРТ ЗАБЕГА И УПРАВЛЕНИЕ ЭТАПАМИ
    # ==========================================
    def start_run(self, char_key=None, seed=None, from_network=False):
        chosen_char = char_key if char_key in SURVIVOR_CLASSES else self.selected_char
        self.selected_char = chosen_char

        self.show_screen('in_game')
        mouse.locked = True

        if is_valid(self.player):
            destroy(self.player)

        if seed is not None:
            self.stage_seed = seed
        elif self.net.mode != 'client':
            self.stage = 1
            self.stage_seed = random.randint(1000, 999999)

        self.stage = 1
        self.elapsed_time = 0.0
        self.player = Survivor(chosen_char)
        self.generate_stage(seed=self.stage_seed)
        self.running = True

        if self.net.connected and self.net.mode == 'host' and not from_network:
            self.net.broadcast({
                'type': 'lobby_start_run',
                'stage': self.stage,
                'seed': self.stage_seed
            })

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

        for e in list(self.enemies):
            if is_valid(e):
                destroy(e)
        self.enemies.clear()
        for obj in list(self.stage_entities):
            if obj and not obj.is_empty():
                destroy(obj)
        self.stage_entities.clear()
        self.obstacles.clear()

        self.my_ready = False
        self.lobby_countdown_active = False
        self.lobby_countdown = 60.0
        for pinfo in self.lobby_players.values():
            pinfo['ready'] = False

        self.show_screen('lobby')
        self.broadcast_lobby_state()
        self.show_banner('ВЫ ПОГИБЛИ! ПОДГОТОВЬТЕСЬ К НОВОМУ ЗАБЕГУ В ЛОББИ', color.red, 4.5)

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
                self.broadcast_lobby_state()
                self.update_lobby_ui()

            elif mtype == 'client_joined':
                pid = msg.get('player_id')
                if pid and pid != self.net.my_id:
                    self.lobby_players.setdefault(pid, {'char_key': 'commando', 'ready': False})
                self.show_banner(f"ИГРОК [{str(pid).upper()}] ВОШЁЛ В ЛОББИ!", color.cyan, 3.0)
                self.broadcast_lobby_state()
                if self.net.mode == 'host' and self.lobby_countdown_active:
                    self.net.broadcast({
                        'type': 'lobby_timer_sync',
                        'active': self.lobby_countdown_active,
                        'countdown': round(self.lobby_countdown, 2)
                    })
                if self.running and self.net.mode == 'host':
                    self.net.broadcast({'type': 'lobby_start_run', 'stage': self.stage, 'seed': self.stage_seed})
                self.refresh_remote_lobby_models()
                self.update_lobby_ui()

            elif mtype == 'player_left':
                pid = msg.get('player_id')
                self.lobby_players.pop(pid, None)
                if pid in self.remote_players:
                    destroy(self.remote_players.pop(pid))
                self.show_banner(f"ИГРОК [{str(pid).upper()}] ПОКИНУЛ ИГРУ", color.orange, 2.5)
                self.evaluate_lobby_countdown()
                self.refresh_remote_lobby_models()
                self.update_lobby_ui()

            elif mtype == 'disconnected':
                self.lobby_players.clear()
                if self.running:
                    self.on_player_death()
                self.show_screen('main')
                self.show_banner("СОЕДИНЕНИЕ С ХОСТОМ ПОТЕРЯНО", color.red, 3.5)

            elif mtype == 'lobby_state':
                pid = msg.get('player_id')
                if not pid or pid == self.net.my_id:
                    continue
                is_new_peer = pid not in self.lobby_players
                self.lobby_players[pid] = {
                    'char_key': msg.get('char_key', 'commando'),
                    'ready': bool(msg.get('ready', False))
                }
                if is_new_peer:
                    self.broadcast_lobby_state()
                self.evaluate_lobby_countdown()
                self.refresh_remote_lobby_models()
                self.update_lobby_ui()

            elif mtype == 'lobby_timer_sync':
                if self.net.mode == 'client':
                    self.lobby_countdown_active = bool(msg.get('active', False))
                    self.lobby_countdown = float(msg.get('countdown', self.lobby_countdown))
                    self.update_lobby_ui()

            elif mtype == 'lobby_start_run':
                # Каждый игрок начинает забег на СВОЁМ выбранном в лобби персонаже!
                self.stage = msg.get('stage', 1)
                self.stage_seed = msg.get('seed', 1001)
                if not self.running:
                    self.start_run(self.selected_char, seed=self.stage_seed, from_network=True)

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
                net_col_map = {
                    'cyan': color.cyan,
                    'commando': color.yellow,
                    'artificer': color.magenta,
                    'huntress': rgb(255, 80, 100),
                    'buzz': rgb(110, 255, 80),
                    'v1': rgb(255, 230, 50),
                    'sol': rgb(255, 110, 25),
                    'gwen': rgb(95, 225, 255),
                }
                p_col = net_col_map.get(col_tag, color.cyan)
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

        if self.banner_timer > 0:
            self.banner_timer -= time.dt
            if self.banner_timer <= 0:
                self.banner_text.text = ''

        # Логика вращения подиума и отсчёта времени в лобби
        if not self.running:
            t = time.time()
            self.local_preview_actor.rotation_y += 22 * time.dt
            if self.local_preview_parts and self.local_preview_parts.get('halo'):
                self.local_preview_parts['halo'].rotation_z += 90 * time.dt

            for slot in self.remote_pedestals:
                if slot['pedestal'].enabled:
                    slot['actor'].rotation_y -= 18 * time.dt
                    if slot['parts'] and slot['parts'].get('halo'):
                        slot['parts']['halo'].rotation_z += 90 * time.dt

            self.menu_crystal.rotation_y += 55 * time.dt
            self.menu_crystal.y = 3.3 + math.sin(t * 2.5) * 0.18

            if self.menu_state == 'lobby' and self.net.connected and self.lobby_countdown_active:
                self.lobby_countdown = max(0.0, self.lobby_countdown - time.dt)
                self.update_lobby_ui()

                if self.net.mode == 'host':
                    self.lobby_sync_timer -= time.dt
                    if self.lobby_sync_timer <= 0:
                        self.lobby_sync_timer = 0.5
                        self.net.broadcast({
                            'type': 'lobby_timer_sync',
                            'active': True,
                            'countdown': round(self.lobby_countdown, 2)
                        })
                    if self.lobby_countdown <= 0.0:
                        self.lobby_countdown_active = False
                        self.start_run(self.selected_char)
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