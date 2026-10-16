from ursina import *
import math
import random
from config import ctx, rgb, is_valid, ITEM_POOL, SURVIVOR_CLASSES, PROGRESS
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
                if is_valid(e) and distance_2d(Vec3(*e.position), p) <= 4.5:
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
                    if is_valid(e) and distance_2d(Vec3(*e.position), my_pos) <= self.radius:
                        e.take_damage(self.tick_dmg)


# ==========================================
# 2. УНИВЕРСАЛЬНЫЕ СНАРЯДЫ
# ==========================================
class Projectile(Entity):
    def __init__(
        self, pos, direction, speed, damage, scale_val, proj_color,
        is_player=True, aoe=0.0, pierce=False, bounces=0, homing=False, is_remote=False
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
            best_d = 22.0
            for e in game.enemies:
                if is_valid(e) and e not in self.hit_memory:
                    d = distance(my_pos, Vec3(*e.position) + Vec3(0, e.hit_height, 0))
                    if d < best_d:
                        best_d = d
                        nearest = e
            if nearest:
                desired = ((Vec3(*nearest.position) + Vec3(0, nearest.hit_height, 0)) - my_pos).normalized()
                self.direction = lerp(self.direction, desired, time.dt * 6.5).normalized()

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
                            LightningBeam(my_pos, next_pos, color.cyan, 0.22)
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

        dmg = self.damage
        is_crit = random.random() < p.crit_chance
        if is_crit:
            dmg *= 2.0
            VisualFX(proj_pos, rgb(255, 45, 70), max_scale=2.2, duration=0.25)

        target.take_damage(dmg)
        VisualFX(proj_pos, self.color, max_scale=1.3 if self.aoe == 0 else self.aoe * 1.5, duration=0.22)

        if self.aoe > 0:
            for other in list(game.enemies):
                if other is not target and is_valid(other):
                    if distance(Vec3(*other.position), target_pos) <= self.aoe:
                        other.take_damage(dmg * 0.65)

        ukulele_stacks = p.items['ukulele']
        if ukulele_stacks > 0 and random.random() < 0.25:
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

        self.max_hp = cfg['hp']
        self.hp = float(cfg['hp'])
        self.base_speed = cfg['speed']
        self.base_damage = cfg['damage']
        self.base_fire_rate = cfg['fire_rate']
        self.proj_speed = cfg['proj_speed']
        self.proj_scale = cfg['proj_scale']
        self.proj_aoe = cfg['aoe']

        self.items = {k: 0 for k in ITEM_POOL.keys()}
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
        self.shoot_side = 0
        self.is_moving = False
        self.net_sync_timer = 0.0

        self.parts = build_survivor_mesh(self, char_key)

        self.cam_pivot = Entity(parent=self, y=2.15)
        camera.parent = self.cam_pivot
        camera.position = (0.85, 0.75, -8.8)
        camera.rotation = (6, 0, 0)

    @property
    def dash_cooldown(self):
        """Совместимость с проверками кулдауна рывка в UI"""
        return self.shift_cd

    @property
    def move_speed(self):
        return self.base_speed * (1.0 + 0.14 * self.items['hoof'])

    @property
    def fire_rate(self):
        return self.base_fire_rate * (1.0 + 0.15 * self.items['syringe'])

    @property
    def block_chance(self):
        stacks = self.items['bear']
        return 1.0 - (1.0 / (1.0 + 0.15 * stacks))

    @property
    def crit_chance(self):
        return min(1.0, 0.05 + 0.10 * self.items['lens'])

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
            self.cam_pivot.rotation_x = clamp(self.cam_pivot.rotation_x - mouse.velocity[1] * sens, -38, 52)

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

        self.hp = min(float(self.max_hp), self.hp + 1.5 * time.dt)

        if self.parts['halo']:
            self.parts['halo'].rotation_z += 95 * time.dt

        if mouse.locked:
            if mouse.left and self.m1_cd <= 0:
                self.use_m1_skill()
            if mouse.right and self.m2_cd <= 0:
                self.use_m2_skill()

        # Отправка позиции по сети (20 раз в секунду)
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
        default_col = color.yellow if self.char_key == 'commando' else (color.magenta if self.char_key == 'artificer' else rgb(255, 80, 100))
        proj_col = col_override if col_override else default_col
        col_name = 'cyan' if col_override else self.char_key

        Projectile(
            pos=spawn_pos,
            direction=aim_dir,
            speed=self.proj_speed,
            damage=self.base_damage * damage_mult,
            scale_val=self.proj_scale,
            proj_color=proj_col,
            is_player=True,
            aoe=self.proj_aoe,
            homing=(self.char_key == 'huntress')
        )
        self._broadcast_shot(spawn_pos, aim_dir, self.proj_speed, self.base_damage * damage_mult, self.proj_scale, col_name, self.proj_aoe, False, 0, self.char_key == 'huntress')

        arm = self.parts['left_arm'] if self.shoot_side % 2 == 0 else self.parts['right_arm']
        self.shoot_side += 1
        arm.rotation_x = -24
        arm.animate_rotation_x(0, duration=0.11)

    def use_m1_skill(self):
        self.m1_cd = 1.0 / self.fire_rate
        self.fire_primary_projectile()

    def use_m2_skill(self):
        skills = SURVIVOR_CLASSES[self.char_key]['skills']
        self.m2_cd = skills['m2']['cd']
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

    def use_shift_skill(self):
        game = ctx.game
        skills = SURVIVOR_CLASSES[self.char_key]['skills']
        self.shift_cd = skills['shift']['cd']
        my_pos = Vec3(*self.position)
        VisualFX(my_pos + Vec3(0, 1, 0), color.cyan, 2.4, 0.3)

        if self.char_key == 'commando':
            self.dash_vector = self.forward * 28.0
            self.dash_timer = 0.22
        elif self.char_key == 'artificer':
            self.vel_y = 16.5
            self.grounded = False
            self.dash_vector = self.forward * 18.0
            self.dash_timer = 0.32
            for e in list(game.enemies):
                if is_valid(e) and distance(Vec3(*e.position), my_pos) <= 6.8:
                    e.take_damage(self.base_damage * 1.8)
        elif self.char_key == 'huntress':
            blink_dir = camera.forward
            blink_dir.y = max(0.0, blink_dir.y)
            target_pos = my_pos + blink_dir.normalized() * 11.0
            LightningBeam(my_pos + Vec3(0, 1, 0), target_pos + Vec3(0, 1, 0), color.cyan, 0.28)
            resolved = game.resolve_horizontal_collision(target_pos, 0.72, self.y)
            self.position = Vec3(clamp(resolved.x, -56, 56), max(0.0, target_pos.y), clamp(resolved.z, -56, 56))
            VisualFX(Vec3(*self.position) + Vec3(0, 1, 0), color.cyan, 2.4, 0.3)

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
                if i < len(targets):
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

    def take_damage(self, amount):
        game = ctx.game
        if random.random() < self.block_chance:
            VisualFX(Vec3(*self.position) + Vec3(0, 1.4, 0), color.cyan, 2.2, 0.25)
            game.show_banner('ЗАБЛОКИРОВАНО! (Tougher Times)', color.cyan, 0.9)
            return

        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            game.on_player_death()


# ==========================================
# 4. УДАЛЁННЫЙ ИГРОК ПО СЕТИ (REMOTE PLAYER)
# ==========================================
class RemotePlayer(Entity):
    """Отображает реального союзника, подключённого по LAN или коду комнаты"""
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
# 5. ВРАГИ И БОСС (С СИНХРОНИЗАЦИЕЙ ПО СЕТИ)
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
        self.coeff = coeff
        self.is_dead = False
        self.parts = build_enemy_mesh(self, enemy_type)
        self.attack_timer = random.uniform(0.6, 1.5)
        self.seed_offset = (self.net_id * 1.37) % 10.0

        if enemy_type == 'lemurian':
            self.max_hp = 36.0 * coeff
            self.damage = 9.0 * coeff
            self.speed = 6.3
            self.gold_reward = int(13 * coeff)
            self.hit_height = 1.1
            self.hit_radius = 1.15
        elif enemy_type == 'wisp':
            self.max_hp = 26.0 * coeff
            self.damage = 11.5 * coeff
            self.speed = 4.6
            self.gold_reward = int(16 * coeff)
            self.hit_height = 2.3
            self.hit_radius = 1.25
        elif enemy_type == 'boss':
            self.max_hp = 450.0 * coeff
            self.damage = 22.0 * coeff
            self.speed = 3.5
            self.gold_reward = int(130 * coeff)
            self.hit_height = 2.8
            self.hit_radius = 2.7

        self.hp = self.max_hp

        bar_y = 6.2 if enemy_type == 'boss' else 2.6
        bar_w = 3.2 if enemy_type == 'boss' else 1.2
        self.hp_bar_bg = Entity(parent=self, model='quad', scale=(bar_w, 0.15), y=bar_y, color=color.black, billboard=True)
        self.hp_bar = Entity(parent=self.hp_bar_bg, model='quad', scale=(1, 1), z=-0.01, color=color.red, unlit=True)

    def _get_nearest_target(self, game):
        """Выбирает ближайшего выжившего (локального или сетевого)"""
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

        p_pos, dist, is_local_target = self._get_nearest_target(game)
        if p_pos is None:
            return

        my_pos = Vec3(*self.position)
        self.look_at_2d(p_pos, 'y')
        t = time.time() + self.seed_offset

        if self.enemy_type == 'lemurian':
            self.parts['tail'].rotation_y = math.sin(t * 6) * 22
            if dist > 1.7:
                self.position += self.forward * self.speed * time.dt
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

        elif self.enemy_type == 'wisp':
            self.parts['ring1'].rotation_x += 120 * time.dt
            self.parts['ring2'].rotation_y += 145 * time.dt
            self.parts['core'].y = 2.3 + math.sin(t * 4) * 0.28

            if dist > 16.0:
                self.position += self.forward * self.speed * time.dt
            self.attack_timer -= time.dt
            if self.attack_timer <= 0 and dist < 36.0:
                aim = (p_pos + Vec3(0, 1.2, 0)) - (my_pos + Vec3(0, 2.3, 0))
                Projectile(my_pos + Vec3(0, 2.3, 0), aim, 25.0, self.damage, 0.35, color.orange, is_player=False)
                self.attack_timer = 2.4

        elif self.enemy_type == 'boss':
            self.parts['crown'].rotation_y += 85 * time.dt
            if dist > 8.5:
                self.position += self.forward * self.speed * time.dt
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

        if is_valid(game.player):
            game.player.gold += self.gold_reward
        VisualFX(death_pos + Vec3(0, 1.2, 0), color.orange, 3.2, 0.35)

        PROGRESS.kills += 1
        if PROGRESS.kills >= 12:
            game.unlock_achievement('ach_slayer')

        if is_valid(game.player):
            gas_stacks = game.player.items['gasoline']
            if gas_stacks > 0 and not from_network:
                radius = 6.0 + gas_stacks * 2.0
                burn_dmg = game.player.base_damage * (1.2 + 0.6 * gas_stacks)
                VisualFX(death_pos + Vec3(0, 1.0, 0), color.red, radius * 1.4, 0.4)
                for other in list(game.enemies):
                    if is_valid(other) and distance(Vec3(*other.position), death_pos) <= radius:
                        other.take_damage(burn_dmg)

        if self.enemy_type == 'boss':
            PROGRESS.boss_kills += 1
            game.unlock_achievement('ach_boss')
            game.active_boss = None
            if not from_network:
                game.spawn_item_drop(death_pos)

        PROGRESS.save()
        destroy(self)