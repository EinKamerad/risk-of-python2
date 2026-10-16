from ursina import *
import math
import random
from config import ctx, is_valid, ITEM_POOL
from models.items import build_item_mesh
from entities.fx import VisualFX

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

