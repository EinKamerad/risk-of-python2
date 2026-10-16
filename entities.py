from ursina import *
import math
import random
from config import ctx, rgb, is_valid, ITEM_POOL, BOSS_TYPES, SURVIVOR_CLASSES, PROGRESS
from models import build_survivor_mesh, build_enemy_mesh


# ==========================================
# 1. СПЕЦЭФФЕКТЫ СПОСОБНОСТЕЙ
# ==========================================
class VisualFX(Entity):
    def __init__(self, pos, fx_color=color.yellow, max_scale=3.0, duration=0.25):
        super().__init__(
            model='sphere',
            position=Vec3(*pos),
            scale=0.2,
            color=fx_color,
            unlit=True
        )
        self.animate_scale(max_scale, duration=duration, curve=curve.out_expo)
        self.animate_color(rgb(0, 0, 0, 0), duration=duration)
        destroy(self, delay=duration + 0.05)


class LightningBeam(Entity):
    def __init__(self, start_pos, end_pos, beam_color=color.magenta, thickness=0.18):
        mid = (start_pos + end_pos) * 0.5
        length = max(0.1, distance(start_pos, end_pos))
        super().__init__(
            model='cube',
            position=mid,
            scale=(thickness, thickness, length),
            color=beam_color,
            unlit=True
        )
        self.look_at(end_pos)
        self.animate_scale_x(0.01, duration=0.25)
        self.animate_scale_y(0.01, duration=0.25)
        destroy(self, delay=0.26)


class OrbitalStrikeFX(Entity):
    def __init__(self, target_pos, dmg):
        p = Vec3(*target_pos)
        super().__init__(
            model='cube',
            position=p + Vec3(0, 18, 0),
            scale=(1.4, 36.0, 1.4),
            color=color.cyan,
            unlit=True
        )
        VisualFX(p + Vec3(0, 0.8, 0), color.cyan, 6.5, 0.4)
        self.animate_scale_x(0.05, duration=0.45)
        self.animate_scale_z(0.05, duration=0.45)
        destroy(self, delay=0.46)

        game = ctx.game
        if game and dmg > 0:
            for e in list(game.enemies):
                if is_valid(e):
                    e_pos = Vec3(*e.position)
                    if distance_2d(e_pos, p) <= 4.5:
                        e.take_damage(dmg)


class ArrowRainZone(Entity):
    def __init__(self, center_pos, tick_dmg):
        super().__init__(position=Vec3(center_pos[0], 0.1, center_pos[2]))
        self.tick_dmg = tick_dmg
        self.duration = 4.0
        self.tick_timer = 0.0
        self.radius = 7.5
        self.ring = Entity(
            parent=self,
            model='sphere',
            scale=(self.radius * 2, 0.1, self.radius * 2),
            color=rgb(255, 60, 90, 80),
            unlit=True
        )

    def update(self):
        game = ctx.game
        if not game or not game.running or self.is_empty():
            return
        self.duration -= time.dt
        if self.duration <= 0:
            destroy(self)
            return

        self.tick_timer -= time.dt
        if self.tick_timer <= 0:
            self.tick_timer = 0.35
            my_pos = Vec3(*self.position)
            for _ in range(3):
                rx = my_pos.x + random.uniform(-self.radius * 0.8, self.radius * 0.8)
                rz = my_pos.z + random.uniform(-self.radius * 0.8, self.radius * 0.8)
                LightningBeam(Vec3(rx, 14, rz), Vec3(rx, 0, rz), rgb(255, 220, 80), 0.14)
            if self.tick_dmg > 0:
                for e in list(game.enemies):
                    if is_valid(e):
                        e_pos = Vec3(*e.position)
                        if distance_2d(e_pos, my_pos) <= self.radius:
                            e.take_damage(self.tick_dmg)


class HallowedMistZone(Entity):
    """Священный Туман Гвен: открытая арена с парящими иглами по периметру"""
    def __init__(self, center_pos, tick_dmg):
        super().__init__(position=Vec3(center_pos[0], 0.08, center_pos[2]))
        self.tick_dmg = tick_dmg
        self.duration = 4.5
        self.tick_timer = 0.0
        self.radius = 7.2
        self.ring = Entity(
            parent=self,
            model='sphere',
            scale=(self.radius * 2, 0.08, self.radius * 2),
            color=rgb(75, 210, 255, 70),
            unlit=True
        )
        self.pillars_hub = Entity(parent=self)
        for i in range(8):
            ang = (i / 8.0) * math.pi * 2
            px = math.cos(ang) * self.radius
            pz = math.sin(ang) * self.radius
            Entity(
                parent=self.pillars_hub,
                model='diamond',
                position=(px, 1.2, pz),
                scale=(0.35, 2.2, 0.35),
                color=rgb(145, 235, 255, 160),
                unlit=True
            )

    def update(self):
        game = ctx.game
        if not game or not game.running or self.is_empty():
            return
        self.duration -= time.dt
        if not self.pillars_hub.is_empty():
            self.pillars_hub.rotation_y += 55 * time.dt
        if self.duration <= 0:
            destroy(self)
            return

        self.tick_timer -= time.dt
        if self.tick_timer <= 0:
            self.tick_timer = 0.4
            my_pos = Vec3(*self.position)
            if is_valid(game.player) and distance_2d(Vec3(*game.player.position), my_pos) <= self.radius:
                game.player.hp = min(float(game.player.max_hp), game.player.hp + 4.5)
            for e in list(game.enemies):
                if is_valid(e):
                    e_pos = Vec3(*e.position)
                    if distance_2d(e_pos, my_pos) <= self.radius:
                        e.take_damage(self.tick_dmg)
                        VisualFX(e_pos + Vec3(0, 1, 0), rgb(130, 230, 255), 1.4, 0.2)


