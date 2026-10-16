from ursina import *
from config import rgb, is_valid, clear_children, ITEM_POOL

class SetupScreensMixin:
    def setup_ui(self):
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
            lbl = Text(
                text=f"[{num_str}]\n{short_code}",
                parent=self.lobby_panel, position=(ix, iy), z=-0.03,
                origin=(0, 0), scale=0.78, color=color.white
            )
            self.char_icon_Widgets[ckey] = {'border': border, 'btn': btn, 'lbl': lbl, 'base_col': col}

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
        # 5. БОЕВОЙ ИНТЕРФЕЙС (HUD С ДИНАМИЧЕСКИМ ИНВЕНТАРЁМ)
        # ------------------------------------------
        self.hud_panel = Entity(parent=camera.ui, enabled=False)
        self.crosshair = Text(text='+', parent=self.hud_panel, origin=(0, 0), z=-0.02, scale=1.6, color=color.cyan)

        self.top_bar_bg = Entity(
            parent=self.hud_panel, model='quad', scale=(1.10, 0.115),
            position=(-0.21, 0.425), z=0.02, color=rgb(14, 18, 28, 210)
        )
        self.hud_room_label = Text(
            text='INVENTORY  [HOLD TAB FOR DETAILS]',
            parent=self.hud_panel, position=(-0.74, 0.472), z=-0.02,
            scale=0.72, color=rgb(175, 195, 225)
        )
        self.empty_inv_hint = Text(
            text='Нет собранных предметов — ищите сундуки на карте [E]',
            parent=self.hud_panel, position=(-0.74, 0.415), z=-0.02,
            scale=0.76, color=rgb(115, 130, 155)
        )
        self.dynamic_inv_root = Entity(parent=self.hud_panel)

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
            z=-0.02, origin=(0, 0), scale=0.88, color=color.white
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
        Entity(parent=self.tab_panel, model='quad', scale=(1.15, 0.68), position=(0, 0), z=0.01, color=rgb(12, 16, 26, 242))
        self.tab_text = Text(text='', parent=self.tab_panel, position=(-0.53, 0.29), z=-0.02, scale=0.78, color=color.white)

        # Баннер уведомлений
        self.banner_text = Text(text='', parent=camera.ui, position=(0, 0.19), z=-0.04, origin=(0, 0), scale=1.15, color=color.yellow)
        self.banner_timer = 0.0

        self.select_lobby_character(self.selected_char)

    def refresh_inventory_hud(self):
        clear_children(self.dynamic_inv_root)
        if not is_valid(self.player):
            self.empty_inv_hint.enabled = True
            return

        owned = [k for k in self.player.item_order if self.player.items.get(k, 0) > 0]
        if not owned:
            self.empty_inv_hint.enabled = True
            self.top_bar_bg.scale_y = 0.115
            self.top_bar_bg.y = 0.425
            return

        self.empty_inv_hint.enabled = False
        per_row = 12
        rows = (len(owned) - 1) // per_row + 1
        self.top_bar_bg.scale_y = 0.055 + rows * 0.054
        self.top_bar_bg.y = 0.482 - self.top_bar_bg.scale_y * 0.5

        for idx, k in enumerate(owned):
            info = ITEM_POOL[k]
            cnt = self.player.items[k]
            r = idx // per_row
            c = idx % per_row
            sx = -0.715 + c * 0.088
            sy = 0.422 - r * 0.052

            Entity(
                parent=self.dynamic_inv_root, model='quad', scale=(0.082, 0.046),
                position=(sx, sy), z=0.01, color=rgb(38, 48, 70, 235)
            )
            Entity(
                parent=self.dynamic_inv_root, model='quad', scale=(0.082, 0.007),
                position=(sx, sy + 0.019), z=-0.01, color=info['color']
            )
            Text(
                text=info['short'], parent=self.dynamic_inv_root,
                position=(sx, sy + 0.005), z=-0.02, origin=(0, 0),
                scale=0.64, color=info['color']
            )
            Text(
                text=f"x{cnt}", parent=self.dynamic_inv_root,
                position=(sx, sy - 0.012), z=-0.02, origin=(0, 0),
                scale=0.68, color=color.white
            )

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

