from ursina import *
import math
import random
from config import ctx, rgb, is_valid, ITEM_POOL
from data.items import LUNAR_ITEMS
from models.items import build_item_mesh
from entities.fx import VisualFX, LightningBeam


class NewtAltar(Entity):
    """Синий Алтарь Тритона: за 1 Лунную Монету открывает Синий Портал на Базар"""
    def __init__(self, pos):
        super().__init__(position=Vec3(*pos))
        self.used = False
        Entity(parent=self, model='diamond', scale=(1.5, 0.6, 1.5), y=0.3, color=rgb(38, 48, 72), collider='box')
        self.crystal = Entity(parent=self, model='diamond', scale=(0.85, 2.2, 0.85), y=1.5, color=rgb(60, 175, 255), unlit=True)
        self.ring = Entity(parent=self, model='diamond', scale=(1.6, 0.12, 1.6), y=1.4, color=color.cyan, unlit=True)
        self.label = Text(
            text='[E] Алтарь Тритона (1 Лунная Монета -> Синий Портал)',
            parent=self, y=3.1, scale=11, origin=(0, 0),
            color=rgb(80, 200, 255), billboard=True
        )

    def update(self):
        game = ctx.game
        if self.used or not game or not game.running or not is_valid(game.player) or self.is_empty():
            return
        self.crystal.rotation_y += 65 * time.dt
        self.ring.rotation_y -= 90 * time.dt
        dist = distance(Vec3(*self.position), Vec3(*game.player.position))
        self.label.enabled = (dist < 7.5)

        if dist < 4.2 and held_keys['e']:
            if game.lunar_coins >= 1:
                game.lunar_coins -= 1
                self.used = True
                self.label.enabled = False
                self.crystal.color = color.gray
                game.blue_orb_spawned = True
                VisualFX(Vec3(*self.position) + Vec3(0, 1.5, 0), color.cyan, 6.0, 0.4)
                game.show_banner('ПОЯВИЛАСЬ СИНЯЯ СФЕРА! ПОСЛЕ ТЕЛЕПОРТА ОТКРОЕТСЯ БАЗАР', rgb(80, 210, 255), 3.5)
            else:
                game.show_banner('НЕДОСТАТОЧНО ЛУННЫХ МОНЕТ (НУЖНА 1 МОНЕТА)', color.red, 2.0)


class BluePortal(Entity):
    """Портал на Базар между Временем (или обратно на трассу этапов)"""
    def __init__(self, pos, target_mode='bazaar'):
        super().__init__(position=Vec3(*pos))
        self.target_mode = target_mode
        self.ring = Entity(parent=self, model='diamond', scale=(4.2, 5.2, 0.35), y=2.7, color=rgb(50, 150, 255), unlit=True)
        self.core = Entity(parent=self, model='sphere', scale=(3.2, 4.2, 0.25), y=2.7, color=rgb(130, 230, 255, 190), unlit=True)
        txt = '[E] Войти в Синий Портал -> Базар Между Временем' if target_mode == 'bazaar' else '[E] Покинуть Базар -> Следующий Этап'
        self.label = Text(text=txt, parent=self, y=5.8, scale=12, origin=(0, 0), color=color.cyan, billboard=True)

    def update(self):
        game = ctx.game
        if not game or not game.running or not is_valid(game.player) or self.is_empty():
            return
        self.ring.rotation_z += 75 * time.dt
        dist = distance(Vec3(*self.position), Vec3(*game.player.position))
        self.label.enabled = (dist < 10.0)
        if dist < 4.5 and held_keys['e']:
            if self.target_mode == 'bazaar':
                game.enter_bazaar()
            else:
                game.next_stage()


class LunarShopBud(Entity):
    """Витрина с Лунным Предметом на Базаре Тритона"""
    def __init__(self, pos, item_key, cost=2):
        super().__init__(position=Vec3(*pos))
        self.item_key = item_key
        self.cost = cost
        self.bought = False
        info = ITEM_POOL[item_key]

        Entity(parent=self, model='diamond', scale=(1.6, 0.8, 1.6), y=0.4, color=rgb(35, 50, 82))
        self.pod = Entity(parent=self, model='sphere', scale=(1.3, 1.6, 1.3), y=1.5, color=rgb(70, 175, 255, 85), unlit=True)
        self.visual = build_item_mesh(self, item_key)
        self.visual.y = 1.5
        self.label = Text(
            text=f"[E] {info['name']} ({self.cost} Лунные Монеты)\n{info['desc']}",
            parent=self, y=3.1, scale=9.5, origin=(0, 0),
            color=rgb(110, 215, 255), billboard=True
        )

    def update(self):
        game = ctx.game
        if self.bought or not game or not game.running or not is_valid(game.player) or self.is_empty():
            return
        self.visual.rotation_y += 85 * time.dt
        dist = distance(Vec3(*self.position), Vec3(*game.player.position))
        self.label.enabled = (dist < 7.0)
        if dist < 3.6 and held_keys['e']:
            if game.lunar_coins >= self.cost:
                game.lunar_coins -= self.cost
                self.bought = True
                self.label.enabled = False
                self.pod.enabled = False
                self.visual.enabled = False
                game.collect_item(self.item_key)
                VisualFX(Vec3(*self.position) + Vec3(0, 1.5, 0), color.cyan, 3.5, 0.35)
            else:
                game.show_banner('НЕ ХВАТАЕТ ЛУННЫХ МОНЕТ!', color.red, 1.8)


