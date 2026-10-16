from ursina import *
import math
import random
from config import rgb, is_valid
from entities.fx import VisualFX, LightningBeam, LunarShockwaveRing, LunarPizzaAttack
from entities.projectile import Projectile


class BossAIMixin:
    def update_boss_ai(self, game, my_pos, p_pos, dist, is_local_target, eff_speed, t):
        if self.enemy_type == 'boss':
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

            self.special_timer -= time.dt
            if self.special_timer <= 0:
                self.special_timer = 6.5
                VisualFX(my_pos + Vec3(0, 3.8, 0), color.cyan, 16.0, 0.55)
                if is_local_target and is_valid(game.player) and dist <= 13.5:
                    game.player.take_damage(self.damage * 1.35)

        elif self.enemy_type == 'overlord':
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

            self.special_timer -= time.dt
            if self.special_timer <= 0 and dist > 7.0:
                self.special_timer = 5.5
                VisualFX(my_pos + Vec3(0, 2.5, 0), rgb(245, 30, 65), 6.0, 0.35)
                tp_dest = p_pos - self.forward * 3.5
                self.position = Vec3(clamp(tp_dest.x, -52, 52), 0, clamp(tp_dest.z, -52, 52))
                VisualFX(Vec3(*self.position) + Vec3(0, 1.5, 0), rgb(245, 30, 65), 8.5, 0.4)

        elif self.enemy_type == 'lunar_chimera':
            self.parts['ring1'].rotation_z += 120 * time.dt
            self.parts['ring2'].rotation_x += 140 * time.dt
            self.parts['core'].y = 2.5 + math.sin(t * 4.5) * 0.25
            if dist > 14.0:
                self.position += self.forward * eff_speed * time.dt
            self.attack_timer -= time.dt
            if self.attack_timer <= 0 and dist < 38.0:
                sp = my_pos + Vec3(0, 2.5, 0)
                aim = (p_pos + Vec3(0, 1.2, 0)) - sp
                for ang in (-8, 0, 8):
                    rad = math.radians(ang)
                    d = Vec3(aim.x * math.cos(rad) - aim.z * math.sin(rad), aim.y, aim.x * math.sin(rad) + aim.z * math.cos(rad))
                    Projectile(sp, d, 34.0, self.damage * 0.75, 0.38, color.cyan, is_player=False)
                self.attack_timer = 2.1

        elif self.enemy_type == 'mithrix':
            self.update_mithrix_phases(game, my_pos, p_pos, dist, is_local_target, eff_speed, t)

    def update_mithrix_phases(self, game, my_pos, p_pos, dist, is_local_target, eff_speed, t):
        # Переходы между фазами 1 -> 2 -> 3 по проценту здоровья (4-я фаза включается в take_damage)
        hp_ratio = self.hp / max(1.0, self.max_hp)
        if self.phase == 1 and hp_ratio <= 0.68:
            self.phase = 2
            game.boss_title.text = 'MITHRIX :: PHASE 2 - CRUSHING SKY LEAP'
            game.show_banner('МИТРИКС (ФАЗА 2): НЕБЕСНЫЙ ОБВАЛ И ХИМЕРЫ!', color.cyan, 3.0)
            VisualFX(my_pos + Vec3(0, 2.5, 0), color.cyan, 10.0, 0.45)
        elif self.phase == 2 and hp_ratio <= 0.38:
            self.phase = 3
            self.parts['phase_ring'].enabled = True
            self.parts['hammer_aura'].color = color.white
            game.boss_title.text = 'MITHRIX :: PHASE 3 - LUNAR REVOLVING PILLARS'
            game.show_banner('МИТРИКС (ФАЗА 3): ЛУННЫЕ РАЗРЕЗЫ АРЕНЫ!', rgb(120, 235, 255), 3.2)
            VisualFX(my_pos + Vec3(0, 2.5, 0), color.white, 12.0, 0.5)

        # Вращение короны, плаща и ауры
        self.parts['crown'].rotation_z += 95 * time.dt
        self.parts['cape'].rotation_x = 14 + math.sin(t * 7.0) * 8.0
        if self.parts['phase_ring'].enabled:
            self.parts['phase_ring'].rotation_y += 140 * time.dt

        arena_y = 22.0 if abs(my_pos.y - 22.0) < 12.0 or self.sky_leap_state > 0 else 0.0

        # Обработка прыжка в стратосферу (Sky Leap во 2-й и 3-й фазе)
        if self.sky_leap_state == 1:
            self.sky_leap_timer -= time.dt
            self.y = arena_y + 24.0
            if self.sky_leap_timer <= 0:
                self.sky_leap_state = 0
                land_pos = Vec3(clamp(p_pos.x, -22, 22), arena_y, clamp(p_pos.z, -22, 22))
                self.position = land_pos
                VisualFX(land_pos + Vec3(0, 1.5, 0), color.cyan, 14.0, 0.5)
                LunarShockwaveRing(land_pos, self.damage * 1.35, max_radius=28.0, speed=21.0)
                for i in range(8):
                    ang = (i / 8.0) * math.pi * 2
                    d = Vec3(math.cos(ang), 0.05, math.sin(ang))
                    Projectile(land_pos + Vec3(0, 1.8, 0), d, 30.0, self.damage, 0.55, color.cyan, is_player=False)
            return

        # Движение и анимация шага
        move_spd = eff_speed * (0.65 if self.phase == 4 else (1.25 if self.phase == 3 else 1.1))
        if dist > 4.2:
            self.position += self.forward * move_spd * time.dt
            # Удерживаем Митрикса в пределах круглой арены Колизея
            if arena_y > 10.0 and math.hypot(self.x, self.z) > 25.0:
                ang = math.atan2(self.z, self.x)
                self.x = math.cos(ang) * 25.0
                self.z = math.sin(ang) * 25.0
            self.y = arena_y

            stride = math.sin(t * 9.5) * 34.0
            self.parts['left_leg'].rotation_x = stride
            self.parts['right_leg'].rotation_x = -stride
            self.parts['left_arm'].rotation_x = -stride * 0.6

        # Плавный возврат замаха правой руки с молотом
        self.parts['right_arm'].rotation_x = lerp(self.parts['right_arm'].rotation_x, 0, time.dt * 7.0)

        # Основная атака: Удар Лунным Молотом + Ударная волна ИЛИ веер игл
        self.attack_timer -= time.dt
        if self.attack_timer <= 0:
            if self.phase == 4:
                # В 4-й фазе (с украденными предметами) стреляет веером сфер и кольцом
                sp = my_pos + Vec3(0, 3.0, 0)
                base_aim = (p_pos + Vec3(0, 1.2, 0)) - sp
                for angle in (-24, -12, 0, 12, 24):
                    rad = math.radians(angle)
                    d = Vec3(base_aim.x * math.cos(rad) - base_aim.z * math.sin(rad), base_aim.y, base_aim.x * math.sin(rad) + base_aim.z * math.cos(rad))
                    Projectile(sp, d, 34.0, self.damage * 0.9, 0.55, color.magenta, is_player=False)
                LunarShockwaveRing(my_pos, self.damage * 1.1, max_radius=26.0, speed=16.0)
                self.attack_timer = 1.9
            elif dist <= 7.5:
                # Сокрушительный удар молотом по земле!
                self.parts['right_arm'].rotation_x = -125
                impact_pos = my_pos + self.forward * 2.5
                VisualFX(impact_pos + Vec3(0, 0.8, 0), color.cyan, 7.5, 0.35)
                LunarShockwaveRing(impact_pos, self.damage * 1.25, max_radius=26.0, speed=19.0)
                if is_local_target and is_valid(game.player) and dist <= 5.5:
                    game.player.take_damage(self.damage * 1.3)
                self.attack_timer = 1.65 if self.phase < 3 else 1.3
            else:
                # Рывок в сторону + залп лунных игл
                dash_side = random.choice([-1, 1])
                self.position += self.right * (dash_side * 4.5)
                VisualFX(my_pos + Vec3(0, 2.0, 0), color.cyan, 3.5, 0.25)
                sp = Vec3(*self.position) + Vec3(0, 3.0, 0)
                base_aim = (p_pos + Vec3(0, 1.2, 0)) - sp
                for angle in (-10, -5, 0, 5, 10):
                    rad = math.radians(angle)
                    d = Vec3(base_aim.x * math.cos(rad) - base_aim.z * math.sin(rad), base_aim.y, base_aim.x * math.sin(rad) + base_aim.z * math.cos(rad))
                    Projectile(sp, d, 42.0, self.damage * 0.7, 0.36, color.cyan, is_player=False)
                self.attack_timer = 1.75

        # Специальные атаки по фазам
        self.special_timer -= time.dt
        if self.special_timer <= 0:
            if self.phase == 1:
                # Стремительный рывок к игроку с ударом молота
                self.special_timer = 5.0
                VisualFX(my_pos + Vec3(0, 2.0, 0), color.cyan, 4.0, 0.25)
                lunge_dest = my_pos + self.forward * min(dist - 2.5, 12.0)
                self.position = Vec3(lunge_dest.x, arena_y, lunge_dest.z)
                self.parts['right_arm'].rotation_x = -130
                LunarShockwaveRing(Vec3(*self.position), self.damage, max_radius=24.0, speed=18.0)

            elif self.phase == 2:
                # Прыжок в стратосферу!
                self.special_timer = 7.0
                self.sky_leap_state = 1
                self.sky_leap_timer = 1.25
                VisualFX(my_pos + Vec3(0, 2.0, 0), color.cyan, 9.0, 0.4)
                LightningBeam(my_pos, my_pos + Vec3(0, 28, 0), color.cyan, 0.8)

            elif self.phase == 3:
                # Атака «Пицца» (вращающиеся лучи по всей арене)
                self.special_timer = 5.2
                self.parts['right_arm'].rotation_x = -135
                LunarPizzaAttack(Vec3(0, arena_y, 0), self.damage * 1.35, num_slices=6)