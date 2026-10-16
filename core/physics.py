from ursina import *
import math


class PhysicsMixin:
    def get_surface_height(self, x, z, current_y):
        max_h = 0.0
        for ox, oz, rad, h in self.obstacles:
            if math.hypot(x - ox, z - oz) <= rad + 0.35:
                if current_y >= h - 0.55:
                    max_h = max(max_h, h)

        for px, pz, rad, top_y in getattr(self, 'sky_platforms', []):
            if math.hypot(x - px, z - pz) <= rad:
                if current_y >= top_y - 1.5:
                    max_h = max(max_h, top_y)
        return max_h

    def resolve_horizontal_collision(self, pos, radius=0.7, entity_y=0.0):
        rx, rz = pos.x, pos.z
        for ox, oz, o_rad, o_h in self.obstacles:
            if entity_y >= o_h - 0.35:
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
        for ox, oz, o_rad, o_h in self.obstacles:
            if 0.0 <= pos.y <= o_h:
                if math.hypot(pos.x - ox, pos.z - oz) <= (o_rad + radius):
                    return True
        return False