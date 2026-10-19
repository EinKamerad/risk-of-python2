from ursina import *
import math
import random
from config import ctx, rgb, is_valid
from entities.fx import VisualFX, LightningBeam


def apply_player_hit_effects(target, hit_pos, base_dmg, hit_color=color.yellow, aoe=0.0, lifesteal=0.0, can_proc=True):
    """Универсальный расчёт урона и срабатывания предметов (работает для снарядов, ближнего боя, клонов и турелей)"""
    game = ctx.game
    if not game or not is_valid(target) or getattr(target, 'is_ally', False) or not is_valid(game.player):
        return

    target_pos = Vec3(*target.position)
    p = game.player
    it = p.items
    luck_bonus = 1.0 + 0.12 * it['clover']

    dmg = base_dmg

    # Shattering Justice: раскол брони (+20% урона по цели)
    if it.get('shattering_justice', 0) > 0:
        target.armor_break_timer = 4.0 * it['shattering_justice']
    if getattr(target, 'armor_break_timer', 0.0) > 0:
        dmg *= (1.0 + 0.20 * max(1, it.get('shattering_justice', 1)))

    # Crowbar: +50% урона врагам с >85% HP
    if it['crowbar'] > 0 and target.hp >= target.max_hp * 0.85:
        dmg *= (1.0 + 0.50 * it['crowbar'])

    # Armor-Piercing Rounds: +20% урона по Боссам
    if it['ap_rounds'] > 0 and target.is_boss:
        dmg *= (1.0 + 0.20 * it['ap_rounds'])

    # Focus Crystal: +20% урона вблизи (<13м)
    if it['focus_crystal'] > 0 and distance(Vec3(*p.position), target_pos) <= 13.0:
        dmg *= (1.0 + 0.20 * it['focus_crystal'])

    # Brilliant Behemoth: +25% урона и взрывной радиус
    eff_aoe = aoe
    if it['behemoth'] > 0:
        dmg *= (1.0 + 0.25 * it['behemoth'])
        eff_aoe = max(eff_aoe, 2.5 + 1.0 * it['behemoth'])

    # Критический удар + Harvester's Scythe + Predatory Instincts
    is_crit = random.random() < p.crit_chance
    if is_crit:
        dmg *= 2.0
        VisualFX(hit_pos, rgb(255, 45, 70), max_scale=2.2, duration=0.25)
        if it['harvester_scythe'] > 0:
            p.heal_amount(2.0 + 4.0 * it['harvester_scythe'])
        if it['predatory'] > 0:
            p.predatory_timer = 3.0

    # Leeching Seed + врождённый вампиризм навыка (с поддержкой Aegis)
    heal_amt = lifesteal + (1.5 * it['leeching_seed'])
    if heal_amt > 0:
        p.heal_amount(heal_amt)

    # Статусы на враге до удара
    if it['chronobauble'] > 0:
        target.slow_timer = max(target.slow_timer, 2.5 * it['chronobauble'])

    if it['stun_grenade'] > 0 and not target.is_boss:
        if random.random() < min(0.65, 0.10 * it['stun_grenade'] * luck_bonus):
            target.stun_timer = max(target.stun_timer, 1.5)
            VisualFX(target_pos + Vec3(0, 1.5, 0), color.white, 2.0, 0.25)

    if it['tri_tip'] > 0:
        if random.random() < min(1.0, 0.15 * it['tri_tip'] * luck_bonus):
            target.bleed_timer = max(target.bleed_timer, 3.0)
            target.bleed_dps = max(target.bleed_dps, p.base_damage * 0.6 * it['tri_tip'])

    target.take_damage(dmg)
    VisualFX(hit_pos, hit_color, max_scale=1.3 if eff_aoe == 0 else eff_aoe * 1.35, duration=0.22)

    # Old Guillotine: мгновенная казнь врагов с низким уровнем здоровья (кроме Митрикса)
    if is_valid(target) and it.get('guillotine', 0) > 0 and target.enemy_type != 'mithrix':
        exec_thresh = min(0.45, 0.13 * it['guillotine'])
        if (target.hp / max(1.0, target.max_hp)) <= exec_thresh:
            VisualFX(target_pos + Vec3(0, 1.5, 0), color.white, 4.0, 0.3)
            target.take_damage(target.hp + 999.0)

    if eff_aoe > 0:
        for other in list(game.enemies):
            if other is not target and is_valid(other) and not getattr(other, 'is_ally', False):
                if distance(Vec3(*other.position), target_pos) <= eff_aoe:
                    other.take_damage(dmg * 0.65)

    if not can_proc or not is_valid(p):
        return

    # Plasma Shrimp: пока у игрока есть щит, каждая атака выпускает плазменную ракету!
    if it.get('plasma_shrimp', 0) > 0 and p.shield >= 1.0:
        m_pos = Vec3(*p.position) + Vec3(0, 2.0, 0)
        Projectile(
            pos=m_pos, direction=Vec3(random.uniform(-0.3, 0.3), 0.5, random.uniform(-0.3, 0.3)).normalized(),
            speed=54.0, damage=p.base_damage * (0.40 * it['plasma_shrimp']),
            scale_val=0.28, proj_color=rgb(195, 95, 255),
            is_player=True, homing=True, can_proc=False
        )

    # Sticky Bomb
    if it['sticky_bomb'] > 0 and random.random() < min(0.75, 0.12 * it['sticky_bomb'] * luck_bonus):
        VisualFX(target_pos + Vec3(0, 1.0, 0), color.orange, 3.8, 0.3)
        if is_valid(target):
            target.take_damage(p.base_damage * (1.4 * it['sticky_bomb']))

    # Kjaro's Band & Runald's Band
    if (dmg >= p.base_damage * 1.8 or random.random() < 0.16 * luck_bonus):
        if it['kjaro_band'] > 0:
            VisualFX(target_pos + Vec3(0, 1.2, 0), rgb(255, 100, 20), 5.2, 0.38)
            for other in list(game.enemies):
                if is_valid(other) and not getattr(other, 'is_ally', False) and distance(Vec3(*other.position), target_pos) <= 4.8:
                    other.take_damage(p.base_damage * (1.5 * it['kjaro_band']))
        if it['runald_band'] > 0 and is_valid(target):
            VisualFX(target_pos + Vec3(0, 1.2, 0), color.cyan, 4.0, 0.35)
            target.slow_timer = 4.0
            target.take_damage(p.base_damage * (1.8 * it['runald_band']))

    # AtG Missile Mk. 1
    if it['atg_missile'] > 0 and random.random() < min(0.75, 0.12 * it['atg_missile'] * luck_bonus):
        m_pos = Vec3(*p.position) + Vec3(0, 2.2, 0)
        Projectile(
            pos=m_pos, direction=Vec3(0, 0.6, 0.8).normalized(),
            speed=48.0, damage=p.base_damage * (2.2 * it['atg_missile']),
            scale_val=0.36, proj_color=rgb(115, 255, 80),
            is_player=True, homing=True, can_proc=False
        )

    polylute_stacks = it.get('polylute', 0)
    if polylute_stacks > 0 and is_valid(target) and random.random() < min(0.85, 0.25 * luck_bonus):
        strikes = 2 + polylute_stacks
        VisualFX(target_pos + Vec3(0, 1.3, 0), rgb(205, 85, 255), 3.0, 0.28)
        LightningBeam(Vec3(*p.position) + Vec3(0, 1.5, 0), target_pos + Vec3(0, 1.2, 0), rgb(205, 85, 255), 0.24)
        target.take_damage(dmg * (0.45 * strikes))

    # Ukulele
    ukulele_stacks = it['ukulele']
    if ukulele_stacks > 0 and random.random() < min(0.85, 0.25 * luck_bonus):
        max_targets = 2 + ukulele_stacks * 2
        chain_radius = 13.0 + ukulele_stacks * 2.5
        chained = 0
        prev_pos = target_pos + Vec3(0, 1.2, 0)
        for other in list(game.enemies):
            if other is not target and is_valid(other) and not getattr(other, 'is_ally', False):
                other_pos = Vec3(*other.position) + Vec3(0, 1.2, 0)
                if distance(other_pos, prev_pos) <= chain_radius:
                    other.take_damage(dmg * 0.8)
                    LightningBeam(prev_pos, other_pos, color.magenta)
                    VisualFX(other_pos, color.magenta, 2.0, 0.25)
                    prev_pos = other_pos
                    chained += 1
                    if chained >= max_targets:
                        break

    


