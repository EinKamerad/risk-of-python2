from ursina import *
import math
import random
from config import ctx, rgb, is_valid, BOSS_TYPES, ITEM_POOL, PROGRESS
from models.enemies import build_enemy_mesh
from entities.fx import VisualFX, LightningBeam, LunarShockwaveRing
from entities.projectile import Projectile
from entities.boss_ai import BossAIMixin
from world.lunar import COLOSSEUM_Y


class Enemy(Entity, BossAIMixin):
    _next_id = 1

    def __init__(self, pos, enemy_type, coeff, net_id=None):
        super().__init__(position=Vec3(*pos))
        if net_id is None:
            self.net_id = Enemy._next_id
            Enemy._next_id += 1
        else:
            self.net_id = net_id
            Enemy._next_id = max(Enemy._next_id, net_id + 1)

        self.enemy_type = enemy_type
        self.is_boss = (enemy_type in BOSS_TYPES or enemy_type == 'mithrix')
        self.coeff = coeff
        self.is_dead = False
        self.parts = build_enemy_mesh(self, enemy_type)
        self.attack_timer = random.uniform(0.7, 1.6)
        self.special_timer = random.uniform(3.5, 5.5)
        self.seed_offset = (self.net_id * 1.37) % 10.0

        # Состояние 4 фаз Митрикса
        self.phase = 1
        self.phase_transition_timer = 0.0
        self.sky_leap_state = 0
        self.sky_leap_timer = 0.0
        self.sky_leap_target = Vec3(0, COLOSSEUM_Y, 0)
        self.telegraph_ring = None
        self.stolen_items = []
        self.reclaim_accum = 0.0

        self.bleed_timer = 0.0
        self.bleed_tick = 0.0
        self.bleed_dps = 0.0
        self.slow_timer = 0.0
        self.stun_timer = 0.0

        stats_table = {
            'lemurian': (36.0, 9.0, 6.3, 13, 1.1, 1.15),
            'wisp': (26.0, 11.5, 4.6, 16, 2.3, 1.25),
            'beetle': (28.0, 7.5, 7.5, 11, 0.7, 1.10),
            'jellyfish': (24.0, 14.0, 8.2, 15, 2.2, 1.25),
            'golem': (95.0, 18.0, 3.8, 28, 1.8, 1.55),
            'imp': (52.0, 13.5, 7.2, 24, 1.3, 1.20),
            'greater_wisp': (82.0, 16.5, 4.0, 32, 2.7, 1.55),
            'lunar_chimera': (110.0, 18.0, 6.0, 38, 2.5, 1.45),
            'boss': (450.0, 22.0, 3.5, 130, 2.8, 2.70),
            'vagrant': (480.0, 20.0, 3.8, 140, 3.8, 2.90),
            'overlord': (520.0, 24.0, 5.2, 150, 2.9, 2.75),
            'mithrix': (1950.0, 26.0, 8.2, 600, 2.8, 2.55),
        }
        hp_b, dmg_b, spd_b, gold_b, hh, hr = stats_table.get(enemy_type, stats_table['lemurian'])

        # Для Митрикса гарантируем минимальный порог силы Финального Босса (даже при раннем заходе после 2 этажа)
        if enemy_type == 'mithrix':
            game = ctx.game
            item_cnt = sum(game.player.items.values()) if (game and is_valid(game.player)) else 0
            eff_coeff = max(coeff, 2.35) * (1.0 + 0.045 * item_cnt)
            self.mithrix_eff_coeff = eff_coeff
            self.max_hp = hp_b * eff_coeff
            self.damage = dmg_b * max(coeff, 1.85)
        else:
            self.max_hp = hp_b * coeff
            self.damage = dmg_b * coeff

        self.speed = spd_b
        self.gold_reward = int(gold_b * coeff)
        self.hit_height = hh
        self.hit_radius = hr
        self.hp = self.max_hp

        bar_y = 6.4 if self.is_boss else (3.6 if enemy_type in ('golem', 'greater_wisp', 'lunar_chimera') else 2.6)
        bar_w = 3.2 if self.is_boss else 1.25
        self.hp_bar_bg = Entity(parent=self, model='quad', scale=(bar_w, 0.15), y=bar_y, color=color.black, billboard=True)
        self.hp_bar = Entity(parent=self.hp_bar_bg, model='quad', scale=(1, 1), z=-0.01, color=color.cyan if enemy_type == 'mithrix' else color.red, unlit=True)

    def _get_nearest_target(self, game):
        my_pos = Vec3(*self.position)
        candidates = []
        if is_valid(game.player):
            candidates.append((distance_2d(my_pos, Vec3(*game.player.position)), Vec3(*game.player.position), True))
        for rp in game.remote_players.values():
            if is_valid(rp):
                candidates.append((distance_2d(my_pos, Vec3(*rp.position)), Vec3(*rp.position), False))
        if not candidates:
            return None, 999.0, False
        candidates.sort(key=lambda x: x[0])
        dist, t_pos, is_local = candidates[0]
        return t_pos, dist, is_local

    def advance_mithrix_phase(self, game):
        """Переводит Митрикса в следующую фазу с новой полной полоской HP (100%)"""
        my_pos = Vec3(*self.position)
        self.phase += 1
        self.phase_transition_timer = 2.0
        self.sky_leap_state = 0
        if self.telegraph_ring and not self.telegraph_ring.is_empty():
            destroy(self.telegraph_ring)
            self.telegraph_ring = None

        eff_c = getattr(self, 'mithrix_eff_coeff', max(self.coeff, 2.35))

        if self.phase == 2:
            self.max_hp = 2250.0 * eff_c
            self.hp = self.max_hp
            self.position = Vec3(0, COLOSSEUM_Y, 0)
            VisualFX(Vec3(0, COLOSSEUM_Y + 2.5, 0), color.cyan, 14.0, 0.55)
            LunarShockwaveRing(Vec3(0, COLOSSEUM_Y, 0), self.damage, max_radius=55.0, speed=22.0)
            # Призыв стражей — Лунных Химер на арену Колизея
            for ang_deg in (0, 120, 240):
                r = math.radians(ang_deg)
                c_pos = Vec3(math.cos(r) * 28.0, COLOSSEUM_Y, math.sin(r) * 28.0)
                chimera = Enemy(c_pos, 'lunar_chimera', self.coeff)
                game.enemies.append(chimera)
            game.boss_title.text = 'MITHRIX [PHASE 2/4] :: CRUSHING SKY LEAP & CHIMERA VANGUARD'
            game.show_banner('МИТРИКС (ФАЗА 2/4): НЕБЕСНЫЙ ОБВАЛ И СТРАЖИ ЛУНЫ!', color.cyan, 3.8)

        elif self.phase == 3:
            self.max_hp = 2500.0 * eff_c
            self.hp = self.max_hp
            self.position = Vec3(0, COLOSSEUM_Y, 0)
            self.parts['phase_ring'].enabled = True
            self.parts['hammer_aura'].color = color.white
            VisualFX(Vec3(0, COLOSSEUM_Y + 2.5, 0), color.white, 16.0, 0.6)
            LunarShockwaveRing(Vec3(0, COLOSSEUM_Y, 0), self.damage * 1.2, max_radius=55.0, speed=25.0)
            for ang_deg in (60, 240):
                r = math.radians(ang_deg)
                c_pos = Vec3(math.cos(r) * 32.0, COLOSSEUM_Y, math.sin(r) * 32.0)
                chimera = Enemy(c_pos, 'lunar_chimera', self.coeff * 1.15)
                game.enemies.append(chimera)
            game.boss_title.text = 'MITHRIX [PHASE 3/4] :: LUNAR REVOLVING PILLARS'
            game.show_banner('МИТРИКС (ФАЗА 3/4): ЛУННЫЕ РАЗРЕЗЫ КОЛИЗЕЯ!', rgb(135, 240, 255), 3.8)

        elif self.phase == 4:
            self.max_hp = 1450.0 * max(self.coeff, 2.0)
            self.hp = self.max_hp
            self.position = Vec3(0, COLOSSEUM_Y, 0)
            self.parts['phase_ring'].enabled = True
            self.parts['phase_ring'].color = color.magenta
            self.parts['hammer_aura'].color = color.magenta
            self.parts['core'].color = color.magenta

            if is_valid(game.player):
                p = game.player
                p_pos = Vec3(*p.position) + Vec3(0, 1.5, 0)
                for k, cnt in list(p.items.items()):
                    for _ in range(cnt):
                        self.stolen_items.append(k)
                    p.items[k] = 0
                p.item_order.clear()
                random.shuffle(self.stolen_items)
                p.hp = min(float(p.max_hp), max(p.hp, float(p.max_hp) * 0.85))
                game.refresh_inventory_hud()
                LightningBeam(p_pos, Vec3(0, COLOSSEUM_Y + 3.0, 0), color.magenta, 0.65)
                VisualFX(Vec3(0, COLOSSEUM_Y + 3.0, 0), color.magenta, 15.0, 0.6)

            game.boss_title.text = 'MITHRIX [PHASE 4/4] :: ITEM STEAL (HIT HIM TO RECLAIM YOUR ITEMS!)'
            game.show_banner('МИТРИКС ЗАБРАЛ ВАШИ ПРЕДМЕТЫ! АТАКУЙТЕ ЕГО, ЧТОБЫ ВЫБИТЬ ИХ ОБРАТНО!', color.magenta, 4.8)

        if not self.hp_bar.is_empty():
            self.hp_bar.scale_x = 1.0

    def take_damage(self, amount, from_network=False):
        if not is_valid(self) or self.sky_leap_state == 1 or self.phase_transition_timer > 0:
            return

        game = ctx.game
        # Адаптивная броня Митрикса: один удар не может снять больше 8.5% HP текущей фазы
        if self.enemy_type == 'mithrix':
            amount = min(amount, self.max_hp * 0.085)

        self.hp -= amount

        # В 4-й фазе урон по Митриксу постепенно возвращает украденные предметы игроку
        if self.enemy_type == 'mithrix' and self.phase == 4 and self.stolen_items and is_valid(game.player):
            self.reclaim_accum += amount
            threshold = max(18.0, self.max_hp / max(4.0, len(self.stolen_items) + 2.0))
            while self.reclaim_accum >= threshold and self.stolen_items:
                self.reclaim_accum -= threshold
                ret_key = self.stolen_items.pop(0)
                if ret_key not in game.player.item_order:
                    game.player.item_order.append(ret_key)
                game.player.items[ret_key] += 1
                game.refresh_inventory_hud()
                LightningBeam(
                    Vec3(*self.position) + Vec3(0, 2.8, 0),
                    Vec3(*game.player.position) + Vec3(0, 1.2, 0),
                    ITEM_POOL[ret_key]['color'], 0.28
                )

        if not self.hp_bar.is_empty():
            self.hp_bar.scale_x = max(0.0, self.hp / self.max_hp)

        if not from_network and getattr(ctx, 'net', None) and ctx.net.connected:
            ctx.net.broadcast({'type': 'enemy_damage', 'net_id': self.net_id, 'amount': round(amount, 1)})

        if self.hp <= 0:
            if self.enemy_type == 'mithrix' and self.phase < 4:
                self.advance_mithrix_phase(game)
                return
            self.die(from_network=from_network)

    def die(self, from_network=False):
        game = ctx.game
        if self.is_dead or self.is_empty():
            return
        self.is_dead = True

        if self.telegraph_ring and not self.telegraph_ring.is_empty():
            destroy(self.telegraph_ring)

        death_pos = Vec3(*self.position)

        if self in game.enemies:
            game.enemies.remove(self)

        VisualFX(death_pos + Vec3(0, 1.2, 0), color.cyan if self.enemy_type == 'mithrix' else color.orange, 3.5, 0.38)

        PROGRESS.kills += 1
        if PROGRESS.kills >= 12:
            game.unlock_achievement('ach_slayer')

        if is_valid(game.player):
            p = game.player
            it = p.items
            p.gold += self.gold_reward

            if self.is_boss or random.random() < 0.08:
                gain = 5 if self.enemy_type == 'mithrix' else (1 if not self.is_boss else 2)
                game.lunar_coins += gain

            if self.enemy_type == 'mithrix' and self.stolen_items:
                for ret_key in self.stolen_items:
                    if ret_key not in p.item_order:
                        p.item_order.append(ret_key)
                    p.items[ret_key] += 1
                self.stolen_items.clear()
                game.refresh_inventory_hud()

            if it['monster_tooth'] > 0:
                p.hp = min(float(p.max_hp), p.hp + 4.0 + 4.0 * it['monster_tooth'])

            if it['topaz_brooch'] > 0:
                p.shield = min(float(p.max_hp), p.shield + 15.0 * it['topaz_brooch'])

            if it['infusion'] > 0 and p.infusion_bonus < 40.0 * it['infusion']:
                p.infusion_bonus += 1.0
                p.hp = min(float(p.max_hp), p.hp + 1.0)

            if it['bandolier'] > 0 and random.random() < min(0.65, 0.18 * it['bandolier']):
                p.m2_cd = max(0.0, p.m2_cd - 1.5)
                p.shift_cd = max(0.0, p.shift_cd - 1.5)
                p.r_cd = max(0.0, p.r_cd - 1.5)

            if not from_network:
                gas_stacks = it['gasoline']
                wisp_stacks = it['will_o_wisp']
                if gas_stacks > 0 or wisp_stacks > 0:
                    radius = 6.0 + gas_stacks * 2.0 + wisp_stacks * 3.0
                    burn_dmg = p.base_damage * (1.2 * gas_stacks + 2.0 * wisp_stacks)
                    VisualFX(death_pos + Vec3(0, 1.0, 0), color.red if gas_stacks >= wisp_stacks else color.orange, radius * 1.35, 0.4)
                    for other in list(game.enemies):
                        if is_valid(other):
                            other_pos = Vec3(*other.position)
                            if distance(other_pos, death_pos) <= radius:
                                other.take_damage(burn_dmg)

        if self.is_boss:
            PROGRESS.boss_kills += 1
            game.unlock_achievement('ach_boss')
            if self.enemy_type == 'mithrix':
                game.active_boss = None
                game.on_mithrix_defeated(death_pos)
            elif not from_network:
                game.active_boss = None
                game.spawn_item_drop(death_pos)

        PROGRESS.save()
        destroy(self)

    def update(self):
        game = ctx.game
        if not game or not game.running or not is_valid(self):
            return

        if self.bleed_timer > 0:
            self.bleed_timer -= time.dt
            self.bleed_tick -= time.dt
            if self.bleed_tick <= 0:
                self.bleed_tick = 0.35
                my_p = Vec3(*self.position)
                VisualFX(my_p + Vec3(0, self.hit_height, 0), rgb(220, 25, 45), 1.1, 0.18)
                self.take_damage(self.bleed_dps * 0.35)
                if not is_valid(self):
                    return

        if self.stun_timer > 0:
            self.stun_timer -= time.dt
            return

        spd_mult = 0.62 if self.slow_timer > 0 else 1.0
        if self.slow_timer > 0:
            self.slow_timer -= time.dt
        eff_speed = self.speed * spd_mult

        p_pos, dist, is_local_target = self._get_nearest_target(game)
        if p_pos is None:
            return

        my_pos = Vec3(*self.position)
        self.look_at_2d(p_pos, 'y')
        t = time.time() + self.seed_offset
        floor_y = game.get_surface_height(my_pos.x, my_pos.z, my_pos.y)

        if self.enemy_type == 'lemurian':
            self.parts['tail'].rotation_y = math.sin(t * 6) * 22
            if dist > 1.7:
                self.position += self.forward * eff_speed * time.dt
                resolved = game.resolve_horizontal_collision(Vec3(*self.position), 0.7, floor_y)
                self.position = Vec3(resolved.x, floor_y, resolved.z)
                leg_swing = math.sin(t * 11) * 36
                self.parts['left_leg'].rotation_x = leg_swing
                self.parts['right_leg'].rotation_x = -leg_swing
                self.parts['left_arm'].rotation_x = -leg_swing * 0.6
                self.parts['right_arm'].rotation_x = leg_swing * 0.6
            else:
                self.attack_timer -= time.dt
                if self.attack_timer <= 0:
                    if is_local_target and is_valid(game.player):
                        game.player.take_damage(self.damage)
                    self.parts['left_arm'].rotation_x = -75
                    self.parts['right_arm'].rotation_x = -75
                    VisualFX(p_pos + Vec3(0, 1, 0), color.red, 1.6, 0.2)
                    self.attack_timer = 1.1

        elif self.enemy_type == 'beetle':
            if dist > 1.65:
                self.position += self.forward * eff_speed * time.dt
                resolved = game.resolve_horizontal_collision(Vec3(*self.position), 0.65, floor_y)
                self.position = Vec3(resolved.x, floor_y, resolved.z)
                scurry = math.sin(t * 16) * 30
                self.parts['left_leg'].rotation_x = scurry
                self.parts['right_leg'].rotation_x = -scurry
            else:
                self.attack_timer -= time.dt
                if self.attack_timer <= 0:
                    if is_local_target and is_valid(game.player):
                        game.player.take_damage(self.damage)
                    VisualFX(p_pos + Vec3(0, 0.8, 0), color.orange, 1.5, 0.2)
                    self.attack_timer = 0.95

        elif self.enemy_type == 'jellyfish':
            self.parts['core'].y = 2.2 + math.sin(t * 5.0) * 0.3
            self.parts['tentacles'].rotation_y += 90 * time.dt
            if dist > 2.2:
                self.position += self.forward * eff_speed * time.dt
            else:
                self.attack_timer -= time.dt
                if self.attack_timer <= 0:
                    VisualFX(my_pos + Vec3(0, 2.0, 0), color.cyan, 5.5, 0.35)
                    if is_local_target and is_valid(game.player) and dist <= 4.5:
                        game.player.take_damage(self.damage)
                    self.attack_timer = 1.8

        elif self.enemy_type == 'wisp':
            self.parts['ring1'].rotation_x += 120 * time.dt
            self.parts['ring2'].rotation_y += 145 * time.dt
            self.parts['core'].y = 2.3 + math.sin(t * 4) * 0.28

            if dist > 16.0:
                self.position += self.forward * eff_speed * time.dt
            self.attack_timer -= time.dt
            if self.attack_timer <= 0 and dist < 36.0:
                aim = (p_pos + Vec3(0, 1.2, 0)) - (my_pos + Vec3(0, 2.3, 0))
                Projectile(my_pos + Vec3(0, 2.3, 0), aim, 25.0, self.damage, 0.35, color.orange, is_player=False)
                self.attack_timer = 2.4

        elif self.enemy_type == 'greater_wisp':
            self.parts['ring1'].rotation_y += 110 * time.dt
            self.parts['core'].y = 2.7 + math.sin(t * 3.2) * 0.3
            if dist > 18.0:
                self.position += self.forward * eff_speed * time.dt
            self.attack_timer -= time.dt
            if self.attack_timer <= 0 and dist < 40.0:
                for side_x in (-1.1, 1.1):
                    sp = my_pos + Vec3(0, 2.7, 0) + self.right * side_x
                    aim = (p_pos + Vec3(0, 1.2, 0)) - sp
                    Projectile(sp, aim, 28.0, self.damage, 0.52, color.lime, is_player=False)
                self.attack_timer = 2.8

        elif self.enemy_type == 'golem':
            if dist > 12.0:
                self.position += self.forward * eff_speed * time.dt
                resolved = game.resolve_horizontal_collision(Vec3(*self.position), 0.95, floor_y)
                self.position = Vec3(resolved.x, floor_y, resolved.z)
                stomp = math.sin(t * 5.5) * 26
                self.parts['left_leg'].rotation_x = stomp
                self.parts['right_leg'].rotation_x = -stomp
            self.attack_timer -= time.dt
            if self.attack_timer <= 0 and dist < 32.0:
                eye_pos = my_pos + Vec3(0, 2.7, 0)
                LightningBeam(eye_pos, p_pos + Vec3(0, 1.2, 0), color.red, 0.28)
                Projectile(eye_pos, (p_pos + Vec3(0, 1.2, 0)) - eye_pos, 46.0, self.damage, 0.48, color.red, is_player=False)
                self.attack_timer = 3.0

        elif self.enemy_type == 'imp':
            self.special_timer -= time.dt
            if self.special_timer <= 0 and 6.0 < dist < 24.0:
                self.special_timer = 4.2
                VisualFX(my_pos + Vec3(0, 1.2, 0), rgb(245, 35, 70), 2.5, 0.25)
                jump_pos = my_pos + self.forward * min(dist - 1.5, 9.0)
                resolved = game.resolve_horizontal_collision(jump_pos, 0.7, floor_y)
                self.position = Vec3(resolved.x, floor_y, resolved.z)
                VisualFX(Vec3(*self.position) + Vec3(0, 1.2, 0), rgb(245, 35, 70), 2.5, 0.25)

            if dist > 1.8:
                self.position += self.forward * eff_speed * time.dt
                leg_swing = math.sin(t * 13) * 38
                self.parts['left_leg'].rotation_x = leg_swing
                self.parts['right_leg'].rotation_x = -leg_swing
            else:
                self.attack_timer -= time.dt
                if self.attack_timer <= 0:
                    if is_local_target and is_valid(game.player):
                        game.player.take_damage(self.damage)
                    VisualFX(p_pos + Vec3(0, 1.1, 0), rgb(245, 35, 70), 2.0, 0.22)
                    self.attack_timer = 1.0

        else:
            self.update_boss_ai(game, my_pos, p_pos, dist, is_local_target, eff_speed, t)