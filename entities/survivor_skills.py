from ursina import *
import math
import random
from config import ctx, rgb, is_valid, SURVIVOR_CLASSES
from entities.fx import (
    VisualFX, MeleeSlashFX, TearGasZone, IFGZone, DummyClone, MindustryTurret,
    LightningBeam, OrbitalStrikeFX, ArrowRainZone, HallowedMistZone
)
from entities.projectile import Projectile, apply_player_hit_effects


def distance_2d(a, b):
    """Переопределяет distance_2d на горизонтальную плоскость X-Z для 3D-мира"""
    return math.hypot(a[0] - b[0], a[2] - b[2])


class V1Coin(Entity):
    """Физическая монетка Marksman Revolver для рикошетов (+RICOSHOT / +ULTRARICOSHOT / +FISTFUL OF DOLLAR)"""
    def __init__(self, owner, start_pos, vel):
        super().__init__(
            model='diamond',
            position=Vec3(*start_pos),
            scale=(0.34, 0.34, 0.08),
            color=color.gold,
            unlit=True
        )
        Entity(parent=self, model='sphere', scale=1.45, color=rgb(255, 240, 120, 95), unlit=True)
        self.owner = owner
        self.vel = Vec3(*vel)
        self.lifetime = 4.2
        self.is_destroyed = False

    def trigger_ricoshot(self, base_dmg, is_rail=False, chain_count=1):
        if self.is_destroyed or self.is_empty():
            return
        self.is_destroyed = True
        game = ctx.game
        my_pos = Vec3(*self.position)
        VisualFX(my_pos, color.cyan if is_rail else color.gold, 2.4, 0.25)

        if not game or not is_valid(self.owner):
            destroy(self)
            return

        # 1. Сначала проверяем, есть ли в воздухе еще одна монетка для цепного рикошета!
        for other_coin in list(getattr(self.owner, 'v1_active_coins', [])):
            if other_coin is not self and is_valid(other_coin) and not other_coin.is_destroyed:
                c_pos = Vec3(*other_coin.position)
                LightningBeam(my_pos, c_pos, color.cyan if is_rail else color.gold, 0.26)
                other_coin.trigger_ricoshot(base_dmg * 1.35, is_rail=is_rail, chain_count=chain_count + 1)
                destroy(self)
                return

        # 2. Также проверяем, нет ли в воздухе ядер дробовика (Core Eject) для +CORE NUKE!
        for core_proj in list(getattr(self.owner, 'v1_active_cores', [])):
            if is_valid(core_proj):
                core_p = Vec3(*core_proj.position)
                LightningBeam(my_pos, core_p, color.red, 0.38)
                self.owner.v1_detonate_core(core_proj, is_nuke=True)
                destroy(self)
                return

        # 3. Бьём в уязвимую точку ближайшего врага!
        best_e = None
        best_d = 65.0
        for e in list(game.enemies):
            if is_valid(e) and not getattr(e, 'is_ally', False):
                d = distance(my_pos, Vec3(*e.position))
                if d < best_d:
                    best_d = d
                    best_e = e

        if best_e:
            weakpoint = Vec3(*best_e.position) + Vec3(0, best_e.hit_height * 1.15, 0)
            beam_col = color.cyan if is_rail else color.gold
            LightningBeam(my_pos, weakpoint, beam_col, 0.35 if is_rail else 0.24)
            VisualFX(weakpoint, beam_col, 4.5 if is_rail else 2.8, 0.3)
            apply_player_hit_effects(
                target=best_e,
                hit_pos=weakpoint,
                base_dmg=base_dmg * (1.25 + 0.35 * chain_count),
                hit_color=beam_col,
                aoe=5.5 if is_rail else 2.2,
                lifesteal=6.0,
                can_proc=True
            )
            if is_rail:
                self.owner.v1_add_style(f'+ ULTRARICOSHOT x{chain_count}', color.cyan, 150 * chain_count)
            else:
                self.owner.v1_add_style(f'+ RICOSHOT x{chain_count}', color.gold, 85 * chain_count)
        destroy(self)

    def update(self):
        game = ctx.game
        if not game or not game.running or self.is_destroyed or self.is_empty():
            return
        self.vel.y -= 18.5 * time.dt
        self.position += self.vel * time.dt
        self.rotation_x += 520 * time.dt
        self.rotation_y += 380 * time.dt
        self.lifetime -= time.dt
        floor_y = game.get_surface_height(self.x, self.z, self.y)
        if self.y <= floor_y + 0.15 or self.lifetime <= 0:
            self.is_destroyed = True
            destroy(self)


class V1Magnet(Entity):
    """Магнит Attractor Nailgun [3 - ПКМ]: стягивает врагов и гвозди, затем взрывается электрической шрапнелью"""
    def __init__(self, owner, pos, stuck_target=None):
        super().__init__(position=Vec3(*pos))
        self.owner = owner
        self.stuck_target = stuck_target
        self.duration = 4.5
        self.pulse_timer = 0.0
        self.is_destroyed = False

        Entity(parent=self, model='cube', scale=(0.25, 0.85, 0.25), y=0.4, color=rgb(60, 75, 95))
        self.coil = Entity(parent=self, model='diamond', scale=(0.65, 0.35, 0.65), y=0.85, color=color.cyan, unlit=True)
        self.ring = Entity(parent=self, model='sphere', scale=(9.0, 0.08, 9.0), y=0.1, color=rgb(60, 200, 255, 55), unlit=True)

    def update(self):
        game = ctx.game
        if not game or not game.running or self.is_destroyed or self.is_empty():
            return
        if is_valid(self.stuck_target):
            self.position = Vec3(*self.stuck_target.position) + Vec3(0, self.stuck_target.hit_height * 0.6, 0)

        self.coil.rotation_y += 220 * time.dt
        self.duration -= time.dt
        my_pos = Vec3(*self.position)

        # Притягиваем обычных врагов к магниту
        for e in list(game.enemies):
            if is_valid(e) and not getattr(e, 'is_ally', False) and not e.is_boss:
                e_pos = Vec3(*e.position)
                d = distance(e_pos, my_pos)
                if 1.2 < d <= 10.5:
                    pull = (my_pos - e_pos).normalized() * 7.5 * time.dt
                    e.x += pull.x
                    e.z += pull.z

        if self.duration <= 0:
            self.is_destroyed = True
            VisualFX(my_pos + Vec3(0, 0.8, 0), color.cyan, 6.5, 0.35)
            if is_valid(self.owner):
                for e in list(game.enemies):
                    if is_valid(e) and not getattr(e, 'is_ally', False) and distance(Vec3(*e.position), my_pos) <= 6.5:
                        apply_player_hit_effects(e, my_pos, self.owner.base_damage * 2.4, color.cyan, aoe=0, lifesteal=2.0)
                self.owner.v1_add_style('+ CONDUCTOR', color.cyan, 80)
            destroy(self)


class V1ScrewdriverDrill(Entity):
    """Бур Screwdriver Railcannon [4 - ПКМ]: сверлит цель, нанося урон и разбрызгивая исцеляющую кровь"""
    def __init__(self, owner, target):
        super().__init__(position=Vec3(*target.position) + Vec3(0, target.hit_height, 0))
        self.owner = owner
        self.target = target
        self.duration = 4.0
        self.tick_timer = 0.0
        self.drill_mesh = Entity(parent=self, model='diamond', scale=(0.45, 0.45, 1.35), color=color.lime, unlit=True)

    def update(self):
        game = ctx.game
        if not game or not game.running or self.is_empty() or not is_valid(self.target) or not is_valid(self.owner):
            if not self.is_empty():
                destroy(self)
            return
        self.position = Vec3(*self.target.position) + Vec3(0, self.target.hit_height, 0)
        self.drill_mesh.rotation_z += 720 * time.dt
        self.duration -= time.dt
        self.tick_timer -= time.dt
        if self.tick_timer <= 0:
            self.tick_timer = 0.25
            apply_player_hit_effects(
                self.target, Vec3(*self.position),
                self.owner.base_damage * 0.75, color.lime, aoe=1.5, lifesteal=4.5
            )
            VisualFX(Vec3(*self.position), color.red, 2.2, 0.2)
        if self.duration <= 0:
            destroy(self)


