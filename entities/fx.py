from ursina import *
import math
import random
from config import ctx, rgb, is_valid
from models.survivors import build_survivor_mesh

def distance_2d(a, b):
    """Переопределяет distance_2d на горизонтальную плоскость X-Z для 3D-мира"""
    return math.hypot(a[0] - b[0], a[2] - b[2])


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


class MeleeSlashFX(Entity):
    """Визуальная 3D-дуга взмаха мечом / разреза ножницами / удара щитом перед игроком"""
    def __init__(self, pos, forward_dir, rot_y, slash_color=color.orange, arc_width=3.6, reach=2.8, tilt_z=0.0, scissor_cross=False):
        spawn_p = Vec3(*pos) + Vec3(0, 1.35, 0) + Vec3(*forward_dir) * (reach * 0.48)
        super().__init__(
            position=spawn_p,
            rotation=(0, rot_y, tilt_z)
        )
        blade1 = Entity(
            parent=self, model='diamond',
            scale=(arc_width, 0.18, reach * 0.72),
            color=slash_color, unlit=True
        )
        core1 = Entity(
            parent=self, model='diamond',
            scale=(arc_width * 0.75, 0.26, reach * 0.45),
            color=color.white, unlit=True
        )
        blade1.animate_scale_x(arc_width * 1.35, duration=0.18)
        blade1.animate_scale_z(0.05, duration=0.18)
        core1.animate_scale_z(0.02, duration=0.16)

        if scissor_cross:
            blade2 = Entity(
                parent=self, model='diamond',
                scale=(arc_width, 0.18, reach * 0.72),
                rotation_z=-tilt_z * 2.0 if tilt_z != 0 else 36.0,
                color=rgb(195, 245, 255), unlit=True
            )
            blade2.animate_scale_x(arc_width * 1.35, duration=0.18)
            blade2.animate_scale_z(0.05, duration=0.18)

        destroy(self, delay=0.19)


class TearGasZone(Entity):
    """Газовая завеса Enforcer [R]: замедляет врагов на 50% и наносит периодический урон"""
    def __init__(self, center_pos, tick_dmg):
        super().__init__(position=Vec3(center_pos[0], center_pos[1] + 0.1, center_pos[2]))
        self.tick_dmg = tick_dmg
        self.duration = 6.0
        self.tick_timer = 0.0
        self.radius = 8.5

        self.ring = Entity(
            parent=self, model='sphere',
            scale=(self.radius * 2, 0.14, self.radius * 2),
            color=rgb(130, 245, 95, 75), unlit=True
        )
        self.clouds_hub = Entity(parent=self)
        for i in range(7):
            ang = (i / 7.0) * math.pi * 2
            dist = self.radius * 0.55
            Entity(
                parent=self.clouds_hub, model='sphere',
                position=(math.cos(ang) * dist, 1.1, math.sin(ang) * dist),
                scale=(4.2, 2.2, 4.2),
                color=rgb(145, 255, 110, 55), unlit=True
            )

    def update(self):
        game = ctx.game
        if not game or not game.running or self.is_empty():
            return
        self.duration -= time.dt
        if not self.clouds_hub.is_empty():
            self.clouds_hub.rotation_y += 35 * time.dt
        if self.duration <= 0:
            destroy(self)
            return

        self.tick_timer -= time.dt
        if self.tick_timer <= 0:
            self.tick_timer = 0.45
            my_pos = Vec3(*self.position)
            for e in list(game.enemies):
                if is_valid(e):
                    e_pos = Vec3(*e.position)
                    if distance_2d(e_pos, my_pos) <= self.radius and abs(e_pos.y - my_pos.y) <= 5.0:
                        e.slow_timer = max(e.slow_timer, 1.5)
                        e.take_damage(self.tick_dmg)
                        VisualFX(e_pos + Vec3(0, 1.1, 0), rgb(140, 255, 100), 1.5, 0.2)