# ==========================================
# 2. УНИВЕРСАЛЬНЫЕ СНАРЯДЫ (С ПРОКАМИ ПРЕДМЕТОВ)
# ==========================================
class Projectile(Entity):
    def __init__(
        self, pos, direction, speed, damage, scale_val, proj_color,
        is_player=True, aoe=0.0, pierce=False, bounces=0, homing=False,
        is_remote=False, lifesteal=0.0, can_proc=True
    ):
        super().__init__(
            model='sphere',
            position=Vec3(*pos),
            scale=scale_val,
            color=proj_color,
            unlit=True
        )
        Entity(parent=self, model='diamond', scale=1.45, color=color.white, unlit=True)
        self.direction = Vec3(*direction).normalized()
        self.speed = speed
        self.damage = damage
        self.is_player = is_player
        self.is_remote = is_remote
        self.aoe = aoe
        self.pierce = pierce
        self.bounces = bounces
        self.homing = homing
        self.lifesteal = lifesteal
        self.can_proc = can_proc
        self.hit_memory = set()
        self.lifetime = 3.4
        self.is_destroyed = False

    def safe_destroy(self):
        if not self.is_destroyed and not self.is_empty():
            self.is_destroyed = True
            destroy(self)

    def update(self):
        game = ctx.game
        if not game or not game.running or self.is_destroyed or self.is_empty():
            return

        my_pos = Vec3(*self.position)

        if self.homing and self.is_player and game.enemies:
            nearest = None
            best_d = 26.0
            for e in game.enemies:
                if is_valid(e) and e not in self.hit_memory:
                    d = distance(my_pos, Vec3(*e.position) + Vec3(0, e.hit_height, 0))
                    if d < best_d:
                        best_d = d
                        nearest = e
            if nearest:
                desired = ((Vec3(*nearest.position) + Vec3(0, nearest.hit_height, 0)) - my_pos).normalized()
                self.direction = lerp(self.direction, desired, time.dt * 7.5).normalized()

        self.position += self.direction * self.speed * time.dt
        self.rotation_z += 360 * time.dt
        self.lifetime -= time.dt
        if self.lifetime <= 0 or self.y < -1:
            self.safe_destroy()
            return

        my_pos = Vec3(*self.position)

        if not self.pierce and game.is_inside_solid_obstacle(my_pos, 0.2):
            VisualFX(my_pos, self.color, 1.2, 0.18)
            self.safe_destroy()
            return

        if self.is_player:
            for e in list(game.enemies):
                if not is_valid(e) or e in self.hit_memory:
                    continue
                hit_center = Vec3(*e.position) + Vec3(0, e.hit_height, 0)
                if distance(my_pos, hit_center) <= e.hit_radius + self.scale_x * 0.4:
                    self.hit_memory.add(e)
                    if not self.is_remote:
                        self.on_hit_enemy(e, my_pos)
                    else:
                        VisualFX(my_pos, self.color, 1.3, 0.2)

                    if self.bounces > 0:
                        self.bounces -= 1
                        next_target = None
                        best_d = 18.0
                        for other in list(game.enemies):
                            if is_valid(other) and other not in self.hit_memory:
                                d = distance(my_pos, Vec3(*other.position))
                                if d < best_d:
                                    best_d = d
                                    next_target = other
                        if next_target:
                            next_pos = Vec3(*next_target.position) + Vec3(0, next_target.hit_height, 0)
                            LightningBeam(my_pos, next_pos, self.color, 0.22)
                            self.direction = (next_pos - my_pos).normalized()
                            return
                        else:
                            self.safe_destroy()
                            return

                    if not self.pierce:
                        self.safe_destroy()
                        return
        else:
            if is_valid(game.player):
                p_center = Vec3(*game.player.position) + Vec3(0, 1.0, 0)
                if distance(my_pos, p_center) <= 1.05:
                    game.player.take_damage(self.damage)
                    VisualFX(my_pos, color.red, 1.6, 0.2)
                    self.safe_destroy()

    def on_hit_enemy(self, target, proj_pos):
        game = ctx.game
        if not is_valid(target) or not is_valid(game.player):
            return

        target_pos = Vec3(*target.position)
        p = game.player
        it = p.items
        luck_bonus = 1.0 + 0.12 * it['clover']

        dmg = self.damage

        # Crowbar: +50% урона врагам с >85% HP
        if it['crowbar'] > 0 and target.hp >= target.max_hp * 0.85:
            dmg *= (1.0 + 0.50 * it['crowbar'])

        # Armor-Piercing Rounds: +20% урона по Боссам
        if it['ap_rounds'] > 0 and target.is_boss:
            dmg *= (1.0 + 0.20 * it['ap_rounds'])

        # Focus Crystal: +20% урона вблизи (<13м)
        if it['focus_crystal'] > 0 and distance(Vec3(*p.position), target_pos) <= 13.0:
            dmg *= (1.0 + 0.20 * it['focus_crystal'])

        # Brilliant Behemoth: +35% урона и взрывной радиус
        eff_aoe = self.aoe
        if it['behemoth'] > 0:
            dmg *= (1.0 + 0.25 * it['behemoth'])
            eff_aoe = max(eff_aoe, 2.5 + 1.0 * it['behemoth'])

        # Критический удар + Harvester's Scythe + Predatory Instincts
        is_crit = random.random() < p.crit_chance
        if is_crit:
            dmg *= 2.0
            VisualFX(proj_pos, rgb(255, 45, 70), max_scale=2.2, duration=0.25)
            if it['harvester_scythe'] > 0:
                p.hp = min(float(p.max_hp), p.hp + 2.0 + 4.0 * it['harvester_scythe'])
            if it['predatory'] > 0:
                p.predatory_timer = 3.0

        # Leeching Seed + врождённый вампиризм навыка
        heal_amt = self.lifesteal + (1.5 * it['leeching_seed'])
        if heal_amt > 0:
            p.hp = min(float(p.max_hp), p.hp + heal_amt)

        # Статусы на враге до удара
        if it['chronobauble'] > 0:
            target.slow_timer = max(target.slow_timer, 2.5 * it['chronobauble'])

        if it['stun_grenade'] > 0 and not target.is_boss:
            if random.random() < min(0.65, 0.10 * it['stun_grenade'] * luck_bonus):
                target.stun_timer = max(target.stun_timer, 1.5)
                VisualFX(target_pos + Vec3(0, 1.5, 0), color.white, 2.0, 0.25)

        if it['tri_tip'] > 0:
            if random.random() < min(1.0, 0.15 * it['tri_tip'] * luck_bonus):
                target.bleed_timer = max(target.bleed_timer, 3.0)
                target.bleed_dps = max(target.bleed_dps, p.base_damage * 0.6 * it['tri_tip'])

        target.take_damage(dmg)
        VisualFX(proj_pos, self.color, max_scale=1.3 if eff_aoe == 0 else eff_aoe * 1.35, duration=0.22)

        if eff_aoe > 0:
            for other in list(game.enemies):
                if other is not target and is_valid(other):
                    if distance(Vec3(*other.position), target_pos) <= eff_aoe:
                        other.take_damage(dmg * 0.65)

        if not self.can_proc or not is_valid(p):
            return

        # Sticky Bomb
        if it['sticky_bomb'] > 0 and random.random() < min(0.75, 0.12 * it['sticky_bomb'] * luck_bonus):
            VisualFX(target_pos + Vec3(0, 1.0, 0), color.orange, 3.8, 0.3)
            if is_valid(target):
                target.take_damage(p.base_damage * (1.4 * it['sticky_bomb']))

        # Kjaro's Band & Runald's Band (прокают на мощных ударах или с шансом)
        if (dmg >= p.base_damage * 1.8 or random.random() < 0.16 * luck_bonus):
            if it['kjaro_band'] > 0:
                VisualFX(target_pos + Vec3(0, 1.2, 0), rgb(255, 100, 20), 5.2, 0.38)
                for other in list(game.enemies):
                    if is_valid(other) and distance(Vec3(*other.position), target_pos) <= 4.8:
                        other.take_damage(p.base_damage * (1.5 * it['kjaro_band']))
            if it['runald_band'] > 0 and is_valid(target):
                VisualFX(target_pos + Vec3(0, 1.2, 0), color.cyan, 4.0, 0.35)
                target.slow_timer = 4.0
                target.take_damage(p.base_damage * (1.8 * it['runald_band']))

        # AtG Missile Mk. 1
        if it['atg_missile'] > 0 and random.random() < min(0.75, 0.12 * it['atg_missile'] * luck_bonus):
            m_pos = Vec3(*p.position) + Vec3(0, 2.2, 0)
            Projectile(
                pos=m_pos, direction=Vec3(0, 0.6, 0.8).normalized(),
                speed=48.0, damage=p.base_damage * (2.2 * it['atg_missile']),
                scale_val=0.36, proj_color=rgb(115, 255, 80),
                is_player=True, homing=True, can_proc=False
            )

        # Ukulele
        ukulele_stacks = it['ukulele']
        if ukulele_stacks > 0 and random.random() < min(0.85, 0.25 * luck_bonus):
            max_targets = 2 + ukulele_stacks * 2
            chain_radius = 13.0 + ukulele_stacks * 2.5
            chained = 0
            prev_pos = target_pos + Vec3(0, 1.2, 0)
            for other in list(game.enemies):
                if other is not target and is_valid(other):
                    other_pos = Vec3(*other.position) + Vec3(0, 1.2, 0)
                    if distance(other_pos, prev_pos) <= chain_radius:
                        other.take_damage(dmg * 0.8)
                        LightningBeam(prev_pos, other_pos, color.magenta)
                        VisualFX(other_pos, color.magenta, 2.0, 0.25)
                        prev_pos = other_pos
                        chained += 1
                        if chained >= max_targets:
                            break