class SurvivorSkillsMixin:
    # ==========================================================
    # УНИКАЛЬНАЯ FPS-СИСТЕМА V1 (ULTRAKILL)
    # ==========================================================
    def init_v1_arsenal(self):
        """Инициализирует камеру от 1-го лица, 3D-модели 5 оружий, 3 рук и Style Meter для V1"""
        self.parts['root'].enabled = False
        self.cam_pivot.y = 1.72
        camera.parent = self.cam_pivot
        camera.position = (0, 0, 0)
        camera.rotation = (0, 0, 0)

        self.v1_weapon = 1
        self.v1_weapon_names = {
            1: 'MARKSMAN REVOLVER',
            2: 'CORE EJECT SHOTGUN',
            3: 'ATTRACTOR NAILGUN',
            4: 'ELECTRIC RAILCANNON',
            5: 'FREEZEFRAME ROCKET'
        }
        self.v1_weapon_cols = {
            1: color.gold,
            2: color.orange,
            3: color.cyan,
            4: rgb(80, 235, 255),
            5: rgb(255, 75, 95)
        }
        self.v1_coins = 4.0
        self.v1_rail_charge = 100.0
        self.v1_rockets_frozen = False
        self.v1_freeze_fuel = 100.0
        self.v1_shotgun_boost_window = 0.0

        self.v1_active_coins = []
        self.v1_active_cores = []
        self.v1_magnets = []

        self.v1_active_arm = 'feedbacker'  # 'feedbacker' (Blue) или 'knuckleblaster' (Red)
        self.v1_arm_cd = 0.0
        self.v1_whiplash_cd = 0.0
        self.v1_whiplash_target_ent = None
        self.v1_whiplash_point = None
        self.v1_whiplash_mode = None
        self.v1_whiplash_timer = 0.0

        self.v1_stamina = 3.0
        self.v1_sliding = False
        self.v1_slamming = False
        self.v1_slam_air_time = 0.0

        self.v1_style_points = 0.0
        self.v1_style_dmg_mult = 1.0
        self.v1_style_log = []

        self._build_v1_fp_viewmodel()

    def _build_v1_fp_viewmodel(self):
        """Создаёт детальные 3D-модели оружия и левой руки от первого лица"""
        if hasattr(self, 'fp_root') and self.fp_root and not self.fp_root.is_empty():
            destroy(self.fp_root)

        self.fp_root = Entity(parent=camera, position=(0, 0, 0))
        self.fp_weapon_holder = Entity(parent=self.fp_root, position=(0.36, -0.27, 0.62))
        self.fp_weapons = {}

        # [1] MARKSMAN REVOLVER
        w1 = Entity(parent=self.fp_weapon_holder, enabled=True)
        Entity(parent=w1, model='cube', scale=(0.08, 0.14, 0.48), color=rgb(38, 45, 62))
        Entity(parent=w1, model='cube', scale=(0.09, 0.05, 0.44), y=0.06, color=rgb(55, 130, 245))
        Entity(parent=w1, model='sphere', scale=(0.11, 0.11, 0.14), position=(0, 0.01, -0.08), color=color.gold, unlit=True)
        Entity(parent=w1, model='cube', scale=(0.04, 0.04, 0.50), y=0.09, color=color.gold, unlit=True)
        self.fp_weapons[1] = w1

        # [2] CORE EJECT SHOTGUN
        w2 = Entity(parent=self.fp_weapon_holder, enabled=False)
        Entity(parent=w2, model='cube', scale=(0.15, 0.14, 0.56), color=rgb(45, 50, 62))
        for sx in (-0.04, 0.04):
            Entity(parent=w2, model='cube', scale=(0.05, 0.06, 0.62), position=(sx, 0.04, 0.04), color=rgb(70, 78, 92))
        Entity(parent=w2, model='cube', scale=(0.17, 0.08, 0.24), position=(0, -0.05, 0.08), color=color.orange, unlit=True)
        self.fp_weapons[2] = w2

        # [3] ATTRACTOR NAILGUN
        w3 = Entity(parent=self.fp_weapon_holder, enabled=False)
        Entity(parent=w3, model='cube', scale=(0.18, 0.16, 0.46), color=rgb(40, 48, 64))
        barrel_hub = Entity(parent=w3, position=(0, 0.02, 0.28))
        for bx, by in ((-0.04, -0.04), (0.04, -0.04), (-0.04, 0.04), (0.04, 0.04)):
            Entity(parent=barrel_hub, model='cube', scale=(0.03, 0.03, 0.36), position=(bx, by, 0), color=rgb(140, 155, 175))
        Entity(parent=w3, model='diamond', scale=(0.20, 0.12, 0.20), position=(0, 0.09, 0.05), color=color.cyan, unlit=True)
        self.fp_nail_rotator = barrel_hub
        self.fp_weapons[3] = w3

        # [4] ELECTRIC RAILCANNON
        w4 = Entity(parent=self.fp_weapon_holder, enabled=False)
        Entity(parent=w4, model='cube', scale=(0.14, 0.16, 0.68), color=rgb(32, 42, 65))
        for rz in (-0.12, 0.06, 0.24):
            Entity(parent=w4, model='diamond', scale=(0.22, 0.22, 0.06), position=(0, 0.02, rz), color=color.cyan, unlit=True)
        Entity(parent=w4, model='cube', scale=(0.06, 0.06, 0.74), y=0.04, color=color.white, unlit=True)
        self.fp_weapons[4] = w4

        # [5] FREEZEFRAME ROCKET LAUNCHER
        w5 = Entity(parent=self.fp_weapon_holder, enabled=False)
        Entity(parent=w5, model='cube', scale=(0.18, 0.18, 0.62), color=rgb(145, 35, 45))
        Entity(parent=w5, model='diamond', scale=(0.22, 0.22, 0.16), z=0.30, color=rgb(55, 62, 75))
        Entity(parent=w5, model='sphere', scale=(0.12, 0.12, 0.24), position=(-0.10, 0.04, 0.02), color=color.cyan, unlit=True)
        self.fp_weapons[5] = w5

        # ЛЕВАЯ МЕХАНИЧЕСКАЯ РУКА (Feedbacker / Knuckleblaster / Whiplash)
        self.fp_left_arm = Entity(parent=self.fp_root, position=(-0.38, -0.34, 0.35), rotation=(-12, 18, 0))
        self.fp_arm_forearm = Entity(parent=self.fp_left_arm, model='cube', scale=(0.11, 0.11, 0.46), color=rgb(45, 115, 235))
        self.fp_arm_fist = Entity(parent=self.fp_left_arm, model='diamond', scale=(0.17, 0.17, 0.22), z=0.26, color=color.cyan, unlit=True)

    def v1_add_style(self, bonus_text, col=color.yellow, points=60.0):
        self.v1_style_points = min(1000.0, self.v1_style_points + points)
        self.v1_style_log.insert(0, [bonus_text, col, 3.2])
        if len(self.v1_style_log) > 6:
            self.v1_style_log.pop()

    def v1_get_style_rank_info(self):
        pts = self.v1_style_points
        if pts >= 920:
            return 'ULTRAKILL', rgb(255, 215, 40), 1.50
        elif pts >= 780:
            return 'SSSHITSTORM', rgb(255, 70, 90), 1.40
        elif pts >= 640:
            return 'SSADISTIC', rgb(255, 95, 50), 1.32
        elif pts >= 500:
            return 'SUPREME', rgb(245, 55, 55), 1.25
        elif pts >= 360:
            return 'ANARCHIC', color.orange, 1.18
        elif pts >= 230:
            return 'BRUTAL', color.yellow, 1.12
        elif pts >= 110:
            return 'CHAOTIC', color.lime, 1.06
        elif pts > 5:
            return 'DESTRUCTIVE', color.cyan, 1.02
        return 'NO STYLE', color.gray, 1.0

    def v1_switch_weapon(self, slot):
        if slot not in (1, 2, 3, 4, 5):
            return
        self.v1_weapon = slot
        for k, w_ent in getattr(self, 'fp_weapons', {}).items():
            if w_ent and not w_ent.is_empty():
                w_ent.enabled = (k == slot)
        if hasattr(self, 'fp_weapon_holder') and not self.fp_weapon_holder.is_empty():
            self.fp_weapon_holder.y = -0.36
            self.fp_weapon_holder.animate_y(-0.27, duration=0.10)

    def handle_combat_input(self, key):
        if self.char_key != 'v1' or not mouse.locked:
            return
        if key in ('1', '2', '3', '4', '5'):
            self.v1_switch_weapon(int(key))
        elif key == 'scroll up':
            nxt = 1 if self.v1_weapon >= 5 else self.v1_weapon + 1
            self.v1_switch_weapon(nxt)
        elif key == 'scroll down':
            prv = 5 if self.v1_weapon <= 1 else self.v1_weapon - 1
            self.v1_switch_weapon(prv)
        elif key == 'f':
            if self.v1_active_arm == 'feedbacker':
                self.v1_use_feedbacker()
            else:
                self.v1_use_knuckleblaster()
        elif key == 'g':
            self.v1_use_knuckleblaster()
        elif key == 'v':
            self.v1_active_arm = 'knuckleblaster' if self.v1_active_arm == 'feedbacker' else 'feedbacker'
            arm_name = 'KNUCKLEBLASTER [RED]' if self.v1_active_arm == 'knuckleblaster' else 'FEEDBACKER [BLUE]'
            arm_col = color.red if self.v1_active_arm == 'knuckleblaster' else color.cyan
            if hasattr(self, 'fp_arm_forearm') and not self.fp_arm_forearm.is_empty():
                self.fp_arm_forearm.color = rgb(210, 40, 45) if self.v1_active_arm == 'knuckleblaster' else rgb(45, 115, 235)
                self.fp_arm_fist.color = arm_col
            ctx.game.show_banner(f'ACTIVE ARM: {arm_name}', arm_col, 1.2)

    def v1_detonate_core(self, core_proj, is_nuke=False):
        if not is_valid(core_proj):
            return
        c_pos = Vec3(*core_proj.position)
        core_proj.safe_destroy()
        rad = 14.0 if is_nuke else 7.5
        dmg_mult = 5.2 if is_nuke else 2.8
        col = color.red if is_nuke else color.orange
        VisualFX(c_pos, col, rad * 1.35, 0.45)
        for e in list(ctx.game.enemies):
            if is_valid(e) and not getattr(e, 'is_ally', False):
                if distance(Vec3(*e.position), c_pos) <= rad:
                    apply_player_hit_effects(e, c_pos, self.base_damage * dmg_mult, col, aoe=0, lifesteal=5.0)
        if is_nuke:
            self.v1_add_style('+ CORE NUKE!', color.red, 175)

    def _v1_animate_weapon_recoil(self, kick_z=-0.14, pitch=-14):
        if hasattr(self, 'fp_weapon_holder') and not self.fp_weapon_holder.is_empty():
            self.fp_weapon_holder.z = 0.62 + kick_z
            self.fp_weapon_holder.rotation_x = pitch
            self.fp_weapon_holder.animate_z(0.62, duration=0.12)
            self.fp_weapon_holder.animate_rotation_x(0, duration=0.14)

    def _v1_animate_left_punch(self, arm_col=color.cyan):
        if hasattr(self, 'fp_left_arm') and not self.fp_left_arm.is_empty():
            self.fp_arm_fist.color = arm_col
            self.fp_left_arm.position = (-0.12, -0.18, 0.85)
            self.fp_left_arm.animate_position((-0.38, -0.34, 0.35), duration=0.18)

    def _v1_check_hitscan_coin_or_core(self, eye_pos, aim_dir, base_dmg, is_rail=False):
        """Проверяет, попал ли луч револьвера или рельсотрона в подброшенную монетку или ядро дробовика"""
        self.v1_active_coins = [c for c in self.v1_active_coins if is_valid(c) and not c.is_destroyed]
        for coin in self.v1_active_coins:
            to_c = Vec3(*coin.position) - eye_pos
            if to_c.length() <= 45.0 and aim_dir.dot(to_c.normalized()) >= 0.92:
                LightningBeam(eye_pos + camera.right * 0.25, Vec3(*coin.position), color.cyan if is_rail else color.gold, 0.22)
                coin.trigger_ricoshot(base_dmg, is_rail=is_rail, chain_count=1)
                return True

        self.v1_active_cores = [c for c in self.v1_active_cores if is_valid(c)]
        for core in self.v1_active_cores:
            to_core = Vec3(*core.position) - eye_pos
            if to_core.length() <= 45.0 and aim_dir.dot(to_core.normalized()) >= 0.90:
                LightningBeam(eye_pos + camera.right * 0.25, Vec3(*core.position), color.red, 0.30)
                self.v1_detonate_core(core, is_nuke=True)
                return True
        return False

    def v1_use_primary(self):
        """[ЛКМ] Основная атака текущего выбранного оружия V1 (1-5)"""
        eye_pos = Vec3(*self.position) + Vec3(0, self.cam_pivot.y, 0)
        aim_dir = camera.forward
        muzzle_pos = eye_pos + aim_dir * 0.85 + camera.right * 0.28 - camera.up * 0.15
        atk_spd = self.fire_rate / self.base_fire_rate

        # [1] MARKSMAN REVOLVER
        if self.v1_weapon == 1:
            self.m1_cd = 0.24 / atk_spd
            self._v1_animate_weapon_recoil(-0.12, -16)
            if self._v1_check_hitscan_coin_or_core(eye_pos, aim_dir, self.base_damage * 2.2, is_rail=False):
                return
            Projectile(
                pos=muzzle_pos, direction=aim_dir, speed=115.0,
                damage=self.base_damage * 1.25, scale_val=0.22,
                proj_color=color.gold, is_player=True, lifesteal=2.0
            )
            self._broadcast_shot(muzzle_pos, aim_dir, 115.0, self.base_damage * 1.25, 0.22, 'v1')

        # [2] CORE EJECT SHOTGUN
        elif self.v1_weapon == 2:
            self.m1_cd = 0.62 / atk_spd
            self.v1_shotgun_boost_window = 0.26
            self._v1_animate_weapon_recoil(-0.22, -24)
            VisualFX(muzzle_pos, color.orange, 1.4, 0.14)
            for _ in range(8):
                spread = Vec3(random.uniform(-0.06, 0.06), random.uniform(-0.05, 0.05), random.uniform(-0.06, 0.06))
                d = (aim_dir + spread).normalized()
                Projectile(
                    pos=muzzle_pos, direction=d, speed=72.0,
                    damage=self.base_damage * 0.42, scale_val=0.18,
                    proj_color=color.orange, is_player=True, max_lifetime=0.48, lifesteal=0.8
                )

        # [3] ATTRACTOR NAILGUN
        elif self.v1_weapon == 3:
            self.m1_cd = 0.075 / atk_spd
            self._v1_animate_weapon_recoil(-0.05, -4)
            if hasattr(self, 'fp_nail_rotator') and not self.fp_nail_rotator.is_empty():
                self.fp_nail_rotator.rotation_z += 55
            spread = Vec3(random.uniform(-0.035, 0.035), random.uniform(-0.035, 0.035), random.uniform(-0.035, 0.035))
            nail = Projectile(
                pos=muzzle_pos, direction=(aim_dir + spread).normalized(), speed=68.0,
                damage=self.base_damage * 0.48, scale_val=0.15,
                proj_color=color.cyan, is_player=True, lifesteal=0.5
            )
            nail.is_v1_nail = True

        # [4] ELECTRIC RAILCANNON
        elif self.v1_weapon == 4:
            if self.v1_rail_charge < 100.0:
                self.m1_cd = 0.2
                ctx.game.show_banner(f'RAILCANNON RECHARGING ({int(self.v1_rail_charge)}%)', color.cyan, 1.0)
                return
            self.v1_rail_charge = 0.0
            self.m1_cd = 0.45
            self._v1_animate_weapon_recoil(-0.28, -28)

            if self._v1_check_hitscan_coin_or_core(eye_pos, aim_dir, self.base_damage * 4.5, is_rail=True):
                return

            end_p = eye_pos + aim_dir * 65.0
            LightningBeam(muzzle_pos, end_p, color.cyan, 0.42)
            Projectile(
                pos=muzzle_pos, direction=aim_dir, speed=140.0,
                damage=self.base_damage * 4.2, scale_val=0.65,
                proj_color=color.cyan, is_player=True, aoe=4.5, pierce=True, lifesteal=12.0
            )
            self.v1_add_style('+ RAILCANNON SURGE', color.cyan, 95)

        # [5] FREEZEFRAME ROCKET LAUNCHER
        elif self.v1_weapon == 5:
            self.m1_cd = 0.52 / atk_spd
            self._v1_animate_weapon_recoil(-0.20, -18)
            r_proj = Projectile(
                pos=muzzle_pos, direction=aim_dir, speed=56.0,
                damage=self.base_damage * 2.35, scale_val=0.38,
                proj_color=rgb(255, 75, 95), is_player=True, aoe=4.8, lifesteal=3.5
            )
            r_proj.is_v1_rocket = True

    def v1_use_secondary(self):
        """[ПКМ] Альтернативная атака текущего оружия V1 (1-5)"""
        eye_pos = Vec3(*self.position) + Vec3(0, self.cam_pivot.y, 0)
        aim_dir = camera.forward
        muzzle_pos = eye_pos + aim_dir * 0.9 + camera.right * 0.22

        # [1] MARKSMAN: Бросок монетки
        if self.v1_weapon == 1:
            if self.v1_coins < 1.0:
                ctx.game.show_banner('НЕТ МОНЕТ (ПЕРЕЗАРЯДКА)', color.gold, 0.9)
                return
            self.v1_coins -= 1.0
            self.m2_cd = 0.16
            self._v1_animate_left_punch(color.gold)
            self_vel = Vec3(self.forward.x, 0, self.forward.z) * (self.move_speed * 0.45 if self.is_moving else 0.0)
            coin_vel = aim_dir * 13.5 + Vec3(0, 10.5, 0) + self_vel
            coin = V1Coin(self, eye_pos + aim_dir * 0.8 + Vec3(0, 0.1, 0), coin_vel)
            self.v1_active_coins.append(coin)
            ctx.game.stage_entities.append(coin)

        # [2] CORE EJECT: Выброс взрывного ядра по дуге
        elif self.v1_weapon == 2:
            self.m2_cd = 1.2
            self._v1_animate_weapon_recoil(-0.24, -22)
            core = Projectile(
                pos=muzzle_pos, direction=(aim_dir + Vec3(0, 0.28, 0)).normalized(),
                speed=34.0, damage=self.base_damage * 2.8, scale_val=0.52,
                proj_color=color.orange, is_player=True, aoe=6.5, lifesteal=4.0
            )
            core.is_v1_core = True
            core.gravity_arc = 1.25
            self.v1_active_cores.append(core)

        # [3] ATTRACTOR MAGNET: Выстрел притягивающим магнитом
        elif self.v1_weapon == 3:
            self.m2_cd = 2.0
            self._v1_animate_weapon_recoil(-0.15, -12)
            self.v1_magnets = [m for m in self.v1_magnets if is_valid(m)]
            if len(self.v1_magnets) >= 3:
                oldest = self.v1_magnets.pop(0)
                oldest.is_destroyed = True
                destroy(oldest)

            anchor = self._find_grapple_anchor(eye_pos, aim_dir, max_dist=32.0)
            hit_enemy = None
            for e in ctx.game.enemies:
                if is_valid(e) and not getattr(e, 'is_ally', False):
                    if distance(anchor, Vec3(*e.position) + Vec3(0, e.hit_height, 0)) <= e.hit_radius + 1.2:
                        hit_enemy = e
                        break
            mag = V1Magnet(self, anchor, stuck_target=hit_enemy)
            self.v1_magnets.append(mag)
            ctx.game.stage_entities.append(mag)
            LightningBeam(muzzle_pos, anchor, color.cyan, 0.14)

        # [4] SCREWDRIVER RAILCANNON: Кровавый бур
        elif self.v1_weapon == 4:
            if self.v1_rail_charge < 100.0:
                ctx.game.show_banner(f'RAILCANNON RECHARGING ({int(self.v1_rail_charge)}%)', color.lime, 1.0)
                return
            self.v1_rail_charge = 0.0
            self.m2_cd = 0.5
            self._v1_animate_weapon_recoil(-0.25, -24)
            best_e = None
            best_dot = 0.88
            for e in ctx.game.enemies:
                if is_valid(e) and not getattr(e, 'is_ally', False):
                    to_e = (Vec3(*e.position) + Vec3(0, e.hit_height, 0)) - eye_pos
                    if to_e.length() <= 45.0 and aim_dir.dot(to_e.normalized()) > best_dot:
                        best_dot = aim_dir.dot(to_e.normalized())
                        best_e = e
            if best_e:
                LightningBeam(muzzle_pos, Vec3(*best_e.position) + Vec3(0, best_e.hit_height, 0), color.lime, 0.35)
                drill = V1ScrewdriverDrill(self, best_e)
                ctx.game.stage_entities.append(drill)
                self.v1_add_style('+ SCREWDRIVER', color.lime, 90)
            else:
                Projectile(
                    pos=muzzle_pos, direction=aim_dir, speed=95.0,
                    damage=self.base_damage * 3.2, scale_val=0.55,
                    proj_color=color.lime, is_player=True, aoe=4.0, lifesteal=10.0
                )

        # [5] FREEZEFRAME: Заморозка / Разморозка всех ракет в воздухе!
        elif self.v1_weapon == 5:
            self.m2_cd = 0.25
            self.v1_rockets_frozen = not self.v1_rockets_frozen
            if self.v1_rockets_frozen:
                VisualFX(muzzle_pos, color.cyan, 1.8, 0.2)
                ctx.game.show_banner('FREEZEFRAME ACTIVE :: РАКЕТЫ ЗАМОРОЖЕНЫ В ВОЗДУХЕ!', color.cyan, 1.6)
            else:
                VisualFX(muzzle_pos, color.orange, 2.2, 0.2)
                self.v1_add_style('+ FREEZEFRAME VOLLEY', color.cyan, 75)
                ctx.game.show_banner('FREEZEFRAME RELEASED :: ЗАЛП ПОШЁЛ!', color.orange, 1.4)

    def v1_use_feedbacker(self):
        """[F] Синяя рука Feedbacker: +PROJECTILE BOOST, +FISTFUL OF DOLLAR и +PARRY вражеских снарядов/атак"""
        if self.v1_arm_cd > 0:
            return
        self.v1_arm_cd = 0.36
        self._v1_animate_left_punch(color.cyan)
        eye_pos = Vec3(*self.position) + Vec3(0, self.cam_pivot.y, 0)
        aim_dir = camera.forward
        game = ctx.game

        # 1. PROJECTILE BOOST (если нажали [F] сразу после выстрела из дробовика [2])
        if self.v1_shotgun_boost_window > 0:
            self.v1_shotgun_boost_window = 0.0
            VisualFX(eye_pos + aim_dir * 1.2, color.gold, 2.2, 0.2)
            Projectile(
                pos=eye_pos + aim_dir * 1.0, direction=aim_dir, speed=96.0,
                damage=self.base_damage * 2.85, scale_val=0.46,
                proj_color=color.gold, is_player=True, aoe=5.2, lifesteal=4.5
            )
            self.v1_add_style('+ PROJECTILE BOOST', color.gold, 95)
            return

        # 2. FISTFUL OF DOLLAR (удар кулаком по подброшенной монетке)
        for coin in list(self.v1_active_coins):
            if is_valid(coin) and not coin.is_destroyed and distance(eye_pos, Vec3(*coin.position)) <= 5.5:
                coin.trigger_ricoshot(self.base_damage * 2.6, is_rail=False, chain_count=2)
                self.v1_add_style('+ FISTFUL OF DOLLAR', color.gold, 110)
                return

        # 3. ПАРИРОВАНИЕ ВРАЖЕСКИХ СНАРЯДОВ (+ PARRY!)
        for ent in list(scene.entities):
            if isinstance(ent, Projectile) and not ent.is_player and not ent.is_destroyed:
                p_pos = Vec3(*ent.position)
                if distance(eye_pos, p_pos) <= 6.2:
                    ent.safe_destroy()
                    VisualFX(p_pos, color.yellow, 4.5, 0.3)
                    Projectile(
                        pos=eye_pos + aim_dir * 1.1, direction=aim_dir, speed=110.0,
                        damage=self.base_damage * 3.8, scale_val=0.58,
                        proj_color=color.yellow, is_player=True, aoe=6.5, lifesteal=15.0
                    )
                    self.heal_amount(self.max_hp)
                    self.v1_stamina = 3.0
                    self.v1_add_style('+ PARRY', color.yellow, 130)
                    game.show_banner('+ PARRY! (ПОЛНОЕ ИСЦЕЛЕНИЕ & СТАМИНА)', color.yellow, 1.5)
                    return

        # 4. Ближний удар кулаком + парирование замаха врага вблизи
        parried_melee = False
        for e in list(game.enemies):
            if is_valid(e) and not getattr(e, 'is_ally', False):
                e_pos = Vec3(*e.position)
                if distance(Vec3(*self.position), e_pos) <= 5.5 + e.hit_radius:
                    if getattr(e, 'attack_timer', 1.0) <= 0.65:
                        parried_melee = True
                        e.attack_timer = 1.8
                        if not e.is_boss:
                            e.stun_timer = 2.0
                        apply_player_hit_effects(e, e_pos + Vec3(0, e.hit_height, 0), self.base_damage * 3.2, color.yellow, aoe=4.5, lifesteal=20.0)
                    else:
                        apply_player_hit_effects(e, e_pos + Vec3(0, e.hit_height, 0), self.base_damage * 1.4, color.cyan, aoe=1.5, lifesteal=5.0)
        if parried_melee:
            self.heal_amount(self.max_hp * 0.5)
            self.v1_stamina = 3.0
            self.v1_add_style('+ PARRY', color.yellow, 125)

    def v1_use_knuckleblaster(self):
        """[G] Красная рука Knuckleblaster: тяжёлый пробивной удар + дробовой взрыв с отбрасыванием"""
        if self.v1_arm_cd > 0:
            return
        self.v1_arm_cd = 0.75
        self._v1_animate_left_punch(color.red)
        my_pos = Vec3(*self.position)
        blast_pos = my_pos + Vec3(0, 1.4, 0) + camera.forward * 2.2
        VisualFX(blast_pos, color.red, 5.8, 0.32)
        hits = self.perform_melee_attack(
            reach=6.5, cleave_radius=4.8, damage_mult=2.5,
            slash_col=color.red, lifesteal=8.0, stun_dur=1.2, knockback=6.5, aoe=4.0
        )
        if hits > 0:
            self.v1_add_style('+ KNUCKLEBLAST', color.red, 75)

    def v1_use_whiplash(self):
        """[R] Зелёная рука Whiplash (Гарпун-лассо): лёгких врагов тянет к V1, к тяжёлым/боссам/стенам тянет самого V1"""
        if self.v1_whiplash_cd > 0:
            return
        self.v1_whiplash_cd = 1.4
        self._v1_animate_left_punch(color.lime)
        eye_pos = Vec3(*self.position) + Vec3(0, self.cam_pivot.y, 0)
        aim_dir = camera.forward
        game = ctx.game

        best_e = None
        best_dot = 0.90
        for e in list(game.enemies):
            if is_valid(e) and not getattr(e, 'is_ally', False):
                e_center = Vec3(*e.position) + Vec3(0, e.hit_height, 0)
                to_e = e_center - eye_pos
                if to_e.length() <= 46.0:
                    dot = aim_dir.dot(to_e.normalized())
                    if dot > best_dot:
                        best_dot = dot
                        best_e = e

        if best_e is not None:
            e_center = Vec3(*best_e.position) + Vec3(0, best_e.hit_height, 0)
            LightningBeam(eye_pos - camera.right * 0.25, e_center, color.lime, 0.22)
            VisualFX(e_center, color.lime, 2.5, 0.25)
            light_types = ('lemurian', 'wisp', 'beetle', 'jellyfish', 'imp')
            if best_e.enemy_type in light_types and not best_e.is_boss:
                self.v1_whiplash_target_ent = best_e
                self.v1_whiplash_mode = 'pull_enemy'
                self.v1_whiplash_timer = 0.45
                self.v1_add_style('+ GET OVER HERE!', color.lime, 60)
            else:
                self.v1_whiplash_target_ent = best_e
                self.v1_whiplash_mode = 'pull_self_to_enemy'
                self.v1_whiplash_timer = 0.65
                self.v1_add_style('+ WHIPLASH', color.lime, 45)
        else:
            anchor = self._find_grapple_anchor(eye_pos, aim_dir, max_dist=44.0)
            LightningBeam(eye_pos - camera.right * 0.25, anchor, color.lime, 0.18)
            VisualFX(anchor, color.lime, 2.0, 0.25)
            self.v1_whiplash_point = anchor
            self.v1_whiplash_mode = 'pull_self_to_point'
            self.v1_whiplash_timer = 0.60

    def v1_update_mechanics(self, dt_step):
        """Постоянное обновление механик V1 в каждом кадре (Стамина, Монетки, Рельсотрон, Лассо, Подкат/Slam, Стиль)"""
        game = ctx.game
        self.v1_arm_cd = max(0.0, self.v1_arm_cd - dt_step)
        self.v1_whiplash_cd = max(0.0, self.v1_whiplash_cd - dt_step)
        self.v1_shotgun_boost_window = max(0.0, self.v1_shotgun_boost_window - dt_step)

        # Регенерация 3 зарядов выносливости, 4 монеток и заряда рельсотрона
        if not self.v1_sliding:
            self.v1_stamina = min(3.0, self.v1_stamina + 0.85 * dt_step)
        self.v1_coins = min(4.0, self.v1_coins + 0.30 * dt_step)
        self.v1_rail_charge = min(100.0, self.v1_rail_charge + 14.0 * dt_step)

        # Топливо заморозки ракет Freezeframe
        if self.v1_rockets_frozen:
            self.v1_freeze_fuel -= 22.0 * dt_step
            if self.v1_freeze_fuel <= 0:
                self.v1_freeze_fuel = 0.0
                self.v1_rockets_frozen = False
        else:
            self.v1_freeze_fuel = min(100.0, self.v1_freeze_fuel + 25.0 * dt_step)

        # Обновление Измерителя крутости (Style Meter)
        if self.v1_style_points > 0:
            self.v1_style_points = max(0.0, self.v1_style_points - 18.0 * dt_step)
        _, _, self.v1_style_dmg_mult = self.v1_get_style_rank_info()
        for entry in list(self.v1_style_log):
            entry[2] -= dt_step
            if entry[2] <= 0:
                self.v1_style_log.remove(entry)

        # Покачивание оружия от 1-го лица при движении
        if hasattr(self, 'fp_weapon_holder') and not self.fp_weapon_holder.is_empty():
            if self.is_moving and self.grounded:
                bob = math.sin(time.time() * 14.0) * 0.018
                self.fp_weapon_holder.x = 0.36 + math.cos(time.time() * 7.0) * 0.015
                self.fp_weapon_holder.y = lerp(self.fp_weapon_holder.y, -0.27 + bob, dt_step * 12.0)
            else:
                self.fp_weapon_holder.x = lerp(self.fp_weapon_holder.x, 0.36, dt_step * 10.0)
                self.fp_weapon_holder.y = lerp(self.fp_weapon_holder.y, -0.27, dt_step * 10.0)

        # Обработка активного гарпуна Whiplash
        if self.v1_whiplash_timer > 0:
            self.v1_whiplash_timer -= dt_step
            my_pos = Vec3(*self.position)
            if self.v1_whiplash_mode == 'pull_enemy' and is_valid(self.v1_whiplash_target_ent):
                target_dest = my_pos + Vec3(camera.forward.x, 0, camera.forward.z).normalized() * 2.2
                self.v1_whiplash_target_ent.position = lerp(self.v1_whiplash_target_ent.position, target_dest, dt_step * 18.0)
                if distance(Vec3(*self.v1_whiplash_target_ent.position), target_dest) <= 1.8:
                    self.v1_whiplash_timer = 0.0
            elif self.v1_whiplash_mode == 'pull_self_to_enemy' and is_valid(self.v1_whiplash_target_ent):
                t_pos = Vec3(*self.v1_whiplash_target_ent.position) + Vec3(0, 1.0, 0)
                to_t = t_pos - (my_pos + Vec3(0, 1.2, 0))
                if to_t.length() <= 3.2:
                    self.v1_whiplash_timer = 0.0
                    self.vel_y = 8.0
                else:
                    self.position += to_t.normalized() * 58.0 * dt_step
                    self.vel_y = 0.0
                    self.grounded = False
            elif self.v1_whiplash_mode == 'pull_self_to_point' and self.v1_whiplash_point is not None:
                to_p = self.v1_whiplash_point - (my_pos + Vec3(0, 1.2, 0))
                if to_p.length() <= 2.6:
                    self.v1_whiplash_timer = 0.0
                    self.vel_y = 6.5
                else:
                    self.position += to_p.normalized() * 56.0 * dt_step
                    self.vel_y = 0.0
                    self.grounded = False
            else:
                self.v1_whiplash_timer = 0.0

        # Подкат (Slide) на земле и Ground Slam в воздухе по клавише [Ctrl]
        ctrl_down = bool(held_keys['control'] or held_keys['left control'] or held_keys['right control'] or held_keys['c'])
        if ctrl_down:
            if self.grounded:
                self.v1_sliding = True
                self.cam_pivot.y = lerp(self.cam_pivot.y, 0.92, dt_step * 16.0)
                slide_dir = Vec3(self.forward.x, 0, self.forward.z).normalized()
                self.position += slide_dir * (self.move_speed * 1.42) * dt_step
            elif not self.v1_slamming and self.vel_y > -38.0:
                self.v1_slamming = True
                self.v1_slam_air_time = 0.0
                self.vel_y = -46.0
        else:
            self.v1_sliding = False
            self.cam_pivot.y = lerp(self.cam_pivot.y, 1.72, dt_step * 14.0)

        if self.v1_slamming:
            self.v1_slam_air_time += dt_step
            self.vel_y = -48.0
            if self.grounded:
                self.v1_slamming = False
                my_pos = Vec3(*self.position)
                VisualFX(my_pos + Vec3(0, 0.4, 0), color.yellow, 8.5, 0.35)
                hit_any = False
                for e in list(game.enemies):
                    if is_valid(e) and not getattr(e, 'is_ally', False):
                        if distance_2d(my_pos, Vec3(*e.position)) <= 7.5:
                            hit_any = True
                            if not e.is_boss:
                                e.y += 3.2
                                e.stun_timer = max(e.stun_timer, 1.4)
                            apply_player_hit_effects(e, Vec3(*e.position) + Vec3(0, 1, 0), self.base_damage * 2.0, color.yellow, aoe=0, lifesteal=4.0)
                if hit_any:
                    self.v1_add_style('+ CRUSH', color.orange, 80)

    def _broadcast_shot(self, pos, aim_dir, speed, dmg, scale_val, col_name, aoe=0.0, pierce=False, bounces=0, homing=False):
        if getattr(ctx, 'net', None) and ctx.net.connected:
            ctx.net.broadcast({
                'type': 'player_shoot',
                'player_id': ctx.net.my_id,
                'pos': [round(pos.x, 2), round(pos.y, 2), round(pos.z, 2)],
                'dir': [round(aim_dir.x, 3), round(aim_dir.y, 3), round(aim_dir.z, 3)],
                'speed': speed,
                'scale': scale_val,
                'col': col_name,
                'aoe': aoe,
                'pierce': pierce,
                'bounces': bounces,
                'homing': homing
            })

    def perform_melee_attack(
        self, reach=5.2, cleave_radius=3.4, damage_mult=1.0, slash_col=color.orange,
        lifesteal=0.0, stun_dur=0.0, knockback=0.0, scissor_cross=False, aoe=0.0
    ):
        """Настоящая атака ближнего боя: создаёт 3D-дугу удара и поражает всех врагов в конусе перед выжившим"""
        game = ctx.game
        if not game:
            return 0

        my_pos = Vec3(*self.position)
        fwd = Vec3(self.forward.x, 0, self.forward.z).normalized()
        if fwd.length() < 0.01:
            fwd = Vec3(0, 0, 1)

        self.shoot_side += 1
        tilt = 22.0 if self.shoot_side % 2 == 0 else -22.0

        MeleeSlashFX(
            pos=my_pos,
            forward_dir=fwd,
            rot_y=self.rotation_y,
            slash_color=slash_col,
            arc_width=cleave_radius * 1.15,
            reach=reach,
            tilt_z=tilt,
            scissor_cross=scissor_cross
        )

        strike_center = my_pos + fwd * (reach * 0.55)
        hit_count = 0

        for e in list(game.enemies):
            if not is_valid(e) or getattr(e, 'is_ally', False):
                continue
            e_pos = Vec3(*e.position)
            if abs((e_pos.y + e.hit_height * 0.5) - (my_pos.y + 1.2)) > 4.2:
                continue

            to_enemy = e_pos - my_pos
            dist_from_player = distance_2d(e_pos, my_pos)
            dist_from_arc = distance_2d(e_pos, strike_center)

            in_cone = False
            if dist_from_player <= reach + e.hit_radius:
                flat_dir = Vec3(to_enemy.x, 0, to_enemy.z).normalized()
                dot = fwd.x * flat_dir.x + fwd.z * flat_dir.z
                if dot >= 0.15 or dist_from_player <= 2.4 + e.hit_radius:
                    in_cone = True

            if in_cone or dist_from_arc <= cleave_radius + e.hit_radius * 0.6:
                hit_count += 1
                hit_p = e_pos + Vec3(0, e.hit_height, 0)
                apply_player_hit_effects(
                    target=e,
                    hit_pos=hit_p,
                    base_dmg=self.base_damage * damage_mult,
                    hit_color=slash_col,
                    aoe=aoe,
                    lifesteal=lifesteal,
                    can_proc=True
                )
                if is_valid(e):
                    if stun_dur > 0 and not e.is_boss:
                        e.stun_timer = max(e.stun_timer, stun_dur)
                    if knockback > 0 and not e.is_boss:
                        push_p = e_pos + fwd * knockback
                        resolved = game.resolve_horizontal_collision(push_p, 0.8, e.y)
                        e.x = resolved.x
                        e.z = resolved.z

        return hit_count

    def _find_grapple_anchor(self, start_pos, aim_dir, max_dist=45.0):
        """Находит точку зацепа крюка-кошки Скаута (препятствие, платформу, врага или точку впереди)"""
        game = ctx.game
        step = 1.5
        cur = Vec3(*start_pos)
        for i in range(1, int(max_dist / step) + 1):
            p = start_pos + aim_dir * (i * step)
            if game.is_inside_solid_obstacle(p, 0.35):
                return p
            surf_h = game.get_surface_height(p.x, p.z, p.y + 1.2)
            if p.y <= surf_h + 0.3:
                return Vec3(p.x, surf_h + 0.5, p.z)
            for e in game.enemies:
                if is_valid(e) and distance(p, Vec3(*e.position) + Vec3(0, e.hit_height, 0)) <= e.hit_radius + 0.6:
                    return Vec3(*e.position) + Vec3(0, e.hit_height, 0)
            cur = p
        floor_y = game.get_surface_height(cur.x, cur.z, cur.y)
        return Vec3(cur.x, max(floor_y + 1.0, cur.y), cur.z)

    def fire_primary_projectile(self, damage_mult=1.0, col_override=None):
        # 1. СОЛ БЭДГАЙ: Ближний бой мечом Junkyard Dog
        if self.char_key == 'sol' and col_override is None:
            di_bonus = 1.25 if self.dragon_install_timer > 0 else 1.0
            reach = 5.8 if self.dragon_install_timer > 0 else 5.2
            self.perform_melee_attack(
                reach=reach,
                cleave_radius=3.5,
                damage_mult=damage_mult * di_bonus,
                slash_col=rgb(255, 115, 25),
                lifesteal=2.2 if self.dragon_install_timer > 0 else 1.0,
                knockback=1.2,
                aoe=2.2
            )
            if self.is_moving and self.grounded and self.dash_timer <= 0:
                self.position += self.forward * 0.35

            arm = self.parts['right_arm']
            arm.rotation_x = -75 if self.shoot_side % 2 == 0 else -35
            arm.rotation_z = -28 if self.shoot_side % 2 == 0 else 28
            arm.animate_rotation((0, 0, 0), duration=0.15)
            return

        # 2. ГВЕН: Ближний бой ножницами Snip Snip!
        if self.char_key == 'gwen' and col_override is None:
            self.perform_melee_attack(
                reach=4.8,
                cleave_radius=3.1,
                damage_mult=damage_mult,
                slash_col=rgb(95, 225, 255),
                lifesteal=2.4,
                scissor_cross=True,
                aoe=1.5
            )
            arm = self.parts['right_arm']
            arm.rotation_x = -65 if self.shoot_side % 2 == 0 else -30
            arm.rotation_y = -20 if self.shoot_side % 2 == 0 else 20
            arm.animate_rotation((0, 0, 0), duration=0.11)
            return

        # 3. ENFORCER: Помповый дробовик Riot Shotgun
        if self.char_key == 'enforcer' and col_override is None:
            aim_dir = camera.forward
            spawn_pos = Vec3(*self.position) + Vec3(0, 1.55, 0) + self.forward * 1.05
            spread = 0.032 if getattr(self, 'shield_stance', False) else 0.075
            for _ in range(6):
                offset = Vec3(
                    random.uniform(-spread, spread),
                    random.uniform(-spread * 0.6, spread * 0.6),
                    random.uniform(-spread, spread)
                )
                d = (aim_dir + offset).normalized()
                Projectile(
                    pos=spawn_pos,
                    direction=d,
                    speed=self.proj_speed,
                    damage=self.base_damage * 0.52 * damage_mult,
                    scale_val=0.20,
                    proj_color=rgb(110, 225, 255),
                    is_player=True,
                    pierce=True,
                    max_lifetime=0.52
                )
            VisualFX(spawn_pos, rgb(120, 225, 255), 1.4, 0.14)
            self._broadcast_shot(
                spawn_pos, aim_dir, self.proj_speed, self.base_damage * damage_mult,
                0.24, 'enforcer', 0.0, True, 0, False
            )
            arm = self.parts['right_arm']
            arm.rotation_x = -34
            arm.animate_rotation_x(0, duration=0.18)
            return

        # 4. ХАКУРЕЙ РЕЙМУ: Парные самонаводящиеся амулеты Офуда (красно-белые)
        if self.char_key == 'reimu' and col_override is None:
            aim_dir = camera.forward
            base_pos = Vec3(*self.position) + Vec3(0, 1.55, 0) + self.forward * 0.9
            for idx, side_off in enumerate((-0.32, 0.32)):
                sp = base_pos + self.right * side_off
                amu_col = rgb(255, 55, 70) if idx == 0 else color.white
                Projectile(
                    pos=sp, direction=aim_dir, speed=self.proj_speed,
                    damage=self.base_damage * 0.65 * damage_mult,
                    scale_val=self.proj_scale, proj_color=amu_col,
                    is_player=True, aoe=self.proj_aoe, homing=True
                )
            self._broadcast_shot(
                base_pos, aim_dir, self.proj_speed, self.base_damage * damage_mult,
                self.proj_scale, 'reimu', self.proj_aoe, False, 0, True
            )
            arm = self.parts['right_arm']
            arm.rotation_x = -28
            arm.animate_rotation_x(0, duration=0.12)
            return

        # 5. КОРАБЛЬ MINDUSTRY: Спаренные бортовые пушки с обоих крыльев
        if self.char_key == 'mindustry' and col_override is None:
            aim_dir = camera.forward
            base_pos = Vec3(*self.position) + Vec3(0, 1.45, 0) + self.forward * 1.0
            for side_off in (-0.55, 0.55):
                sp = base_pos + self.right * side_off
                Projectile(
                    pos=sp, direction=aim_dir, speed=self.proj_speed,
                    damage=self.base_damage * 0.58 * damage_mult,
                    scale_val=self.proj_scale, proj_color=rgb(255, 215, 65),
                    is_player=True, aoe=self.proj_aoe
                )
            self._broadcast_shot(
                base_pos, aim_dir, self.proj_speed, self.base_damage * damage_mult,
                self.proj_scale, 'mindustry', self.proj_aoe, False, 0, False
            )
            return

        # 6. Остальные стрелковые классы (Commando, Artificer, Huntress, Buzz, V1, Scout, M4A1, Medic, Aigis)
        aim_dir = camera.forward
        spawn_pos = Vec3(*self.position) + Vec3(0, 1.55, 0) + self.forward * 0.95
        color_map = {
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
            'mindustry': rgb(255, 215, 65)
        }
        default_col = color_map.get(self.char_key, color.yellow)
        proj_col = col_override if col_override else default_col
        col_name = 'cyan' if col_override else self.char_key

        steal = 1.6 if self.char_key == 'v1' else 0.0
        ally_heal = (12.0 + self.base_damage * 0.85) if self.char_key == 'medic' else 0.0

        Projectile(
            pos=spawn_pos,
            direction=aim_dir,
            speed=self.proj_speed,
            damage=self.base_damage * damage_mult,
            scale_val=self.proj_scale,
            proj_color=proj_col,
            is_player=True,
            aoe=self.proj_aoe,
            pierce=False,
            homing=(self.char_key == 'huntress'),
            lifesteal=steal,
            heal_allies=ally_heal
        )
        self._broadcast_shot(
            spawn_pos, aim_dir, self.proj_speed, self.base_damage * damage_mult,
            self.proj_scale, col_name, self.proj_aoe, False, 0, self.char_key == 'huntress'
        )

        if self.char_key in ('buzz', 'v1', 'scout', 'm4a1', 'medic', 'aigis'):
            arm = self.parts['right_arm']
            arm.rotation_x = -26
            arm.animate_rotation_x(0, duration=0.12)
        else:
            arm = self.parts['left_arm'] if self.shoot_side % 2 == 0 else self.parts['right_arm']
            self.shoot_side += 1
            arm.rotation_x = -24
            arm.animate_rotation_x(0, duration=0.11)

    def use_m1_skill(self):
        if self.char_key == 'v1':
            self.v1_use_primary()
            return
        self.m1_cd = 1.0 / self.fire_rate
        self.fire_primary_projectile()

    def use_m2_skill(self):
        if self.char_key == 'v1':
            self.v1_use_secondary()
            return
        if getattr(self, 'skill_lock_timer', 0.0) > 0:
            ctx.game.show_banner(f'НЕЙРОСЕТЬ ПЕРЕГРУЖЕНА ПОСЛЕ ПЕРЕСЕЛЕНИЯ ({self.skill_lock_timer:.1f}С)!', color.red, 1.2)
            return

        game = ctx.game
        skills = SURVIVOR_CLASSES[self.char_key]['skills']
        alien_cdr = 0.80 ** self.items.get('alien_head', 0)
        cd_mult = max(0.20, (1.0 - 0.12 * self.items['backup_mag']) * alien_cdr)
        self.m2_cd = skills['m2']['cd'] * cd_mult
        spawn_pos = Vec3(*self.position) + Vec3(0, 1.55, 0) + self.forward * 1.1
        aim_dir = camera.forward

        if self.char_key == 'commando':
            Projectile(
                pos=spawn_pos, direction=aim_dir, speed=68.0,
                damage=self.base_damage * 3.0, scale_val=0.48,
                proj_color=color.cyan, is_player=True, pierce=True
            )
            self._broadcast_shot(spawn_pos, aim_dir, 68.0, self.base_damage * 3.0, 0.48, 'cyan', 0.0, True, 0, False)

        elif self.char_key == 'artificer':
            Projectile(
                pos=spawn_pos, direction=aim_dir, speed=26.0,
                damage=self.base_damage * 2.8, scale_val=0.95,
                proj_color=color.cyan, is_player=True, aoe=7.5
            )
            self._broadcast_shot(spawn_pos, aim_dir, 26.0, self.base_damage * 2.8, 0.95, 'cyan', 7.5, False, 0, False)

        elif self.char_key == 'huntress':
            Projectile(
                pos=spawn_pos, direction=aim_dir, speed=48.0,
                damage=self.base_damage * 2.2, scale_val=0.55,
                proj_color=color.cyan, is_player=True, bounces=5, homing=True
            )
            self._broadcast_shot(spawn_pos, aim_dir, 48.0, self.base_damage * 2.2, 0.55, 'cyan', 0.0, False, 5, True)

        elif self.char_key == 'buzz':
            Projectile(
                pos=spawn_pos, direction=aim_dir, speed=74.0,
                damage=self.base_damage * 2.9, scale_val=0.55,
                proj_color=color.red, is_player=True, aoe=4.2, pierce=True
            )
            self._broadcast_shot(spawn_pos, aim_dir, 74.0, self.base_damage * 2.9, 0.55, 'sol', 4.2, True, 0, False)

        elif self.char_key == 'v1':
            VisualFX(spawn_pos + Vec3(0, 0.6, 0), color.gold, 1.8, 0.25)
            Projectile(
                pos=spawn_pos, direction=aim_dir, speed=85.0,
                damage=self.base_damage * 2.5, scale_val=0.45,
                proj_color=color.gold, is_player=True, bounces=4, homing=True, lifesteal=6.0
            )
            self._broadcast_shot(spawn_pos, aim_dir, 85.0, self.base_damage * 2.5, 0.45, 'v1', 0.0, False, 4, True)

        elif self.char_key == 'sol':
            self.vel_y = 14.5
            self.grounded = False
            self.perform_melee_attack(
                reach=6.5, cleave_radius=4.5, damage_mult=2.8,
                slash_col=rgb(255, 90, 20), lifesteal=4.0, knockback=3.0, aoe=3.5
            )
            gf_dir = Vec3(self.forward.x, 0.0, self.forward.z).normalized()
            Projectile(
                pos=spawn_pos, direction=gf_dir, speed=34.0,
                damage=self.base_damage * 1.8, scale_val=0.85,
                proj_color=rgb(255, 110, 20), is_player=True, aoe=4.2, pierce=True, max_lifetime=0.38
            )

        elif self.char_key == 'gwen':
            self.perform_melee_attack(
                reach=7.2, cleave_radius=4.2, damage_mult=3.2,
                slash_col=rgb(155, 240, 255), lifesteal=6.5, scissor_cross=True, aoe=2.8
            )
            arm = self.parts['right_arm']
            arm.rotation_x = -95
            arm.animate_rotation_x(0, duration=0.22)

        elif self.char_key == 'enforcer':
            self.dash_vector = self.forward * 16.0
            self.dash_timer = 0.16
            self.shield = min(float(self.max_hp), self.shield + 20.0)
            self.perform_melee_attack(
                reach=5.6, cleave_radius=3.8, damage_mult=2.6,
                slash_col=color.cyan, stun_dur=2.0, knockback=5.5, aoe=2.5
            )
            l_arm = self.parts['left_arm']
            l_arm.rotation_y = 45
            l_arm.animate_rotation_y(0, duration=0.22)

        elif self.char_key == 'scout':
            for _ in range(8):
                offset = Vec3(random.uniform(-0.09, 0.09), random.uniform(-0.06, 0.06), random.uniform(-0.09, 0.09))
                d = (aim_dir + offset).normalized()
                Projectile(
                    pos=spawn_pos, direction=d, speed=66.0,
                    damage=self.base_damage * 0.55, scale_val=0.24,
                    proj_color=color.orange, is_player=True, pierce=True, max_lifetime=0.38
                )
            self.perform_melee_attack(
                reach=4.8, cleave_radius=3.4, damage_mult=1.6,
                slash_col=color.orange, knockback=4.5, aoe=2.0
            )
            if not self.grounded or aim_dir.y < -0.15:
                recoil_dir = -aim_dir
                self.vel_y = max(14.5, recoil_dir.y * 22.0)
                self.grounded = False
                self.dash_vector = Vec3(recoil_dir.x, 0, recoil_dir.z) * 24.0
                self.dash_timer = 0.28
                VisualFX(spawn_pos, color.yellow, 3.2, 0.25)

        elif self.char_key == 'm4a1':
            VisualFX(spawn_pos, rgb(95, 255, 135), 3.0, 0.28)
            Projectile(
                pos=spawn_pos, direction=aim_dir, speed=58.0,
                damage=self.base_damage * 3.4, scale_val=0.78,
                proj_color=rgb(95, 255, 135), is_player=True, aoe=6.8, pierce=True
            )
            self._broadcast_shot(spawn_pos, aim_dir, 58.0, self.base_damage * 3.4, 0.78, 'buzz', 6.8, True, 0, False)
            for clone in list(getattr(self, 'dummy_clones', [])):
                if is_valid(clone):
                    clone.command_burst_shot()

        elif self.char_key == 'medic':
            # Kritzkrieg Medi-Beam: лечит и баффает союзников впереди + выкачивает HP из врагов по лучу
            my_pos = Vec3(*self.position) + Vec3(0, 1.4, 0)
            end_beam = my_pos + aim_dir * 26.0
            LightningBeam(my_pos, end_beam, rgb(255, 55, 80), 0.32)
            self.heal_amount(18.0)
            self.shield = min(float(self.max_hp), self.shield + 20.0)

            allies = (
                list(getattr(self, 'dummy_clones', []))
                + list(getattr(self, 'mindustry_turrets', []))
                + [e for e in game.enemies if is_valid(e) and getattr(e, 'is_ally', False)]
                + list(game.remote_players.values())
            )
            for al in allies:
                if is_valid(al) and distance(my_pos, Vec3(*al.position)) <= 24.0:
                    if hasattr(al, 'heal_ally'):
                        al.heal_ally(amount=al.max_hp * 0.40, shield_amt=20.0)
                    else:
                        al.hp = min(float(al.max_hp), al.hp + al.max_hp * 0.40)
                    LightningBeam(my_pos, Vec3(*al.position) + Vec3(0, 1.2, 0), color.lime, 0.24)
                    VisualFX(Vec3(*al.position) + Vec3(0, 1.2, 0), color.lime, 2.5, 0.25)

            Projectile(
                pos=spawn_pos, direction=aim_dir, speed=78.0,
                damage=self.base_damage * 2.6, scale_val=0.52,
                proj_color=rgb(255, 55, 80), is_player=True, aoe=3.5,
                pierce=True, lifesteal=12.0, heal_allies=35.0
            )

        elif self.char_key == 'aigis':
            # Pandora Grenade Cannon: мощный фугасный снаряд (300% урона, AoE 5.2м)
            VisualFX(spawn_pos, color.gold, 2.4, 0.22)
            Projectile(
                pos=spawn_pos, direction=aim_dir, speed=52.0,
                damage=self.base_damage * 3.0, scale_val=0.65,
                proj_color=rgb(255, 195, 50), is_player=True, aoe=5.2
            )
            self._broadcast_shot(spawn_pos, aim_dir, 52.0, self.base_damage * 3.0, 0.65, 'aigis', 5.2, False, 0, False)

        elif self.char_key == 'reimu':
            # Yin-Yang Persuasion Orb: рикошетящая до 6 раз сфера Инь-Ян с AoE
            Projectile(
                pos=spawn_pos, direction=aim_dir, speed=46.0,
                damage=self.base_damage * 2.4, scale_val=0.68,
                proj_color=rgb(245, 45, 65), is_player=True,
                aoe=3.2, bounces=6, homing=True
            )
            self._broadcast_shot(spawn_pos, aim_dir, 46.0, self.base_damage * 2.4, 0.68, 'reimu', 3.2, False, 6, True)

        elif self.char_key == 'mindustry':
            # Surge Alloy Blast: пробивной разряд Кинетического Сплава с цепными молниями
            VisualFX(spawn_pos, color.yellow, 2.8, 0.25)
            Projectile(
                pos=spawn_pos, direction=aim_dir, speed=58.0,
                damage=self.base_damage * 2.8, scale_val=0.65,
                proj_color=rgb(255, 215, 50), is_player=True,
                aoe=4.8, pierce=True
            )
            self._broadcast_shot(spawn_pos, aim_dir, 58.0, self.base_damage * 2.8, 0.65, 'mindustry', 4.8, True, 0, False)

    def use_shift_skill(self):
        if getattr(self, 'skill_lock_timer', 0.0) > 0:
            ctx.game.show_banner(f'НЕЙРОСЕТЬ ПЕРЕГРУЖЕНА ПОСЛЕ ПЕРЕСЕЛЕНИЯ ({self.skill_lock_timer:.1f}С)!', color.red, 1.2)
            return

        game = ctx.game
        skills = SURVIVOR_CLASSES[self.char_key]['skills']
        alien_cdr = 0.80 ** self.items.get('alien_head', 0)
        burn_cdr = 0.70 ** self.items.get('afterburner', 0)
        self.shift_cd = max(0.25, skills['shift']['cd'] * alien_cdr * burn_cdr)
        my_pos = Vec3(*self.position)
        nrg_mult = (
            1.0
            + 0.18 * self.items['energy_drink']
            + 0.35 * self.items.get('afterburner', 0)
        )

        if self.char_key == 'enforcer':
            self.shield_stance = not getattr(self, 'shield_stance', False)
            sh_ent = self.parts.get('shield')
            aura_ent = self.parts.get('shield_aura')
            if self.shield_stance:
                if sh_ent:
                    sh_ent.animate_position((0.35, -0.08, 0.68), duration=0.15)
                    sh_ent.animate_rotation((0, 0, 0), duration=0.15)
                if aura_ent:
                    aura_ent.enabled = True
                VisualFX(my_pos + Vec3(0, 1.2, 0), color.cyan, 2.6, 0.22)
                game.show_banner('СТОЙКА ЩИТА АКТИВНА: БРОНЯ +65% | СКОРОСТЬ СТРЕЛЬБЫ +45%', color.cyan, 1.8)
            else:
                if sh_ent:
                    sh_ent.animate_position((-0.28, -0.15, 0.45), duration=0.15)
                    sh_ent.animate_rotation((0, -25, 0), duration=0.15)
                if aura_ent:
                    aura_ent.enabled = False
                self.dash_vector = self.forward * 18.0 * nrg_mult
                self.dash_timer = 0.18
                VisualFX(my_pos + Vec3(0, 1.0, 0), color.white, 2.0, 0.2)
            return

        if self.char_key == 'scout':
            start_p = my_pos + Vec3(0, 1.5, 0)
            anchor = self._find_grapple_anchor(start_p, camera.forward, max_dist=45.0 * nrg_mult)
            self.grapple_active = True
            self.grapple_target = anchor
            self.grapple_timer = 0.72
            self.scout_speed_buff = 3.2
            VisualFX(anchor, color.cyan, 2.2, 0.35)
            LightningBeam(start_p, anchor, color.cyan, 0.16)
            return

        VisualFX(my_pos + Vec3(0, 1, 0), color.cyan, 2.4, 0.3)

        if self.char_key == 'commando':
            self.dash_vector = self.forward * 28.0 * nrg_mult
            self.dash_timer = 0.22
        elif self.char_key == 'artificer':
            self.vel_y = 16.5
            self.grounded = False
            self.dash_vector = self.forward * 18.0 * nrg_mult
            self.dash_timer = 0.32
            for e in list(game.enemies):
                if is_valid(e) and not getattr(e, 'is_ally', False):
                    e_pos = Vec3(*e.position)
                    if distance(e_pos, my_pos) <= 6.8:
                        e.take_damage(self.base_damage * 1.8)
        elif self.char_key == 'huntress':
            blink_dir = camera.forward
            blink_dir.y = max(0.0, blink_dir.y)
            target_pos = my_pos + blink_dir.normalized() * (11.0 * nrg_mult)
            LightningBeam(my_pos + Vec3(0, 1, 0), target_pos + Vec3(0, 1, 0), color.cyan, 0.28)
            resolved = game.resolve_horizontal_collision(target_pos, 0.72, self.y)
            bound = getattr(game, 'world_bound', 56.0) - 2.0
            self.position = Vec3(clamp(resolved.x, -bound, bound), max(self.y, target_pos.y), clamp(resolved.z, -bound, bound))
            VisualFX(Vec3(*self.position) + Vec3(0, 1, 0), color.cyan, 2.4, 0.3)
        elif self.char_key == 'buzz':
            self.vel_y = 18.5
            self.grounded = False
            self.dash_vector = self.forward * 24.0 * nrg_mult
            self.dash_timer = 0.36
            VisualFX(my_pos, rgb(125, 255, 80), 4.2, 0.35)
        elif self.char_key == 'v1':
            if self.v1_stamina < 1.0:
                self.shift_cd = 0.1
                return
            self.v1_stamina -= 1.0
            self.shift_cd = 0.12
            move_in = Vec3(held_keys['d'] - held_keys['a'], 0, held_keys['w'] - held_keys['s'])
            dash_dir = (self.forward * move_in.z + self.right * move_in.x).normalized() if move_in.length() > 0 else self.forward
            self.dash_vector = dash_dir * 38.0 * nrg_mult
            self.dash_timer = 0.16
        elif self.char_key == 'sol':
            self.dash_vector = self.forward * 27.0 * nrg_mult
            self.dash_timer = 0.26
            self.perform_melee_attack(
                reach=6.5, cleave_radius=4.2, damage_mult=2.4,
                slash_col=rgb(255, 100, 20), knockback=4.0, aoe=3.0
            )
        elif self.char_key == 'gwen':
            self.dash_vector = self.forward * 22.0 * nrg_mult
            self.dash_timer = 0.22
            self.m1_cd = 0.0
            mist = HallowedMistZone(my_pos + self.forward * 3.0, self.base_damage * 0.65)
            game.stage_entities.append(mist)
        elif self.char_key == 'm4a1':
            self.dash_vector = self.forward * 25.0 * nrg_mult
            self.dash_timer = 0.20
            self.shield = min(float(self.max_hp), self.shield + 25.0)
            VisualFX(my_pos + Vec3(0, 1.2, 0), rgb(95, 255, 135), 2.6, 0.25)
            for clone in list(getattr(self, 'dummy_clones', [])):
                if is_valid(clone):
                    clone.command_burst_shot()
        elif self.char_key == 'medic':
            # Amputator Healing Surge: рывок с ударом пилой Ubersaw и целебным импульсом +25% HP всем вокруг
            self.dash_vector = self.forward * 24.0 * nrg_mult
            self.dash_timer = 0.22
            self.perform_melee_attack(
                reach=5.5, cleave_radius=3.8, damage_mult=2.2,
                slash_col=rgb(255, 65, 85), lifesteal=10.0, aoe=2.5
            )
            self.heal_amount(self.max_hp * 0.25)
            VisualFX(my_pos + Vec3(0, 1.0, 0), color.lime, 8.0, 0.35)
            shift_allies = (
                list(self.dummy_clones)
                + list(self.mindustry_turrets)
                + [e for e in game.enemies if is_valid(e) and getattr(e, 'is_ally', False)]
                + list(game.remote_players.values())
            )
            for al in shift_allies:
                if is_valid(al) and distance(my_pos, Vec3(*al.position)) <= 15.0:
                    if hasattr(al, 'heal_ally'):
                        al.heal_ally(amount=al.max_hp * 0.25)
                    else:
                        al.hp = min(float(al.max_hp), al.hp + al.max_hp * 0.25)
                    VisualFX(Vec3(*al.position) + Vec3(0, 1.2, 0), color.lime, 2.5, 0.25)
        elif self.char_key == 'aigis':
            # Orgia Mode Overdrive: реактивный взлёт и перегрузка Orgia на 5.5 сек
            self.vel_y = 14.5
            self.grounded = False
            self.dash_vector = self.forward * 24.0 * nrg_mult
            self.dash_timer = 0.28
            self.orgia_timer = 5.5
            VisualFX(my_pos + Vec3(0, 1.2, 0), color.gold, 5.5, 0.35)
            game.show_banner('ORGIA MODE OVERDRIVE :: АТАКА +50% | СКОРОСТЬ +45% | УРОН +35%!', color.gold, 2.2)
        elif self.char_key == 'reimu':
            # Fantasy Nature Float: парящий рывок + щит + 4 самонаводящихся талисмана
            self.vel_y = 12.5
            self.grounded = False
            self.dash_vector = self.forward * 24.0 * nrg_mult
            self.dash_timer = 0.24
            self.shield = min(float(self.max_hp), self.shield + 20.0)
            sp = my_pos + Vec3(0, 1.5, 0)
            for i in range(4):
                ang = (i / 4.0) * math.pi * 2
                d = Vec3(math.cos(ang), 0.2, math.sin(ang)).normalized()
                Projectile(
                    pos=sp, direction=d, speed=54.0,
                    damage=self.base_damage * 1.4, scale_val=0.30,
                    proj_color=rgb(255, 65, 80), is_player=True, homing=True
                )
        # В use_shift_skill:
        elif self.char_key == 'mindustry':
            # Core Engine Overdrive: ускоренный пролёт в направлении взгляда + авто-ремонт корпуса (+15% HP)
            self.dash_vector = camera.forward * 28.0 * nrg_mult
            self.dash_timer = 0.28
            self.heal_amount(self.max_hp * 0.15)
            VisualFX(my_pos + Vec3(0, 1.2, 0), color.yellow, 4.0, 0.3)

        

    def use_r_skill(self):
        if getattr(self, 'skill_lock_timer', 0.0) > 0:
            ctx.game.show_banner(f'НЕЙРОСЕТЬ ПЕРЕГРУЖЕНА ПОСЛЕ ПЕРЕСЕЛЕНИЯ ({self.skill_lock_timer:.1f}С)!', color.red, 1.2)
            return

        
        game = ctx.game
        skills = SURVIVOR_CLASSES[self.char_key]['skills']
        # В начале use_r_skill (добавлен бонус Lysate Cell):
        alien_cdr = 0.80 ** self.items.get('alien_head', 0)
        cell_cdr = 0.75 ** self.items.get('lysate_cell', 0)
        self.r_cd = max(0.5, skills['r']['cd'] * alien_cdr * cell_cdr)
        my_pos = Vec3(*self.position)

        if self.char_key == 'commando':
            self.barrage_shots = 8
            self.barrage_timer = 0.01
        elif self.char_key == 'artificer':
            targets = [e for e in game.enemies if is_valid(e) and not getattr(e, 'is_ally', False) and distance(Vec3(*e.position), my_pos) <= 28.0]
            for i in range(5):
                if i < len(targets) and is_valid(targets[i]):
                    t_pos = Vec3(*targets[i].position)
                else:
                    ang = random.uniform(0, math.pi * 2)
                    t_pos = my_pos + Vec3(math.cos(ang) * 8.0, 0, math.sin(ang) * 8.0)
                OrbitalStrikeFX(t_pos, self.base_damage * 2.2)
        elif self.char_key == 'huntress':
            self.vel_y = 14.0
            self.grounded = False
            zone_pos = my_pos + self.forward * 12.0
            zone = ArrowRainZone(zone_pos, self.base_damage * 0.75)
            game.stage_entities.append(zone)
        elif self.char_key == 'buzz':
            spawn_pos = my_pos + Vec3(0, 1.8, 0)
            for i in range(6):
                ang = math.radians(-30 + i * 12)
                d = Vec3(
                    self.forward.x * math.cos(ang) - self.forward.z * math.sin(ang),
                    0.15,
                    self.forward.x * math.sin(ang) + self.forward.z * math.cos(ang)
                ).normalized()
                Projectile(
                    pos=spawn_pos, direction=d, speed=46.0,
                    damage=self.base_damage * 2.1, scale_val=0.42,
                    proj_color=rgb(130, 255, 90), is_player=True, aoe=3.8, homing=True
                )
                self._broadcast_shot(spawn_pos, d, 46.0, self.base_damage * 2.1, 0.42, 'buzz', 3.8, False, 0, True)
        elif self.char_key == 'v1':
            self.r_cd = 0.2
            self.v1_use_whiplash()
        elif self.char_key == 'sol':
            self.dragon_install_timer = 6.0
            VisualFX(my_pos + Vec3(0, 1.5, 0), rgb(255, 60, 20), 11.0, 0.45)
            for e in list(game.enemies):
                if is_valid(e) and not getattr(e, 'is_ally', False):
                    e_pos = Vec3(*e.position)
                    if distance(e_pos, my_pos) <= 11.0:
                        e.take_damage(self.base_damage * 3.4)
            game.show_banner('DRAGON INSTALL :: LET IT OUT!', rgb(255, 120, 30), 2.5)
        elif self.char_key == 'gwen':
            spawn_pos = my_pos + Vec3(0, 1.6, 0)
            base_f = camera.forward
            for angle_deg in (-16, -8, 0, 8, 16):
                rad = math.radians(angle_deg)
                d = Vec3(
                    base_f.x * math.cos(rad) - base_f.z * math.sin(rad),
                    base_f.y,
                    base_f.x * math.sin(rad) + base_f.z * math.cos(rad)
                ).normalized()
                Projectile(
                    pos=spawn_pos, direction=d, speed=62.0,
                    damage=self.base_damage * 2.4, scale_val=0.46,
                    proj_color=rgb(110, 225, 255), is_player=True, aoe=2.5, pierce=True, lifesteal=4.0
                )
                self._broadcast_shot(spawn_pos, d, 62.0, self.base_damage * 2.4, 0.46, 'gwen', 2.5, True, 0, False)
        elif self.char_key == 'enforcer':
            target_pos = my_pos + self.forward * 10.0
            floor_y = game.get_surface_height(target_pos.x, target_pos.z, my_pos.y)
            gas_pos = Vec3(target_pos.x, floor_y, target_pos.z)
            VisualFX(gas_pos + Vec3(0, 1.0, 0), rgb(140, 255, 100), 6.5, 0.35)
            gas_zone = TearGasZone(gas_pos, self.base_damage * 0.85)
            game.stage_entities.append(gas_zone)
            game.show_banner('TEAR GAS DEPLOYED :: CROWD CONTROL!', rgb(140, 255, 100), 2.0)
        elif self.char_key == 'scout':
            target_pos = my_pos + self.forward * 11.0
            floor_y = game.get_surface_height(target_pos.x, target_pos.z, my_pos.y)
            ifg_pos = Vec3(target_pos.x, floor_y, target_pos.z)
            VisualFX(ifg_pos + Vec3(0, 1.2, 0), color.cyan, 6.5, 0.35)
            ifg = IFGZone(ifg_pos, self.base_damage * 0.90)
            game.stage_entities.append(ifg)
            game.show_banner('ROCK AND STONE! :: IFG FIELD & FLARE DEPLOYED!', color.yellow, 2.2)
        elif self.char_key == 'm4a1':
            self.dummy_clones = [c for c in self.dummy_clones if is_valid(c)]
            used_slots = {c.slot_idx for c in self.dummy_clones}
            spawned = 0
            for slot in range(4):
                if len(self.dummy_clones) >= 4 or spawned >= 2:
                    break
                if slot not in used_slots:
                    clone = DummyClone(self, slot_idx=slot)
                    self.dummy_clones.append(clone)
                    game.stage_entities.append(clone)
                    VisualFX(Vec3(*clone.position) + Vec3(0, 1.2, 0), rgb(95, 255, 135), 3.0, 0.3)
                    spawned += 1

            for c in self.dummy_clones:
                c.hp = float(c.max_hp)
                c.command_burst_shot()

            active_links = 1 + len(self.dummy_clones)
            game.show_banner(
                f'DUMMY LINK ACTIVE :: ОТРЯД M4A1 [{active_links}x LINK] ({len(self.dummy_clones)}/4 КЛОНОВ)!',
                rgb(95, 255, 135), 2.6
            )
        elif self.char_key == 'medic':
            # Ульта Медика TF2:
            # 1) Если прицел направлен на врага (<50% HP, для боссов <30% HP) — переманивает его на сторону игрока!
            # 2) Если прицел направлен на союзника (или нет подходящего врага в прицеле) — активирует Убер-заряд и бафф союзников!
            aim_dir = camera.forward
            eye_pos = my_pos + Vec3(0, 1.55, 0)
            best_enemy = None
            best_dot = 0.84
            for e in list(game.enemies):
                if is_valid(e) and not getattr(e, 'is_ally', False) and e.enemy_type != 'mithrix':
                    e_center = Vec3(*e.position) + Vec3(0, e.hit_height, 0)
                    to_e = e_center - eye_pos
                    if to_e.length() <= 32.0:
                        dot = aim_dir.dot(to_e.normalized())
                        if dot > best_dot:
                            best_dot = dot
                            best_enemy = e

            if best_enemy is not None:
                hp_pct = best_enemy.hp / max(1.0, best_enemy.max_hp)
                req_pct = 0.30 if best_enemy.is_boss else 0.50
                if hp_pct <= req_pct:
                    best_enemy.convert_to_ally()
                    e_p = Vec3(*best_enemy.position) + Vec3(0, best_enemy.hit_height, 0)
                    LightningBeam(eye_pos, e_p, color.lime, 0.45)
                    VisualFX(e_p, color.lime, 5.5, 0.4)
                    game.show_banner(
                        f'MIND CONTROL :: {best_enemy.enemy_type.upper()} ПЕРЕШЁЛ НА ВАШУ СТОРОНУ!',
                        color.lime, 3.2
                    )
                    return

            # Если врага под порог переманивания в прицеле нет — даём УБЕР-ЗАРЯД себе и всем союзникам!
            self.uber_timer = 6.5
            self.heal_amount(self.max_hp * 0.50)
            self.shield = min(float(self.max_hp), self.shield + 50.0)
            VisualFX(my_pos + Vec3(0, 1.2, 0), rgb(255, 55, 80), 7.5, 0.4)

            allies = (
                list(getattr(self, 'dummy_clones', []))
                + list(getattr(self, 'mindustry_turrets', []))
                + [e for e in game.enemies if is_valid(e) and getattr(e, 'is_ally', False)]
                + list(game.remote_players.values())
            )
            for al in allies:
                if is_valid(al):
                    if hasattr(al, 'heal_ally'):
                        al.heal_ally(amount=al.max_hp, shield_amt=50.0, uber_dur=6.5)
                    else:
                        al.hp = float(al.max_hp)
                        if hasattr(al, 'damage'):
                            al.damage *= 1.30
                    LightningBeam(eye_pos, Vec3(*al.position) + Vec3(0, 1.2, 0), rgb(255, 55, 80), 0.35)
                    VisualFX(Vec3(*al.position) + Vec3(0, 1.2, 0), rgb(255, 55, 80), 3.5, 0.35)

            game.show_banner('ÜBERCHARGE READY :: НЕУЯЗВИМОСТЬ И УСИЛЕНИЕ СОЮЗНИКОВ (6.5 СЕК)!', rgb(255, 75, 90), 3.0)

        elif self.char_key == 'aigis':
            # Persona: Palladion Strike — +45 щита и удар копьями света по врагам вокруг
            self.shield = min(float(self.max_hp), self.shield + 45.0)
            VisualFX(my_pos + Vec3(0, 1.6, 0), color.cyan, 8.0, 0.4)
            targets = [e for e in game.enemies if is_valid(e) and not getattr(e, 'is_ally', False) and distance(Vec3(*e.position), my_pos) <= 28.0]
            for i in range(6):
                if i < len(targets) and is_valid(targets[i]):
                    t_pos = Vec3(*targets[i].position)
                else:
                    ang = (i / 6.0) * math.pi * 2
                    t_pos = my_pos + Vec3(math.cos(ang) * 9.0, 0, math.sin(ang) * 9.0)
                OrbitalStrikeFX(t_pos, self.base_damage * 3.2)
            game.show_banner('PERSONA :: PALLADION STRIKE!', color.cyan, 2.5)

        elif self.char_key == 'reimu':
            # Spell Card: Fantasy Seal — 10 радужных самонаводящихся сфер Данмаку
            spawn_pos = my_pos + Vec3(0, 1.8, 0)
            rainbow = [
                rgb(255, 60, 80), rgb(255, 165, 45), color.yellow,
                color.lime, color.cyan, rgb(185, 85, 255)
            ]
            for i in range(10):
                ang = (i / 10.0) * math.pi * 2
                d = Vec3(math.cos(ang), 0.25, math.sin(ang)).normalized()
                col = rainbow[i % len(rainbow)]
                Projectile(
                    pos=spawn_pos, direction=d, speed=50.0,
                    damage=self.base_damage * 1.9, scale_val=0.58,
                    proj_color=col, is_player=True, aoe=4.0, homing=True
                )
            VisualFX(spawn_pos, rgb(255, 75, 95), 7.5, 0.4)
            game.show_banner('SPELL CARD :: FANTASY SEAL!', rgb(255, 85, 100), 2.5)

        elif self.char_key == 'mindustry':
            # Build Mode: Spectre & Mend Turret (тратит 20% от макс. HP)
            hp_cost = self.max_hp * 0.20
            if self.hp <= hp_cost + 2.0:
                self.r_cd = 1.0
                game.show_banner('НЕДОСТАТОЧНО HP ДЛЯ СТРОИТЕЛЬСТВА ТУРЕЛИ (НУЖНО >20% HP)!', color.red, 2.0)
                return

            self.hp = max(1.0, self.hp - hp_cost)
            self.mindustry_turrets = [t for t in self.mindustry_turrets if is_valid(t)]
            if len(self.mindustry_turrets) >= 4:
                oldest = self.mindustry_turrets.pop(0)
                oldest.is_dead = True
                destroy(oldest)

            build_pos = my_pos + self.forward * 4.2
            floor_y = game.get_surface_height(build_pos.x, build_pos.z, my_pos.y)
            turret_pos = Vec3(build_pos.x, floor_y, build_pos.z)
            slot_idx = len(self.mindustry_turrets)
            turret = MindustryTurret(self, turret_pos, slot_idx=slot_idx)
            self.mindustry_turrets.append(turret)
            game.stage_entities.append(turret)

            LightningBeam(my_pos + Vec3(0, 1.4, 0), turret_pos + Vec3(0, 1.0, 0), color.yellow, 0.35)
            VisualFX(turret_pos + Vec3(0, 1.0, 0), color.lime, 3.8, 0.35)
            game.show_banner(
                f'BUILD MODE :: ПОСТРОЕНА ТУРЕЛЬ SPECTRE [{len(self.mindustry_turrets)}/4] (-{int(hp_cost)} HP)!',
                rgb(255, 215, 65), 2.6
            )