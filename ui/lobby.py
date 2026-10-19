from ursina import *
import textwrap
from config import rgb, SURVIVOR_CLASSES

class LobbyMixin:
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

        for k, w in self.char_icon_Widgets.items():
            if k == char_key:
                w['border'].color = color.white
                w['border'].scale = (0.079, 0.084)
                w['lbl'].color = color.yellow
            else:
                w['border'].color = w['base_col']
                w['border'].scale = (0.073, 0.078)
                w['lbl'].color = color.white

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
        if not self.net.connected:
            self.start_run(self.selected_char)
            return

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