# ==========================================
# 3. ВЫЖИВШИЙ (ЛОКАЛЬНЫЙ ИГРОК)
# ==========================================
class Survivor(Entity):
    def __init__(self, char_key='commando'):
        super().__init__(position=(0, 0, 0))
        self.char_key = char_key
        cfg = SURVIVOR_CLASSES[char_key]

        self.base_max_hp = cfg['hp']
        self.hp = float(cfg['hp'])
        self.shield = 0.0
        self.infusion_bonus = 0.0

        self.base_speed = cfg['speed']
        self.base_damage = cfg['damage']
        self.base_fire_rate = cfg['fire_rate']
        self.proj_speed = cfg['proj_speed']
        self.proj_scale = cfg['proj_scale']
        self.proj_aoe = cfg['aoe']

        self.items = {k: 0 for k in ITEM_POOL.keys()}
        self.item_order = []  # Хранит порядок подбора предметов для динамического UI
        self.gold = 35

        self.vel_y = 0.0
        self.grounded = True
        self.jumps_left = 1
        self.space_was_pressed = False

        self.m1_cd = 0.0
        self.m2_cd = 0.0
        self.shift_cd = 0.0
        self.r_cd = 0.0

        self.dash_vector = Vec3(0, 0, 0)
        self.dash_timer = 0.0
        self.barrage_shots = 0
        self.barrage_timer = 0.0
        self.dragon_install_timer = 0.0
        self.predatory_timer = 0.0
        self.opal_timer = 0.0
        self.medkit_timer = 0.0
        self.shoot_side = 0
        self.is_moving = False
        self.net_sync_timer = 0.0

        self.parts = build_survivor_mesh(self, char_key)

        self.cam_pivot = Entity(parent=self, y=2.15)
        camera.parent = self.cam_pivot
        camera.position = (0.85, 0.75, -8.8)
        camera.rotation = (6, 0, 0)

    @property
    def max_hp(self):
        return int(self.base_max_hp + 25 * self.items['bison_steak'] + self.infusion_bonus)

    @property
    def dash_cooldown(self):
        return self.shift_cd

    @property
    def move_speed(self):
        di_mult = 1.45 if self.dragon_install_timer > 0 else 1.0
        spd_bonus = (
            1.0
            + 0.14 * self.items['hoof']
            + 0.08 * self.items['energy_drink']
            + 0.12 * self.items['red_whip']
        )
        return self.base_speed * spd_bonus * di_mult

    @property
    def fire_rate(self):
        di_mult = 1.65 if self.dragon_install_timer > 0 else 1.0
        pred_bonus = 0.12 * self.items['predatory'] if self.predatory_timer > 0 else 0.0
        return self.base_fire_rate * (1.0 + 0.15 * self.items['syringe'] + pred_bonus) * di_mult

    @property
    def block_chance(self):
        stacks = self.items['bear']
        return 1.0 - (1.0 / (1.0 + 0.15 * stacks))

    @property
    def crit_chance(self):
        return min(
            1.0,
            0.05
            + 0.10 * self.items['lens']
            + 0.05 * self.items['harvester_scythe']
            + 0.07 * self.items['clover']
        )

    @property
    def max_jumps(self):
        return 1 + self.items['feather']

    def update(self):
        game = ctx.game
        if not game or not game.running or self.is_empty():
            return

        sens = game.settings.get('sensitivity', 45)
        if mouse.locked:
            self.rotation_y += mouse.velocity[0] * sens
            self.cam_pivot.rotation_x = clamp(self.cam_pivot.rotation_x - mouse.velocity[1] * sens, -42, 48)

        move_input = Vec3(held_keys['d'] - held_keys['a'], 0, held_keys['w'] - held_keys['s'])
        self.is_moving = move_input.length() > 0
        if self.is_moving:
            move_dir = (self.forward * move_input.z + self.right * move_input.x).normalized()
            self.position += move_dir * self.move_speed * time.dt

            walk_cycle = time.time() * (11.0 + self.items['hoof'] * 1.2)
            swing = math.sin(walk_cycle) * 38.0
            self.parts['left_leg'].rotation_x = swing
            self.parts['right_leg'].rotation_x = -swing
            self.parts['torso'].y = 1.26 + abs(math.cos(walk_cycle)) * 0.08
            self.parts['torso'].rotation_z = math.sin(walk_cycle) * 3.0
        else:
            self.parts['left_leg'].rotation_x = lerp(self.parts['left_leg'].rotation_x, 0, time.dt * 10)
            self.parts['right_leg'].rotation_x = lerp(self.parts['right_leg'].rotation_x, 0, time.dt * 10)
            self.parts['torso'].y = 1.26 + math.sin(time.time() * 2.5) * 0.03
            self.parts['torso'].rotation_z = lerp(self.parts['torso'].rotation_z, 0, time.dt * 10)

        self.m1_cd = max(0.0, self.m1_cd - time.dt)
        self.m2_cd = max(0.0, self.m2_cd - time.dt)
        self.shift_cd = max(0.0, self.shift_cd - time.dt)
        self.r_cd = max(0.0, self.r_cd - time.dt)
        self.predatory_timer = max(0.0, self.predatory_timer - time.dt)
        self.opal_timer = max(0.0, self.opal_timer - time.dt)
        self.shield = max(0.0, self.shield - 1.5 * time.dt)

        # Medkit: отложенное лечение после получения урона
        if self.medkit_timer > 0:
            self.medkit_timer -= time.dt
            if self.medkit_timer <= 0 and self.items['medkit'] > 0:
                heal = 5.0 + 10.0 * self.items['medkit']
                self.hp = min(float(self.max_hp), self.hp + heal)
                VisualFX(Vec3(*self.position) + Vec3(0, 1.2, 0), color.green, 2.2, 0.25)

        if self.dragon_install_timer > 0:
            self.dragon_install_timer -= time.dt
            self.hp = min(float(self.max_hp), self.hp + 6.0 * time.dt)
            if random.random() < 0.25:
                VisualFX(Vec3(*self.position) + Vec3(0, 1.2, 0), rgb(255, 110, 20), 2.2, 0.18)

        if held_keys['shift'] and self.shift_cd <= 0:
            self.use_shift_skill()

        if held_keys['r'] and self.r_cd <= 0:
            self.use_r_skill()

        if self.dash_timer > 0:
            self.position += self.dash_vector * time.dt
            self.dash_timer -= time.dt
            self.parts['torso'].rotation_x = 30.0
        else:
            self.parts['torso'].rotation_x = lerp(self.parts['torso'].rotation_x, 0, time.dt * 10)

        if self.barrage_shots > 0:
            self.barrage_timer -= time.dt
            if self.barrage_timer <= 0:
                self.barrage_timer = 0.065
                self.barrage_shots -= 1
                self.fire_primary_projectile(damage_mult=1.25, col_override=color.cyan)

        space_down = bool(held_keys['space'])
        if space_down and not self.space_was_pressed and self.jumps_left > 0:
            self.vel_y = 12.0
            self.grounded = False
            self.jumps_left -= 1
            # Wax Quill: рывок вперёд при прыжке
            if self.items['wax_quill'] > 0 and self.is_moving:
                self.dash_vector = self.forward * (14.0 + 4.0 * self.items['wax_quill'])
                self.dash_timer = max(self.dash_timer, 0.16)
            if not self.grounded:
                VisualFX(Vec3(*self.position), color.cyan, 1.8, 0.22)
        self.space_was_pressed = space_down

        self.vel_y -= 26.0 * time.dt
        self.y += self.vel_y * time.dt

        floor_h = game.get_surface_height(self.position.x, self.position.z, self.y)
        if self.y <= floor_h:
            self.y = floor_h
            self.vel_y = 0.0
            self.grounded = True
            self.jumps_left = self.max_jumps

        resolved = game.resolve_horizontal_collision(Vec3(*self.position), radius=0.72, entity_y=self.y)
        self.x = clamp(resolved.x, -58, 58)
        self.z = clamp(resolved.z, -58, 58)

        # Защита камеры от проваливания под пол при взгляде вверх
        pitch_rad = math.radians(self.cam_pivot.rotation_x)
        base_dist = 8.8
        if pitch_rad < 0:
            sin_p = math.sin(-pitch_rad)
            cos_p = math.cos(pitch_rad)
            pivot_world_y = self.y + 2.15 + 0.75 * cos_p
            min_cam_y = 0.55
            avail_drop = max(0.4, pivot_world_y - min_cam_y)
            safe_dist = avail_drop / max(0.01, sin_p)
            camera.z = -clamp(min(base_dist, safe_dist), 2.0, base_dist)
        else:
            camera.z = -base_dist

        self.hp = min(float(self.max_hp), self.hp + 1.5 * time.dt)

        if self.parts['halo']:
            self.parts['halo'].rotation_z += 95 * time.dt

        if mouse.locked:
            if mouse.left and self.m1_cd <= 0:
                self.use_m1_skill()
            if mouse.right and self.m2_cd <= 0:
                self.use_m2_skill()

        if getattr(ctx, 'net', None) and ctx.net.connected:
            self.net_sync_timer -= time.dt
            if self.net_sync_timer <= 0:
                self.net_sync_timer = 0.05
                ctx.net.broadcast({
                    'type': 'player_state',
                    'player_id': ctx.net.my_id,
                    'char_key': self.char_key,
                    'pos': [round(self.x, 2), round(self.y, 2), round(self.z, 2)],
                    'rot_y': round(self.rotation_y, 1),
                    'hp': round(self.hp, 1),
                    'max_hp': self.max_hp,
                    'moving': self.is_moving
                })

    def _broadcast_shot(self, pos, aim_dir, speed, dmg, scale_val, col_name, aoe=0.0, pierce=False, bounces=0, homing=False):
        if getattr(ctx, 'net', None) and ctx.net.connected:
            ctx.net.broadcast({
                'type': 'player_shoot',
                'player_id': ctx.net.my_id,
                'pos': [round(pos.x, 2), round(pos.y, 2), round(pos.z, 2)],
                'dir': [round(aim_dir.x, 3), round(aim_dir.y, 3), round(aim_dir.z, 3)],
                'speed': speed,
                'scale': scale_val,
                'col': col_name,
                'aoe': aoe,
                'pierce': pierce,
                'bounces': bounces,
                'homing': homing
            })

    def fire_primary_projectile(self, damage_mult=1.0, col_override=None):
        aim_dir = camera.forward
        spawn_pos = Vec3(*self.position) + Vec3(0, 1.55, 0) + self.forward * 0.95
        color_map = {
            'commando': color.yellow,
            'artificer': color.magenta,
            'huntress': rgb(255, 80, 100),
            'buzz': rgb(110, 255, 80),
            'v1': rgb(255, 230, 50),
            'sol': rgb(255, 110, 25),
            'gwen': rgb(95, 225, 255)
        }
        default_col = color_map.get(self.char_key, color.yellow)
        proj_col = col_override if col_override else default_col
        col_name = 'cyan' if col_override else self.char_key

        is_pierce = (self.char_key == 'sol')
        steal = 1.6 if self.char_key in ('v1', 'gwen') else 0.0

        Projectile(
            pos=spawn_pos,
            direction=aim_dir,
            speed=self.proj_speed,
            damage=self.base_damage * damage_mult,
            scale_val=self.proj_scale,
            proj_color=proj_col,
            is_player=True,
            aoe=self.proj_aoe,
            pierce=is_pierce,
            homing=(self.char_key == 'huntress'),
            lifesteal=steal
        )
        self._broadcast_shot(
            spawn_pos, aim_dir, self.proj_speed, self.base_damage * damage_mult,
            self.proj_scale, col_name, self.proj_aoe, is_pierce, 0, self.char_key == 'huntress'
        )

        if self.char_key in ('sol', 'gwen', 'buzz', 'v1'):
            arm = self.parts['right_arm']
            arm.rotation_x = -48 if self.char_key in ('sol', 'gwen') else -26
            arm.animate_rotation_x(0, duration=0.14)
        else:
            arm = self.parts['left_arm'] if self.shoot_side % 2 == 0 else self.parts['right_arm']
            self.shoot_side += 1
            arm.rotation_x = -24
            arm.animate_rotation_x(0, duration=0.11)

    def use_m1_skill(self):
        self.m1_cd = 1.0 / self.fire_rate
        self.fire_primary_projectile()

    def use_m2_skill(self):
        game = ctx.game
        skills = SURVIVOR_CLASSES[self.char_key]['skills']
        cd_mult = max(0.25, 1.0 - 0.12 * self.items['backup_mag'])
        self.m2_cd = skills['m2']['cd'] * cd_mult
        spawn_pos = Vec3(*self.position) + Vec3(0, 1.55, 0) + self.forward * 1.1
        aim_dir = camera.forward

        if self.char_key == 'commando':
            Projectile(
                pos=spawn_pos, direction=aim_dir, speed=68.0,
                damage=self.base_damage * 3.0, scale_val=0.48,
                proj_color=color.cyan, is_player=True, pierce=True
            )
            self._broadcast_shot(spawn_pos, aim_dir, 68.0, self.base_damage * 3.0, 0.48, 'cyan', 0.0, True, 0, False)
        elif self.char_key == 'artificer':
            Projectile(
                pos=spawn_pos, direction=aim_dir, speed=26.0,
                damage=self.base_damage * 2.8, scale_val=0.95,
                proj_color=color.cyan, is_player=True, aoe=7.5
            )
            self._broadcast_shot(spawn_pos, aim_dir, 26.0, self.base_damage * 2.8, 0.95, 'cyan', 7.5, False, 0, False)
        elif self.char_key == 'huntress':
            Projectile(
                pos=spawn_pos, direction=aim_dir, speed=48.0,
                damage=self.base_damage * 2.2, scale_val=0.55,
                proj_color=color.cyan, is_player=True, bounces=5, homing=True
            )
            self._broadcast_shot(spawn_pos, aim_dir, 48.0, self.base_damage * 2.2, 0.55, 'cyan', 0.0, False, 5, True)
        elif self.char_key == 'buzz':
            Projectile(
                pos=spawn_pos, direction=aim_dir, speed=74.0,
                damage=self.base_damage * 2.9, scale_val=0.55,
                proj_color=color.red, is_player=True, aoe=4.2, pierce=True
            )
            self._broadcast_shot(spawn_pos, aim_dir, 74.0, self.base_damage * 2.9, 0.55, 'sol', 4.2, True, 0, False)
        elif self.char_key == 'v1':
            VisualFX(spawn_pos + Vec3(0, 0.6, 0), color.gold, 1.8, 0.25)
            Projectile(
                pos=spawn_pos, direction=aim_dir, speed=85.0,
                damage=self.base_damage * 2.5, scale_val=0.45,
                proj_color=color.gold, is_player=True, bounces=4, homing=True, lifesteal=6.0
            )
            self._broadcast_shot(spawn_pos, aim_dir, 85.0, self.base_damage * 2.5, 0.45, 'v1', 0.0, False, 4, True)
        elif self.char_key == 'sol':
            self.vel_y = 14.8
            self.grounded = False
            my_pos = Vec3(*self.position)
            VisualFX(my_pos + Vec3(0, 1.5, 0), rgb(255, 90, 20), 6.8, 0.35)
            for e in list(game.enemies):
                if is_valid(e):
                    e_pos = Vec3(*e.position)
                    if distance(e_pos, my_pos) <= 6.5:
                        e.take_damage(self.base_damage * 2.6)
            Projectile(
                pos=spawn_pos, direction=aim_dir, speed=46.0,
                damage=self.base_damage * 2.0, scale_val=0.75,
                proj_color=rgb(255, 110, 20), is_player=True, aoe=4.5, pierce=True
            )
            self._broadcast_shot(spawn_pos, aim_dir, 46.0, self.base_damage * 2.0, 0.75, 'sol', 4.5, True, 0, False)
        elif self.char_key == 'gwen':
            Projectile(
                pos=spawn_pos, direction=aim_dir, speed=64.0,
                damage=self.base_damage * 3.1, scale_val=0.68,
                proj_color=rgb(140, 235, 255), is_player=True, aoe=3.2, pierce=True, lifesteal=5.0
            )
            self._broadcast_shot(spawn_pos, aim_dir, 64.0, self.base_damage * 3.1, 0.68, 'gwen', 3.2, True, 0, False)

    def use_shift_skill(self):
        game = ctx.game
        skills = SURVIVOR_CLASSES[self.char_key]['skills']
        self.shift_cd = skills['shift']['cd']
        my_pos = Vec3(*self.position)
        VisualFX(my_pos + Vec3(0, 1, 0), color.cyan, 2.4, 0.3)
        nrg_mult = 1.0 + 0.18 * self.items['energy_drink']

        if self.char_key == 'commando':
            self.dash_vector = self.forward * 28.0 * nrg_mult
            self.dash_timer = 0.22
        elif self.char_key == 'artificer':
            self.vel_y = 16.5
            self.grounded = False
            self.dash_vector = self.forward * 18.0 * nrg_mult
            self.dash_timer = 0.32
            for e in list(game.enemies):
                if is_valid(e):
                    e_pos = Vec3(*e.position)
                    if distance(e_pos, my_pos) <= 6.8:
                        e.take_damage(self.base_damage * 1.8)
        elif self.char_key == 'huntress':
            blink_dir = camera.forward
            blink_dir.y = max(0.0, blink_dir.y)
            target_pos = my_pos + blink_dir.normalized() * (11.0 * nrg_mult)
            LightningBeam(my_pos + Vec3(0, 1, 0), target_pos + Vec3(0, 1, 0), color.cyan, 0.28)
            resolved = game.resolve_horizontal_collision(target_pos, 0.72, self.y)
            self.position = Vec3(clamp(resolved.x, -56, 56), max(0.0, target_pos.y), clamp(resolved.z, -56, 56))
            VisualFX(Vec3(*self.position) + Vec3(0, 1, 0), color.cyan, 2.4, 0.3)
        elif self.char_key == 'buzz':
            self.vel_y = 18.5
            self.grounded = False
            self.dash_vector = self.forward * 24.0 * nrg_mult
            self.dash_timer = 0.36
            VisualFX(my_pos, rgb(125, 255, 80), 4.2, 0.35)
        elif self.char_key == 'v1':
            self.dash_vector = self.forward * 35.0 * nrg_mult
            self.dash_timer = 0.18
            for e in list(game.enemies):
                if is_valid(e):
                    e_pos = Vec3(*e.position)
                    if distance(e_pos, my_pos) <= 6.0:
                        e.take_damage(self.base_damage * 1.5)
                        self.hp = min(float(self.max_hp), self.hp + 8.0)
                        VisualFX(e_pos + Vec3(0, 1, 0), color.red, 2.2, 0.25)
        elif self.char_key == 'sol':
            self.dash_vector = self.forward * 27.0 * nrg_mult
            self.dash_timer = 0.26
            lunge_center = my_pos + self.forward * 2.5
            VisualFX(lunge_center + Vec3(0, 1, 0), rgb(255, 100, 20), 5.5, 0.32)
            for e in list(game.enemies):
                if is_valid(e):
                    e_pos = Vec3(*e.position)
                    if distance(e_pos, lunge_center) <= 6.5:
                        e.take_damage(self.base_damage * 2.2)
        elif self.char_key == 'gwen':
            self.dash_vector = self.forward * 20.0 * nrg_mult
            self.dash_timer = 0.22
            mist = HallowedMistZone(my_pos + self.forward * 3.0, self.base_damage * 0.65)
            game.stage_entities.append(mist)

    def use_r_skill(self):
        game = ctx.game
        skills = SURVIVOR_CLASSES[self.char_key]['skills']
        self.r_cd = skills['r']['cd']
        my_pos = Vec3(*self.position)

        if self.char_key == 'commando':
            self.barrage_shots = 8
            self.barrage_timer = 0.01
        elif self.char_key == 'artificer':
            targets = [e for e in game.enemies if is_valid(e) and distance(Vec3(*e.position), my_pos) <= 28.0]
            for i in range(5):
                if i < len(targets) and is_valid(targets[i]):
                    t_pos = Vec3(*targets[i].position)
                else:
                    ang = random.uniform(0, math.pi * 2)
                    t_pos = my_pos + Vec3(math.cos(ang) * 8.0, 0, math.sin(ang) * 8.0)
                OrbitalStrikeFX(t_pos, self.base_damage * 2.2)
        elif self.char_key == 'huntress':
            self.vel_y = 14.0
            self.grounded = False
            zone_pos = my_pos + self.forward * 12.0
            zone = ArrowRainZone(zone_pos, self.base_damage * 0.75)
            game.stage_entities.append(zone)
        elif self.char_key == 'buzz':
            spawn_pos = my_pos + Vec3(0, 1.8, 0)
            for i in range(6):
                ang = math.radians(-30 + i * 12)
                d = Vec3(
                    self.forward.x * math.cos(ang) - self.forward.z * math.sin(ang),
                    0.15,
                    self.forward.x * math.sin(ang) + self.forward.z * math.cos(ang)
                ).normalized()
                Projectile(
                    pos=spawn_pos, direction=d, speed=46.0,
                    damage=self.base_damage * 2.1, scale_val=0.42,
                    proj_color=rgb(130, 255, 90), is_player=True, aoe=3.8, homing=True
                )
                self._broadcast_shot(spawn_pos, d, 46.0, self.base_damage * 2.1, 0.42, 'buzz', 3.8, False, 0, True)
        elif self.char_key == 'v1':
            aim_dir = camera.forward
            start_p = my_pos + Vec3(0, 1.55, 0)
            end_p = start_p + aim_dir * 45.0
            LightningBeam(start_p, end_p, color.cyan, 0.45)
            Projectile(
                pos=start_p, direction=aim_dir, speed=95.0,
                damage=self.base_damage * 3.8, scale_val=0.65,
                proj_color=color.cyan, is_player=True, aoe=4.5, pierce=True, lifesteal=12.0
            )
            self._broadcast_shot(start_p, aim_dir, 95.0, self.base_damage * 3.8, 0.65, 'cyan', 4.5, True, 0, False)
            for e in list(game.enemies):
                if is_valid(e):
                    e_pos = Vec3(*e.position)
                    if distance(e_pos, my_pos) <= 20.0:
                        LightningBeam(start_p, e_pos + Vec3(0, 1.2, 0), color.yellow, 0.22)
                        e.take_damage(self.base_damage * 1.8)
                        self.hp = min(float(self.max_hp), self.hp + 5.0)
            game.show_banner('ULTRARICOSHOT :: BLOOD IS FUEL!', color.yellow, 1.8)
        elif self.char_key == 'sol':
            self.dragon_install_timer = 6.0
            VisualFX(my_pos + Vec3(0, 1.5, 0), rgb(255, 60, 20), 11.0, 0.45)
            for e in list(game.enemies):
                if is_valid(e):
                    e_pos = Vec3(*e.position)
                    if distance(e_pos, my_pos) <= 11.0:
                        e.take_damage(self.base_damage * 3.4)
            game.show_banner('DRAGON INSTALL :: LET IT OUT!', rgb(255, 120, 30), 2.5)
        elif self.char_key == 'gwen':
            spawn_pos = my_pos + Vec3(0, 1.6, 0)
            base_f = camera.forward
            for angle_deg in (-16, -8, 0, 8, 16):
                rad = math.radians(angle_deg)
                d = Vec3(
                    base_f.x * math.cos(rad) - base_f.z * math.sin(rad),
                    base_f.y,
                    base_f.x * math.sin(rad) + base_f.z * math.cos(rad)
                ).normalized()
                Projectile(
                    pos=spawn_pos, direction=d, speed=62.0,
                    damage=self.base_damage * 2.4, scale_val=0.46,
                    proj_color=rgb(110, 225, 255), is_player=True, aoe=2.5, pierce=True, lifesteal=4.0
                )
                self._broadcast_shot(spawn_pos, d, 62.0, self.base_damage * 2.4, 0.46, 'gwen', 2.5, True, 0, False)

    def take_damage(self, amount):
        game = ctx.game
        if random.random() < self.block_chance:
            VisualFX(Vec3(*self.position) + Vec3(0, 1.4, 0), color.cyan, 2.2, 0.25)
            game.show_banner('ЗАБЛОКИРОВАНО! (Tougher Times)', color.cyan, 0.9)
            return

        dmg = amount
        # Rose Buckler: снижение урона в движении
        if self.is_moving and self.items['rose_buckler'] > 0:
            dmg *= (1.0 / (1.0 + 0.15 * self.items['rose_buckler']))

        # Oddly-shaped Opal: снижение первого удара раз в 5 сек
        if self.items['opal'] > 0 and self.opal_timer <= 0:
            dmg *= max(0.25, 1.0 - (0.20 + 0.10 * self.items['opal']))
            self.opal_timer = 5.0
            VisualFX(Vec3(*self.position) + Vec3(0, 1.2, 0), color.magenta, 2.0, 0.22)

        # Repulsion Armor Plate: плоское снижение урона
        if self.items['repulsion_armor'] > 0:
            dmg = max(1.0, dmg - 4.0 * self.items['repulsion_armor'])

        # Medkit: запуск таймера аптечки
        if self.items['medkit'] > 0:
            self.medkit_timer = 1.1

        # Поглощение урона барьером Topaz Brooch
        if self.shield > 0:
            absorbed = min(self.shield, dmg)
            self.shield -= absorbed
            dmg -= absorbed

        self.hp -= dmg
        if self.hp <= 0:
            self.hp = 0
            game.on_player_death()


