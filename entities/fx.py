from ursina import *
import math
import random
from config import ctx, rgb, is_valid


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


# ==========================================================
# СПЕЦЭФФЕКТЫ АТАК МИТРИКСА (SHOCKWAVE RING & PIZZA CUTTER)
# ==========================================================
class LunarShockwaveRing(Entity):
    """Расширяющееся по полу кольцо от удара молота Митрикса (можно перепрыгнуть!)"""
    def __init__(self, center_pos, damage, max_radius=26.0, speed=18.0):
        super().__init__(position=Vec3(center_pos[0], center_pos[1] + 0.15, center_pos[2]))
        self.damage = damage
        self.cur_radius = 1.5
        self.max_radius = max_radius
        self.speed = speed
        self.hit_player = False

        self.ring = Entity(
            parent=self, model='diamond',
            scale=(3.0, 0.35, 3.0),
            color=rgb(80, 230, 255, 160),
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

        self.ring.scale = (self.cur_radius * 2.0, 0.35, self.cur_radius * 2.0)
        self.ring.rotation_y += 90 * time.dt

        if not self.hit_player and is_valid(game.player):
            p = game.player
            p_pos = Vec3(*p.position)
            # Если игрок находится на линии кольца и НЕ подпрыгнул выше 1.3м от пола арены
            if abs(distance_2d(p_pos, Vec3(*self.position)) - self.cur_radius) <= 1.25:
                if abs(p_pos.y - self.position.y) < 1.35:
                    self.hit_player = True
                    p.take_damage(self.damage)
                    VisualFX(p_pos + Vec3(0, 1, 0), color.cyan, 2.5, 0.25)


class LunarPizzaAttack(Entity):
    """Культовая атака 3-й фазы Митрикса: вращающиеся лучи по всей арене с последующим взрывом"""
    def __init__(self, center_pos, damage, num_slices=6):
        super().__init__(position=Vec3(center_pos[0], center_pos[1] + 0.12, center_pos[2]))
        self.damage = damage
        self.num_slices = num_slices
        self.rot_speed = random.choice([-32.0, 32.0])
        self.timer = 1.9
        self.detonated = False

        self.lines = []
        for i in range(num_slices):
            ang = i * (180.0 / num_slices)
            line = Entity(
                parent=self, model='cube',
                scale=(1.1, 0.12, 54.0),
                rotation_y=ang,
                color=rgb(70, 215, 255, 135),
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
            # За 0.35 сек до взрыва лучи фиксируются и вспыхивают белым
            if self.timer <= 0.35:
                self.rot_speed = 0.0
                for ln in self.lines:
                    ln.color = color.white

            if self.timer <= 0:
                self.detonate(game)

    def detonate(self, game):
        self.detonated = True
        for ln in self.lines:
            ln.scale_y = 18.0
            ln.y = 9.0
            ln.color = rgb(80, 235, 255, 220)
            ln.animate_scale_x(0.05, duration=0.38)

        if is_valid(game.player):
            p_pos = Vec3(*game.player.position)
            c_pos = Vec3(*self.position)
            dx = p_pos.x - c_pos.x
            dz = p_pos.z - c_pos.z
            if math.hypot(dx, dz) <= 28.0:
                for ln in self.lines:
                    world_ang = math.radians(self.rotation_y + ln.rotation_y)
                    lx, lz = math.sin(world_ang), math.cos(world_ang)
                    perp_dist = abs(dx * lz - dz * lx)
                    if perp_dist <= 1.25:
                        game.player.take_damage(self.damage)
                        VisualFX(p_pos + Vec3(0, 1, 0), color.cyan, 3.2, 0.3)
                        break

        destroy(self, delay=0.4)