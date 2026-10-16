from ursina import *
import math
import random
from config import ctx, rgb, is_valid, SURVIVOR_CLASSES
from entities.fx import VisualFX, LightningBeam, OrbitalStrikeFX, ArrowRainZone, HallowedMistZone
from entities.projectile import Projectile

class SurvivorSkillsMixin:
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

