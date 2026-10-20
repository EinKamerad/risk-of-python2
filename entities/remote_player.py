from ursina import *
import math
from config import ctx, SURVIVOR_CLASSES
from models.survivors import build_survivor_mesh
from entities.fx import VisualFX


class RemotePlayer(Entity):
    def __init__(self, player_id, char_key='commando'):
        super().__init__(position=(2, 0, 2))
        self.player_id = player_id
        self.char_key = char_key
        self.target_pos = Vec3(2, 0, 2)
        self.target_rot_y = 0.0
        self.is_moving = False
        self.hp = 110.0
        self.max_hp = 110.0
        self.hit_height = 1.2
        self.hit_radius = 1.1

        self.parts = build_survivor_mesh(self, char_key)
        self.label = Text(
            text=f"[{player_id.upper()}] {SURVIVOR_CLASSES[char_key]['name']}",
            parent=self,
            y=2.85,
            scale=9.5,
            origin=(0, 0),
            color=color.cyan,
            billboard=True
        )
        self.hp_bg = Entity(parent=self, model='quad', scale=(1.2, 0.12), y=2.5, color=color.black, billboard=True)
        self.hp_fill = Entity(parent=self.hp_bg, model='quad', scale=(1, 1), z=-0.01, color=color.green, unlit=True)

    def heal_ally(self, amount=0.0, shield_amt=0.0, uber_dur=0.0):
        """Лечит и баффает сетевого союзника, отправляя пакет реальному игроку"""
        if amount > 0:
            self.hp = min(float(self.max_hp), self.hp + amount)
            if not self.hp_fill.is_empty():
                self.hp_fill.scale_x = clamp(self.hp / max(1.0, self.max_hp), 0.0, 1.0)
        if getattr(ctx, 'net', None) and ctx.net.connected:
            ctx.net.broadcast({
                'type': 'ally_buff',
                'target_id': self.player_id,
                'heal': round(amount, 1),
                'shield': round(shield_amt, 1),
                'uber': round(uber_dur, 1)
            })

    def take_damage(self, amount):
        """Визуальный отклик удара по сетевому игроку (урон рассчитывается на стороне самого игрока)"""
        if not self.is_empty():
            VisualFX(Vec3(*self.position) + Vec3(0, 1.1, 0), color.red, 1.5, 0.2)
            
    def rebuild_class(self, new_char_key):
        if new_char_key == self.char_key or new_char_key not in SURVIVOR_CLASSES:
            return
        self.char_key = new_char_key
        if self.parts and self.parts.get('root'):
            destroy(self.parts['root'])
        self.parts = build_survivor_mesh(self, new_char_key)
        self.label.text = f"[{self.player_id.upper()}] {SURVIVOR_CLASSES[new_char_key]['name']}"

    def apply_net_state(self, msg):
        self.rebuild_class(msg.get('char_key', self.char_key))
        pos = msg.get('pos', [0, 0, 0])
        self.target_pos = Vec3(pos[0], pos[1], pos[2])
        self.target_rot_y = msg.get('rot_y', 0.0)
        self.is_moving = msg.get('moving', False)
        self.hp = msg.get('hp', self.hp)
        self.max_hp = max(1, msg.get('max_hp', self.max_hp))
        if not self.hp_fill.is_empty():
            self.hp_fill.scale_x = clamp(self.hp / self.max_hp, 0.0, 1.0)

    def update(self):
        if self.is_empty():
            return
        self.position = lerp(self.position, self.target_pos, min(1.0, time.dt * 14.0))
        self.rotation_y = lerp(self.rotation_y, self.target_rot_y, min(1.0, time.dt * 14.0))

        if self.is_moving and self.char_key != 'mindustry':
            swing = math.sin(time.time() * 11.5) * 36.0
            self.parts['left_leg'].rotation_x = swing
            self.parts['right_leg'].rotation_x = -swing
        else:
            self.parts['left_leg'].rotation_x = lerp(self.parts['left_leg'].rotation_x, 0, time.dt * 10)
            self.parts['right_leg'].rotation_x = lerp(self.parts['right_leg'].rotation_x, 0, time.dt * 10)

        if self.parts.get('halo'):
            self.parts['halo'].rotation_z += 95 * time.dt

