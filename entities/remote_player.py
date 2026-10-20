from ursina import *
import math
from config import ctx, rgb, SURVIVOR_CLASSES
from models.survivors import build_survivor_mesh
from entities.fx import VisualFX


class RemoteDummyClone(Entity):
    """Визуальная 3D-модель клона M4A1 (Dummy Link) у других игроков по сети"""
    def __init__(self, owner_id, slot_idx, pos):
        super().__init__(position=Vec3(*pos))
        self.owner_id = owner_id
        self.slot_idx = slot_idx
        self.target_pos = Vec3(*pos)
        self.target_rot_y = 0.0
        self.hp = 80.0
        self.max_hp = 80.0
        self.hit_height = 1.2
        self.hit_radius = 1.1

        self.parts = build_survivor_mesh(self, 'm4a1')
        self.link_ring = Entity(
            parent=self, model='diamond', scale=(1.35, 0.08, 1.35),
            y=0.06, color=rgb(95, 255, 135, 180), unlit=True
        )
        self.label = Text(
            text=f'[{owner_id.upper()}] DUMMY #{slot_idx + 1}',
            parent=self, y=2.75, scale=8.5, origin=(0, 0),
            color=rgb(95, 255, 135), billboard=True
        )
        self.hp_bg = Entity(parent=self, model='quad', scale=(1.0, 0.10), y=2.45, color=color.black, billboard=True)
        self.hp_fill = Entity(parent=self.hp_bg, model='quad', scale=(1, 1), z=-0.01, color=rgb(95, 255, 135), unlit=True)

    def apply_state(self, cx, cy, cz, rot_y, hp, max_hp):
        self.target_pos = Vec3(cx, cy, cz)
        self.target_rot_y = rot_y
        self.hp = hp
        self.max_hp = max(1.0, max_hp)
        if not self.hp_fill.is_empty():
            self.hp_fill.scale_x = clamp(self.hp / self.max_hp, 0.0, 1.0)

    def update(self):
        if self.is_empty():
            return
        self.link_ring.rotation_y += 90 * time.dt
        prev_pos = Vec3(*self.position)
        self.position = lerp(self.position, self.target_pos, min(1.0, time.dt * 14.0))
        self.rotation_y = lerp(self.rotation_y, self.target_rot_y, min(1.0, time.dt * 14.0))
        if (self.target_pos - prev_pos).length() > 0.03:
            swing = math.sin(time.time() * 12.0 + self.slot_idx) * 34.0
            self.parts['left_leg'].rotation_x = swing
            self.parts['right_leg'].rotation_x = -swing
        else:
            self.parts['left_leg'].rotation_x = lerp(self.parts['left_leg'].rotation_x, 0, time.dt * 10)
            self.parts['right_leg'].rotation_x = lerp(self.parts['right_leg'].rotation_x, 0, time.dt * 10)


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
        self.remote_clones = {}

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

    def clear_remote_clones(self):
        for c in list(self.remote_clones.values()):
            if c and not c.is_empty():
                destroy(c)
        self.remote_clones.clear()

    def on_destroy(self):
        self.clear_remote_clones()

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

        # Синхронизация клонов M4A1 (Dummy Link)
        clones_list = msg.get('clones', [])
        active_slots = set()
        for c_info in clones_list:
            slot_idx, cx, cy, cz, crot, chp, cmax = c_info
            active_slots.add(slot_idx)
            if slot_idx not in self.remote_clones or self.remote_clones[slot_idx].is_empty():
                self.remote_clones[slot_idx] = RemoteDummyClone(self.player_id, slot_idx, (cx, cy, cz))
            self.remote_clones[slot_idx].apply_state(cx, cy, cz, crot, chp, cmax)

        for old_slot in list(self.remote_clones.keys()):
            if old_slot not in active_slots:
                old_c = self.remote_clones.pop(old_slot)
                if old_c and not old_c.is_empty():
                    VisualFX(Vec3(*old_c.position) + Vec3(0, 1.2, 0), rgb(95, 255, 135), 2.5, 0.25)
                    destroy(old_c)

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

