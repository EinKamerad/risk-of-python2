from ursina import *
import math
import random
from config import ctx, rgb, is_valid, ITEM_POOL, SURVIVOR_CLASSES
from models.survivors import build_survivor_mesh
from entities.fx import VisualFX
from entities.survivor_skills import SurvivorSkillsMixin

class Survivor(Entity, SurvivorSkillsMixin):
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
    def base_damage(self):
        raw = SURVIVOR_CLASSES[self.char_key]['damage']
        glass_mult = 2.0 ** self.items.get('shaped_glass', 0)
        tonic_mult = 1.0 + 0.25 * self.items.get('spinel_tonic', 0)
        return raw * glass_mult * tonic_mult

    @base_damage.setter
    def base_damage(self, val):
        pass

    @property
    def max_hp(self):
        raw = self.base_max_hp + 25 * self.items['bison_steak'] + self.infusion_bonus
        trans_mult = 1.0 + 0.50 * self.items.get('transcendence', 0)
        flux_mult = 2.0 ** self.items.get('lunar_pauldron', 0)
        tonic_mult = 1.0 + 0.25 * self.items.get('spinel_tonic', 0)
        glass_div = 0.5 ** self.items.get('shaped_glass', 0)
        return max(1, int(raw * trans_mult * flux_mult * tonic_mult * glass_div))

    @property
    def dash_cooldown(self):
        return self.shift_cd

    @property
    def move_speed(self):
        di_mult = 1.45 if self.dragon_install_timer > 0 else 1.0
        tonic_mult = 1.0 + 0.25 * self.items.get('spinel_tonic', 0)
        flux_pen = 0.70 ** self.items.get('lunar_pauldron', 0)
        spd_bonus = (
            1.0
            + 0.14 * self.items['hoof']
            + 0.08 * self.items['energy_drink']
            + 0.12 * self.items['red_whip']
        )
        return self.base_speed * spd_bonus * di_mult * tonic_mult * flux_pen

    @property
    def fire_rate(self):
        di_mult = 1.65 if self.dragon_install_timer > 0 else 1.0
        tonic_mult = 1.0 + 0.25 * self.items.get('spinel_tonic', 0)
        pred_bonus = 0.12 * self.items['predatory'] if self.predatory_timer > 0 else 0.0
        return self.base_fire_rate * (1.0 + 0.15 * self.items['syringe'] + pred_bonus) * di_mult * tonic_mult

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

