from ursina import *
import math
import random
from config import ctx, rgb, is_valid, SURVIVOR_CLASSES
from entities.fx import (
    VisualFX, MeleeSlashFX, TearGasZone, LightningBeam,
    OrbitalStrikeFX, ArrowRainZone, HallowedMistZone
)
from entities.projectile import Projectile, apply_player_hit_effects


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

        # Центры проверки попадания: прямо перед игроком и на дистанции взмаха
        strike_center = my_pos + fwd * (reach * 0.55)
        hit_count = 0

        for e in list(game.enemies):
            if not is_valid(e):
                continue
            e_pos = Vec3(*e.position)
            # Проверка по высоте (чтобы можно было бить летающих виспов и медуз над головой)
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
            # Лёгкий боевой шаг вперёд при ударе мечом на земле
            if self.is_moving and self.grounded and self.dash_timer <= 0:
                self.position += self.forward * 0.35

            arm = self.parts['right_arm']
            arm.rotation_x = -75 if self.shoot_side % 2 == 0 else -35
            arm.rotation_z = -28 if self.shoot_side % 2 == 0 else 28
            arm.animate_rotation((0, 0, 0), duration=0.15)
            return

        # 2. ГВЕН: Ближний бой ножницами Snip Snip! (быстрые перекрестные разрезы с вампиризмом)
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

        # 3. ENFORCER: Помповый дробовик Riot Shotgun (веер из 6 картечин)
        if self.char_key == 'enforcer' and col_override is None:
            aim_dir = camera.forward
            spawn_pos = Vec3(*self.position) + Vec3(0, 1.55, 0) + self.forward * 1.05
            spread = 0.032 if getattr(self, 'shield_stance', False) else 0.075
            pellets = 6
            for i in range(pellets):
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

        # 4. Стрелковые классы (Commando, Artificer, Huntress, Buzz, V1)
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
            'enforcer': rgb(110, 225, 255)
        }
        default_col = color_map.get(self.char_key, color.yellow)
        proj_col = col_override if col_override else default_col
        col_name = 'cyan' if col_override else self.char_key

        steal = 1.6 if self.char_key == 'v1' else 0.0

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
            lifesteal=steal
        )
        self._broadcast_shot(
            spawn_pos, aim_dir, self.proj_speed, self.base_damage * damage_mult,
            self.proj_scale, col_name, self.proj_aoe, False, 0, self.char_key == 'huntress'
        )

        if self.char_key in ('buzz', 'v1'):
            arm = self.parts['right_arm']
            arm.rotation_x = -26
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
            # Volcanic Viper + Gun Flame Pillar (ближний апперкот + короткая огненная волна по земле)
            self.vel_y = 14.5
            self.grounded = False
            self.perform_melee_attack(
                reach=6.5, cleave_radius=4.5, damage_mult=2.8,
                slash_col=rgb(255, 90, 20), lifesteal=4.0, knockback=3.0, aoe=3.5
            )
            # Короткая волна пламени Gun Flame на 12 метров вперёд
            gf_dir = Vec3(self.forward.x, 0.0, self.forward.z).normalized()
            Projectile(
                pos=spawn_pos, direction=gf_dir, speed=34.0,
                damage=self.base_damage * 1.8, scale_val=0.85,
                proj_color=rgb(255, 110, 20), is_player=True, aoe=4.2, pierce=True, max_lifetime=0.38
            )

        elif self.char_key == 'gwen':
            # Center Snip! — мощный финальный смыкающий разрез гигантскими ножницами вблизи
            self.perform_melee_attack(
                reach=7.2, cleave_radius=4.2, damage_mult=3.2,
                slash_col=rgb(155, 240, 255), lifesteal=6.5, scissor_cross=True, aoe=2.8
            )
            arm = self.parts['right_arm']
            arm.rotation_x = -95
            arm.animate_rotation_x(0, duration=0.22)

        elif self.char_key == 'enforcer':
            # Shield Bash — оглушающий удар щитом вблизи с отбрасыванием и получением барьера
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

    def use_shift_skill(self):
        game = ctx.game
        skills = SURVIVOR_CLASSES[self.char_key]['skills']
        self.shift_cd = skills['shift']['cd']
        my_pos = Vec3(*self.position)
        nrg_mult = 1.0 + 0.18 * self.items['energy_drink']

        if self.char_key == 'enforcer':
            # Protect and Serve: переключение боевой стойки со щитом
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
                # При складывании щита Enforcer делает короткий тактический марш-рывок вперёд
                self.dash_vector = self.forward * 18.0 * nrg_mult
                self.dash_timer = 0.18
                VisualFX(my_pos + Vec3(0, 1.0, 0), color.white, 2.0, 0.2)
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
                if is_valid(e):
                    e_pos = Vec3(*e.position)
                    if distance(e_pos, my_pos) <= 6.0:
                        e.take_damage(self.base_damage * 1.5)
                        self.hp = min(float(self.max_hp), self.hp + 8.0)
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
        elif self.char_key == 'enforcer':
            # Tear Gas Grenade: бросает газовую гранату перед собой
            target_pos = my_pos + self.forward * 10.0
            floor_y = game.get_surface_height(target_pos.x, target_pos.z, my_pos.y)
            gas_pos = Vec3(target_pos.x, floor_y, target_pos.z)
            VisualFX(gas_pos + Vec3(0, 1.0, 0), rgb(140, 255, 100), 6.5, 0.35)
            gas_zone = TearGasZone(gas_pos, self.base_damage * 0.85)
            game.stage_entities.append(gas_zone)
            game.show_banner('TEAR GAS DEPLOYED :: CROWD CONTROL!', rgb(140, 255, 100), 2.0)