# ==========================================
# 4. УДАЛЁННЫЙ ИГРОК ПО СЕТИ (REMOTE PLAYER)
# ==========================================
class RemotePlayer(Entity):
    def __init__(self, player_id, char_key='commando'):
        super().__init__(position=(2, 0, 2))
        self.player_id = player_id
        self.char_key = char_key
        self.target_pos = Vec3(2, 0, 2)
        self.target_rot_y = 0.0
        self.is_moving = False
        self.hp = 110.0
        self.max_hp = 110.0

        self.parts = build_survivor_mesh(self, char_key)
        self.label = Text(
            text=f"[{player_id.upper()}] {SURVIVOR_CLASSES[char_key]['name']}",
            parent=self,
            y=2.85,
            scale=9.5,
            origin=(0, 0),
            color=color.cyan,
            billboard=True
        )
        self.hp_bg = Entity(parent=self, model='quad', scale=(1.2, 0.12), y=2.5, color=color.black, billboard=True)
        self.hp_fill = Entity(parent=self.hp_bg, model='quad', scale=(1, 1), z=-0.01, color=color.green, unlit=True)

    def rebuild_class(self, new_char_key):
        if new_char_key == self.char_key or new_char_key not in SURVIVOR_CLASSES:
            return
        self.char_key = new_char_key
        if self.parts and self.parts.get('root'):
            destroy(self.parts['root'])
        self.parts = build_survivor_mesh(self, new_char_key)
        self.label.text = f"[{self.player_id.upper()}] {SURVIVOR_CLASSES[new_char_key]['name']}"

    def apply_net_state(self, msg):
        self.rebuild_class(msg.get('char_key', self.char_key))
        pos = msg.get('pos', [0, 0, 0])
        self.target_pos = Vec3(pos[0], pos[1], pos[2])
        self.target_rot_y = msg.get('rot_y', 0.0)
        self.is_moving = msg.get('moving', False)
        self.hp = msg.get('hp', self.hp)
        self.max_hp = max(1, msg.get('max_hp', self.max_hp))
        if not self.hp_fill.is_empty():
            self.hp_fill.scale_x = clamp(self.hp / self.max_hp, 0.0, 1.0)

    def update(self):
        if self.is_empty():
            return
        self.position = lerp(self.position, self.target_pos, min(1.0, time.dt * 14.0))
        self.rotation_y = lerp(self.rotation_y, self.target_rot_y, min(1.0, time.dt * 14.0))

        if self.is_moving:
            swing = math.sin(time.time() * 11.5) * 36.0
            self.parts['left_leg'].rotation_x = swing
            self.parts['right_leg'].rotation_x = -swing
        else:
            self.parts['left_leg'].rotation_x = lerp(self.parts['left_leg'].rotation_x, 0, time.dt * 10)
            self.parts['right_leg'].rotation_x = lerp(self.parts['right_leg'].rotation_x, 0, time.dt * 10)

        if self.parts.get('halo'):
            self.parts['halo'].rotation_z += 95 * time.dt


