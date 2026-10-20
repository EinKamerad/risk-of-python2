from ursina import *
import math
import random
from config import (
    ctx, rgb, is_valid, SETTINGS, ITEM_POOL, roll_item_from_pool,
    ACHIEVEMENTS, BOSS_TYPES, BOSS_TITLES, SURVIVOR_CLASSES, PROGRESS
)
from entities import Survivor, Enemy, VisualFX
from world import ItemDrop, build_stage_world
from world.lunar import EscapeShip, LunarEscapePad, COLOSSEUM_Y
from network import NetworkManager
from core.physics import PhysicsMixin
from ui.diorama import DioramaMixin
from ui.setup_screens import SetupScreensMixin
from ui.lobby import LobbyMixin
from ui.net_handler import NetHandlerMixin


class GameManager(Entity, PhysicsMixin, DioramaMixin, SetupScreensMixin, LobbyMixin, NetHandlerMixin):
    def __init__(self):
        super().__init__()
        ctx.game = self
        self.settings = dict(SETTINGS)
        self.net = NetworkManager()

        self.running = False
        self.menu_state = 'main'
        self.selected_char = 'commando'

        self.my_ready = False
        self.lobby_players = {}
        self.lobby_countdown_active = False
        self.lobby_countdown = 60.0
        self.lobby_sync_timer = 0.0

        self.stage = 1
        self.stage_seed = 1001
        self.stage_name = ''
        self.special_mode = None   # None, 'bazaar', 'moon'
        self.world_bound = 58.0
        self.lunar_coins = 5       # Стартовый запас Лунных Монет
        self.blue_orb_spawned = False
        self.moon_pillars_done = 0
        self.mithrix_spawned = False
        self.moon_detonation_timer = 0.0

        self.elapsed_time = 0.0
        self.director_credits = 0.0
        self.spawn_timer = 1.5
        self.active_boss = None

        self.player = None
        self.remote_players = {}
        self.enemies = []
        self.stage_entities = []
        self.obstacles = []
        self.sky_platforms = []
        self.teleporter = None

        self.typing_code = False
        self.room_code_input = ""

        self.setup_lighting()
        self.setup_menu_diorama()
        self.setup_ui()
        self.show_screen('main')

    def setup_lighting(self):
        DirectionalLight(y=12, z=6, rotation=(45, -35, 0), shadows=False)
        AmbientLight(color=rgb(145, 150, 180, 255))

    def unlock_achievement(self, ach_key):
        if ach_key in ACHIEVEMENTS and ach_key not in PROGRESS.unlocked_achievements:
            PROGRESS.unlocked_achievements.append(ach_key)
            ach = ACHIEVEMENTS[ach_key]
            item_k = ach.get('unlocks_item')
            if item_k and item_k not in PROGRESS.unlocked_items:
                PROGRESS.unlocked_items.append(item_k)
            PROGRESS.save()
            self.show_banner(f"ДОСТИЖЕНИЕ: {ach['name']} ({ach['reward_text']})", color.gold, 4.0)

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
        self.special_mode = None
        self.moon_detonation_timer = 0.0
        self.elapsed_time = 0.0
        self.player = Survivor(chosen_char)
        self.refresh_inventory_hud()
        self.generate_stage(seed=self.stage_seed)
        self.running = True

        if self.net.connected and self.net.mode == 'host' and not from_network:
            self.net.broadcast({
                'type': 'lobby_start_run',
                'stage': self.stage,
                'seed': self.stage_seed
            })

    def generate_stage(self, seed=None, special_mode=None):
        if seed is None:
            seed = random.randint(1000, 999999)
        self.stage_seed = seed
        self.special_mode = special_mode
        self.blue_orb_spawned = False
        self.moon_pillars_done = 0
        self.mithrix_spawned = False
        self.moon_detonation_timer = 0.0

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
        self.sky_platforms.clear()
        self.active_boss = None

        res = build_stage_world(self.stage, seed=self.stage_seed, special_mode=special_mode)
        self.stage_entities, self.obstacles, self.teleporter, stage_info = res
        self.stage_name = stage_info['name'] if isinstance(stage_info, dict) else str(stage_info)

        if is_valid(self.player):
            if special_mode == 'bazaar':
                self.player.position = Vec3(0, 1, -2)
            elif special_mode == 'moon':
                self.player.position = Vec3(0, 1, -16)
            else:
                self.player.position = Vec3(0, 1, 0)
            self.player.vel_y = 0.0

        self.director_credits = 26.0 * self.difficulty_coeff
        if special_mode == 'bazaar':
            self.show_banner('БАЗАР МЕЖДУ ВРЕМЕНЕМ :: ТОРГОВЛЯ С ТРИТОНОМ', rgb(80, 215, 255), 3.5)
        elif special_mode == 'moon':
            self.show_banner('COMMENCEMENT :: ЗАРЯДИТЕ ВСЕ 4 СТОЛПА ЛУНЫ НА БАСТИОНАХ!', rgb(100, 225, 255), 4.5)
        else:
            self.show_banner(f'STAGE {self.stage}: {self.stage_name.upper()}', color.yellow, 3.0)

        if self.stage >= 2:
            self.unlock_achievement('ach_traveler')

    def enter_bazaar(self):
        self.generate_stage(seed=random.randint(1000, 999999), special_mode='bazaar')

    def enter_moon_stage(self):
        self.generate_stage(seed=random.randint(1000, 999999), special_mode='moon')

    def on_moon_pillar_charged(self):
        self.moon_pillars_done += 1
        if self.teleporter and hasattr(self.teleporter, 'update_progress_label'):
            self.teleporter.update_progress_label(self.moon_pillars_done, 4)

        if self.moon_pillars_done >= 4 and self.teleporter and hasattr(self.teleporter, 'unlock_pad'):
            self.teleporter.unlock_pad()
            self.show_banner('ВСЕ 4 СТОЛПА ЗАРЯЖЕНЫ! ГРАВИ-ЛИФТ В ЦЕНТРЕ ОТКРЫТ (Y=120м)!', color.cyan, 5.0)
        else:
            rem = max(0, 4 - self.moon_pillars_done)
            self.show_banner(f'СТОЛП ЗАРЯЖЕН ({self.moon_pillars_done}/4)! ОСТАЛОСЬ ЗАРЯДИТЬ ЕЩЁ {rem}', color.lime, 3.2)

    def start_mithrix_encounter(self):
        if self.mithrix_spawned:
            return
        self.mithrix_spawned = True
        for e in list(self.enemies):
            if is_valid(e) and not e.is_boss:
                destroy(e)
        self.enemies = [e for e in self.enemies if is_valid(e)]

        boss = Enemy(Vec3(0, COLOSSEUM_Y, 22.0), 'mithrix', self.difficulty_coeff)
        self.active_boss = boss
        self.boss_title.text = 'MITHRIX [PHASE 1/4] :: KING OF NOTHING'
        self.enemies.append(boss)
        self.show_banner('МИТРИКС, КОРОЛЬ НИЧЕГО [ФАЗА 1/4] :: БИТВА В НЕБЕСНОМ КОЛИЗЕЕ!', color.cyan, 4.2)

    def on_mithrix_defeated(self, death_pos):
        self.moon_detonation_timer = 75.0
        ship_pos = Vec3(0, 0, -52.0)
        ship = EscapeShip(ship_pos)
        self.stage_entities.append(ship)

        # Зелёный эвакуационный портал-трамплин на южном краю Колизея для быстрого спуска к кораблю
        escape_pad = LunarEscapePad(Vec3(0, COLOSSEUM_Y, -46.0), ship_pos)
        self.stage_entities.append(escape_pad)

        self.show_banner(
            'МИТРИКС ПОВЕРЖЕН! ПРЫГАЙТЕ В ЗЕЛЁНЫЙ ЛУЧ НА КРАЮ КОЛИЗЕЯ К КОРАБЛЮ (75 СЕК)!',
            color.lime, 6.5
        )

    def on_run_victory(self):
        self.running = False
        mouse.locked = False
        self.tab_panel.enabled = False
        if is_valid(self.player):
            destroy(self.player)
        self.player = None
        for e in list(self.enemies):
            if is_valid(e):
                destroy(e)
        self.enemies.clear()
        for obj in list(self.stage_entities):
            if obj and not obj.is_empty():
                destroy(obj)
        self.stage_entities.clear()
        self.obstacles.clear()
        self.sky_platforms.clear()

        self.lunar_coins += 10
        self.show_screen('lobby')
        self.show_banner('ПОБЕДА! ВЫ ПОКИНУЛИ ЛУНУ НА СПАСАТЕЛЬНОМ КОРАБЛЕ (+10 ЛУННЫХ МОНЕТ)!', color.gold, 8.0)

    def next_stage(self, from_network=False):
        self.stage += 1
        new_seed = random.randint(1000, 999999) if not from_network else self.stage_seed
        self.generate_stage(seed=new_seed, special_mode=None)
        if not from_network and self.net.connected:
            self.net.broadcast({'type': 'stage_sync', 'stage': self.stage, 'seed': self.stage_seed})

    def spawn_boss(self, pos, boss_type=None, net_id=None, from_network=False):
        b_type = boss_type if boss_type in BOSS_TYPES else random.choice(BOSS_TYPES)
        boss = Enemy(pos, b_type, self.difficulty_coeff, net_id=net_id)
        self.active_boss = boss
        self.boss_title.text = BOSS_TITLES.get(b_type, BOSS_TITLES['boss'])
        self.enemies.append(boss)
        if not from_network and self.net.connected and self.net.mode == 'host':
            self.net.broadcast({
                'type': 'enemy_spawn',
                'net_id': boss.net_id,
                'enemy_type': b_type,
                'pos': [round(pos.x, 2), round(pos.y, 2), round(pos.z, 2)],
                'coeff': round(self.difficulty_coeff, 2)
            })

    def spawn_item_drop(self, pos, item_key=None, pool_type='small_chest', broadcast=True):
        key = item_key if item_key in ITEM_POOL else roll_item_from_pool(pool_type)
        drop = ItemDrop(pos, key)
        self.stage_entities.append(drop)
        if broadcast and self.net.connected:
            self.net.broadcast({
                'type': 'item_drop',
                'item_key': key,
                'pos': [round(pos.x, 2), round(pos.y, 2), round(pos.z, 2)]
            })

    def collect_item(self, key):
        if key not in self.player.item_order:
            self.player.item_order.append(key)
        self.player.items[key] += 1
        if key in ('bison_steak', 'tarrasque', 'transcendence', 'lunar_pauldron'):
            self.player.hp = float(self.player.max_hp)
        elif key == 'shaped_glass':
            self.player.hp = min(self.player.hp, float(self.player.max_hp))
        self.refresh_inventory_hud()
        info = ITEM_POOL[key]
        self.show_banner(f"ПОДОБРАНО: {info['name']} ({info['desc']})", info['color'], 3.2)
        if sum(self.player.items.values()) >= 6:
            self.unlock_achievement('ach_hoarder')

    def show_banner(self, msg, col=color.yellow, duration=2.5):
        self.banner_text.text = msg
        self.banner_text.color = col
        self.banner_timer = duration

    def toggle_pause_menu(self):
        if not self.running:
            return
        is_paused = not self.pause_panel.enabled
        self.pause_panel.enabled = is_paused
        mouse.locked = not is_paused

    def resume_game(self):
        if not self.running:
            return
        self.pause_panel.enabled = False
        mouse.locked = True

    def quit_run_to_menu(self, to_lobby=False):
        self.running = False
        mouse.locked = False
        self.tab_panel.enabled = False
        self.pause_panel.enabled = False
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
        self.sky_platforms.clear()

        self.my_ready = False
        self.lobby_countdown_active = False
        self.lobby_countdown = 60.0
        for pinfo in self.lobby_players.values():
            pinfo['ready'] = False

        if to_lobby:
            self.show_screen('lobby')
            self.broadcast_lobby_state()
        else:
            self.net.stop_session()
            self.lobby_players.clear()
            self.show_screen('main')

    def on_player_death(self):
        self.quit_run_to_menu(to_lobby=True)
        self.show_banner('ВЫ ПОГИБЛИ! ПОДГОТОВЬТЕСЬ К НОВОМУ ЗАБЕГУ В ЛОББИ', color.red, 4.5)

    def update(self):
        self.process_network()

        if self.banner_timer > 0:
            self.banner_timer -= time.dt
            if self.banner_timer <= 0:
                self.banner_text.text = ''

        if not self.running:
            t = time.time()
            self.update_diorama_inspection()

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

        # Таймер детонации Луны после победы над Митриксом
        if self.moon_detonation_timer > 0:
            self.moon_detonation_timer -= time.dt
            if random.random() < 0.15:
                rx = random.uniform(-65, 65)
                rz = random.uniform(-65, 65)
                VisualFX(Vec3(rx, 1.0, rz), color.cyan, 6.5, 0.4)
            if self.moon_detonation_timer <= 0:
                self.on_player_death()
                return

        # ИИ-Режиссёр (отключён на Базаре и во время дуэли с Митриксом)
        if self.net.mode != 'client' and self.special_mode != 'bazaar' and not self.mithrix_spawned:
            tp_mult = 1.8 if (self.teleporter and getattr(self.teleporter, 'state', '') == 'charging') else 1.0
            self.director_credits += (4.2 * coeff * tp_mult) * time.dt
            self.spawn_timer -= time.dt

            if self.spawn_timer <= 0 and len(self.enemies) < 24:
                self.spawn_timer = random.uniform(1.6, 3.2)
                if self.special_mode == 'moon':
                    spawn_table = [('lunar_chimera', 18.0), ('golem', 28.0), ('greater_wisp', 26.0)]
                else:
                    spawn_table = [
                        ('beetle', 10.0), ('lemurian', 12.0), ('jellyfish', 14.0),
                        ('wisp', 16.0), ('imp', 22.0), ('greater_wisp', 30.0), ('golem', 34.0),
                    ]
                affordable = [(et, c) for et, c in spawn_table if self.director_credits >= c]
                if affordable:
                    enemy_type, cost = random.choice(affordable)
                    self.director_credits -= cost

                    ang = random.uniform(0, math.pi * 2)
                    dist = random.uniform(16.0, 28.0)
                    p_pos = Vec3(*self.player.position)
                    max_b = self.world_bound - 4.0
                    sx = clamp(p_pos.x + math.cos(ang) * dist, -max_b, max_b)
                    sz = clamp(p_pos.z + math.sin(ang) * dist, -max_b, max_b)
                    sy = self.get_surface_height(sx, sz, p_pos.y)
                    new_enemy = Enemy(Vec3(sx, sy, sz), enemy_type, coeff)
                    self.enemies.append(new_enemy)
                    if self.net.connected and self.net.mode == 'host':
                        self.net.broadcast({
                            'type': 'enemy_spawn',
                            'net_id': new_enemy.net_id,
                            'enemy_type': enemy_type,
                            'pos': [round(sx, 2), round(sy, 2), round(sz, 2)],
                            'coeff': round(coeff, 2)
                        })

        if self.net.connected and self.net.mode == 'host':
            self._enemy_net_timer = getattr(self, '_enemy_net_timer', 0.0) - time.dt
            if self._enemy_net_timer <= 0:
                self._enemy_net_timer = 0.22
                pack = [
                    [e.net_id, round(e.x, 2), round(e.y, 2), round(e.z, 2), round(e.hp, 1), e.enemy_type, round(e.coeff, 2), bool(e.is_ally)]
                    for e in self.enemies if is_valid(e)
                ]
                self.net.broadcast({'type': 'enemies_sync', 'enemies': pack})

        p = self.player
        if p.items.get('transcendence', 0) > 0:
            p.shield = min(float(p.max_hp * 0.5), p.shield + 8.0 * time.dt)

        purity_stacks = p.items.get('purity', 0)
        if purity_stacks > 0:
            extra_cdr = (1.2 + 0.6 * purity_stacks) * time.dt
            p.m2_cd = max(0.0, p.m2_cd - extra_cdr)
            p.shift_cd = max(0.0, p.shift_cd - extra_cdr)
            p.r_cd = max(0.0, p.r_cd - extra_cdr)

        self.gold_text.text = f"${p.gold}  |  LUNAR: {self.lunar_coins}C  |  {SURVIVOR_CLASSES[p.char_key]['name']}"
        hp_ratio = clamp(p.hp / p.max_hp, 0.0, 1.0)
        self.hp_bar_fill.scale_x = max(0.001, hp_ratio)
        self.hp_bar_fill.color = rgb(75, 195, 255) if p.items.get('transcendence', 0) > 0 else (rgb(85, 225, 95) if hp_ratio > 0.35 else rgb(245, 70, 60))
        if p.shield >= 1.0:
            self.hp_text.text = f"{int(p.hp)} (+{int(p.shield)}) / {p.max_hp} HP"
        else:
            self.hp_text.text = f"{int(p.hp)} / {p.max_hp} HP"

        if p.char_key == 'v1':
            self.v1_style_hud.enabled = (p.v1_style_points > 0 or len(p.v1_style_log) > 0 or True)
            rank_name, rank_col, style_mult = p.v1_get_style_rank_info()
            self.v1_rank_title.text = f"{rank_name} (x{style_mult:.2f})"
            self.v1_rank_title.color = rank_col
            self.v1_rank_line.color = rank_col
            self.v1_style_bar_fill.scale_x = max(0.001, 0.36 * (p.v1_style_points / 1000.0))
            self.v1_style_bar_fill.color = rank_col

            log_lines = [f"{txt}" for txt, _, _ in p.v1_style_log[:5]]
            self.v1_style_log_text.text = '\n'.join(log_lines) if log_lines else 'BLOOD IS FUEL\nСражайтесь стильно вблизи!'

            w_name = p.v1_weapon_names.get(p.v1_weapon, 'REVOLVER')
            arm_tag = 'BLUE [F]' if p.v1_active_arm == 'feedbacker' else 'RED [F]'
            self.v1_arsenal_text.text = (
                f"[{p.v1_weapon}] {w_name}  |  COINS: {int(p.v1_coins)}/4  |  RAIL: {int(p.v1_rail_charge)}%\n"
                f"STAMINA: {'█' * int(p.v1_stamina)}{'░' * (3 - int(p.v1_stamina))}  |  ARM: {arm_tag} (Swap [V] / Red [G] / Hook [R])"
            )
            self.v1_arsenal_text.color = p.v1_weapon_cols.get(p.v1_weapon, color.cyan)

            v1_slots = {
                'm1': (f"WPN [{p.v1_weapon}]", p.v1_weapon_cols.get(p.v1_weapon, color.yellow)),
                'm2': (f"COIN {int(p.v1_coins)}" if p.v1_weapon == 1 else ("FROZEN" if p.v1_rockets_frozen else "ALT"), color.gold),
                'shift': (f"DASH x{int(p.v1_stamina)}", color.cyan),
                'r': ("HOOK" if p.v1_whiplash_cd <= 0 else f"{p.v1_whiplash_cd:.1f}s", color.lime)
            }
            for sk_key, (box, cd_lbl, _) in self.skill_boxes.items():
                txt_val, c_val = v1_slots[sk_key]
                cd_lbl.text = txt_val
                cd_lbl.color = c_val
                box.color = rgb(35, 55, 75, 235)
        else:
            self.v1_style_hud.enabled = False
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
            if self.active_boss.enemy_type == 'mithrix':
                self.boss_bar_fill.color = color.magenta if self.active_boss.phase == 4 else color.cyan
            else:
                self.boss_bar_fill.color = color.red
        else:
            self.boss_hud.enabled = False

        mins = int(self.elapsed_time // 60)
        secs = int(self.elapsed_time % 60)
        diff_label, diff_col = self.get_difficulty_info()
        self.diff_badge.color = diff_col
        det_str = f"  |  ESCAPE: {self.moon_detonation_timer:.1f}s!" if self.moon_detonation_timer > 0 else ""
        self.diff_text.text = (
            f"STAGE {self.stage}: {self.stage_name}{det_str}\n"
            f"TIME: {mins:02d}:{secs:02d}  |  {diff_label} (x{coeff:.2f})\n"
            f"MONSTERS: {len(self.enemies)}  |  LUNAR COINS: {self.lunar_coins}"
        )

        self.tab_panel.enabled = bool(held_keys['tab'])
        if self.tab_panel.enabled:
            atk_bonus = p.items['syringe'] * 15
            spd_bonus = p.items['hoof'] * 14 + p.items['energy_drink'] * 8 + p.items['red_whip'] * 12
            blk_pct = p.block_chance * 100.0
            net_line = f"Сеть: Комната {self.net.room_code} ({1 + len(self.remote_players)} игр.)" if self.net.connected else "Сеть: Одиночная игра"
            lines = [
                f"=== SURVIVOR OVERVIEW: {SURVIVOR_CLASSES[p.char_key]['name']} | {net_line} ===",
                f"Base Damage: {p.base_damage:.1f}   |   Attack Speed: +{atk_bonus}% ({p.fire_rate:.1f} shots/s)",
                f"Move Speed: +{spd_bonus}% ({p.move_speed:.1f})   |   Block Chance: {blk_pct:.1f}%   |   Crit: {p.crit_chance*100:.0f}%",
                "",
                f"=== СОБРАННЫЕ АРТЕФАКТЫ ({sum(p.items.values())} ШТ.) ==="
            ]
            if not p.item_order:
                lines.append(" Пока нет собранных предметов. Открывайте сундуки за золото клавишей [E]!")
            else:
                for k in p.item_order[:16]:
                    info = ITEM_POOL[k]
                    lines.append(f" • {info['name']} [x{p.items[k]}]: {info['desc']}")
                if len(p.item_order) > 16:
                    lines.append(f" ... и ещё {len(p.item_order) - 16} типов предметов.")
            self.tab_text.text = '\n'.join(lines)