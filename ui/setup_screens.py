from ursina import *
import textwrap
from config import (
    rgb, is_valid, clear_children, ITEM_POOL, SURVIVOR_CLASSES,
    MONSTER_LOG, BOSS_TYPES, STAGE_PALETTES, ACHIEVEMENTS, PROGRESS
)
from data.stages import SPECIAL_PALETTES


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
            ('ОДИНОЧНАЯ ИГРА', 0.11, rgb(38, 105, 70), rgb(55, 150, 95), self.open_singleplayer_lobby),
            ('СЕТЕВАЯ ИГРА (CO-OP)', 0.02, rgb(40, 85, 145), rgb(60, 125, 205), lambda: self.show_screen('mp_connect')),
            ('ЖУРНАЛ (LOGBOOK)', -0.07, rgb(125, 75, 165), rgb(165, 105, 215), self.open_logbook),
            ('НАСТРОЙКИ', -0.16, rgb(65, 72, 95), rgb(95, 105, 135), lambda: self.show_screen('settings')),
            ('ВЫХОД ИЗ ИГРЫ', -0.25, rgb(135, 40, 45), rgb(185, 60, 65), application.quit),
        ]
        for label, by, col, hcol, action in menu_Actions:
            btn = Button(
                text=label, parent=self.main_menu_panel,
                scale=(0.50, 0.072), position=(-0.46, by), z=-0.01,
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
        # 4. ЛОББИ ВЫБОРА ПЕРСОНАЖА (14 ВЫЖИВШИХ)
        # ------------------------------------------
        self.lobby_panel = Entity(parent=camera.ui, enabled=False)

        Text(
            text='ВЫБЕРИТЕ ВЫЖИВШЕГО [Клавиши 1-9, 0, -, =, [, ]]:',
            parent=self.lobby_panel, position=(-0.84, 0.365), z=-0.02,
            scale=0.80, color=rgb(170, 220, 255)
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
            ('enforcer', '8', 'ENF', rgb(85, 155, 245)),
            ('scout', '9', 'SCT', rgb(245, 185, 40)),
            ('m4a1', '0', 'M4', rgb(85, 235, 125)),
            ('medic', '-', 'MED', rgb(235, 55, 65)),
            ('aigis', '=', 'AIG', rgb(245, 205, 65)),
            ('reimu', '[', 'RMU', rgb(235, 45, 60)),
            ('mindustry', ']', 'MND', rgb(255, 190, 45)),
        ]
        for idx, (ckey, num_str, short_code, col) in enumerate(char_order):
            row = idx // 7
            col_idx = idx % 7
            ix = -0.80 + col_idx * 0.108
            iy = 0.312 - row * 0.064
            border = Entity(
                parent=self.lobby_panel, model='quad',
                scale=(0.098, 0.056), position=(ix, iy), z=0.01, color=col
            )
            btn = Button(
                text='', parent=self.lobby_panel,
                scale=(0.090, 0.048), position=(ix, iy), z=-0.01,
                color=rgb(22, 28, 42, 245), highlight_color=col
            )
            btn.on_click = lambda k=ckey: self.select_lobby_character(k)
            lbl = Text(
                text=f"[{num_str}] {short_code}",
                parent=self.lobby_panel, position=(ix, iy), z=-0.03,
                origin=(0, 0), scale=0.62, color=color.white
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

        Text(
            text='[3D-ОСМОТР: Зажмите ЛКМ/ПКМ и двигайте мышь | Колёсико — Зум | Q/E — Поворот]',
            parent=self.lobby_panel, position=(0.38, -0.19), z=-0.02,
            origin=(0, 0), scale=0.66, color=rgb(155, 215, 255)
        )

        # ------------------------------------------
        # 4.5. ЖУРНАЛ ВЫЖИВШЕГО (LOGBOOK)
        # ------------------------------------------
        self.logbook_panel = Entity(parent=camera.ui, enabled=False)
        self.logbook_category = 'items'
        self.logbook_page = 0
        self.logbook_selected_key = 'syringe'

        # Вкладки категорий сверху
        self.logbook_tab_buttons = {}
        log_tabs = [
            ('items', 'АРТЕФАКТЫ', -0.68),
            ('survivors', 'ПЕРСОНАЖИ', -0.44),
            ('monsters', 'ВРАГИ', -0.20),
            ('bosses', 'БОССЫ', 0.04),
            ('stages', 'ЛОКАЦИИ', 0.28),
            ('achievements', 'ДОСТИЖЕНИЯ', 0.52),
        ]
        for cat_id, cat_title, tx in log_tabs:
            tbtn = Button(
                text=cat_title, parent=self.logbook_panel,
                scale=(0.22, 0.052), position=(tx, 0.335), z=-0.01,
                color=rgb(32, 40, 62), highlight_color=rgb(65, 95, 145)
            )
            tbtn.on_click = lambda c=cat_id: self.switch_logbook_category(c)
            self.logbook_tab_buttons[cat_id] = tbtn

        # Левая панель сетки записей и описания
        Entity(
            parent=self.logbook_panel, model='quad',
            scale=(0.82, 0.72), position=(-0.45, -0.065), z=0.02,
            color=rgb(12, 16, 28, 240)
        )
        self.logbook_stats_header = Text(
            text='', parent=self.logbook_panel, position=(-0.83, 0.275),
            z=-0.02, scale=0.72, color=color.gold
        )

        self.logbook_grid_root = Entity(parent=self.logbook_panel)

        self.btn_log_prev = Button(
            text='<- ПРЕД.', parent=self.logbook_panel,
            scale=(0.16, 0.042), position=(-0.65, -0.115), z=-0.01,
            color=rgb(40, 52, 78), highlight_color=rgb(65, 85, 120)
        )
        self.btn_log_prev.on_click = lambda: self.change_logbook_page(-1)

        self.logbook_page_text = Text(
            text='Стр. 1/1', parent=self.logbook_panel,
            position=(-0.45, -0.115), z=-0.02, origin=(0, 0), scale=0.72, color=color.white
        )

        self.btn_log_next = Button(
            text='СЛЕД. ->', parent=self.logbook_panel,
            scale=(0.16, 0.042), position=(-0.25, -0.115), z=-0.01,
            color=rgb(40, 52, 78), highlight_color=rgb(65, 85, 120)
        )
        self.btn_log_next.on_click = lambda: self.change_logbook_page(1)

        # Карточка подробного описания выбранного объекта
        Entity(
            parent=self.logbook_panel, model='quad',
            scale=(0.78, 0.24), position=(-0.45, -0.28), z=0.01,
            color=rgb(18, 24, 40, 245)
        )
        self.logbook_detail_line = Entity(
            parent=self.logbook_panel, model='quad',
            scale=(0.78, 0.005), position=(-0.45, -0.16), z=-0.01,
            color=color.cyan
        )
        self.logbook_entry_title = Text(
            text='', parent=self.logbook_panel, position=(-0.82, -0.18),
            z=-0.02, scale=1.02, color=color.cyan
        )
        self.logbook_entry_sub = Text(
            text='', parent=self.logbook_panel, position=(-0.82, -0.22),
            z=-0.02, scale=0.75, color=color.gold
        )
        self.logbook_entry_desc = Text(
            text='', parent=self.logbook_panel, position=(-0.82, -0.26),
            z=-0.02, scale=0.74, color=color.white
        )

        # Правая панель управления 3D-осмотром
        Text(
            text='[Зажмите ЛКМ/ПКМ и двигайте мышь для осмотра со всех сторон | Колёсико — Зум]',
            parent=self.logbook_panel, position=(0.38, -0.27), z=-0.02,
            origin=(0, 0), scale=0.66, color=rgb(155, 215, 255)
        )
        btn_reset_view = Button(
            text='СБРОСИТЬ РАКУРС', parent=self.logbook_panel,
            scale=(0.24, 0.05), position=(0.24, -0.34), z=-0.01,
            color=rgb(42, 62, 92), highlight_color=rgb(65, 95, 140)
        )
        btn_reset_view.on_click = self.reset_preview_orientation

        btn_unlock_all = Button(
            text='ОТКРЫТЬ ВСЁ В ЖУРНАЛЕ', parent=self.logbook_panel,
            scale=(0.28, 0.05), position=(0.54, -0.34), z=-0.01,
            color=rgb(95, 65, 30), highlight_color=rgb(140, 95, 45)
        )
        btn_unlock_all.on_click = self.action_unlock_all_logbook

        btn_log_back = Button(
            text='<- НАЗАД В ГЛАВНОЕ МЕНЮ', parent=self.logbook_panel,
            scale=(0.44, 0.06), position=(0.38, -0.42), z=-0.01,
            color=rgb(60, 65, 82), highlight_color=rgb(85, 92, 115)
        )
        btn_log_back.on_click = lambda: self.show_screen('main')

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

    def open_logbook(self):
        self.show_screen('logbook')
        self.switch_logbook_category(self.logbook_category)

    def action_unlock_all_logbook(self):
        PROGRESS.unlock_all()
        self.switch_logbook_category(self.logbook_category)
        self.show_banner('ВСЕ ЗАПИСИ ЖУРНАЛА ОТКРЫТЫ!', color.gold, 2.5)

    def _get_logbook_entries(self, category):
        if category == 'items':
            return [(k, v['short'], v['color'], k in PROGRESS.unlocked_items) for k, v in ITEM_POOL.items()]
        elif category == 'survivors':
            return [(k, v['icon'], v['body_color'], True) for k, v in SURVIVOR_CLASSES.items()]
        elif category == 'monsters':
            reg_keys = [k for k in MONSTER_LOG.keys() if k not in BOSS_TYPES and k != 'mithrix']
            return [(k, k[:5].upper(), rgb(255, 140, 60), True) for k in reg_keys]
        elif category == 'bosses':
            boss_keys = [k for k in MONSTER_LOG.keys() if k in BOSS_TYPES or k == 'mithrix']
            return [(k, k[:5].upper(), color.cyan if k == 'mithrix' else color.red, True) for k in boss_keys]
        elif category == 'stages':
            all_st = list(STAGE_PALETTES) + [SPECIAL_PALETTES['bazaar'], SPECIAL_PALETTES['moon']]
            return [(p['id'], p['id'][:5].upper(), p['accent'], p['id'] in PROGRESS.discovered_stages) for p in all_st]
        elif category == 'achievements':
            return [(k, 'ACH', color.gold, k in PROGRESS.unlocked_achievements) for k in ACHIEVEMENTS.keys()]
        return []

    def switch_logbook_category(self, category):
        self.logbook_category = category
        self.logbook_page = 0
        for cid, btn in self.logbook_tab_buttons.items():
            btn.color = rgb(75, 115, 185) if cid == category else rgb(32, 40, 62)

        entries = self._get_logbook_entries(category)
        if entries:
            self.select_logbook_entry(entries[0][0])
        self.refresh_logbook_grid()

    def change_logbook_page(self, delta):
        entries = self._get_logbook_entries(self.logbook_category)
        per_page = 18
        max_page = max(0, (len(entries) - 1) // per_page)
        self.logbook_page = clamp(self.logbook_page + delta, 0, max_page)
        self.refresh_logbook_grid()

    def refresh_logbook_grid(self):
        clear_children(self.logbook_grid_root)
        entries = self._get_logbook_entries(self.logbook_category)
        per_page = 18
        total_pages = max(1, (len(entries) - 1) // per_page + 1)
        self.logbook_page = clamp(self.logbook_page, 0, total_pages - 1)
        self.logbook_page_text.text = f"Стр. {self.logbook_page + 1} / {total_pages}"

        unlocked_cnt = sum(1 for _, _, _, u in entries if u)
        self.logbook_stats_header.text = (
            f"Открыто в разделе: {unlocked_cnt}/{len(entries)}   |   "
            f"Всего убийств: {PROGRESS.kills}   |   Боссов повержено: {PROGRESS.boss_kills}"
        )

        page_slice = entries[self.logbook_page * per_page:(self.logbook_page + 1) * per_page]
        for idx, (ekey, short_lbl, col, is_unlocked) in enumerate(page_slice):
            r = idx // 6
            c = idx % 6
            bx = -0.765 + c * 0.125
            by = 0.205 - r * 0.102
            is_sel = (ekey == self.logbook_selected_key)

            border_col = color.white if is_sel else (col if is_unlocked else rgb(60, 65, 80))
            Entity(
                parent=self.logbook_grid_root, model='quad',
                scale=(0.114, 0.088) if is_sel else (0.108, 0.082),
                position=(bx, by), z=0.01, color=border_col
            )
            btn = Button(
                text='', parent=self.logbook_grid_root,
                scale=(0.100, 0.074), position=(bx, by), z=-0.01,
                color=rgb(24, 32, 48) if is_unlocked else rgb(16, 18, 26),
                highlight_color=col
            )
            btn.on_click = lambda k=ekey: self.select_logbook_entry(k)
            Text(
                text=short_lbl if is_unlocked else '???',
                parent=self.logbook_grid_root, position=(bx, by), z=-0.02,
                origin=(0, 0), scale=0.66, color=col if is_unlocked else color.gray
            )

    def select_logbook_entry(self, entry_key):
        self.logbook_selected_key = entry_key
        cat = self.logbook_category
        self.reset_preview_orientation()
        self.build_logbook_preview(cat, entry_key)
        self.refresh_logbook_grid()

        if cat == 'items':
            info = ITEM_POOL[entry_key]
            self.logbook_detail_line.color = info['color']
            self.logbook_entry_title.text = info['name']
            self.logbook_entry_title.color = info['color']
            self.logbook_entry_sub.text = f"Редкость: {info['tier_name']}   |   Код: [{info['short']}]"
            self.logbook_entry_desc.text = textwrap.fill(info['desc'], width=58)

        elif cat == 'survivors':
            cfg = SURVIVOR_CLASSES[entry_key]
            self.logbook_detail_line.color = cfg['body_color']
            self.logbook_entry_title.text = f"{cfg['name']} — {cfg['subtitle']}"
            self.logbook_entry_title.color = cfg['body_color']
            self.logbook_entry_sub.text = f"HP: {cfg['hp']}  |  Скорость: {cfg['speed']}  |  Урон: {cfg['damage']}  |  Атака: {cfg['fire_rate']}/с"
            sk_names = " / ".join(cfg['skills'][s]['name'] for s in ('m1', 'm2', 'shift', 'r'))
            self.logbook_entry_desc.text = textwrap.fill(f"Навыки: {sk_names}", width=58)

        elif cat in ('monsters', 'bosses'):
            m = MONSTER_LOG[entry_key]
            col = color.cyan if entry_key == 'mithrix' else (color.red if cat == 'bosses' else rgb(255, 145, 60))
            self.logbook_detail_line.color = col
            self.logbook_entry_title.text = m['name']
            self.logbook_entry_title.color = col
            self.logbook_entry_sub.text = f"Базовое HP: {m['hp']}   |   Базовый урон: {m['damage']}"
            self.logbook_entry_desc.text = textwrap.fill(m['desc'], width=58)

        elif cat == 'stages':
            all_st = {p['id']: p for p in STAGE_PALETTES}
            all_st.update(SPECIAL_PALETTES)
            st = all_st[entry_key]
            disc = entry_key in PROGRESS.discovered_stages
            self.logbook_detail_line.color = st['accent']
            self.logbook_entry_title.text = st['name']
            self.logbook_entry_title.color = st['accent']
            self.logbook_entry_sub.text = "Статус: ИССЛЕДОВАНА ✓" if disc else "Статус: ЕЩЁ НЕ ПОСЕЩЕНА"
            self.logbook_entry_desc.text = textwrap.fill(st['desc'], width=58)

        elif cat == 'achievements':
            ach = ACHIEVEMENTS[entry_key]
            unlocked = entry_key in PROGRESS.unlocked_achievements
            col = color.lime if unlocked else color.orange
            self.logbook_detail_line.color = col
            self.logbook_entry_title.text = ach['name']
            self.logbook_entry_title.color = col
            self.logbook_entry_sub.text = "Статус: ВЫПОЛНЕНО ✓" if unlocked else "Статус: НЕ ВЫПОЛНЕНО"
            self.logbook_entry_desc.text = textwrap.fill(f"{ach['desc']} ({ach['reward_text']})", width=58)

    def show_screen(self, screen_name):
        self.typing_code = False
        self.menu_state = screen_name
        self.header_panel.enabled = (screen_name != 'in_game')
        self.main_menu_panel.enabled = (screen_name == 'main')
        self.mp_panel.enabled = (screen_name == 'mp_connect')
        self.settings_panel.enabled = (screen_name == 'settings')
        self.lobby_panel.enabled = (screen_name == 'lobby')
        self.logbook_panel.enabled = (screen_name == 'logbook')
        self.hud_panel.enabled = (screen_name == 'in_game')
        self.diorama_root.enabled = (screen_name != 'in_game')

        if screen_name != 'in_game':
            mouse.locked = False
            window.color = rgb(18, 20, 32)
            scene.fog_color = rgb(18, 20, 32)
            self.reset_menu_camera()
            self.refresh_remote_lobby_models()
            if screen_name in ('main', 'lobby'):
                self.reset_preview_orientation()
                self.rebuild_local_lobby_model()
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