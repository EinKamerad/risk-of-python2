from ursina import *
import math
import random
from config import ctx, rgb, is_valid, BOSS_TYPES
from world.lunar import BluePortal


class Teleporter(Entity):
    def __init__(self, pos):
        super().__init__(position=Vec3(*pos))
        self.state = 'idle'
        self.charge = 0.0
        self.zone_radius = 18.0
        self.aligned_to_moon = False
        self.align_cd = 0.0
        self.spawned_blue_portal = None

        Entity(parent=self, model='cube', scale=(6.2, 0.3, 6.2), y=0.15, color=rgb(50, 55, 65), collider='box')
        Entity(parent=self, model='cube', scale=(4.4, 0.45, 4.4), y=0.38, color=rgb(70, 75, 88), collider='box')

        self.prongs = []
        for angle in (0, 90, 180, 270):
            rad = math.radians(angle)
            px, pz = math.cos(rad) * 2.2, math.sin(rad) * 2.2
            Entity(parent=self, model='cube', scale=(0.7, 1.6, 0.7), position=(px, 0.9, pz), color=rgb(45, 50, 60))
            prong = Entity(
                parent=self, model='diamond', scale=(0.55, 2.4, 0.55),
                position=(px, 2.3, pz), color=color.red, unlit=True
            )
            self.prongs.append(prong)

        self.core = Entity(parent=self, model='diamond', scale=(1.1, 1.6, 1.1), y=2.6, color=color.red, unlit=True)
        self.zone_ring = Entity(
            parent=self, model='sphere',
            scale=(self.zone_radius * 2, 0.05, self.zone_radius * 2),
            y=0.05, color=rgb(255, 60, 60, 45), unlit=True, enabled=False
        )
        self.label = Text(
            text='[E] Активировать Телепорт\n[F] Цель: ПЛАНЕТА (Продолжить Цикл)',
            parent=self, y=4.8, scale=12, origin=(0, 0),
            color=color.red, billboard=True
        )

    def toggle_alignment(self):
        self.aligned_to_moon = not self.aligned_to_moon
        game = ctx.game
        if self.aligned_to_moon:
            col = rgb(80, 215, 255)
            for p in self.prongs:
                p.color = col
            self.core.color = col
            self.label.color = col
            self.label.text = '[E] Активировать Изначальный Телепорт\n[F] Цель: ЛУНА (Отправиться к Митриксу!)'
            if game:
                game.show_banner('ГРАНИ ТЕЛЕПОРТА СМЕСТИЛИСЬ И СМОТРЯТ НА ЛУНУ...', col, 3.0)
        else:
            for p in self.prongs:
                p.color = color.red
            self.core.color = color.red
            self.label.color = color.red
            self.label.text = '[E] Активировать Телепорт\n[F] Цель: ПЛАНЕТА (Продолжить Цикл)'
            if game:
                game.show_banner('ГРАНИ ТЕЛЕПОРТА ВЫРОВНЕНЫ С ПЛАНЕТОЙ', color.orange, 2.5)

    def _try_spawn_blue_portal(self, game, my_pos):
        if getattr(game, 'blue_orb_spawned', False) and self.spawned_blue_portal is None:
            game.blue_orb_spawned = False
            # Спавним Синий Портал на 26 метров в сторону от Телепорта (с поворотом на 35 градусов к центру),
            # чтобы он находился полностью за пределами 18-метровой зоны Телепорта и не перекрывал [E]
            to_center = Vec3(-my_pos.x, 0, -my_pos.z)
            base_dir = to_center.normalized() if to_center.length() > 1.0 else Vec3(-1, 0, 0)
            rad = math.radians(32.0)
            rot_dir = Vec3(
                base_dir.x * math.cos(rad) - base_dir.z * math.sin(rad),
                0,
                base_dir.x * math.sin(rad) + base_dir.z * math.cos(rad)
            ).normalized()
            bp_pos = my_pos + rot_dir * 26.0
            resolved = game.resolve_horizontal_collision(bp_pos, radius=2.5, entity_y=0.0)
            bp = BluePortal(Vec3(resolved.x, 0.0, resolved.z), target_mode='bazaar')
            self.spawned_blue_portal = bp
            game.stage_entities.append(bp)
            
    def activate_teleporter(self, boss_type=None, from_network=False):
        if self.state != 'idle':
            return
        game = ctx.game
        self.state = 'charging'
        self.zone_ring.enabled = True
        my_pos = Vec3(*self.position)
        chosen_boss = boss_type if boss_type in BOSS_TYPES else random.choice(BOSS_TYPES)
        game.spawn_boss(my_pos + Vec3(9, 0, 9), boss_type=chosen_boss, from_network=from_network)
        game.show_banner('ТЕЛЕПОРТ АКТИВИРОВАН! ПОБЕДИТЕ БОССА ТЕЛЕПОРТА!', color.red, 3.2)
        if not from_network and getattr(ctx, 'net', None) and ctx.net.connected:
            ctx.net.broadcast({'type': 'tp_activate', 'boss_type': chosen_boss})

    def update(self):
        game = ctx.game
        if not game or not game.running or not is_valid(game.player) or self.is_empty():
            return

        self.align_cd = max(0.0, self.align_cd - time.dt)
        self.core.y = 2.6 + math.sin(time.time() * 3.2) * 0.35
        self.core.rotation_y += 75 * time.dt
        my_pos = Vec3(*self.position)
        p_pos = Vec3(*game.player.position)
        dist = distance(my_pos, p_pos)

        if self.state == 'idle':
            self.label.enabled = (dist < 12.5)
            if dist < 5.8 and held_keys['f'] and self.align_cd <= 0:
                self.align_cd = 0.45
                self.toggle_alignment()
            if dist < 5.0 and held_keys['e']:
                self.activate_teleporter(from_network=False)

        elif self.state == 'charging':
            self.label.enabled = True
            any_in_zone = (dist <= self.zone_radius)
            for rp in game.remote_players.values():
                if is_valid(rp) and distance(my_pos, Vec3(*rp.position)) <= self.zone_radius:
                    any_in_zone = True

            if any_in_zone:
                self.charge = min(100.0, self.charge + 3.8 * time.dt)
                self.zone_ring.color = rgb(255, 80, 80, 55)
            else:
                self.zone_ring.color = rgb(120, 120, 120, 35)

            boss_alive = is_valid(game.active_boss)
            status = 'БОСС ЖИВ!' if boss_alive else 'ЗАРЯДКА'
            self.label.text = f'Телепорт: {int(self.charge)}% ({status})'

            if self.charge >= 100.0 and not boss_alive:
                self.state = 'ready'
                self.core.color = color.cyan
                for p in self.prongs:
                    p.color = color.cyan
                self.zone_ring.color = rgb(60, 255, 220, 55)
                self.label.color = color.cyan
                dest_str = 'ЛУНА (К МИТРИКСУ!)' if self.aligned_to_moon else 'СЛЕДУЮЩИЙ ЭТАП'
                self.label.text = f'[E] Войти в Телепорт -> {dest_str}'
                game.show_banner('ТЕЛЕПОРТ ЗАРЯЖЕН! НАЖМИТЕ [E] ДЛЯ ПРЫЖКА', color.cyan, 3.5)
                self._try_spawn_blue_portal(game, my_pos)

        elif self.state == 'ready':
            self._try_spawn_blue_portal(game, my_pos)

            # Если рядом открыт Синий Портал и игрок ближе к нему — уступаем нажатие [E] Синему Порталу
            if self.spawned_blue_portal and not self.spawned_blue_portal.is_empty():
                bp_dist = distance(Vec3(*self.spawned_blue_portal.position), p_pos)
                if bp_dist < 5.5 and bp_dist < dist:
                    return

            if dist < 4.5 and held_keys['e']:
                if self.aligned_to_moon:
                    game.enter_moon_stage()
                else:
                    game.next_stage(from_network=False)