# ==========================================
# 5. 7 ОБЫЧНЫХ ВРАГОВ И 3 БОССА ТЕЛЕПОРТА
# ==========================================
class Enemy(Entity):
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
        self.is_boss = (enemy_type in BOSS_TYPES)
        self.coeff = coeff
        self.is_dead = False
        self.parts = build_enemy_mesh(self, enemy_type)
        self.attack_timer = random.uniform(0.7, 1.6)
        self.special_timer = random.uniform(3.5, 5.5)
        self.seed_offset = (self.net_id * 1.37) % 10.0

        # Статусы от предметов игрока
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
            'boss': (450.0, 22.0, 3.5, 130, 2.8, 2.70),
            'vagrant': (480.0, 20.0, 3.8, 140, 3.8, 2.90),
            'overlord': (520.0, 24.0, 5.2, 150, 2.9, 2.75),
        }
        hp_b, dmg_b, spd_b, gold_b, hh, hr = stats_table.get(enemy_type, stats_table['lemurian'])
        self.max_hp = hp_b * coeff
        self.damage = dmg_b * coeff
        self.speed = spd_b
        self.gold_reward = int(gold_b * coeff)
        self.hit_height = hh
        self.hit_radius = hr
        self.hp = self.max_hp

        bar_y = 6.4 if self.is_boss else (3.6 if enemy_type in ('golem', 'greater_wisp') else 2.6)
        bar_w = 3.2 if self.is_boss else 1.25
        self.hp_bar_bg = Entity(parent=self, model='quad', scale=(bar_w, 0.15), y=bar_y, color=color.black, billboard=True)
        self.hp_bar = Entity(parent=self.hp_bar_bg, model='quad', scale=(1, 1), z=-0.01, color=color.red, unlit=True)

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

    def update(self):
        game = ctx.game
        if not game or not game.running or not is_valid(self):
            return

        # Обработка кровотечения (Tri-Tip Dagger)
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

        # Оглушение (Stun Grenade)
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

        if self.enemy_type == 'lemurian':
            self.parts['tail'].rotation_y = math.sin(t * 6) * 22
            if dist > 1.7:
                self.position += self.forward * eff_speed * time.dt
                resolved = game.resolve_horizontal_collision(Vec3(*self.position), 0.7, 0)
                self.position = Vec3(resolved.x, 0, resolved.z)
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
                resolved = game.resolve_horizontal_collision(Vec3(*self.position), 0.65, 0)
                self.position = Vec3(resolved.x, 0, resolved.z)
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
                resolved = game.resolve_horizontal_collision(Vec3(*self.position), 0.95, 0)
                self.position = Vec3(resolved.x, 0, resolved.z)
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
                resolved = game.resolve_horizontal_collision(jump_pos, 0.7, 0)
                self.position = Vec3(resolved.x, 0, resolved.z)
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

        elif self.enemy_type == 'boss':
            self.parts['crown'].rotation_y += 85 * time.dt
            if dist > 8.5:
                self.position += self.forward * eff_speed * time.dt
                stomp = math.sin(t * 4.5) * 24
                self.parts['left_leg'].rotation_x = stomp
                self.parts['right_leg'].rotation_x = -stomp
                self.parts['left_arm'].rotation_x = -stomp * 0.5
                self.parts['right_arm'].rotation_x = stomp * 0.5

            self.attack_timer -= time.dt
            if self.attack_timer <= 0:
                base_aim = (p_pos + Vec3(0, 1.2, 0)) - (my_pos + Vec3(0, 3.4, 0))
                for angle in (-14, 0, 14):
                    rot_dir = Vec3(
                        base_aim.x * math.cos(math.radians(angle)) - base_aim.z * math.sin(math.radians(angle)),
                        base_aim.y,
                        base_aim.x * math.sin(math.radians(angle)) + base_aim.z * math.cos(math.radians(angle))
                    )
                    Projectile(my_pos + Vec3(0, 3.4, 0), rot_dir, 27.0, self.damage, 0.65, color.red, is_player=False)
                self.attack_timer = 2.0

        elif self.enemy_type == 'vagrant':
            # БОСС 2: Wandering Vagrant
            self.parts['bell'].y = 4.2 + math.sin(t * 2.8) * 0.45
            self.parts['tentacles'].rotation_y += 65 * time.dt
            if dist > 12.0:
                self.position += self.forward * eff_speed * time.dt

            self.attack_timer -= time.dt
            if self.attack_timer <= 0:
                sp = my_pos + Vec3(0, 3.8, 0)
                base_aim = (p_pos + Vec3(0, 1.2, 0)) - sp
                for angle in (-18, -6, 6, 18):
                    rad = math.radians(angle)
                    rot_dir = Vec3(
                        base_aim.x * math.cos(rad) - base_aim.z * math.sin(rad),
                        base_aim.y,
                        base_aim.x * math.sin(rad) + base_aim.z * math.cos(rad)
                    )
                    Projectile(sp, rot_dir, 24.0, self.damage * 0.85, 0.62, color.cyan, is_player=False)
                self.attack_timer = 2.2

            # Сверхновая при низком здоровье
            self.special_timer -= time.dt
            if self.special_timer <= 0:
                self.special_timer = 6.5
                VisualFX(my_pos + Vec3(0, 3.8, 0), color.cyan, 16.0, 0.55)
                if is_local_target and is_valid(game.player) and dist <= 13.5:
                    game.player.take_damage(self.damage * 1.35)

        elif self.enemy_type == 'overlord':
            # БОСС 3: Imp Overlord
            self.parts['crown'].rotation_y -= 95 * time.dt
            if dist > 5.5:
                self.position += self.forward * eff_speed * time.dt
                stomp = math.sin(t * 6.0) * 28
                self.parts['left_leg'].rotation_x = stomp
                self.parts['right_leg'].rotation_x = -stomp

            self.attack_timer -= time.dt
            if self.attack_timer <= 0:
                sp = my_pos + Vec3(0, 3.2, 0)
                base_aim = (p_pos + Vec3(0, 1.2, 0)) - sp
                for angle in (-20, -10, 0, 10, 20):
                    rad = math.radians(angle)
                    rot_dir = Vec3(
                        base_aim.x * math.cos(rad) - base_aim.z * math.sin(rad),
                        base_aim.y,
                        base_aim.x * math.sin(rad) + base_aim.z * math.cos(rad)
                    )
                    Projectile(sp, rot_dir, 32.0, self.damage * 0.8, 0.55, rgb(245, 30, 65), is_player=False)
                self.attack_timer = 2.1

            # Телепорт-прыжок к игроку
            self.special_timer -= time.dt
            if self.special_timer <= 0 and dist > 7.0:
                self.special_timer = 5.5
                VisualFX(my_pos + Vec3(0, 2.5, 0), rgb(245, 30, 65), 6.0, 0.35)
                tp_dest = p_pos - self.forward * 3.5
                self.position = Vec3(clamp(tp_dest.x, -52, 52), 0, clamp(tp_dest.z, -52, 52))
                VisualFX(Vec3(*self.position) + Vec3(0, 1.5, 0), rgb(245, 30, 65), 8.5, 0.4)

    def take_damage(self, amount, from_network=False):
        if not is_valid(self):
            return
        self.hp -= amount
        if not self.hp_bar.is_empty():
            self.hp_bar.scale_x = max(0.0, self.hp / self.max_hp)

        if not from_network and getattr(ctx, 'net', None) and ctx.net.connected:
            ctx.net.broadcast({'type': 'enemy_damage', 'net_id': self.net_id, 'amount': round(amount, 1)})

        if self.hp <= 0:
            self.die(from_network=from_network)

    def die(self, from_network=False):
        game = ctx.game
        if self.is_dead or self.is_empty():
            return
        self.is_dead = True

        death_pos = Vec3(*self.position)

        if self in game.enemies:
            game.enemies.remove(self)

        VisualFX(death_pos + Vec3(0, 1.2, 0), color.orange, 3.2, 0.35)

        PROGRESS.kills += 1
        if PROGRESS.kills >= 12:
            game.unlock_achievement('ach_slayer')

        if is_valid(game.player):
            p = game.player
            it = p.items
            p.gold += self.gold_reward

            # Monster Tooth: лечение при убийстве
            if it['monster_tooth'] > 0:
                p.hp = min(float(p.max_hp), p.hp + 4.0 + 4.0 * it['monster_tooth'])

            # Topaz Brooch: временный щит при убийстве
            if it['topaz_brooch'] > 0:
                p.shield = min(float(p.max_hp), p.shield + 15.0 * it['topaz_brooch'])

            # Infusion: постоянное увеличение макс. HP
            if it['infusion'] > 0 and p.infusion_bonus < 40.0 * it['infusion']:
                p.infusion_bonus += 1.0
                p.hp = min(float(p.max_hp), p.hp + 1.0)

            # Bandolier: сокращение перезарядки всех навыков
            if it['bandolier'] > 0 and random.random() < min(0.65, 0.18 * it['bandolier']):
                p.m2_cd = max(0.0, p.m2_cd - 1.5)
                p.shift_cd = max(0.0, p.shift_cd - 1.5)
                p.r_cd = max(0.0, p.r_cd - 1.5)

            # Gasoline + Will-o'-the-wisp: цепные взрывы при смерти
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
            game.active_boss = None
            if not from_network:
                game.spawn_item_drop(death_pos)

        PROGRESS.save()
        destroy(self)