class IFGZone(Entity):
    """Ингибиторное поле (IFG) Скаута из DRG + осветительный флаер: замедляет врагов и бьёт током"""
    def __init__(self, center_pos, tick_dmg):
        super().__init__(position=Vec3(center_pos[0], center_pos[1] + 0.1, center_pos[2]))
        self.tick_dmg = tick_dmg
        self.duration = 6.5
        self.tick_timer = 0.0
        self.radius = 8.5

        self.ring = Entity(
            parent=self, model='sphere',
            scale=(self.radius * 2, 0.15, self.radius * 2),
            color=rgb(60, 195, 255, 80), unlit=True
        )
        # Центральный маяк-генератор IFG и яркий флаер
        self.pylon = Entity(parent=self, model='diamond', scale=(0.8, 2.6, 0.8), y=1.3, color=color.cyan, unlit=True)
        Entity(parent=self, model='sphere', scale=0.65, y=2.8, color=color.yellow, unlit=True)

    def update(self):
        game = ctx.game
        if not game or not game.running or self.is_empty():
            return
        self.duration -= time.dt
        if not self.pylon.is_empty():
            self.pylon.rotation_y += 140 * time.dt
        if self.duration <= 0:
            destroy(self)
            return

        self.tick_timer -= time.dt
        if self.tick_timer <= 0:
            self.tick_timer = 0.40
            my_pos = Vec3(*self.position)
            for e in list(game.enemies):
                if is_valid(e):
                    e_pos = Vec3(*e.position)
                    if distance_2d(e_pos, my_pos) <= self.radius and abs(e_pos.y - my_pos.y) <= 5.5:
                        e.slow_timer = max(e.slow_timer, 2.0)
                        e.take_damage(self.tick_dmg)
                        LightningBeam(my_pos + Vec3(0, 2.2, 0), e_pos + Vec3(0, 1.2, 0), color.cyan, 0.14)


