from ursina import *
import math
import random
from config import ctx, rgb, is_valid, SURVIVOR_CLASSES
from entities.fx import (
    VisualFX, MeleeSlashFX, TearGasZone, IFGZone, DummyClone, MindustryTurret,
    LightningBeam, OrbitalStrikeFX, ArrowRainZone, HallowedMistZone
)
from entities.projectile import Projectile, apply_player_hit_effects


def distance_2d(a, b):
    """Переопределяет distance_2d на горизонтальную плоскость X-Z для 3D-мира"""
    return math.hypot(a[0] - b[0], a[2] - b[2])


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

    def perform_melee_attack(
        self, reach=5.2, cleave_radius=3.4, damage_mult=1.0, slash_col=color.orange,
        lifesteal=0.0, stun_dur=0.0, knockback=0.0, scissor_cross=False, aoe=0.0
    ):
        """Настоящая атака ближнего боя: создаёт 3D-дугу удара и поражает всех врагов в конусе перед выжившим"""
        game = ctx.game
        if not game:
            return 0

        my_pos = Vec3(*self.position)
        fwd = Vec3(self.forward.x, 0, self.forward.z).normalized()
        if fwd.length() < 0.01:
            fwd = Vec3(0, 0, 1)

        self.shoot_side += 1
        tilt = 22.0 if self.shoot_side % 2 == 0 else -22.0

        MeleeSlashFX(
            pos=my_pos,
            forward_dir=fwd,
            rot_y=self.rotation_y,
            slash_color=slash_col,
            arc_width=cleave_radius * 1.15,
            reach=reach,
            tilt_z=tilt,
            scissor_cross=scissor_cross
        )

        strike_center = my_pos + fwd * (reach * 0.55)
        hit_count = 0

        for e in list(game.enemies):
            if not is_valid(e) or getattr(e, 'is_ally', False):
                continue
            e_pos = Vec3(*e.position)
            if abs((e_pos.y + e.hit_height * 0.5) - (my_pos.y + 1.2)) > 4.2:
                continue

            to_enemy = e_pos - my_pos
            dist_from_player = distance_2d(e_pos, my_pos)
            dist_from_arc = distance_2d(e_pos, strike_center)

            in_cone = False
            if dist_from_player <= reach + e.hit_radius:
                flat_dir = Vec3(to_enemy.x, 0, to_enemy.z).normalized()
                dot = fwd.x * flat_dir.x + fwd.z * flat_dir.z
                if dot >= 0.15 or dist_from_player <= 2.4 + e.hit_radius:
                    in_cone = True

            if in_cone or dist_from_arc <= cleave_radius + e.hit_radius * 0.6:
                hit_count += 1
                hit_p = e_pos + Vec3(0, e.hit_height, 0)
                apply_player_hit_effects(
                    target=e,
                    hit_pos=hit_p,
                    base_dmg=self.base_damage * damage_mult,
                    hit_color=slash_col,
                    aoe=aoe,
                    lifesteal=lifesteal,
                    can_proc=True
                )
                if is_valid(e):
                    if stun_dur > 0 and not e.is_boss:
                        e.stun_timer = max(e.stun_timer, stun_dur)
                    if knockback > 0 and not e.is_boss:
                        push_p = e_pos + fwd * knockback
                        resolved = game.resolve_horizontal_collision(push_p, 0.8, e.y)
                        e.x = resolved.x
                        e.z = resolved.z

        return hit_count

    def _find_grapple_anchor(self, start_pos, aim_dir, max_dist=45.0):
        """Находит точку зацепа крюка-кошки Скаута (препятствие, платформу, врага или точку впереди)"""
        game = ctx.game
        step = 1.5
        cur = Vec3(*start_pos)
        for i in range(1, int(max_dist / step) + 1):
            p = start_pos + aim_dir * (i * step)
            if game.is_inside_solid_obstacle(p, 0.35):
                return p
            surf_h = game.get_surface_height(p.x, p.z, p.y + 1.2)
            if p.y <= surf_h + 0.3:
                return Vec3(p.x, surf_h + 0.5, p.z)
            for e in game.enemies:
                if is_valid(e) and distance(p, Vec3(*e.position) + Vec3(0, e.hit_height, 0)) <= e.hit_radius + 0.6:
                    return Vec3(*e.position) + Vec3(0, e.hit_height, 0)
            cur = p
        floor_y = game.get_surface_height(cur.x, cur.z, cur.y)
        return Vec3(cur.x, max(floor_y + 1.0, cur.y), cur.z)

    def fire_primary_projectile(self, damage_mult=1.0, col_override=None):
        # 1. СОЛ БЭДГАЙ: Ближний бой мечом Junkyard Dog
        if self.char_key == 'sol' and col_override is None:
            di_bonus = 1.25 if self.dragon_install_timer > 0 else 1.0
            reach = 5.8 if self.dragon_install_timer > 0 else 5.2
            self.perform_melee_attack(
                reach=reach,
                cleave_radius=3.5,
                damage_mult=damage_mult * di_bonus,
                slash_col=rgb(255, 115, 25),
                lifesteal=2.2 if self.dragon_install_timer > 0 else 1.0,
                knockback=1.2,
                aoe=2.2
            )
            if self.is_moving and self.grounded and self.dash_timer <= 0:
                self.position += self.forward * 0.35

            arm = self.parts['right_arm']
            arm.rotation_x = -75 if self.shoot_side % 2 == 0 else -35
            arm.rotation_z = -28 if self.shoot_side % 2 == 0 else 28
            arm.animate_rotation((0, 0, 0), duration=0.15)
            return

        # 2. ГВЕН: Ближний бой ножницами Snip Snip!
        if self.char_key == 'gwen' and col_override is None:
            self.perform_melee_attack(
                reach=4.8,
                cleave_radius=3.1,
                damage_mult=damage_mult,
                slash_col=rgb(95, 225, 255),
                lifesteal=2.4,
                scissor_cross=True,
                aoe=1.5
            )
            arm = self.parts['right_arm']
            arm.rotation_x = -65 if self.shoot_side % 2 == 0 else -30
            arm.rotation_y = -20 if self.shoot_side % 2 == 0 else 20
            arm.animate_rotation((0, 0, 0), duration=0.11)
            return

        # 3. ENFORCER: Помповый дробовик Riot Shotgun
        if self.char_key == 'enforcer' and col_override is None:
            aim_dir = camera.forward
            spawn_pos = Vec3(*self.position) + Vec3(0, 1.55, 0) + self.forward * 1.05
            spread = 0.032 if getattr(self, 'shield_stance', False) else 0.075
            for _ in range(6):
                offset = Vec3(
                    random.uniform(-spread, spread),
                    random.uniform(-spread * 0.6, spread * 0.6),
                    random.uniform(-spread, spread)
                )
                d = (aim_dir + offset).normalized()
                Projectile(
                    pos=spawn_pos,
                    direction=d,
                    speed=self.proj_speed,
                    damage=self.base_damage * 0.52 * damage_mult,
                    scale_val=0.20,
                    proj_color=rgb(110, 225, 255),
                    is_player=True,
                    pierce=True,
                    max_lifetime=0.52
                )
            VisualFX(spawn_pos, rgb(120, 225, 255), 1.4, 0.14)
            self._broadcast_shot(
                spawn_pos, aim_dir, self.proj_speed, self.base_damage * damage_mult,
                0.24, 'enforcer', 0.0, True, 0, False
            )
            arm = self.parts['right_arm']
            arm.rotation_x = -34
            arm.animate_rotation_x(0, duration=0.18)
            return

        # 4. ХАКУРЕЙ РЕЙМУ: Парные самонаводящиеся амулеты Офуда (красно-белые)
        if self.char_key == 'reimu' and col_override is None:
            aim_dir = camera.forward
            base_pos = Vec3(*self.position) + Vec3(0, 1.55, 0) + self.forward * 0.9
            for idx, side_off in enumerate((-0.32, 0.32)):
                sp = base_pos + self.right * side_off
                amu_col = rgb(255, 55, 70) if idx == 0 else color.white
                Projectile(
                    pos=sp, direction=aim_dir, speed=self.proj_speed,
                    damage=self.base_damage * 0.65 * damage_mult,
                    scale_val=self.proj_scale, proj_color=amu_col,
                    is_player=True, aoe=self.proj_aoe, homing=True
                )
            self._broadcast_shot(
                base_pos, aim_dir, self.proj_speed, self.base_damage * damage_mult,
                self.proj_scale, 'reimu', self.proj_aoe, False, 0, True
            )
            arm = self.parts['right_arm']
            arm.rotation_x = -28
            arm.animate_rotation_x(0, duration=0.12)
            return

        # 5. КОРАБЛЬ MINDUSTRY: Спаренные бортовые пушки с обоих крыльев
        if self.char_key == 'mindustry' and col_override is None:
            aim_dir = camera.forward
            base_pos = Vec3(*self.position) + Vec3(0, 1.45, 0) + self.forward * 1.0
            for side_off in (-0.55, 0.55):
                sp = base_pos + self.right * side_off
                Projectile(
                    pos=sp, direction=aim_dir, speed=self.proj_speed,
                    damage=self.base_damage * 0.58 * damage_mult,
                    scale_val=self.proj_scale, proj_color=rgb(255, 215, 65),
                    is_player=True, aoe=self.proj_aoe
                )
            self._broadcast_shot(
                base_pos, aim_dir, self.proj_speed, self.base_damage * damage_mult,
                self.proj_scale, 'mindustry', self.proj_aoe, False, 0, False
            )
            return

        # 6. Остальные стрелковые классы (Commando, Artificer, Huntress, Buzz, V1, Scout, M4A1, Medic, Aigis)
        aim_dir = camera.forward
        spawn_pos = Vec3(*self.position) + Vec3(0, 1.55, 0) + self.forward * 0.95
        color_map = {
            'commando': color.yellow,
            'artificer': color.magenta,
            'huntress': rgb(255, 80, 100),
            'buzz': rgb(110, 255, 80),
            'v1': rgb(255, 230, 50),
            'sol': rgb(255, 110, 25),
            'gwen': rgb(95, 225, 255),
            'enforcer': rgb(110, 225, 255),
            'scout': rgb(255, 215, 65),
            'm4a1': rgb(95, 255, 135),
            'medic': rgb(255, 75, 90),
            'aigis': rgb(255, 235, 95),
            'reimu': rgb(255, 65, 80),
            'mindustry': rgb(255, 215, 65)
        }
        default_col = color_map.get(self.char_key, color.yellow)
        proj_col = col_override if col_override else default_col
        col_name = 'cyan' if col_override else self.char_key

        steal = 1.6 if self.char_key == 'v1' else 0.0
        ally_heal = (12.0 + self.base_damage * 0.85) if self.char_key == 'medic' else 0.0

        Projectile(
            pos=spawn_pos,
            direction=aim_dir,
            speed=self.proj_speed,
            damage=self.base_damage * damage_mult,
            scale_val=self.proj_scale,
            proj_color=proj_col,
            is_player=True,
            aoe=self.proj_aoe,
            pierce=False,
            homing=(self.char_key == 'huntress'),
            lifesteal=steal,
            heal_allies=ally_heal
        )
        self._broadcast_shot(
            spawn_pos, aim_dir, self.proj_speed, self.base_damage * damage_mult,
            self.proj_scale, col_name, self.proj_aoe, False, 0, self.char_key == 'huntress'
        )

        if self.char_key in ('buzz', 'v1', 'scout', 'm4a1', 'medic', 'aigis'):
            arm = self.parts['right_arm']
            arm.rotation_x = -26
            arm.animate_rotation_x(0, duration=0.12)
        else:
            arm = self.parts['left_arm'] if self.shoot_side % 2 == 0 else self.parts['right_arm']
            self.shoot_side += 1
            arm.rotation_x = -24
            arm.animate_rotation_x(0, duration=0.11)

    def use_m1_skill(self):
        self.m1_cd = 1.0 / self.fire_rate
        self.fire_primary_projectile()

    def use_m2_skill(self):
        if getattr(self, 'skill_lock_timer', 0.0) > 0:
            ctx.game.show_banner(f'НЕЙРОСЕТЬ ПЕРЕГРУЖЕНА ПОСЛЕ ПЕРЕСЕЛЕНИЯ ({self.skill_lock_timer:.1f}С)!', color.red, 1.2)
            return

        game = ctx.game
        skills = SURVIVOR_CLASSES[self.char_key]['skills']
        alien_cdr = 0.80 ** self.items.get('alien_head', 0)
        cd_mult = max(0.20, (1.0 - 0.12 * self.items['backup_mag']) * alien_cdr)
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
            self.vel_y = 14.5
            self.grounded = False
            self.perform_melee_attack(
                reach=6.5, cleave_radius=4.5, damage_mult=2.8,
                slash_col=rgb(255, 90, 20), lifesteal=4.0, knockback=3.0, aoe=3.5
            )
            gf_dir = Vec3(self.forward.x, 0.0, self.forward.z).normalized()
            Projectile(
                pos=spawn_pos, direction=gf_dir, speed=34.0,
                damage=self.base_damage * 1.8, scale_val=0.85,
                proj_color=rgb(255, 110, 20), is_player=True, aoe=4.2, pierce=True, max_lifetime=0.38
            )

        elif self.char_key == 'gwen':
            self.perform_melee_attack(
                reach=7.2, cleave_radius=4.2, damage_mult=3.2,
                slash_col=rgb(155, 240, 255), lifesteal=6.5, scissor_cross=True, aoe=2.8
            )
            arm = self.parts['right_arm']
            arm.rotation_x = -95
            arm.animate_rotation_x(0, duration=0.22)

        elif self.char_key == 'enforcer':
            self.dash_vector = self.forward * 16.0
            self.dash_timer = 0.16
            self.shield = min(float(self.max_hp), self.shield + 20.0)
            self.perform_melee_attack(
                reach=5.6, cleave_radius=3.8, damage_mult=2.6,
                slash_col=color.cyan, stun_dur=2.0, knockback=5.5, aoe=2.5
            )
            l_arm = self.parts['left_arm']
            l_arm.rotation_y = 45
            l_arm.animate_rotation_y(0, duration=0.22)

        elif self.char_key == 'scout':
            for _ in range(8):
                offset = Vec3(random.uniform(-0.09, 0.09), random.uniform(-0.06, 0.06), random.uniform(-0.09, 0.09))
                d = (aim_dir + offset).normalized()
                Projectile(
                    pos=spawn_pos, direction=d, speed=66.0,
                    damage=self.base_damage * 0.55, scale_val=0.24,
                    proj_color=color.orange, is_player=True, pierce=True, max_lifetime=0.38
                )
            self.perform_melee_attack(
                reach=4.8, cleave_radius=3.4, damage_mult=1.6,
                slash_col=color.orange, knockback=4.5, aoe=2.0
            )
            if not self.grounded or aim_dir.y < -0.15:
                recoil_dir = -aim_dir
                self.vel_y = max(14.5, recoil_dir.y * 22.0)
                self.grounded = False
                self.dash_vector = Vec3(recoil_dir.x, 0, recoil_dir.z) * 24.0
                self.dash_timer = 0.28
                VisualFX(spawn_pos, color.yellow, 3.2, 0.25)

        elif self.char_key == 'm4a1':
            VisualFX(spawn_pos, rgb(95, 255, 135), 3.0, 0.28)
            Projectile(
                pos=spawn_pos, direction=aim_dir, speed=58.0,
                damage=self.base_damage * 3.4, scale_val=0.78,
                proj_color=rgb(95, 255, 135), is_player=True, aoe=6.8, pierce=True
            )
            self._broadcast_shot(spawn_pos, aim_dir, 58.0, self.base_damage * 3.4, 0.78, 'buzz', 6.8, True, 0, False)
            for clone in list(getattr(self, 'dummy_clones', [])):
                if is_valid(clone):
                    clone.command_burst_shot()

        elif self.char_key == 'medic':
            # Kritzkrieg Medi-Beam: лечит и баффает союзников впереди + выкачивает HP из врагов по лучу
            my_pos = Vec3(*self.position) + Vec3(0, 1.4, 0)
            end_beam = my_pos + aim_dir * 26.0
            LightningBeam(my_pos, end_beam, rgb(255, 55, 80), 0.32)
            self.heal_amount(18.0)
            self.shield = min(float(self.max_hp), self.shield + 20.0)

            allies = (
                list(getattr(self, 'dummy_clones', []))
                + list(getattr(self, 'mindustry_turrets', []))
                + [e for e in game.enemies if is_valid(e) and getattr(e, 'is_ally', False)]
                + list(game.remote_players.values())
            )
            for al in allies:
                if is_valid(al) and distance(my_pos, Vec3(*al.position)) <= 24.0:
                    if hasattr(al, 'heal_ally'):
                        al.heal_ally(amount=al.max_hp * 0.40, shield_amt=20.0)
                    else:
                        al.hp = min(float(al.max_hp), al.hp + al.max_hp * 0.40)
                    LightningBeam(my_pos, Vec3(*al.position) + Vec3(0, 1.2, 0), color.lime, 0.24)
                    VisualFX(Vec3(*al.position) + Vec3(0, 1.2, 0), color.lime, 2.5, 0.25)

            Projectile(
                pos=spawn_pos, direction=aim_dir, speed=78.0,
                damage=self.base_damage * 2.6, scale_val=0.52,
                proj_color=rgb(255, 55, 80), is_player=True, aoe=3.5,
                pierce=True, lifesteal=12.0, heal_allies=35.0
            )

        elif self.char_key == 'aigis':
            # Pandora Grenade Cannon: мощный фугасный снаряд (300% урона, AoE 5.2м)
            VisualFX(spawn_pos, color.gold, 2.4, 0.22)
            Projectile(
                pos=spawn_pos, direction=aim_dir, speed=52.0,
                damage=self.base_damage * 3.0, scale_val=0.65,
                proj_color=rgb(255, 195, 50), is_player=True, aoe=5.2
            )
            self._broadcast_shot(spawn_pos, aim_dir, 52.0, self.base_damage * 3.0, 0.65, 'aigis', 5.2, False, 0, False)

        elif self.char_key == 'reimu':
            # Yin-Yang Persuasion Orb: рикошетящая до 6 раз сфера Инь-Ян с AoE
            Projectile(
                pos=spawn_pos, direction=aim_dir, speed=46.0,
                damage=self.base_damage * 2.4, scale_val=0.68,
                proj_color=rgb(245, 45, 65), is_player=True,
                aoe=3.2, bounces=6, homing=True
            )
            self._broadcast_shot(spawn_pos, aim_dir, 46.0, self.base_damage * 2.4, 0.68, 'reimu', 3.2, False, 6, True)

        elif self.char_key == 'mindustry':
            # Surge Alloy Blast: пробивной разряд Кинетического Сплава с цепными молниями
            VisualFX(spawn_pos, color.yellow, 2.8, 0.25)
            Projectile(
                pos=spawn_pos, direction=aim_dir, speed=58.0,
                damage=self.base_damage * 2.8, scale_val=0.65,
                proj_color=rgb(255, 215, 50), is_player=True,
                aoe=4.8, pierce=True
            )
            self._broadcast_shot(spawn_pos, aim_dir, 58.0, self.base_damage * 2.8, 0.65, 'mindustry', 4.8, True, 0, False)

    def use_shift_skill(self):
        if getattr(self, 'skill_lock_timer', 0.0) > 0:
            ctx.game.show_banner(f'НЕЙРОСЕТЬ ПЕРЕГРУЖЕНА ПОСЛЕ ПЕРЕСЕЛЕНИЯ ({self.skill_lock_timer:.1f}С)!', color.red, 1.2)
            return

        game = ctx.game
        skills = SURVIVOR_CLASSES[self.char_key]['skills']
        alien_cdr = 0.80 ** self.items.get('alien_head', 0)
        burn_cdr = 0.70 ** self.items.get('afterburner', 0)
        self.shift_cd = max(0.25, skills['shift']['cd'] * alien_cdr * burn_cdr)
        my_pos = Vec3(*self.position)
        nrg_mult = (
            1.0
            + 0.18 * self.items['energy_drink']
            + 0.35 * self.items.get('afterburner', 0)
        )

        if self.char_key == 'enforcer':
            self.shield_stance = not getattr(self, 'shield_stance', False)
            sh_ent = self.parts.get('shield')
            aura_ent = self.parts.get('shield_aura')
            if self.shield_stance:
                if sh_ent:
                    sh_ent.animate_position((0.35, -0.08, 0.68), duration=0.15)
                    sh_ent.animate_rotation((0, 0, 0), duration=0.15)
                if aura_ent:
                    aura_ent.enabled = True
                VisualFX(my_pos + Vec3(0, 1.2, 0), color.cyan, 2.6, 0.22)
                game.show_banner('СТОЙКА ЩИТА АКТИВНА: БРОНЯ +65% | СКОРОСТЬ СТРЕЛЬБЫ +45%', color.cyan, 1.8)
            else:
                if sh_ent:
                    sh_ent.animate_position((-0.28, -0.15, 0.45), duration=0.15)
                    sh_ent.animate_rotation((0, -25, 0), duration=0.15)
                if aura_ent:
                    aura_ent.enabled = False
                self.dash_vector = self.forward * 18.0 * nrg_mult
                self.dash_timer = 0.18
                VisualFX(my_pos + Vec3(0, 1.0, 0), color.white, 2.0, 0.2)
            return

        if self.char_key == 'scout':
            start_p = my_pos + Vec3(0, 1.5, 0)
            anchor = self._find_grapple_anchor(start_p, camera.forward, max_dist=45.0 * nrg_mult)
            self.grapple_active = True
            self.grapple_target = anchor
            self.grapple_timer = 0.72
            self.scout_speed_buff = 3.2
            VisualFX(anchor, color.cyan, 2.2, 0.35)
            LightningBeam(start_p, anchor, color.cyan, 0.16)
            return

        VisualFX(my_pos + Vec3(0, 1, 0), color.cyan, 2.4, 0.3)

        if self.char_key == 'commando':
            self.dash_vector = self.forward * 28.0 * nrg_mult
            self.dash_timer = 0.22
        elif self.char_key == 'artificer':
            self.vel_y = 16.5
            self.grounded = False
            self.dash_vector = self.forward * 18.0 * nrg_mult
            self.dash_timer = 0.32
            for e in list(game.enemies):
                if is_valid(e) and not getattr(e, 'is_ally', False):
                    e_pos = Vec3(*e.position)
                    if distance(e_pos, my_pos) <= 6.8:
                        e.take_damage(self.base_damage * 1.8)
        elif self.char_key == 'huntress':
            blink_dir = camera.forward
            blink_dir.y = max(0.0, blink_dir.y)
            target_pos = my_pos + blink_dir.normalized() * (11.0 * nrg_mult)
            LightningBeam(my_pos + Vec3(0, 1, 0), target_pos + Vec3(0, 1, 0), color.cyan, 0.28)
            resolved = game.resolve_horizontal_collision(target_pos, 0.72, self.y)
            bound = getattr(game, 'world_bound', 56.0) - 2.0
            self.position = Vec3(clamp(resolved.x, -bound, bound), max(self.y, target_pos.y), clamp(resolved.z, -bound, bound))
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
                if is_valid(e) and not getattr(e, 'is_ally', False):
                    e_pos = Vec3(*e.position)
                    if distance(e_pos, my_pos) <= 6.0:
                        e.take_damage(self.base_damage * 1.5)
                        self.heal_amount(8.0)
                        VisualFX(e_pos + Vec3(0, 1, 0), color.red, 2.2, 0.25)
        elif self.char_key == 'sol':
            self.dash_vector = self.forward * 27.0 * nrg_mult
            self.dash_timer = 0.26
            self.perform_melee_attack(
                reach=6.5, cleave_radius=4.2, damage_mult=2.4,
                slash_col=rgb(255, 100, 20), knockback=4.0, aoe=3.0
            )
        elif self.char_key == 'gwen':
            self.dash_vector = self.forward * 22.0 * nrg_mult
            self.dash_timer = 0.22
            self.m1_cd = 0.0
            mist = HallowedMistZone(my_pos + self.forward * 3.0, self.base_damage * 0.65)
            game.stage_entities.append(mist)
        elif self.char_key == 'm4a1':
            self.dash_vector = self.forward * 25.0 * nrg_mult
            self.dash_timer = 0.20
            self.shield = min(float(self.max_hp), self.shield + 25.0)
            VisualFX(my_pos + Vec3(0, 1.2, 0), rgb(95, 255, 135), 2.6, 0.25)
            for clone in list(getattr(self, 'dummy_clones', [])):
                if is_valid(clone):
                    clone.command_burst_shot()
        elif self.char_key == 'medic':
            # Amputator Healing Surge: рывок с ударом пилой Ubersaw и целебным импульсом +25% HP всем вокруг
            self.dash_vector = self.forward * 24.0 * nrg_mult
            self.dash_timer = 0.22
            self.perform_melee_attack(
                reach=5.5, cleave_radius=3.8, damage_mult=2.2,
                slash_col=rgb(255, 65, 85), lifesteal=10.0, aoe=2.5
            )
            self.heal_amount(self.max_hp * 0.25)
            VisualFX(my_pos + Vec3(0, 1.0, 0), color.lime, 8.0, 0.35)
            shift_allies = (
                list(self.dummy_clones)
                + list(self.mindustry_turrets)
                + [e for e in game.enemies if is_valid(e) and getattr(e, 'is_ally', False)]
                + list(game.remote_players.values())
            )
            for al in shift_allies:
                if is_valid(al) and distance(my_pos, Vec3(*al.position)) <= 15.0:
                    if hasattr(al, 'heal_ally'):
                        al.heal_ally(amount=al.max_hp * 0.25)
                    else:
                        al.hp = min(float(al.max_hp), al.hp + al.max_hp * 0.25)
                    VisualFX(Vec3(*al.position) + Vec3(0, 1.2, 0), color.lime, 2.5, 0.25)
        elif self.char_key == 'aigis':
            # Orgia Mode Overdrive: реактивный взлёт и перегрузка Orgia на 5.5 сек
            self.vel_y = 14.5
            self.grounded = False
            self.dash_vector = self.forward * 24.0 * nrg_mult
            self.dash_timer = 0.28
            self.orgia_timer = 5.5
            VisualFX(my_pos + Vec3(0, 1.2, 0), color.gold, 5.5, 0.35)
            game.show_banner('ORGIA MODE OVERDRIVE :: АТАКА +50% | СКОРОСТЬ +45% | УРОН +35%!', color.gold, 2.2)
        elif self.char_key == 'reimu':
            # Fantasy Nature Float: парящий рывок + щит + 4 самонаводящихся талисмана
            self.vel_y = 12.5
            self.grounded = False
            self.dash_vector = self.forward * 24.0 * nrg_mult
            self.dash_timer = 0.24
            self.shield = min(float(self.max_hp), self.shield + 20.0)
            sp = my_pos + Vec3(0, 1.5, 0)
            for i in range(4):
                ang = (i / 4.0) * math.pi * 2
                d = Vec3(math.cos(ang), 0.2, math.sin(ang)).normalized()
                Projectile(
                    pos=sp, direction=d, speed=54.0,
                    damage=self.base_damage * 1.4, scale_val=0.30,
                    proj_color=rgb(255, 65, 80), is_player=True, homing=True
                )
        # В use_shift_skill:
        elif self.char_key == 'mindustry':
            # Core Engine Overdrive: ускоренный пролёт в направлении взгляда + авто-ремонт корпуса (+15% HP)
            self.dash_vector = camera.forward * 28.0 * nrg_mult
            self.dash_timer = 0.28
            self.heal_amount(self.max_hp * 0.15)
            VisualFX(my_pos + Vec3(0, 1.2, 0), color.yellow, 4.0, 0.3)

        

    def use_r_skill(self):
        if getattr(self, 'skill_lock_timer', 0.0) > 0:
            ctx.game.show_banner(f'НЕЙРОСЕТЬ ПЕРЕГРУЖЕНА ПОСЛЕ ПЕРЕСЕЛЕНИЯ ({self.skill_lock_timer:.1f}С)!', color.red, 1.2)
            return

        
        game = ctx.game
        skills = SURVIVOR_CLASSES[self.char_key]['skills']
        # В начале use_r_skill (добавлен бонус Lysate Cell):
        alien_cdr = 0.80 ** self.items.get('alien_head', 0)
        cell_cdr = 0.75 ** self.items.get('lysate_cell', 0)
        self.r_cd = max(0.5, skills['r']['cd'] * alien_cdr * cell_cdr)
        my_pos = Vec3(*self.position)

        if self.char_key == 'commando':
            self.barrage_shots = 8
            self.barrage_timer = 0.01
        elif self.char_key == 'artificer':
            targets = [e for e in game.enemies if is_valid(e) and not getattr(e, 'is_ally', False) and distance(Vec3(*e.position), my_pos) <= 28.0]
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
                if is_valid(e) and not getattr(e, 'is_ally', False):
                    e_pos = Vec3(*e.position)
                    if distance(e_pos, my_pos) <= 20.0:
                        LightningBeam(start_p, e_pos + Vec3(0, 1.2, 0), color.yellow, 0.22)
                        e.take_damage(self.base_damage * 1.8)
                        self.heal_amount(5.0)
            game.show_banner('ULTRARICOSHOT :: BLOOD IS FUEL!', color.yellow, 1.8)
        elif self.char_key == 'sol':
            self.dragon_install_timer = 6.0
            VisualFX(my_pos + Vec3(0, 1.5, 0), rgb(255, 60, 20), 11.0, 0.45)
            for e in list(game.enemies):
                if is_valid(e) and not getattr(e, 'is_ally', False):
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
        elif self.char_key == 'enforcer':
            target_pos = my_pos + self.forward * 10.0
            floor_y = game.get_surface_height(target_pos.x, target_pos.z, my_pos.y)
            gas_pos = Vec3(target_pos.x, floor_y, target_pos.z)
            VisualFX(gas_pos + Vec3(0, 1.0, 0), rgb(140, 255, 100), 6.5, 0.35)
            gas_zone = TearGasZone(gas_pos, self.base_damage * 0.85)
            game.stage_entities.append(gas_zone)
            game.show_banner('TEAR GAS DEPLOYED :: CROWD CONTROL!', rgb(140, 255, 100), 2.0)
        elif self.char_key == 'scout':
            target_pos = my_pos + self.forward * 11.0
            floor_y = game.get_surface_height(target_pos.x, target_pos.z, my_pos.y)
            ifg_pos = Vec3(target_pos.x, floor_y, target_pos.z)
            VisualFX(ifg_pos + Vec3(0, 1.2, 0), color.cyan, 6.5, 0.35)
            ifg = IFGZone(ifg_pos, self.base_damage * 0.90)
            game.stage_entities.append(ifg)
            game.show_banner('ROCK AND STONE! :: IFG FIELD & FLARE DEPLOYED!', color.yellow, 2.2)
        elif self.char_key == 'm4a1':
            self.dummy_clones = [c for c in self.dummy_clones if is_valid(c)]
            used_slots = {c.slot_idx for c in self.dummy_clones}
            spawned = 0
            for slot in range(4):
                if len(self.dummy_clones) >= 4 or spawned >= 2:
                    break
                if slot not in used_slots:
                    clone = DummyClone(self, slot_idx=slot)
                    self.dummy_clones.append(clone)
                    game.stage_entities.append(clone)
                    VisualFX(Vec3(*clone.position) + Vec3(0, 1.2, 0), rgb(95, 255, 135), 3.0, 0.3)
                    spawned += 1

            for c in self.dummy_clones:
                c.hp = float(c.max_hp)
                c.command_burst_shot()

            active_links = 1 + len(self.dummy_clones)
            game.show_banner(
                f'DUMMY LINK ACTIVE :: ОТРЯД M4A1 [{active_links}x LINK] ({len(self.dummy_clones)}/4 КЛОНОВ)!',
                rgb(95, 255, 135), 2.6
            )
        elif self.char_key == 'medic':
            # Ульта Медика TF2:
            # 1) Если прицел направлен на врага (<50% HP, для боссов <30% HP) — переманивает его на сторону игрока!
            # 2) Если прицел направлен на союзника (или нет подходящего врага в прицеле) — активирует Убер-заряд и бафф союзников!
            aim_dir = camera.forward
            eye_pos = my_pos + Vec3(0, 1.55, 0)
            best_enemy = None
            best_dot = 0.84
            for e in list(game.enemies):
                if is_valid(e) and not getattr(e, 'is_ally', False) and e.enemy_type != 'mithrix':
                    e_center = Vec3(*e.position) + Vec3(0, e.hit_height, 0)
                    to_e = e_center - eye_pos
                    if to_e.length() <= 32.0:
                        dot = aim_dir.dot(to_e.normalized())
                        if dot > best_dot:
                            best_dot = dot
                            best_enemy = e

            if best_enemy is not None:
                hp_pct = best_enemy.hp / max(1.0, best_enemy.max_hp)
                req_pct = 0.30 if best_enemy.is_boss else 0.50
                if hp_pct <= req_pct:
                    best_enemy.convert_to_ally()
                    e_p = Vec3(*best_enemy.position) + Vec3(0, best_enemy.hit_height, 0)
                    LightningBeam(eye_pos, e_p, color.lime, 0.45)
                    VisualFX(e_p, color.lime, 5.5, 0.4)
                    game.show_banner(
                        f'MIND CONTROL :: {best_enemy.enemy_type.upper()} ПЕРЕШЁЛ НА ВАШУ СТОРОНУ!',
                        color.lime, 3.2
                    )
                    return

            # Если врага под порог переманивания в прицеле нет — даём УБЕР-ЗАРЯД себе и всем союзникам!
            self.uber_timer = 6.5
            self.heal_amount(self.max_hp * 0.50)
            self.shield = min(float(self.max_hp), self.shield + 50.0)
            VisualFX(my_pos + Vec3(0, 1.2, 0), rgb(255, 55, 80), 7.5, 0.4)

            allies = (
                list(getattr(self, 'dummy_clones', []))
                + list(getattr(self, 'mindustry_turrets', []))
                + [e for e in game.enemies if is_valid(e) and getattr(e, 'is_ally', False)]
                + list(game.remote_players.values())
            )
            for al in allies:
                if is_valid(al):
                    if hasattr(al, 'heal_ally'):
                        al.heal_ally(amount=al.max_hp, shield_amt=50.0, uber_dur=6.5)
                    else:
                        al.hp = float(al.max_hp)
                        if hasattr(al, 'damage'):
                            al.damage *= 1.30
                    LightningBeam(eye_pos, Vec3(*al.position) + Vec3(0, 1.2, 0), rgb(255, 55, 80), 0.35)
                    VisualFX(Vec3(*al.position) + Vec3(0, 1.2, 0), rgb(255, 55, 80), 3.5, 0.35)

            game.show_banner('ÜBERCHARGE READY :: НЕУЯЗВИМОСТЬ И УСИЛЕНИЕ СОЮЗНИКОВ (6.5 СЕК)!', rgb(255, 75, 90), 3.0)

        elif self.char_key == 'aigis':
            # Persona: Palladion Strike — +45 щита и удар копьями света по врагам вокруг
            self.shield = min(float(self.max_hp), self.shield + 45.0)
            VisualFX(my_pos + Vec3(0, 1.6, 0), color.cyan, 8.0, 0.4)
            targets = [e for e in game.enemies if is_valid(e) and not getattr(e, 'is_ally', False) and distance(Vec3(*e.position), my_pos) <= 28.0]
            for i in range(6):
                if i < len(targets) and is_valid(targets[i]):
                    t_pos = Vec3(*targets[i].position)
                else:
                    ang = (i / 6.0) * math.pi * 2
                    t_pos = my_pos + Vec3(math.cos(ang) * 9.0, 0, math.sin(ang) * 9.0)
                OrbitalStrikeFX(t_pos, self.base_damage * 3.2)
            game.show_banner('PERSONA :: PALLADION STRIKE!', color.cyan, 2.5)

        elif self.char_key == 'reimu':
            # Spell Card: Fantasy Seal — 10 радужных самонаводящихся сфер Данмаку
            spawn_pos = my_pos + Vec3(0, 1.8, 0)
            rainbow = [
                rgb(255, 60, 80), rgb(255, 165, 45), color.yellow,
                color.lime, color.cyan, rgb(185, 85, 255)
            ]
            for i in range(10):
                ang = (i / 10.0) * math.pi * 2
                d = Vec3(math.cos(ang), 0.25, math.sin(ang)).normalized()
                col = rainbow[i % len(rainbow)]
                Projectile(
                    pos=spawn_pos, direction=d, speed=50.0,
                    damage=self.base_damage * 1.9, scale_val=0.58,
                    proj_color=col, is_player=True, aoe=4.0, homing=True
                )
            VisualFX(spawn_pos, rgb(255, 75, 95), 7.5, 0.4)
            game.show_banner('SPELL CARD :: FANTASY SEAL!', rgb(255, 85, 100), 2.5)

        elif self.char_key == 'mindustry':
            # Build Mode: Spectre & Mend Turret (тратит 20% от макс. HP)
            hp_cost = self.max_hp * 0.20
            if self.hp <= hp_cost + 2.0:
                self.r_cd = 1.0
                game.show_banner('НЕДОСТАТОЧНО HP ДЛЯ СТРОИТЕЛЬСТВА ТУРЕЛИ (НУЖНО >20% HP)!', color.red, 2.0)
                return

            self.hp = max(1.0, self.hp - hp_cost)
            self.mindustry_turrets = [t for t in self.mindustry_turrets if is_valid(t)]
            if len(self.mindustry_turrets) >= 4:
                oldest = self.mindustry_turrets.pop(0)
                oldest.is_dead = True
                destroy(oldest)

            build_pos = my_pos + self.forward * 4.2
            floor_y = game.get_surface_height(build_pos.x, build_pos.z, my_pos.y)
            turret_pos = Vec3(build_pos.x, floor_y, build_pos.z)
            slot_idx = len(self.mindustry_turrets)
            turret = MindustryTurret(self, turret_pos, slot_idx=slot_idx)
            self.mindustry_turrets.append(turret)
            game.stage_entities.append(turret)

            LightningBeam(my_pos + Vec3(0, 1.4, 0), turret_pos + Vec3(0, 1.0, 0), color.yellow, 0.35)
            VisualFX(turret_pos + Vec3(0, 1.0, 0), color.lime, 3.8, 0.35)
            game.show_banner(
                f'BUILD MODE :: ПОСТРОЕНА ТУРЕЛЬ SPECTRE [{len(self.mindustry_turrets)}/4] (-{int(hp_cost)} HP)!',
                rgb(255, 215, 65), 2.6
            )