class LunarCauldron(Entity):
    """Котел Обмена на Базаре: меняет 3 обычных предмета на 1 мощный предмет"""
    def __init__(self, pos, reward_key, req_count=3):
        super().__init__(position=Vec3(*pos))
        self.reward_key = reward_key
        self.req_count = req_count
        self.cooldown = 0.0
        info = ITEM_POOL[reward_key]

        Entity(parent=self, model='cube', scale=(2.2, 1.2, 2.2), y=0.6, color=rgb(48, 54, 68), collider='box')
        Entity(parent=self, model='sphere', scale=(1.9, 0.4, 1.9), y=1.25, color=color.red if req_count >= 5 else color.green, unlit=True)
        self.visual = build_item_mesh(self, reward_key)
        self.visual.y = 2.2
        self.label = Text(
            text=f"[E] Котёл Обмена: Отдать {req_count} предмета -> {info['name']}",
            parent=self, y=3.5, scale=10, origin=(0, 0),
            color=color.gold if req_count >= 5 else color.lime, billboard=True
        )

    def update(self):
        game = ctx.game
        if not game or not game.running or not is_valid(game.player) or self.is_empty():
            return
        self.visual.rotation_y += 80 * time.dt
        self.cooldown = max(0.0, self.cooldown - time.dt)
        dist = distance(Vec3(*self.position), Vec3(*game.player.position))
        self.label.enabled = (dist < 7.5 and self.cooldown <= 0)

        if dist < 4.0 and self.cooldown <= 0 and held_keys['e']:
            p = game.player
            non_lunar = [k for k, cnt in p.items.items() if cnt > 0 and k not in LUNAR_ITEMS]
            total_avail = sum(p.items[k] for k in non_lunar)
            if total_avail >= self.req_count:
                self.cooldown = 1.5
                for _ in range(self.req_count):
                    avail_keys = [k for k in non_lunar if p.items[k] > 0]
                    take_k = random.choice(avail_keys)
                    p.items[take_k] -= 1
                    if p.items[take_k] <= 0 and take_k in p.item_order:
                        p.item_order.remove(take_k)
                game.collect_item(self.reward_key)
                VisualFX(Vec3(*self.position) + Vec3(0, 1.8, 0), color.gold, 4.5, 0.4)
            else:
                game.show_banner(f'НУЖНО МИНИМУМ {self.req_count} ОБЫЧНЫХ ПРЕДМЕТА ДЛЯ ОБМЕНА!', color.orange, 2.0)


class MoonPillar(Entity):
    """Столпы Луны (Массы, Дизайна, Крови и Души), которые нужно зарядить для подъёма к Митриксу"""
    def __init__(self, pos, pillar_type='mass'):
        super().__init__(position=Vec3(*pos))
        self.pillar_type = pillar_type
        self.state = 'idle'
        self.charge = 0.0
        self.radius = 12.0
        self.pulse_timer = 2.0

        titles = {
            'mass': ('Столп Массы', rgb(75, 210, 255)),
            'design': ('Столп Дизайна (Импульсы)', rgb(110, 180, 255)),
            'blood': ('Столп Крови (Поглощает HP)', rgb(245, 65, 85)),
            'soul': ('Столп Души (Не выходите из зоны)', rgb(165, 110, 255))
        }
        self.title, self.col = titles.get(pillar_type, titles['mass'])

        Entity(parent=self, model='cube', scale=(2.8, 0.6, 2.8), y=0.3, color=rgb(50, 62, 84), collider='box')
        self.obelisk = Entity(parent=self, model='diamond', scale=(1.5, 5.5, 1.5), y=3.2, color=rgb(215, 225, 242))
        self.core = Entity(parent=self, model='diamond', scale=(1.9, 1.4, 1.9), y=3.2, color=self.col, unlit=True)
        self.zone_ring = Entity(
            parent=self, model='sphere',
            scale=(self.radius * 2, 0.06, self.radius * 2),
            y=0.06, color=rgb(70, 200, 255, 45), unlit=True, enabled=False
        )
        self.label = Text(
            text=f'[E] Активировать {self.title}',
            parent=self, y=6.5, scale=11.5, origin=(0, 0),
            color=self.col, billboard=True
        )

    def update(self):
        game = ctx.game
        if not game or not game.running or not is_valid(game.player) or self.is_empty():
            return

        self.core.rotation_y += 75 * time.dt
        my_pos = Vec3(*self.position)
        p = game.player
        p_pos = Vec3(*p.position)
        dist = distance_2d(my_pos, p_pos)

        if self.state == 'idle':
            self.label.enabled = (dist < 14.0)
            if dist < 4.8 and held_keys['e']:
                self.state = 'charging'
                self.zone_ring.enabled = True
                game.show_banner(f'ЗАРЯДКА: {self.title.upper()}!', self.col, 2.5)

        elif self.state == 'charging':
            self.label.enabled = True
            if dist <= self.radius and p_pos.y < 10.0:
                rate = 14.0
                if self.pillar_type == 'blood':
                    rate = 24.0
                    p.hp = max(1.0, p.hp - 8.5 * time.dt)
                elif self.pillar_type == 'design':
                    self.pulse_timer -= time.dt
                    if self.pulse_timer <= 0:
                        self.pulse_timer = 2.4
                        LunarPos = my_pos + Vec3(0, 0.5, 0)
                        VisualFX(LunarPos, self.col, 14.0, 0.35)
                        push_dir = (p_pos - my_pos).normalized()
                        p.dash_vector = Vec3(push_dir.x * 20.0, 0, push_dir.z * 20.0)
                        p.dash_timer = 0.22

                self.charge = min(100.0, self.charge + rate * time.dt)
            else:
                if self.pillar_type == 'soul':
                    self.charge = max(0.0, self.charge - 12.0 * time.dt)

            self.label.text = f'{self.title}: {int(self.charge)}%'
            if self.charge >= 100.0:
                self.state = 'done'
                self.zone_ring.enabled = False
                self.core.color = color.lime
                self.label.color = color.lime
                self.label.text = f'{self.title} ЗАРЯЖЕН ✓'
                LightningBeam(my_pos + Vec3(0, 4, 0), Vec3(0, 22, 0), color.cyan, 0.45)
                game.on_moon_pillar_charged()