class DummyClone(Entity):
    """Тактический ИИ-клон M4A1 (Dummy Link): наследует все предметы игрока, сам ведёт бой и спасает от смерти!"""
    def __init__(self, owner, slot_idx=0):
        spawn_offset = Vec3(math.cos(slot_idx * 1.57) * 3.0, 0, math.sin(slot_idx * 1.57) * 3.0)
        start_p = Vec3(*owner.position) + spawn_offset
        super().__init__(position=start_p)
        self.owner = owner
        self.slot_idx = slot_idx
        self.is_dead = False
        self.max_hp = max(60, int(owner.max_hp * 0.85))
        self.hp = float(self.max_hp)
        self.shoot_cd = random.uniform(0.1, 0.35)

        self.parts = build_survivor_mesh(self, 'm4a1')
        # Голографическое кольцо Dummy Link под ногами клона
        self.link_ring = Entity(
            parent=self, model='diamond', scale=(1.35, 0.08, 1.35),
            y=0.06, color=rgb(95, 255, 135, 180), unlit=True
        )
        self.label = Text(
            text=f'DUMMY LINK #{slot_idx + 1}',
            parent=self, y=2.75, scale=8.5, origin=(0, 0),
            color=rgb(95, 255, 135), billboard=True
        )
        self.hp_bg = Entity(parent=self, model='quad', scale=(1.0, 0.10), y=2.45, color=color.black, billboard=True)
        self.hp_fill = Entity(parent=self.hp_bg, model='quad', scale=(1, 1), z=-0.01, color=rgb(95, 255, 135), unlit=True)

    def command_burst_shot(self):
        """Синхронный выстрел по команде хозяйки M4A1"""
        if self.is_dead or self.is_empty():
            return
        self.fire_at_nearest(dmg_mult=0.75)

    def fire_at_nearest(self, dmg_mult=0.65):
        game = ctx.game
        if not game or not is_valid(self.owner):
            return
        my_pos = Vec3(*self.position)
        nearest = None
        best_d = 38.0
        for e in game.enemies:
            if is_valid(e) and not getattr(e, 'is_ally', False):
                d = distance(my_pos, Vec3(*e.position))
                if d < best_d:
                    best_d = d
                    nearest = e
        if nearest:
            from entities.projectile import Projectile
            self.look_at_2d(Vec3(*nearest.position), 'y')
            sp = my_pos + Vec3(0, 1.5, 0) + self.forward * 0.85
            aim = ((Vec3(*nearest.position) + Vec3(0, nearest.hit_height, 0)) - sp).normalized()
            Projectile(
                pos=sp, direction=aim, speed=self.owner.proj_speed,
                damage=self.owner.base_damage * dmg_mult,
                scale_val=0.20, proj_color=rgb(95, 255, 135),
                is_player=True, can_proc=True
            )
            if hasattr(self.owner, '_broadcast_shot'):
                self.owner._broadcast_shot(sp, aim, self.owner.proj_speed, self.owner.base_damage * dmg_mult, 0.20, 'm4a1')
            arm = self.parts['right_arm']
            arm.rotation_x = -24
            arm.animate_rotation_x(0, duration=0.10)

    def take_damage(self, amount):
        if self.is_dead or self.is_empty():
            return
        self.hp -= amount
        if not self.hp_fill.is_empty():
            self.hp_fill.scale_x = max(0.0, self.hp / max(1.0, self.max_hp))
        if self.hp <= 0:
            self.is_dead = True
            VisualFX(Vec3(*self.position) + Vec3(0, 1.2, 0), rgb(95, 255, 135), 2.8, 0.3)
            destroy(self)

    def update(self):
        game = ctx.game
        if not game or not game.running or self.is_dead or self.is_empty() or not is_valid(self.owner):
            return

        self.link_ring.rotation_y += 90 * time.dt
        my_pos = Vec3(*self.position)
        owner_pos = Vec3(*self.owner.position)

        # Обновляем максимальное HP клона при подборе предметов хозяйкой
        self.max_hp = max(60, int(self.owner.max_hp * 0.85))
        self.hp = min(float(self.max_hp), self.hp + 2.0 * time.dt)
        if not self.hp_fill.is_empty():
            self.hp_fill.scale_x = clamp(self.hp / self.max_hp, 0.0, 1.0)

        # Позиция в тактическом строю вокруг M4A1
        form_angle = time.time() * 0.6 + self.slot_idx * (math.pi * 0.5)
        desired_pos = owner_pos + Vec3(math.cos(form_angle) * 3.8, 0, math.sin(form_angle) * 3.8)

        # Если клон слишком далеко от хозяйки (например, после телепорта или лифта), телепортируем его к ней
        dist_to_owner = distance(my_pos, owner_pos)
        if dist_to_owner > 28.0 or abs(my_pos.y - owner_pos.y) > 14.0:
            self.position = desired_pos + Vec3(0, 0.5, 0)
            VisualFX(Vec3(*self.position) + Vec3(0, 1, 0), rgb(95, 255, 135), 2.0, 0.2)
            return

        # Передвижение к точке строя
        to_desired = Vec3(desired_pos.x - my_pos.x, 0, desired_pos.z - my_pos.z)
        if to_desired.length() > 0.65:
            move_dir = to_desired.normalized()
            self.position += move_dir * (self.owner.move_speed * 0.98) * time.dt
            self.look_at_2d(desired_pos, 'y')
            swing = math.sin(time.time() * 12.0 + self.slot_idx) * 34.0
            self.parts['left_leg'].rotation_x = swing
            self.parts['right_leg'].rotation_x = -swing
        else:
            self.parts['left_leg'].rotation_x = lerp(self.parts['left_leg'].rotation_x, 0, time.dt * 10)
            self.parts['right_leg'].rotation_x = lerp(self.parts['right_leg'].rotation_x, 0, time.dt * 10)

        floor_h = game.get_surface_height(self.x, self.z, self.y, prev_y=my_pos.y)
        self.y = floor_h

        # Автоматическая стрельба клона с учётом скорости атаки хозяйки (Soldier's Syringe и др.)
        self.shoot_cd -= time.dt
        if self.shoot_cd <= 0:
            self.shoot_cd = max(0.14, 1.35 / max(1.0, self.owner.fire_rate))
            self.fire_at_nearest(dmg_mult=0.60)

        # Враги вплотную к клону могут наносить ему урон (клоны также прикрывают хозяйку!)
        for e in list(game.enemies):
            if is_valid(e) and distance(Vec3(*self.position), Vec3(*e.position)) <= 1.65:
                self.take_damage(e.damage * 0.45 * time.dt)

