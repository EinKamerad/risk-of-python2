from ursina import *
from config import rgb, clear_children, SURVIVOR_CLASSES
from models.survivors import build_survivor_mesh

class DioramaMixin:
    def setup_menu_diorama(self):
        self.diorama_root = Entity(position=(0, 0, 0))

        self.main_pedestal = Entity(parent=self.diorama_root, position=(1.15, 0, -1.0))
        Entity(parent=self.main_pedestal, model='cube', scale=(3.4, 0.35, 3.4), y=-0.18, color=rgb(34, 42, 58))
        Entity(parent=self.main_pedestal, model='cube', scale=(2.8, 0.14, 2.8), y=0.04, color=rgb(55, 70, 96))
        Entity(parent=self.main_pedestal, model='cube', scale=(2.9, 0.05, 2.9), y=0.10, color=color.cyan, unlit=True)

        self.local_preview_actor = Entity(parent=self.main_pedestal, position=(0, 0.12, 0), rotation_y=15)
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

    def rebuild_local_lobby_model(self):
        clear_children(self.local_preview_actor)
        self.local_preview_parts = build_survivor_mesh(self.local_preview_actor, self.selected_char)

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

