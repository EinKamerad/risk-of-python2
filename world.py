from ursina import *
import math
import random
from config import ctx, rgb, is_valid, ITEM_POOL, STAGE_PALETTES, PROGRESS
from models import build_item_mesh, build_map_structure, build_skybox
from entities import VisualFX


class ItemDrop(Entity):
    def __init__(self, start_pos, item_key):
        super().__init__(position=Vec3(*start_pos) + Vec3(0, 1.2, 0))
        self.item_key = item_key
        self.info = ITEM_POOL[item_key]
        self.is_destroyed = False

        ang = random.uniform(0, math.pi * 2)
        self.vel = Vec3(math.cos(ang) * 4.2, 9.5, math.sin(ang) * 4.2)
        self.landed = False

        self.visual = build_item_mesh(self, item_key)
        self.beam = Entity(
            parent=self, model='cube', scale=(0.08, 4.5, 0.08),
            y=2.2, color=self.info['color'], unlit=True
        )
        self.ring = Entity(
            parent=self, model='diamond', scale=(1.1, 0.08, 1.1),
            y=-0.35, color=self.info['color'], unlit=True
        )
        self.label = Text(
            text=f"[E] {self.info['name']}",
            parent=self, y=1.6, scale=11, origin=(0, 0),
            color=self.info['color'], billboard=True
        )

    def update(self):
        game = ctx.game
        if not game or not game.running or self.is_destroyed or self.is_empty():
            return

        if not self.landed:
            self.vel.y -= 22.0 * time.dt
            self.position += self.vel * time.dt
            if self.y <= 0.85:
                self.y = 0.85
                self.landed = True
        else:
            self.visual.y = math.sin(time.time() * 3.5) * 0.15

        self.visual.rotation_y += 95 * time.dt
        self.ring.rotation_y -= 60 * time.dt

        if is_valid(game.player):
            dist = distance(Vec3(*self.position), Vec3(*game.player.position))
            self.label.enabled = (dist < 7.0)
            if self.landed and (dist < 2.0 or (dist < 4.0 and held_keys['e'])):
                self.is_destroyed = True
                game.collect_item(self.item_key)
                VisualFX(Vec3(*self.position), self.info['color'], 2.5, 0.3)
                if self in game.stage_entities:
                    game.stage_entities.remove(self)
                destroy(self)


class Chest(Entity):
    def __init__(self, pos, cost, chest_id=0):
        super().__init__(position=Vec3(*pos))
        self.chest_id = chest_id
        self.cost = cost
        self.opened = False

        Entity(parent=self, model='cube', scale=(1.5, 0.2, 1.1), y=0.1, color=rgb(45, 50, 62), collider='box')
        Entity(parent=self, model='cube', scale=(1.35, 0.7, 0.95), y=0.45, color=rgb(55, 105, 175))
        Entity(parent=self, model='cube', scale=(1.38, 0.12, 0.98), y=0.55, color=color.cyan, unlit=True)

        self.lid = Entity(parent=self, position=(0, 0.85, 0))
        Entity(parent=self.lid, model='cube', scale=(1.42, 0.25, 1.02), color=rgb(75, 85, 105))
        self.lock_gem = Entity(parent=self.lid, model='diamond', scale=(0.35, 0.35, 0.35), z=0.5, color=color.gold, unlit=True)

        self.label = Text(
            text=f'[E] Сундук (${self.cost})',
            parent=self, y=2.2, scale=11, origin=(0, 0),
            color=color.yellow, billboard=True
        )

    def open_visual(self, item_key=None):
        if self.opened:
            return
        self.opened = True
        self.label.enabled = False
        self.lock_gem.color = color.gray
        self.lid.animate_position((0, 1.25, -0.45), duration=0.28)
        self.lid.animate_rotation((-70, 0, 0), duration=0.28)
        my_pos = Vec3(*self.position)
        VisualFX(my_pos + Vec3(0, 1.0, 0), color.gold, 3.0, 0.35)
        if ctx.game:
            ctx.game.spawn_item_drop(my_pos, item_key=item_key, broadcast=False)

    def update(self):
        game = ctx.game
        if self.opened or not game or not game.running or not is_valid(game.player) or self.is_empty():
            return

        my_pos = Vec3(*self.position)
        dist = distance(my_pos, Vec3(*game.player.position))
        self.label.enabled = (dist < 6.8)

        if dist < 4.2 and held_keys['e']:
            if game.player.gold >= self.cost:
                game.player.gold -= self.cost
                chosen_key = random.choice(list(ITEM_POOL.keys()))
                self.open_visual(chosen_key)
                if getattr(ctx, 'net', None) and ctx.net.connected:
                    ctx.net.broadcast({'type': 'chest_open', 'chest_id': self.chest_id, 'item_key': chosen_key})


