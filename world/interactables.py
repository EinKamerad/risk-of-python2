from ursina import *
import math
import random
from config import ctx, rgb, is_valid, roll_item_from_pool
from entities.fx import VisualFX
from entities.projectile import Projectile


class Chest(Entity):
    def __init__(self, pos, cost, chest_id=0, chest_type='small'):
        super().__init__(position=Vec3(*pos))
        self.chest_id = chest_id
        self.chest_type = chest_type
        self.opened = False

        if chest_type == 'large':
            self.cost = int(cost * 2.0)
            self.pool_type = 'large_chest'
            body_col = rgb(40, 115, 95)
            trim_col = rgb(85, 235, 95)
            lid_col = rgb(55, 135, 110)
            sc = 1.25
            title_str = f'[E] Большой Сундук (${self.cost}) [Зелёный/Красный]'
            lbl_col = rgb(85, 235, 95)
        elif chest_type == 'legendary':
            self.cost = int(cost * 4.5)
            self.pool_type = 'legendary_chest'
            body_col = rgb(145, 35, 45)
            trim_col = color.gold
            lid_col = rgb(185, 50, 60)
            sc = 1.45
            title_str = f'[E] Легендарный Сундук (${self.cost}) [100% Легендарный!]'
            lbl_col = rgb(255, 75, 85)
        elif chest_type == 'lunar_pod':
            self.cost = 1  # 1 Лунная Монета!
            self.pool_type = 'lunar_pod'
            body_col = rgb(38, 52, 88)
            trim_col = rgb(165, 110, 255)
            lid_col = rgb(65, 175, 255)
            sc = 1.15
            title_str = '[E] Лунный Бутон (1 Лунная Монета) [Лунный / Пустота]'
            lbl_col = rgb(150, 195, 255)
        else:
            self.cost = cost
            self.pool_type = 'small_chest'
            body_col = rgb(55, 105, 175)
            trim_col = color.cyan
            lid_col = rgb(75, 85, 105)
            sc = 1.0
            title_str = f'[E] Сундук (${self.cost})'
            lbl_col = color.yellow

        if chest_type == 'lunar_pod':
            # Органическая капсула Лунного Бутона
            Entity(parent=self, model='diamond', scale=(1.5 * sc, 0.55 * sc, 1.5 * sc), y=0.25, color=body_col, collider='box')
            self.lid = Entity(parent=self, position=(0, 0.9 * sc, 0))
            Entity(parent=self.lid, model='sphere', scale=(1.15 * sc, 1.35 * sc, 1.15 * sc), color=rgb(75, 165, 255, 150), unlit=True)
            self.lock_gem = Entity(parent=self.lid, model='diamond', scale=(0.65 * sc, 0.95 * sc, 0.65 * sc), color=trim_col, unlit=True)
        else:
            Entity(parent=self, model='cube', scale=(1.5 * sc, 0.2 * sc, 1.1 * sc), y=0.1 * sc, color=rgb(45, 50, 62), collider='box')
            Entity(parent=self, model='cube', scale=(1.35 * sc, 0.7 * sc, 0.95 * sc), y=0.45 * sc, color=body_col)
            Entity(parent=self, model='cube', scale=(1.38 * sc, 0.12 * sc, 0.98 * sc), y=0.55 * sc, color=trim_col, unlit=True)

            self.lid = Entity(parent=self, position=(0, 0.85 * sc, 0))
            Entity(parent=self.lid, model='cube', scale=(1.42 * sc, 0.25 * sc, 1.02 * sc), color=lid_col)
            self.lock_gem = Entity(parent=self.lid, model='diamond', scale=(0.38 * sc, 0.38 * sc, 0.38 * sc), z=0.5 * sc, color=color.gold, unlit=True)

        self.label = Text(
            text=title_str,
            parent=self, y=2.2 * sc + 0.2, scale=10.5, origin=(0, 0),
            color=lbl_col, billboard=True
        )

    def open_visual(self, item_key=None):
        if self.opened:
            return
        self.opened = True
        self.label.enabled = False
        self.lock_gem.color = color.gray
        if self.chest_type == 'lunar_pod':
            self.lid.enabled = False
        else:
            self.lid.animate_position((0, self.lid.y + 0.4, -0.45), duration=0.28)
            self.lid.animate_rotation((-70, 0, 0), duration=0.28)

        my_pos = Vec3(*self.position)
        VisualFX(my_pos + Vec3(0, 1.0, 0), color.cyan if self.chest_type == 'lunar_pod' else color.gold, 3.2, 0.35)

        game = ctx.game
        if game:
            game.spawn_item_drop(my_pos, item_key=item_key, pool_type=self.pool_type, broadcast=False)
            if is_valid(game.player):
                fw_stacks = game.player.items.get('bundle_fireworks', 0)
                if fw_stacks > 0:
                    rockets = min(16, 4 + fw_stacks * 3)
                    for i in range(rockets):
                        ang = (i / float(rockets)) * math.pi * 2
                        d = Vec3(math.cos(ang) * 0.5, 1.0, math.sin(ang) * 0.5).normalized()
                        Projectile(
                            pos=my_pos + Vec3(0, 1.6, 0),
                            direction=d,
                            speed=42.0,
                            damage=game.player.base_damage * 1.35,
                            scale_val=0.30,
                            proj_color=rgb(255, 95, 215),
                            is_player=True,
                            aoe=2.2,
                            homing=True,
                            can_proc=False
                        )

    def update(self):
        game = ctx.game
        if self.opened or not game or not game.running or not is_valid(game.player) or self.is_empty():
            return

        if self.chest_type == 'lunar_pod' and not self.lock_gem.is_empty():
            self.lock_gem.rotation_y += 80 * time.dt

        my_pos = Vec3(*self.position)
        dist = distance(my_pos, Vec3(*game.player.position))
        self.label.enabled = (dist < 7.2)

        if dist < 4.2 and held_keys['e']:
            if self.chest_type == 'lunar_pod':
                if game.lunar_coins >= self.cost:
                    game.lunar_coins -= self.cost
                    chosen_key = roll_item_from_pool(self.pool_type)
                    self.open_visual(chosen_key)
                    if getattr(ctx, 'net', None) and ctx.net.connected:
                        ctx.net.broadcast({'type': 'chest_open', 'chest_id': self.chest_id, 'item_key': chosen_key})
                else:
                    game.show_banner('НУЖНА 1 ЛУННАЯ МОНЕТА ДЛЯ ОТКРЫТИЯ БУТОНА!', color.red, 1.8)
            else:
                if game.player.gold >= self.cost:
                    game.player.gold -= self.cost
                    chosen_key = roll_item_from_pool(self.pool_type)
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
                game.player.heal_amount(game.player.max_hp * 0.6)
                VisualFX(my_pos + Vec3(0, 1.5, 0), color.green, 8.0, 0.45)
                game.show_banner('БЛАГОСЛОВЕНИЕ АЛТАРЯ: +60% HP', color.green, 2.0)