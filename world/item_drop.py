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
        self.tier = self.info.get('tier', 'white')
        self.tier_name = self.info.get('tier_name', 'ОБЫЧНЫЙ')
        self.tier_col = self.info['color']
        self.is_destroyed = False

        ang = random.uniform(0, math.pi * 2)
        self.vel = Vec3(math.cos(ang) * 4.2, 9.5, math.sin(ang) * 4.2)
        self.landed = False
        # Таймер блокировки подбора после приземления, чтобы игрок успел разглядеть предмет!
        self.lock_timer = 1.35
        self.base_y = start_pos[1] + 0.85

        self.visual = build_item_mesh(self, item_key)
        beam_h = 6.5 if self.tier in ('red', 'void', 'lunar') else 4.5
        beam_w = 0.13 if self.tier in ('red', 'void', 'lunar') else 0.08
        self.beam = Entity(
            parent=self, model='cube', scale=(beam_w, beam_h, beam_w),
            y=beam_h * 0.5, color=self.tier_col, unlit=True
        )
        self.ring = Entity(
            parent=self, model='diamond', scale=(1.25, 0.08, 1.25),
            y=-0.35, color=self.tier_col, unlit=True
        )
        self.label = Text(
            text=f"[{self.tier_name}] {self.info['name']}\n{self.info['desc']}",
            parent=self, y=1.85, scale=10.5, origin=(0, 0),
            color=self.tier_col, billboard=True
        )

    def update(self):
        game = ctx.game
        if not game or not game.running or self.is_destroyed or self.is_empty():
            return

        if not self.landed:
            prev_y = self.y
            self.vel.y -= 22.0 * time.dt
            self.position += self.vel * time.dt
            floor_h = game.get_surface_height(self.x, self.z, self.y, prev_y=prev_y)
            target_y = floor_h + 0.85
            if self.y <= target_y:
                self.y = target_y
                self.base_y = target_y
                self.landed = True
        else:
            self.visual.y = math.sin(time.time() * 3.5) * 0.15
            if self.lock_timer > 0:
                self.lock_timer -= time.dt
                if self.lock_timer <= 0:
                    self.label.text = f"[E] {self.info['name']} [{self.tier_name}]\n{self.info['desc']}"

        self.visual.rotation_y += 95 * time.dt
        self.ring.rotation_y -= 60 * time.dt

        if is_valid(game.player):
            dist = distance(Vec3(*self.position), Vec3(*game.player.position))
            self.label.enabled = (dist < 8.5)
            # Подобрать предмет можно только после приземления и окончания lock_timer (1.35с)
            if self.landed and self.lock_timer <= 0:
                if dist < 2.0 or (dist < 4.2 and held_keys['e']):
                    self.is_destroyed = True
                    game.collect_item(self.item_key)
                    VisualFX(Vec3(*self.position), self.tier_col, 2.8, 0.3)
                    if self in game.stage_entities:
                        game.stage_entities.remove(self)
                    destroy(self)