class Projectile(Entity):
    def __init__(
        self, pos, direction, speed, damage, scale_val, proj_color,
        is_player=True, aoe=0.0, pierce=False, bounces=0, homing=False,
        is_remote=False, lifesteal=0.0, can_proc=True, max_lifetime=3.4,
        heal_allies=0.0
    ):
        super().__init__(
            model='sphere',
            position=Vec3(*pos),
            scale=scale_val,
            color=proj_color,
            unlit=True
        )
        Entity(parent=self, model='diamond', scale=1.45, color=color.white, unlit=True)
        self.direction = Vec3(*direction).normalized()
        self.speed = speed
        self.damage = damage
        self.is_player = is_player
        self.is_remote = is_remote
        self.aoe = aoe
        self.pierce = pierce
        self.bounces = bounces
        self.homing = homing
        self.lifesteal = lifesteal
        self.can_proc = can_proc
        self.heal_allies = heal_allies
        self.hit_memory = set()
        self.lifetime = max_lifetime
        self.is_destroyed = False

    def safe_destroy(self):
        if not self.is_destroyed and not self.is_empty():
            self.is_destroyed = True
            destroy(self)

    def update(self):
        game = ctx.game
        if not game or not game.running or self.is_destroyed or self.is_empty():
            return

        my_pos = Vec3(*self.position)

        if self.homing and self.is_player and game.enemies:
            nearest = None
            best_d = 28.0
            for e in game.enemies:
                if is_valid(e) and not getattr(e, 'is_ally', False) and e not in self.hit_memory:
                    d = distance(my_pos, Vec3(*e.position) + Vec3(0, e.hit_height, 0))
                    if d < best_d:
                        best_d = d
                        nearest = e
            if nearest:
                desired = ((Vec3(*nearest.position) + Vec3(0, nearest.hit_height, 0)) - my_pos).normalized()
                self.direction = lerp(self.direction, desired, time.dt * 8.0).normalized()

        self.position += self.direction * self.speed * time.dt
        self.rotation_z += 360 * time.dt
        self.lifetime -= time.dt
        if self.lifetime <= 0 or self.y < -1:
            self.safe_destroy()
            return

        my_pos = Vec3(*self.position)

        if not self.pierce and game.is_inside_solid_obstacle(my_pos, 0.2):
            VisualFX(my_pos, self.color, 1.2, 0.18)
            self.safe_destroy()
            return

        if self.is_player:
            # Если снаряд лечит союзников (шприцемёт Медика TF2): проверяем клонов, турели, сетевых игроков и переманенных врагов
            if self.heal_allies > 0:
                allies_list = []
                if is_valid(game.player):
                    allies_list.extend(getattr(game.player, 'dummy_clones', []))
                    allies_list.extend(getattr(game.player, 'mindustry_turrets', []))
                allies_list.extend(game.remote_players.values())
                allies_list.extend([e for e in game.enemies if is_valid(e) and getattr(e, 'is_ally', False)])

                for al in allies_list:
                    if is_valid(al) and al not in self.hit_memory:
                        al_center = Vec3(*al.position) + Vec3(0, getattr(al, 'hit_height', 1.2), 0)
                        if distance(my_pos, al_center) <= getattr(al, 'hit_radius', 1.1) + 0.5:
                            self.hit_memory.add(al)
                            al.hp = min(float(al.max_hp), al.hp + self.heal_allies)
                            if hasattr(al, 'hp_bar') and not al.hp_bar.is_empty():
                                al.hp_bar.scale_x = clamp(al.hp / max(1.0, al.max_hp), 0.0, 1.0)
                            if hasattr(al, 'hp_fill') and not al.hp_fill.is_empty():
                                al.hp_fill.scale_x = clamp(al.hp / max(1.0, al.max_hp), 0.0, 1.0)
                            VisualFX(al_center, color.lime, 2.2, 0.25)
                            if is_valid(game.player):
                                game.player.heal_amount(self.heal_allies * 0.25)
                            self.safe_destroy()
                            return

            for e in list(game.enemies):
                if not is_valid(e) or getattr(e, 'is_ally', False) or e in self.hit_memory:
                    continue
                hit_center = Vec3(*e.position) + Vec3(0, e.hit_height, 0)
                if distance(my_pos, hit_center) <= e.hit_radius + self.scale_x * 0.4:
                    self.hit_memory.add(e)
                    if not self.is_remote:
                        self.on_hit_enemy(e, my_pos)
                    else:
                        VisualFX(my_pos, self.color, 1.3, 0.2)

                    if self.bounces > 0:
                        self.bounces -= 1
                        next_target = None
                        best_d = 18.0
                        for other in list(game.enemies):
                            if is_valid(other) and not getattr(other, 'is_ally', False) and other not in self.hit_memory:
                                d = distance(my_pos, Vec3(*other.position))
                                if d < best_d:
                                    best_d = d
                                    next_target = other
                        if next_target:
                            next_pos = Vec3(*next_target.position) + Vec3(0, next_target.hit_height, 0)
                            LightningBeam(my_pos, next_pos, self.color, 0.22)
                            self.direction = (next_pos - my_pos).normalized()
                            return
                        else:
                            self.safe_destroy()
                            return

                    if not self.pierce:
                        self.safe_destroy()
                        return
        else:
            if is_valid(game.player):
                p_center = Vec3(*game.player.position) + Vec3(0, 1.0, 0)
                if distance(my_pos, p_center) <= 1.05:
                    game.player.take_damage(self.damage)
                    VisualFX(my_pos, color.red, 1.6, 0.2)
                    self.safe_destroy()
                    return
            # Вражеские снаряды также могут попадать в переманенных монстров-союзников
            for al in list(game.enemies):
                if is_valid(al) and getattr(al, 'is_ally', False):
                    al_c = Vec3(*al.position) + Vec3(0, al.hit_height, 0)
                    if distance(my_pos, al_c) <= al.hit_radius:
                        al.take_damage(self.damage)
                        VisualFX(my_pos, color.orange, 1.4, 0.2)
                        self.safe_destroy()
                        return

    def on_hit_enemy(self, target, proj_pos):
        apply_player_hit_effects(
            target=target,
            hit_pos=proj_pos,
            base_dmg=self.damage,
            hit_color=self.color,
            aoe=self.aoe,
            lifesteal=self.lifesteal,
            can_proc=self.can_proc,
            
        )