class MindustryTurret(Entity):
    """Оборонительная турель Mindustry (Spectre + Mend Projector): наследует предметы игрока, стреляет во врагов и лечит союзников!"""
    def __init__(self, owner, pos, slot_idx=0):
        super().__init__(position=Vec3(*pos))
        self.owner = owner
        self.slot_idx = slot_idx
        self.is_dead = False
        self.max_hp = max(90, int(owner.max_hp * 1.1))
        self.hp = float(self.max_hp)
        self.shoot_cd = 0.2
        self.mend_timer = 1.8

        # Бронированное основание блока 2x2 из Mindustry
        Entity(parent=self, model='cube', scale=(2.1, 0.45, 2.1), y=0.22, color=rgb(55, 62, 75))
        Entity(parent=self, model='diamond', scale=(2.2, 0.15, 2.2), y=0.45, color=rgb(245, 185, 45), unlit=True)

        # Вращающаяся башня турели Spectre
        self.head = Entity(parent=self, position=(0, 0.85, 0))
        Entity(parent=self.head, model='cube', scale=(1.15, 0.65, 1.25), color=rgb(235, 175, 45))
        Entity(parent=self.head, model='cube', scale=(0.24, 0.24, 1.35), position=(-0.28, 0.05, 0.55), color=rgb(42, 48, 58))
        Entity(parent=self.head, model='cube', scale=(0.24, 0.24, 1.35), position=(0.28, 0.05, 0.55), color=rgb(42, 48, 58))
        Entity(parent=self.head, model='diamond', scale=(0.55, 0.35, 0.55), y=0.42, color=color.lime, unlit=True)

        # Кольцо Mend Projector
        self.mend_ring = Entity(
            parent=self, model='diamond', scale=(1.8, 0.08, 1.8),
            y=0.12, color=rgb(95, 255, 135, 160), unlit=True
        )
        self.label = Text(
            text=f'MINDUSTRY TURRET #{slot_idx + 1}',
            parent=self, y=2.5, scale=8.5, origin=(0, 0),
            color=rgb(255, 215, 65), billboard=True
        )
        self.hp_bg = Entity(parent=self, model='quad', scale=(1.1, 0.10), y=2.15, color=color.black, billboard=True)
        self.hp_fill = Entity(parent=self.hp_bg, model='quad', scale=(1, 1), z=-0.01, color=color.lime, unlit=True)

    def take_damage(self, amount):
        if self.is_dead or self.is_empty():
            return
        self.hp -= amount
        if not self.hp_fill.is_empty():
            self.hp_fill.scale_x = max(0.0, self.hp / max(1.0, self.max_hp))
        if self.hp <= 0:
            self.is_dead = True
            VisualFX(Vec3(*self.position) + Vec3(0, 1.0, 0), color.orange, 3.2, 0.3)
            destroy(self)

    def update(self):
        game = ctx.game
        if not game or not game.running or self.is_dead or self.is_empty() or not is_valid(self.owner):
            return

        self.mend_ring.rotation_y += 85 * time.dt
        my_pos = Vec3(*self.position)

        # Импульс Mend Projector: лечит корабль игрока, клонов и соседние турели в радиусе 14м
        self.mend_timer -= time.dt
        if self.mend_timer <= 0:
            self.mend_timer = 2.0
            VisualFX(my_pos + Vec3(0, 0.8, 0), color.lime, 5.5, 0.3)
            self.hp = min(float(self.max_hp), self.hp + self.max_hp * 0.08)
            if is_valid(game.player) and distance(my_pos, Vec3(*game.player.position)) <= 14.0:
                game.player.heal_amount(game.player.max_hp * 0.06 + 6.0)

        # Поиск ближайшего вражеского монстра и стрельба с наследованием всех предметов игрока
        self.shoot_cd -= time.dt
        if self.shoot_cd <= 0:
            self.shoot_cd = max(0.14, 1.1 / max(1.0, self.owner.fire_rate))
            nearest = None
            best_d = 36.0
            for e in game.enemies:
                if is_valid(e) and not getattr(e, 'is_ally', False):
                    d = distance(my_pos, Vec3(*e.position))
                    if d < best_d:
                        best_d = d
                        nearest = e
            if nearest:
                from entities.projectile import Projectile
                target_p = Vec3(*nearest.position) + Vec3(0, nearest.hit_height, 0)
                self.head.look_at(target_p)
                sp = my_pos + Vec3(0, 1.0, 0) + self.head.forward * 1.1
                aim = (target_p - sp).normalized()
                Projectile(
                    pos=sp, direction=aim, speed=72.0,
                    damage=self.owner.base_damage * 0.72,
                    scale_val=0.22, proj_color=rgb(255, 210, 55),
                    is_player=True, can_proc=True
                )

        # Контактный урон от врагов вплотную
        for e in list(game.enemies):
            if is_valid(e) and not getattr(e, 'is_ally', False):
                if distance(my_pos, Vec3(*e.position)) <= 2.1:
                    self.take_damage(e.damage * 0.5 * time.dt)


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
        super().__init__(position=Vec3(center_pos[0], center_pos[1] + 0.1, center_pos[2]))
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
                LightningBeam(Vec3(rx, my_pos.y + 14, rz), Vec3(rx, my_pos.y, rz), rgb(255, 220, 80), 0.14)
            if self.tick_dmg > 0:
                for e in list(game.enemies):
                    if is_valid(e):
                        e_pos = Vec3(*e.position)
                        if distance_2d(e_pos, my_pos) <= self.radius:
                            e.take_damage(self.tick_dmg)