class LunarJumpPad(Entity):
    """Гравитационный лифт в центре Луны, подбрасывающий игрока на Небесный Колизей Митрикса"""
    def __init__(self, pos):
        super().__init__(position=Vec3(*pos))
        self.active = False
        Entity(parent=self, model='cube', scale=(5.2, 0.4, 5.2), y=0.2, color=rgb(45, 58, 82), collider='box')
        self.beam = Entity(parent=self, model='cube', scale=(1.8, 22.0, 1.8), y=11.0, color=rgb(70, 225, 255, 95), unlit=True, enabled=False)
        self.ring = Entity(parent=self, model='diamond', scale=(4.2, 0.25, 4.2), y=0.5, color=color.gray, unlit=True)
        self.label = Text(
            text='Зарядите минимум 2 Столпа Луны для активации Лифта к Митриксу',
            parent=self, y=3.8, scale=11.5, origin=(0, 0),
            color=color.yellow, billboard=True
        )

    def unlock_pad(self):
        self.active = True
        self.beam.enabled = True
        self.ring.color = color.cyan
        self.label.color = color.cyan
        self.label.text = '[ВСТАНЬТЕ В ЛУЧ] Грави-лифт к Колизею Митрикса!'

    def update(self):
        game = ctx.game
        if not game or not game.running or not is_valid(game.player) or self.is_empty():
            return
        self.ring.rotation_y += 95 * time.dt
        p = game.player
        dist = distance_2d(Vec3(*self.position), Vec3(*p.position))
        if self.active and dist < 2.8 and p.y < 8.0:
            p.position = Vec3(0, 24.5, -18.0)
            p.vel_y = 6.0
            VisualFX(Vec3(0, 23.0, -18.0), color.cyan, 6.0, 0.4)
            game.start_mithrix_encounter()


class EscapeShip(Entity):
    """Спасательный челнок UES для эвакуации после победы над Митриксом"""
    def __init__(self, pos):
        super().__init__(position=Vec3(*pos))
        self.charge = 0.0
        self.radius = 12.0

        hull = Entity(parent=self, y=1.8)
        Entity(parent=hull, model='cube', scale=(4.5, 2.2, 7.5), color=rgb(215, 225, 240))
        Entity(parent=hull, model='diamond', scale=(4.2, 1.8, 3.5), z=4.2, color=rgb(235, 130, 35))
        Entity(parent=hull, model='cube', scale=(3.2, 0.9, 2.5), position=(0, 0.6, 2.6), color=color.cyan, unlit=True)
        Entity(parent=hull, model='cube', scale=(7.8, 0.3, 2.8), y=-0.4, color=rgb(65, 75, 92))

        self.zone_ring = Entity(
            parent=self, model='sphere',
            scale=(self.radius * 2, 0.08, self.radius * 2),
            y=0.08, color=rgb(80, 255, 120, 65), unlit=True
        )
        self.label = Text(
            text='ЭВАКУАЦИЯ: ВСТАНЬТЕ В ЗОНУ КОРАБЛЯ СПАСЕНИЯ!',
            parent=self, y=5.5, scale=13, origin=(0, 0),
            color=color.lime, billboard=True
        )

    def update(self):
        game = ctx.game
        if not game or not game.running or not is_valid(game.player) or self.is_empty():
            return
        dist = distance(Vec3(*self.position), Vec3(*game.player.position))
        if dist <= self.radius:
            self.charge = min(100.0, self.charge + 14.0 * time.dt)
            self.label.text = f'ЗАПУСК ДВИГАТЕЛЕЙ СПАСЕНИЯ: {int(self.charge)}%'
            if self.charge >= 100.0:
                game.on_run_victory()