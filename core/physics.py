from ursina import *
import math


class PhysicsMixin:
    def get_surface_height(self, x, z, current_y, prev_y=None):
        check_y = max(current_y, prev_y) if prev_y is not None else current_y
        max_h = 0.0

        for obs in self.obstacles:
            ox, oz, rad, top_h = obs[0], obs[1], obs[2], obs[3]
            if math.hypot(x - ox, z - oz) <= rad + 0.35:
                if check_y >= top_h - 1.2:
                    max_h = max(max_h, top_h)

        for plat in getattr(self, 'sky_platforms', []):
            px, pz, rad, top_y = plat[0], plat[1], plat[2], plat[3]
            if math.hypot(x - px, z - pz) <= rad:
                # Увеличенный допуск захвата платформы исключает проваливание при падении
                if check_y >= top_y - 4.5:
                    max_h = max(max_h, top_y)

        # Железная страховка пола Небесного Колизея на Луне (Y = 120.0, R = 56.5)
        if getattr(self, 'special_mode', None) == 'moon' and check_y >= 108.0:
            if math.hypot(x, z) <= 56.5:
                max_h = max(max_h, 120.0)

        return max_h

    def resolve_horizontal_collision(self, pos, radius=0.7, entity_y=0.0):
        rx, rz = pos.x, pos.z
        for obs in self.obstacles:
            ox, oz, o_rad, o_h = obs[0], obs[1], obs[2], obs[3]
            base_y = obs[4] if len(obs) > 4 else 0.0
            if entity_y >= o_h - 0.35 or entity_y + 1.8 < base_y:
                continue
            dx = rx - ox
            dz = rz - oz
            dist = math.hypot(dx, dz)
            min_d = radius + o_rad
            if dist < min_d:
                if dist < 0.001:
                    rx += min_d
                else:
                    push = (min_d - dist) / dist
                    rx += dx * push
                    rz += dz * push
        return Vec3(rx, pos.y, rz)

    def is_inside_solid_obstacle(self, pos, radius=0.2):
        for obs in self.obstacles:
            ox, oz, o_rad, o_h = obs[0], obs[1], obs[2], obs[3]
            base_y = obs[4] if len(obs) > 4 else 0.0
            if base_y <= pos.y <= o_h:
                if math.hypot(pos.x - ox, pos.z - oz) <= (o_rad + radius):
                    return True
        return False