class HallowedMistZone(Entity):
    def __init__(self, center_pos, tick_dmg):
        super().__init__(position=Vec3(center_pos[0], center_pos[1] + 0.08, center_pos[2]))
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


class LunarShockwaveRing(Entity):
    """Расширяющееся по полу кольцо от удара молота Митрикса (можно перепрыгнуть или уйти на платформу!)"""
    def __init__(self, center_pos, damage, max_radius=54.0, speed=22.0):
        super().__init__(position=Vec3(center_pos[0], center_pos[1] + 0.15, center_pos[2]))
        self.damage = damage
        self.cur_radius = 1.5
        self.max_radius = max_radius
        self.speed = speed
        self.hit_player = False

        self.ring = Entity(
            parent=self, model='diamond',
            scale=(3.0, 0.45, 3.0),
            color=rgb(80, 230, 255, 175),
            unlit=True
        )

    def update(self):
        game = ctx.game
        if not game or not game.running or self.is_empty():
            return

        self.cur_radius += self.speed * time.dt
        if self.cur_radius >= self.max_radius:
            destroy(self)
            return

        self.ring.scale = (self.cur_radius * 2.0, 0.45, self.cur_radius * 2.0)
        self.ring.rotation_y += 90 * time.dt

        if not self.hit_player and is_valid(game.player):
            p = game.player
            p_pos = Vec3(*p.position)
            if abs(distance_2d(p_pos, Vec3(*self.position)) - self.cur_radius) <= 1.4:
                if abs(p_pos.y - self.position.y) < 1.45:
                    self.hit_player = True
                    p.take_damage(self.damage)
                    VisualFX(p_pos + Vec3(0, 1, 0), color.cyan, 2.5, 0.25)


class LunarPizzaAttack(Entity):
    """Атака 3-й фазы Митрикса на весь 112-метровый Колизей: вращающиеся лучи света с взрывом"""
    def __init__(self, center_pos, damage, num_slices=8):
        super().__init__(position=Vec3(center_pos[0], center_pos[1] + 0.12, center_pos[2]))
        self.damage = damage
        self.num_slices = num_slices
        self.rot_speed = random.choice([-28.0, 28.0])
        self.timer = 2.1
        self.detonated = False

        self.lines = []
        for i in range(num_slices):
            ang = i * (180.0 / num_slices)
            line = Entity(
                parent=self, model='cube',
                scale=(1.4, 0.15, 110.0),
                rotation_y=ang,
                color=rgb(70, 215, 255, 140),
                unlit=True
            )
            self.lines.append(line)

    def update(self):
        game = ctx.game
        if not game or not game.running or self.is_empty():
            return

        if not self.detonated:
            self.rotation_y += self.rot_speed * time.dt
            self.timer -= time.dt
            if self.timer <= 0.40:
                self.rot_speed = 0.0
                for ln in self.lines:
                    ln.color = color.white

            if self.timer <= 0:
                self.detonate(game)

    def detonate(self, game):
        self.detonated = True
        for ln in self.lines:
            ln.scale_y = 22.0
            ln.y = 11.0
            ln.color = rgb(80, 235, 255, 225)
            ln.animate_scale_x(0.05, duration=0.42)

        if is_valid(game.player):
            p_pos = Vec3(*game.player.position)
            c_pos = Vec3(*self.position)
            dx = p_pos.x - c_pos.x
            dz = p_pos.z - c_pos.z
            if math.hypot(dx, dz) <= 56.0:
                for ln in self.lines:
                    world_ang = math.radians(self.rotation_y + ln.rotation_y)
                    lx, lz = math.sin(world_ang), math.cos(world_ang)
                    perp_dist = abs(dx * lz - dz * lx)
                    if perp_dist <= 1.45:
                        game.player.take_damage(self.damage)
                        VisualFX(p_pos + Vec3(0, 1, 0), color.cyan, 3.2, 0.3)
                        break

        destroy(self, delay=0.45)
