from ursina import *
import math
import random
from config import ctx, rgb, is_valid, ITEM_POOL
from entities.fx import VisualFX
from entities.projectile import Projectile

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

        game = ctx.game
        if game:
            game.spawn_item_drop(my_pos, item_key=item_key, broadcast=False)
            # Bundle of Fireworks: выпускает самонаводящиеся ракеты из открытого сундука
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