class HealingShrine(Entity):
    def __init__(self, pos, cost):
        super().__init__(position=Vec3(*pos))
        self.cost = cost
        self.cooldown = 0.0

        Entity(parent=self, model='cube', scale=(1.8, 0.4, 1.8), y=0.2, color=rgb(65, 75, 70), collider='box')
        Entity(parent=self, model='diamond', scale=(1.1, 2.8, 1.1), y=1.6, color=rgb(75, 95, 85))
        self.orb = Entity(parent=self, model='diamond', scale=(0.8, 1.2, 0.8), y=3.4, color=color.green, unlit=True)
        self.label = Text(
            text=f'[E] Алтарь Леса (${self.cost} -> Лечение 60%)',
            parent=self, y=4.5, scale=11, origin=(0, 0),
            color=color.green, billboard=True
        )

    def update(self):
        game = ctx.game
        if not game or not game.running or not is_valid(game.player) or self.is_empty():
            return

        self.orb.rotation_y += 70 * time.dt
        self.cooldown = max(0.0, self.cooldown - time.dt)
        my_pos = Vec3(*self.position)
        dist = distance(my_pos, Vec3(*game.player.position))
        self.label.enabled = (dist < 7.5 and self.cooldown <= 0)

        if dist < 4.5 and self.cooldown <= 0 and held_keys['e']:
            if game.player.gold >= self.cost:
                game.player.gold -= self.cost
                self.cooldown = 3.0
                self.cost = int(self.cost * 1.5)
                self.label.text = f'[E] Алтарь Леса (${self.cost} -> Лечение 60%)'
                game.player.hp = min(float(game.player.max_hp), game.player.hp + game.player.max_hp * 0.6)
                VisualFX(my_pos + Vec3(0, 1.5, 0), color.green, 8.0, 0.45)
                game.show_banner('БЛАГОСЛОВЕНИЕ АЛТАРЯ: +60% HP', color.green, 2.0)


class Teleporter(Entity):
    def __init__(self, pos):
        super().__init__(position=Vec3(*pos))
        self.state = 'idle'
        self.charge = 0.0
        self.zone_radius = 18.0

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
            text='[E] Активировать Древний Телепорт',
            parent=self, y=4.8, scale=13, origin=(0, 0),
            color=color.red, billboard=True
        )

    def activate_teleporter(self, from_network=False):
        if self.state != 'idle':
            return
        game = ctx.game
        self.state = 'charging'
        self.zone_ring.enabled = True
        my_pos = Vec3(*self.position)
        game.spawn_boss(my_pos + Vec3(9, 0, 9), from_network=from_network)
        game.show_banner('ТЕЛЕПОРТ АКТИВИРОВАН! ПОБЕДИТЕ КАМЕННОГО ТИТАНА!', color.red, 3.2)
        if not from_network and getattr(ctx, 'net', None) and ctx.net.connected:
            ctx.net.broadcast({'type': 'tp_activate'})

    def update(self):
        game = ctx.game
        if not game or not game.running or not is_valid(game.player) or self.is_empty():
            return

        self.core.y = 2.6 + math.sin(time.time() * 3.2) * 0.35
        self.core.rotation_y += 75 * time.dt
        my_pos = Vec3(*self.position)
        dist = distance(my_pos, Vec3(*game.player.position))

        if self.state == 'idle':
            self.label.enabled = (dist < 12.0)
            if dist < 5.5 and held_keys['e']:
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
                self.label.text = '[E] Войти в Телепорт -> Следующий Этап'
                game.show_banner('ТЕЛЕПОРТ ЗАРЯЖЕН! НАЖМИТЕ [E] ДЛЯ ПРЫЖКА', color.cyan, 3.5)

        elif self.state == 'ready':
            if dist < 5.8 and held_keys['e']:
                game.next_stage(from_network=False)


def build_stage_world(stage_num, seed=None):
    """Строит мир по общему сиду (для идентичной генерации в мультиплеере)"""
    entities_list = []
    obstacles_list = []
    palette = STAGE_PALETTES[(stage_num - 1) % len(STAGE_PALETTES)]

    if palette['id'] not in PROGRESS.discovered_stages:
        PROGRESS.discovered_stages.append(palette['id'])
        PROGRESS.save()

    window.color = palette['sky']
    scene.fog_color = palette['sky']
    sky_ent = build_skybox(scene, palette)
    entities_list.append(sky_ent)

    if seed is not None:
        random.seed(seed)

    ground = Entity(model='cube', scale=(126, 1, 126), y=-0.5, color=palette['ground'], collider='box')
    entities_list.append(ground)

    struct_types = ['arch', 'monolith', 'crystals', 'platform']
    for _ in range(28):
        px = random.uniform(-50, 50)
        pz = random.uniform(-50, 50)
        if abs(px) < 10 and abs(pz) < 10:
            continue
        st = random.choice(struct_types)
        rot_y = random.uniform(0, 360)
        s_ent, local_obs = build_map_structure(scene, st, palette, Vec3(px, 0, pz), rot_y)
        entities_list.append(s_ent)
        obstacles_list.extend(local_obs)

    chest_cost = int(25 * (1.25 ** (stage_num - 1)))
    for idx in range(9):
        cx = random.uniform(-44, 44)
        cz = random.uniform(-44, 44)
        if abs(cx) < 6 and abs(cz) < 6:
            continue
        chest = Chest(Vec3(cx, 0, cz), chest_cost, chest_id=idx)
        entities_list.append(chest)
        obstacles_list.append((cx, cz, 0.9, 1.0))

    for _ in range(2):
        sx = random.uniform(-36, 36)
        sz = random.uniform(-36, 36)
        shrine = HealingShrine(Vec3(sx, 0, sz), int(chest_cost * 0.8))
        entities_list.append(shrine)
        obstacles_list.append((sx, sz, 1.1, 3.2))

    angle = random.uniform(0, math.pi * 2)
    tp_pos = Vec3(math.cos(angle) * 35, 0, math.sin(angle) * 35)
    tp = Teleporter(tp_pos)
    entities_list.append(tp)
    for a in (0, 90, 180, 270):
        r = math.radians(a)
        obstacles_list.append((tp_pos.x + math.cos(r) * 2.2, tp_pos.z + math.sin(r) * 2.2, 0.65, 3.2))

    random.seed()
    return entities_list, obstacles_list, tp, palette['name']