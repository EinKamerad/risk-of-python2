from ursina import *
from config import rgb, clear_children, SURVIVOR_CLASSES, ITEM_POOL, MONSTER_LOG, STAGE_PALETTES, ACHIEVEMENTS, PROGRESS
from data.stages import SPECIAL_PALETTES
from models.survivors import build_survivor_mesh
from models.enemies import build_enemy_mesh
from models.items import build_item_mesh
from models.structures import build_map_structure


class DioramaMixin:
    def setup_menu_diorama(self):
        self.diorama_root = Entity(position=(0, 0, 0))
        self.preview_manual_timer = 0.0
        self.preview_zoom = 1.0

        self.main_pedestal = Entity(parent=self.diorama_root, position=(1.15, 0, -1.0))
        Entity(parent=self.main_pedestal, model='cube', scale=(3.4, 0.35, 3.4), y=-0.18, color=rgb(34, 42, 58))
        Entity(parent=self.main_pedestal, model='cube', scale=(2.8, 0.14, 2.8), y=0.04, color=rgb(55, 70, 96))
        self.pedestal_ring = Entity(parent=self.main_pedestal, model='cube', scale=(2.9, 0.05, 2.9), y=0.10, color=color.cyan, unlit=True)

        self.local_preview_actor = Entity(parent=self.main_pedestal, position=(0, 0.12, 0), rotation=(0, 15, 0))
        self.local_preview_parts = build_survivor_mesh(self.local_preview_actor, self.selected_char)

        self.remote_pedestals = []
        back_coords = [
            (-0.95, 0.35, 2.3, 18),
            (1.15, 0.35, 2.8, 0),
            (3.25, 0.35, 2.3, -18)
        ]
        for bx, by, bz, rot_y in back_coords:
            ped = Entity(parent=self.diorama_root, position=(bx, by, bz), enabled=False)
            Entity(parent=ped, model='cube', scale=(2.2, 0.3, 2.2), y=-0.15, color=rgb(28, 34, 48))
            ring = Entity(parent=ped, model='cube', scale=(1.9, 0.06, 1.9), y=0.03, color=rgb(80, 180, 255), unlit=True)
            actor = Entity(parent=ped, position=(0, 0.06, 0), rotation_y=rot_y)
            lbl = Text(
                text='', parent=ped, y=2.95, scale=8.5,
                origin=(0, 0), color=color.cyan, billboard=True
            )
            self.remote_pedestals.append({
                'pedestal': ped,
                'ring': ring,
                'actor': actor,
                'label': lbl,
                'char_key': None,
                'parts': None
            })

        self.menu_crystal = Entity(
            parent=self.diorama_root, model='diamond',
            scale=(0.85, 1.85, 0.85), position=(1.15, 3.3, 2.2),
            color=rgb(60, 215, 255), unlit=True
        )

        self.reset_menu_camera()

    def reset_menu_camera(self):
        camera.parent = scene
        camera.position = (0, 2.15, -8.6)
        camera.rotation = (5, 0, 0)
        camera.fov = self.settings.get('fov', 90)

    def reset_preview_orientation(self):
        self.preview_manual_timer = 0.0
        self.preview_zoom = 1.0
        if hasattr(self, 'local_preview_actor') and not self.local_preview_actor.is_empty():
            self.local_preview_actor.rotation = (0, 15, 0)

    def adjust_preview_zoom(self, delta):
        self.preview_zoom = clamp(self.preview_zoom + delta, 0.55, 1.75)
        self.preview_manual_timer = 4.0

    def update_diorama_inspection(self):
        """Позволяет вращать 3D-модель во всех плоскостях мышью (ЛКМ/ПКМ) или клавишами Q/E/стрелками"""
        if not hasattr(self, 'local_preview_actor') or self.local_preview_actor.is_empty():
            return

        # Вращение зажатой ПКМ (в любой точке) или ЛКМ (в правой части экрана над пьедесталом)
        dragging = mouse.right or (mouse.left and mouse.x > -0.04)
        if dragging and (abs(mouse.velocity[0]) > 0.0001 or abs(mouse.velocity[1]) > 0.0001):
            self.local_preview_actor.rotation_y -= mouse.velocity[0] * 280.0
            self.local_preview_actor.rotation_x = clamp(
                self.local_preview_actor.rotation_x + mouse.velocity[1] * 200.0, -65.0, 65.0
            )
            self.preview_manual_timer = 4.5

        # Вращение с клавиатуры (Q/E и стрелки)
        rot_spd = 110.0 * time.dt
        if held_keys['q'] or held_keys['left arrow']:
            self.local_preview_actor.rotation_y += rot_spd
            self.preview_manual_timer = 3.0
        if held_keys['e'] or held_keys['right arrow']:
            self.local_preview_actor.rotation_y -= rot_spd
            self.preview_manual_timer = 3.0
        if held_keys['up arrow']:
            self.local_preview_actor.rotation_x = clamp(self.local_preview_actor.rotation_x + rot_spd * 0.7, -65.0, 65.0)
            self.preview_manual_timer = 3.0
        if held_keys['down arrow']:
            self.local_preview_actor.rotation_x = clamp(self.local_preview_actor.rotation_x - rot_spd * 0.7, -65.0, 65.0)
            self.preview_manual_timer = 3.0

        base_scale = getattr(self, '_preview_base_scale', 1.0)
        self.local_preview_actor.scale = base_scale * self.preview_zoom

        if self.preview_manual_timer > 0:
            self.preview_manual_timer -= time.dt
        else:
            self.local_preview_actor.rotation_y += 22.0 * time.dt
            self.local_preview_actor.rotation_x = lerp(self.local_preview_actor.rotation_x, 0.0, time.dt * 5.0)

        # Анимация деталей превью (ореолы, короны, кольца, щупальца)
        if isinstance(self.local_preview_parts, dict):
            if self.local_preview_parts.get('halo'):
                self.local_preview_parts['halo'].rotation_z += 90 * time.dt
            if self.local_preview_parts.get('crown'):
                self.local_preview_parts['crown'].rotation_y += 85 * time.dt
            if self.local_preview_parts.get('ring1'):
                self.local_preview_parts['ring1'].rotation_y += 110 * time.dt
            if self.local_preview_parts.get('ring2'):
                self.local_preview_parts['ring2'].rotation_x += 125 * time.dt
            if self.local_preview_parts.get('tentacles'):
                self.local_preview_parts['tentacles'].rotation_y += 70 * time.dt

    def rebuild_local_lobby_model(self):
        clear_children(self.local_preview_actor)
        self._preview_base_scale = 1.0
        self.local_preview_actor.position = (0, 0.12, 0)
        self.local_preview_actor.rotation = (0, 15, 0)
        self.local_preview_actor.scale = self.preview_zoom
        self.pedestal_ring.color = SURVIVOR_CLASSES[self.selected_char]['body_color']
        self.local_preview_parts = build_survivor_mesh(self.local_preview_actor, self.selected_char)

    def build_logbook_preview(self, category, entry_key):
        """Строит 3D-модель выбранной записи Журнала на главном пьедестале"""
        clear_children(self.local_preview_actor)
        self.local_preview_parts = None
        self.local_preview_actor.rotation = (0, 20, 0)

        if category == 'items':
            info = ITEM_POOL[entry_key]
            self._preview_base_scale = 1.85
            self.local_preview_actor.position = (0, 1.35, 0)
            self.pedestal_ring.color = info['color']
            build_item_mesh(self.local_preview_actor, entry_key)

        elif category == 'survivors':
            cfg = SURVIVOR_CLASSES[entry_key]
            self._preview_base_scale = 1.0
            self.local_preview_actor.position = (0, 0.12, 0)
            self.pedestal_ring.color = cfg['body_color']
            self.local_preview_parts = build_survivor_mesh(self.local_preview_actor, entry_key)

        elif category == 'monsters':
            scale_map = {'golem': 0.78, 'greater_wisp': 0.75, 'lunar_chimera': 0.75}
            y_map = {'wisp': -0.75, 'jellyfish': -0.65, 'greater_wisp': -0.85, 'lunar_chimera': -0.75}
            self._preview_base_scale = scale_map.get(entry_key, 0.95)
            self.local_preview_actor.position = (0, y_map.get(entry_key, 0.12), 0)
            self.pedestal_ring.color = rgb(255, 140, 50)
            self.local_preview_parts = build_enemy_mesh(self.local_preview_actor, entry_key)

        elif category == 'bosses':
            scale_map = {'boss': 0.48, 'vagrant': 0.44, 'overlord': 0.48, 'mithrix': 0.50}
            y_map = {'vagrant': -0.35}
            self._preview_base_scale = scale_map.get(entry_key, 0.48)
            self.local_preview_actor.position = (0, y_map.get(entry_key, 0.12), 0)
            self.pedestal_ring.color = color.cyan if entry_key == 'mithrix' else color.red
            self.local_preview_parts = build_enemy_mesh(self.local_preview_actor, entry_key)
            if entry_key == 'mithrix' and isinstance(self.local_preview_parts, dict) and self.local_preview_parts.get('phase_ring'):
                self.local_preview_parts['phase_ring'].enabled = True

        elif category == 'stages':
            all_stages = {p['id']: p for p in STAGE_PALETTES}
            all_stages.update(SPECIAL_PALETTES)
            pal = all_stages.get(entry_key, STAGE_PALETTES[0])
            self._preview_base_scale = 0.24
            self.local_preview_actor.position = (0, 0.45, 0)
            self.pedestal_ring.color = pal['accent']

            root = Entity(parent=self.local_preview_actor)
            Entity(parent=root, model='sphere', scale=(9.5, 1.2, 9.5), y=-0.4, color=pal['ground'])
            Entity(parent=root, model='diamond', scale=(10.0, 0.25, 10.0), y=0.0, color=pal['accent'], unlit=True)
            st_type = 'arch' if entry_key in ('roost', 'moon') else ('monolith' if entry_key in ('acres', 'bazaar') else 'crystals')
            build_map_structure(root, st_type, pal, Vec3(0, 0, 0), 25)
            moon = Entity(parent=root, model='sphere', scale=2.2, position=(2.5, 6.5, -2.0), color=pal['moon'], unlit=True)
            Entity(parent=moon, model='diamond', scale=(2.2, 0.12, 2.2), color=pal['accent'], unlit=True)

        elif category == 'achievements':
            ach = ACHIEVEMENTS[entry_key]
            unlocked = entry_key in PROGRESS.unlocked_achievements
            self._preview_base_scale = 1.45
            self.local_preview_actor.position = (0, 1.25, 0)
            self.pedestal_ring.color = color.gold if unlocked else color.gray
            root = Entity(parent=self.local_preview_actor)
            if ach.get('unlocks_item') and ach['unlocks_item'] in ITEM_POOL:
                build_item_mesh(root, ach['unlocks_item'])
            else:
                Entity(parent=root, model='diamond', scale=(0.75, 1.15, 0.75), color=color.gold if unlocked else color.gray, unlit=True)
            ring = Entity(parent=root, model='diamond', scale=(1.45, 0.10, 1.45), color=color.gold if unlocked else color.gray, unlit=True)
            self.local_preview_parts = {'ring1': ring}

        self.local_preview_actor.scale = self._preview_base_scale * self.preview_zoom

    def refresh_remote_lobby_models(self):
        if not self.net.connected or self.menu_state != 'lobby':
            for slot in self.remote_pedestals:
                slot['pedestal'].enabled = False
            return

        peers = sorted(self.lobby_players.items(), key=lambda x: x[0])
        for idx, slot in enumerate(self.remote_pedestals):
            if idx < len(peers):
                pid, info = peers[idx]
                ckey = info.get('char_key', 'commando')
                if ckey not in SURVIVOR_CLASSES:
                    ckey = 'commando'
                is_rdy = info.get('ready', False)

                slot['pedestal'].enabled = True
                if slot['char_key'] != ckey:
                    clear_children(slot['actor'])
                    slot['parts'] = build_survivor_mesh(slot['actor'], ckey)
                    slot['char_key'] = ckey

                rdy_str = "ГОТОВ ✓" if is_rdy else "ВЫБИРАЕТ..."
                slot['label'].text = f"[{pid.upper()}] {SURVIVOR_CLASSES[ckey]['name']}\n[{rdy_str}]"
                slot['label'].color = color.lime if is_rdy else color.yellow
                slot['ring'].color = color.lime if is_rdy else rgb(80, 180, 255)
            else:
                slot['pedestal'].enabled = False

