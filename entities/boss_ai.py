from ursina import *
import math
import random
from config import rgb, is_valid
from entities.fx import VisualFX, LightningBeam, OrbitalStrikeFX, LunarShockwaveRing, LunarPizzaAttack
from entities.projectile import Projectile
from world.lunar import COLOSSEUM_Y, COLOSSEUM_RADIUS

def distance_2d(a, b):
    """Переопределяет distance_2d на горизонтальную плоскость X-Z для 3D-мира"""
    return math.hypot(a[0] - b[0], a[2] - b[2])

class BossAIMixin:
    def update_boss_ai(self, game, my_pos, p_pos, dist, is_local_target, eff_speed, t):
        floor_y = game.get_surface_height(my_pos.x, my_pos.z, my_pos.y)

        if self.enemy_type == 'boss':
            self.parts['crown'].rotation_y += 85 * time.dt
            if dist > 8.5:
                self.position += self.forward * eff_speed * time.dt
                resolved = game.resolve_horizontal_collision(Vec3(*self.position), 1.4, floor_y)
                self.position = Vec3(resolved.x, floor_y, resolved.z)
                stomp = math.sin(t * 4.5) * 24
                self.parts['left_leg'].rotation_x = stomp
                self.parts['right_leg'].rotation_x = -stomp
                self.parts['left_arm'].rotation_x = -stomp * 0.5
                self.parts['right_arm'].rotation_x = stomp * 0.5

            self.attack_timer -= time.dt
            if self.attack_timer <= 0:
                base_aim = (p_pos + Vec3(0, 1.2, 0)) - (my_pos + Vec3(0, 3.4, 0))
                for angle in (-14, 0, 14):
                    rad = math.radians(angle)
                    rot_dir = Vec3(
                        base_aim.x * math.cos(rad) - base_aim.z * math.sin(rad),
                        base_aim.y,
                        base_aim.x * math.sin(rad) + base_aim.z * math.cos(rad)
                    )
                    Projectile(my_pos + Vec3(0, 3.4, 0), rot_dir, 27.0, self.damage, 0.65, color.red, is_player=False)
                self.attack_timer = 2.0

        elif self.enemy_type == 'vagrant':
            self.parts['bell'].y = 4.2 + math.sin(t * 2.8) * 0.45
            self.parts['tentacles'].rotation_y += 65 * time.dt
            if dist > 12.0:
                self.position += self.forward * eff_speed * time.dt
                self.y = floor_y

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
                resolved = game.resolve_horizontal_collision(Vec3(*self.position), 1.3, floor_y)
                self.position = Vec3(resolved.x, floor_y, resolved.z)
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
                bound = getattr(game, 'world_bound', 52.0) - 4.0
                dest_x = clamp(tp_dest.x, -bound, bound)
                dest_z = clamp(tp_dest.z, -bound, bound)
                dest_y = game.get_surface_height(dest_x, dest_z, p_pos.y)
                self.position = Vec3(dest_x, dest_y, dest_z)
                VisualFX(Vec3(*self.position) + Vec3(0, 1.5, 0), rgb(245, 30, 65), 8.5, 0.4)

        elif self.enemy_type == 'lunar_chimera':
            self.parts['ring1'].rotation_z += 120 * time.dt
            self.parts['ring2'].rotation_x += 140 * time.dt
            self.parts['core'].y = 2.5 + math.sin(t * 4.5) * 0.25
            if dist > 14.0:
                self.position += self.forward * eff_speed * time.dt
                self.y = floor_y
            self.attack_timer -= time.dt
            if self.attack_timer <= 0 and dist < 42.0:
                sp = my_pos + Vec3(0, 2.5, 0)
                aim = (p_pos + Vec3(0, 1.2, 0)) - sp
                for ang in (-8, 0, 8):
                    rad = math.radians(ang)
                    d = Vec3(
                        aim.x * math.cos(rad) - aim.z * math.sin(rad),
                        aim.y,
                        aim.x * math.sin(rad) + aim.z * math.cos(rad)
                    )
                    Projectile(sp, d, 36.0, self.damage * 0.75, 0.38, color.cyan, is_player=False)
                self.attack_timer = 2.0

        elif self.enemy_type == 'mithrix':
            self.update_mithrix_phases(game, my_pos, p_pos, dist, is_local_target, eff_speed, t)

    def update_mithrix_phases(self, game, my_pos, p_pos, dist, is_local_target, eff_speed, t):
        arena_y = COLOSSEUM_Y
        max_arena_r = COLOSSEUM_RADIUS - 4.0

        # Вращение короны, плаща и ауры
        self.parts['crown'].rotation_z += 95 * time.dt
        self.parts['cape'].rotation_x = 14 + math.sin(t * 7.0) * 8.0
        if self.parts['phase_ring'].enabled:
            self.parts['phase_ring'].rotation_y += 140 * time.dt

        # Короткая передышка и энергетическая вспышка при смене фаз
        if self.phase_transition_timer > 0:
            self.phase_transition_timer -= time.dt
            self.position = Vec3(0, arena_y + math.sin(time.time() * 8.0) * 0.5, 0)
            return

        # Обработка прыжка в стратосферу (Sky Leap во 2-й и 3-й фазе)
        if self.sky_leap_state == 1:
            self.sky_leap_timer -= time.dt
            self.y = arena_y + 42.0

            # В первой половине полёта прицел следует за игроком, затем фиксируется
            if self.sky_leap_timer > 0.55:
                tx = clamp(p_pos.x, -max_arena_r, max_arena_r)
                tz = clamp(p_pos.z, -max_arena_r, max_arena_r)
                if math.hypot(tx, tz) > max_arena_r:
                    ang = math.atan2(tz, tx)
                    tx, tz = math.cos(ang) * max_arena_r, math.sin(ang) * max_arena_r
                self.sky_leap_target = Vec3(tx, arena_y, tz)

            if self.telegraph_ring and not self.telegraph_ring.is_empty():
                self.telegraph_ring.position = self.sky_leap_target + Vec3(0, 0.15, 0)
                self.telegraph_ring.rotation_y += 180 * time.dt
                if self.sky_leap_timer <= 0.55:
                    self.telegraph_ring.color = rgb(255, 70, 90, 190)

            if self.sky_leap_timer <= 0:
                self.sky_leap_state = 0
                if self.telegraph_ring and not self.telegraph_ring.is_empty():
                    destroy(self.telegraph_ring)
                self.telegraph_ring = None

                land_pos = Vec3(*self.sky_leap_target)
                self.position = land_pos
                LightningBeam(land_pos + Vec3(0, 42.0, 0), land_pos, color.cyan, 1.2)
                VisualFX(land_pos + Vec3(0, 1.5, 0), color.cyan, 16.0, 0.55)
                LunarShockwaveRing(land_pos, self.damage * 1.35, max_radius=55.0, speed=24.0)

                if is_local_target and is_valid(game.player):
                    if distance_2d(Vec3(*game.player.position), land_pos) <= 7.5 and abs(game.player.y - arena_y) < 3.0:
                        game.player.take_damage(self.damage * 1.45)

                for i in range(12):
                    ang = (i / 12.0) * math.pi * 2
                    d = Vec3(math.cos(ang), 0.04, math.sin(ang))
                    Projectile(land_pos + Vec3(0, 1.8, 0), d, 32.0, self.damage, 0.58, color.cyan, is_player=False)
            return

        # Движение и анимация шага по Колизею (и обход внутренних колонн)
        move_spd = eff_speed * (0.68 if self.phase == 4 else (1.30 if self.phase == 3 else (1.18 if self.phase == 2 else 1.05)))
        if dist > 4.4:
            self.position += self.forward * move_spd * time.dt
            resolved = game.resolve_horizontal_collision(Vec3(*self.position), radius=1.5, entity_y=arena_y)
            rx, rz = resolved.x, resolved.z
            if math.hypot(rx, rz) > max_arena_r:
                ang = math.atan2(rz, rx)
                rx = math.cos(ang) * max_arena_r
                rz = math.sin(ang) * max_arena_r
            self.position = Vec3(rx, arena_y, rz)

            stride = math.sin(t * 10.0) * 36.0
            self.parts['left_leg'].rotation_x = stride
            self.parts['right_leg'].rotation_x = -stride
            self.parts['left_arm'].rotation_x = -stride * 0.6

        # Плавный возврат замаха правой руки с молотом
        self.parts['right_arm'].rotation_x = lerp(self.parts['right_arm'].rotation_x, 0, time.dt * 7.0)

        # Основная атака: Удар Лунным Молотом + Ударная волна ИЛИ веер лунных осколков
        self.attack_timer -= time.dt
        if self.attack_timer <= 0:
            if self.phase == 4:
                sp = my_pos + Vec3(0, 3.0, 0)
                base_aim = (p_pos + Vec3(0, 1.2, 0)) - sp
                for angle in (-24, -12, 0, 12, 24):
                    rad = math.radians(angle)
                    d = Vec3(
                        base_aim.x * math.cos(rad) - base_aim.z * math.sin(rad),
                        base_aim.y,
                        base_aim.x * math.sin(rad) + base_aim.z * math.cos(rad)
                    )
                    Projectile(sp, d, 36.0, self.damage * 0.9, 0.55, color.magenta, is_player=False)
                LunarShockwaveRing(my_pos, self.damage * 1.1, max_radius=54.0, speed=18.5)
                self.attack_timer = 1.85

            elif dist <= 8.0 and abs(p_pos.y - arena_y) <= 4.0:
                # Сокрушительный удар молотом по земле!
                self.parts['right_arm'].rotation_x = -125
                impact_pos = Vec3(my_pos.x + self.forward.x * 2.5, arena_y, my_pos.z + self.forward.z * 2.5)
                VisualFX(impact_pos + Vec3(0, 0.8, 0), color.cyan, 8.0, 0.35)
                LunarShockwaveRing(impact_pos, self.damage * 1.25, max_radius=54.0, speed=21.0)
                if is_local_target and is_valid(game.player) and dist <= 5.8 and abs(p_pos.y - arena_y) < 2.5:
                    game.player.take_damage(self.damage * 1.3)
                self.attack_timer = 1.55 if self.phase < 3 else 1.25

            else:
                # Боковой рывок + веер скоростных лунных игл (попадает даже по игроку на платформах)
                dash_side = random.choice([-1, 1])
                new_p = my_pos + self.right * (dash_side * 5.5)
                if math.hypot(new_p.x, new_p.z) <= max_arena_r:
                    self.position = Vec3(new_p.x, arena_y, new_p.z)
                VisualFX(my_pos + Vec3(0, 2.0, 0), color.cyan, 3.8, 0.25)

                sp = Vec3(*self.position) + Vec3(0, 3.0, 0)
                base_aim = (p_pos + Vec3(0, 1.2, 0)) - sp
                angles = (-12, -6, 0, 6, 12) if self.phase >= 2 else (-8, 0, 8)
                for angle in angles:
                    rad = math.radians(angle)
                    d = Vec3(
                        base_aim.x * math.cos(rad) - base_aim.z * math.sin(rad),
                        base_aim.y,
                        base_aim.x * math.sin(rad) + base_aim.z * math.cos(rad)
                    )
                    Projectile(sp, d, 46.0, self.damage * 0.72, 0.38, color.cyan, is_player=False)
                self.attack_timer = 1.65 if self.phase < 3 else 1.35

        # Специальные атаки по фазам
        self.special_timer -= time.dt
        if self.special_timer <= 0:
            if self.phase == 1:
                # Стремительный рывок к игроку с ударом молота
                self.special_timer = 4.8
                VisualFX(my_pos + Vec3(0, 2.0, 0), color.cyan, 4.5, 0.25)
                lunge_dest = my_pos + self.forward * min(dist - 2.5, 16.0)
                if math.hypot(lunge_dest.x, lunge_dest.z) > max_arena_r:
                    ang = math.atan2(lunge_dest.z, lunge_dest.x)
                    lunge_dest.x = math.cos(ang) * max_arena_r
                    lunge_dest.z = math.sin(ang) * max_arena_r
                self.position = Vec3(lunge_dest.x, arena_y, lunge_dest.z)
                self.parts['right_arm'].rotation_x = -130
                LunarShockwaveRing(Vec3(*self.position), self.damage, max_radius=54.0, speed=20.0)

            elif self.phase == 2:
                # Прыжок в стратосферу с наведением на игрока!
                self.special_timer = 6.8
                self.sky_leap_state = 1
                self.sky_leap_timer = 1.45
                self.sky_leap_target = Vec3(clamp(p_pos.x, -max_arena_r, max_arena_r), arena_y, clamp(p_pos.z, -max_arena_r, max_arena_r))
                self.telegraph_ring = Entity(
                    model='diamond',
                    position=self.sky_leap_target + Vec3(0, 0.15, 0),
                    scale=(14.0, 0.25, 14.0),
                    color=rgb(80, 225, 255, 150),
                    unlit=True
                )
                VisualFX(my_pos + Vec3(0, 2.0, 0), color.cyan, 10.0, 0.4)
                LightningBeam(my_pos, my_pos + Vec3(0, 42, 0), color.cyan, 0.9)

            elif self.phase == 3:
                # Атака «Пицца» на весь Колизей + орбитальный удар по позиции игрока
                self.special_timer = 5.0
                self.parts['right_arm'].rotation_x = -135
                LunarPizzaAttack(Vec3(0, arena_y, 0), self.damage * 1.35, num_slices=8)
                OrbitalStrikeFX(Vec3(p_pos.x, arena_y, p_pos.z), 0)

            elif self.phase == 4:
                # В 4-й фазе периодически обрушивает лунные лучи вокруг себя
                self.special_timer = 4.5
                for _ in range(3):
                    ang = random.uniform(0, math.pi * 2)
                    r = random.uniform(8.0, 32.0)
                    strike_p = Vec3(math.cos(ang) * r, arena_y, math.sin(ang) * r)
                    LightningBeam(strike_p + Vec3(0, 30, 0), strike_p, color.magenta, 0.7)
                    VisualFX(strike_p + Vec3(0, 1.0, 0), color.magenta, 6.0, 0.35)
