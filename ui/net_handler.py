from ursina import *
from config import rgb, is_valid, BOSS_TYPES
from entities import RemotePlayer, Enemy, Projectile
from world import Chest

class NetHandlerMixin:
    def process_network(self):
        for msg in self.net.poll_messages():
            mtype = msg.get('type')

            if mtype == 'welcome':
                self.net.my_id = msg.get('player_id', 'p2')
                self.net.room_code = msg.get('room_code', self.net.room_code)
                self.show_banner(f"ПОДКЛЮЧЕНО К КОМНАТЕ {self.net.room_code}!", color.lime, 3.0)
                self.broadcast_lobby_state()
                self.update_lobby_ui()

            elif mtype == 'client_joined':
                pid = msg.get('player_id')
                if pid and pid != self.net.my_id:
                    self.lobby_players.setdefault(pid, {'char_key': 'commando', 'ready': False})
                self.show_banner(f"ИГРОК [{str(pid).upper()}] ВОШЁЛ В ЛОББИ!", color.cyan, 3.0)
                self.broadcast_lobby_state()
                if self.net.mode == 'host' and self.lobby_countdown_active:
                    self.net.broadcast({
                        'type': 'lobby_timer_sync',
                        'active': self.lobby_countdown_active,
                        'countdown': round(self.lobby_countdown, 2)
                    })
                if self.running and self.net.mode == 'host':
                    self.net.broadcast({'type': 'lobby_start_run', 'stage': self.stage, 'seed': self.stage_seed})
                self.refresh_remote_lobby_models()
                self.update_lobby_ui()

            elif mtype == 'player_left':
                pid = msg.get('player_id')
                self.lobby_players.pop(pid, None)
                if pid in self.remote_players:
                    destroy(self.remote_players.pop(pid))
                self.show_banner(f"ИГРОК [{str(pid).upper()}] ПОКИНУЛ ИГРУ", color.orange, 2.5)
                self.evaluate_lobby_countdown()
                self.refresh_remote_lobby_models()
                self.update_lobby_ui()

            elif mtype == 'disconnected':
                self.lobby_players.clear()
                if self.running:
                    self.on_player_death()
                self.show_screen('main')
                self.show_banner("СОЕДИНЕНИЕ С ХОСТОМ ПОТЕРЯНО", color.red, 3.5)

            elif mtype == 'lobby_state':
                pid = msg.get('player_id')
                if not pid or pid == self.net.my_id:
                    continue
                is_new_peer = pid not in self.lobby_players
                self.lobby_players[pid] = {
                    'char_key': msg.get('char_key', 'commando'),
                    'ready': bool(msg.get('ready', False))
                }
                if is_new_peer:
                    self.broadcast_lobby_state()
                self.evaluate_lobby_countdown()
                self.refresh_remote_lobby_models()
                self.update_lobby_ui()

            elif mtype == 'lobby_timer_sync':
                if self.net.mode == 'client':
                    self.lobby_countdown_active = bool(msg.get('active', False))
                    self.lobby_countdown = float(msg.get('countdown', self.lobby_countdown))
                    self.update_lobby_ui()

            elif mtype == 'lobby_start_run':
                self.stage = msg.get('stage', 1)
                self.stage_seed = msg.get('seed', 1001)
                if not self.running:
                    self.start_run(self.selected_char, seed=self.stage_seed, from_network=True)

            elif mtype == 'player_state':
                pid = msg.get('player_id')
                if not pid or pid == self.net.my_id:
                    continue
                if not self.running:
                    continue
                if pid not in self.remote_players or not is_valid(self.remote_players[pid]):
                    self.remote_players[pid] = RemotePlayer(pid, msg.get('char_key', 'commando'))
                self.remote_players[pid].apply_net_state(msg)

            elif mtype == 'player_shoot':
                pid = msg.get('player_id')
                if not self.running or pid == self.net.my_id:
                    continue
                col_tag = msg.get('col', 'cyan')
                net_col_map = {
                    'cyan': color.cyan,
                    'commando': color.yellow,
                    'artificer': color.magenta,
                    'huntress': rgb(255, 80, 100),
                    'buzz': rgb(110, 255, 80),
                    'v1': rgb(255, 230, 50),
                    'sol': rgb(255, 110, 25),
                    'gwen': rgb(95, 225, 255),
                    'enforcer': rgb(110, 225, 255),
                    'scout': rgb(255, 215, 65),
                    'm4a1': rgb(95, 255, 135),
                    'medic': rgb(255, 75, 90),
                    'aigis': rgb(255, 235, 95),
                    'reimu': rgb(255, 65, 80),
                    'mindustry': rgb(255, 215, 65),
                }
                p_col = net_col_map.get(col_tag, color.cyan)
                Projectile(
                    pos=msg['pos'], direction=msg['dir'], speed=msg['speed'],
                    damage=0, scale_val=msg['scale'], proj_color=p_col,
                    is_player=True, aoe=msg.get('aoe', 0.0), pierce=msg.get('pierce', False),
                    bounces=msg.get('bounces', 0), homing=msg.get('homing', False), is_remote=True
                )

            elif mtype == 'stage_sync':
                new_stage = msg.get('stage', self.stage)
                new_seed = msg.get('seed', 1001)
                new_mode = msg.get('special_mode', None)
                if self.stage != new_stage or self.stage_seed != new_seed or self.special_mode != new_mode:
                    self.stage = new_stage
                    self.stage_seed = new_seed
                    if self.running:
                        self.generate_stage(seed=self.stage_seed, special_mode=new_mode)

            elif mtype == 'enemy_spawn':
                if self.running and self.net.mode == 'client':
                    nid = msg.get('net_id')
                    if not any(is_valid(e) and e.net_id == nid for e in self.enemies):
                        etype = msg['enemy_type']
                        pos = Vec3(*msg['pos'])
                        if etype in BOSS_TYPES or etype == 'mithrix':
                            self.spawn_boss(pos, boss_type=etype, net_id=nid, from_network=True)
                        else:
                            e = Enemy(pos, etype, msg.get('coeff', self.difficulty_coeff), net_id=nid)
                            self.enemies.append(e)

            elif mtype == 'enemies_sync':
                if self.running and self.net.mode == 'client':
                    by_id = {e.net_id: e for e in self.enemies if is_valid(e)}
                    for item in msg.get('enemies', []):
                        nid, ex, ey, ez, ehp, etype, ecoeff, is_al = item[:8]
                        own_id = item[8] if len(item) > 8 else None
                        if nid in by_id:
                            ent = by_id[nid]
                            t_pos = Vec3(ex, ey, ez)
                            if distance(Vec3(*ent.position), t_pos) > 6.0:
                                ent.position = t_pos
                            else:
                                ent.position = lerp(ent.position, t_pos, 0.45)
                            ent.hp = ehp
                            if not ent.hp_bar.is_empty():
                                ent.hp_bar.scale_x = clamp(ent.hp / max(1.0, ent.max_hp), 0.0, 1.0)
                            if is_al and not ent.is_ally:
                                ent.convert_to_ally(from_network=True, owner_id=own_id)
                            elif is_al and own_id:
                                ent.ally_owner_id = own_id
                        else:
                            pos = Vec3(ex, ey, ez)
                            if etype in BOSS_TYPES or etype == 'mithrix':
                                self.spawn_boss(pos, boss_type=etype, net_id=nid, from_network=True)
                            else:
                                new_e = Enemy(pos, etype, ecoeff, net_id=nid)
                                if is_al:
                                    new_e.convert_to_ally(from_network=True, owner_id=own_id)
                                self.enemies.append(new_e)

            elif mtype == 'enemy_convert':
                if self.running:
                    nid = msg.get('net_id')
                    own_id = msg.get('owner_id')
                    for e in list(self.enemies):
                        if is_valid(e) and e.net_id == nid:
                            e.convert_to_ally(from_network=True, owner_id=own_id)
                            break

            elif mtype == 'enemy_heal':
                if self.running:
                    nid = msg.get('net_id')
                    amt = float(msg.get('amount', 0.0))
                    uber_v = float(msg.get('uber', 0.0))
                    for e in list(self.enemies):
                        if is_valid(e) and e.net_id == nid:
                            e.heal_ally(amount=amt, uber_dur=uber_v, from_network=True)
                            break

            elif mtype == 'ally_buff':
                if self.running and is_valid(self.player):
                    tid = msg.get('target_id')
                    if tid in (self.net.my_id, 'all'):
                        heal_v = float(msg.get('heal', 0.0))
                        sh_v = float(msg.get('shield', 0.0))
                        uber_v = float(msg.get('uber', 0.0))
                        if heal_v > 0:
                            self.player.heal_amount(heal_v)
                        if sh_v > 0:
                            self.player.shield = min(float(self.player.max_hp), self.player.shield + sh_v)
                        if uber_v > 0:
                            self.player.uber_timer = max(self.player.uber_timer, uber_v)
                            self.show_banner('МЕДИК АКТИВИРОВАЛ НА ВАС УБЕР-ЗАРЯД (НЕУЯЗВИМОСТЬ)!', rgb(255, 75, 90), 3.0)

            elif mtype == 'enemy_damage':
                if self.running:
                    nid = msg.get('net_id')
                    amt = msg.get('amount', 0)
                    for e in list(self.enemies):
                        if is_valid(e) and e.net_id == nid:
                            e.take_damage(amt, from_network=True)
                            break

            elif mtype == 'chest_open':
                if self.running:
                    cid = msg.get('chest_id')
                    ikey = msg.get('item_key')
                    for obj in self.stage_entities:
                        if isinstance(obj, Chest) and obj.chest_id == cid:
                            obj.open_visual(ikey)
                            break

            elif mtype == 'item_drop':
                if self.running:
                    self.spawn_item_drop(Vec3(*msg['pos']), item_key=msg.get('item_key'), broadcast=False)

            elif mtype == 'newt_altar':
                if self.running:
                    self.blue_orb_spawned = True
                    self.show_banner('ПОЯВИЛАСЬ СИНЯЯ СФЕРА! У ТЕЛЕПОРТА ОТКРОЕТСЯ ПОРТАЛ НА БАЗАР', rgb(80, 210, 255), 3.5)

            elif mtype == 'tp_align':
                if self.running and self.teleporter and hasattr(self.teleporter, 'set_alignment'):
                    self.teleporter.set_alignment(msg.get('aligned_to_moon', False), from_network=True)

            elif mtype == 'tp_activate':
                if self.running and self.teleporter:
                    self.teleporter.activate_teleporter(boss_type=msg.get('boss_type'), from_network=True)

            elif mtype == 'moon_pillar_done':
                if self.running and self.special_mode == 'moon':
                    self.on_moon_pillar_charged(from_network=True)

            elif mtype == 'mithrix_start':
                if self.running and self.special_mode == 'moon':
                    self.start_mithrix_encounter(from_network=True)

