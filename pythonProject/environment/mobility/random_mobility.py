import random
import math
from .base import MobilityBase
from ..coordinates import Coordinates


class RandomMobility(MobilityBase):
    """
    Simple random waypoint-like mobility in the box [0,x_dim]x[0,y_dim].
    - Choose a random target point
    - Move with a random speed until you reach it
    - Then pick a new target
    """

    def __init__(self, x_dim=120, y_dim=80, z_dim=10, coordinates=None):
        super().__init__(x_dim, y_dim, z_dim, coordinates, logic_name="Random")
        self.speed = 0.0
        self.target = self._sample_new_target()
        self.min_speed = 0.1
        self.max_speed = 1.38  # same upper bound as your RSD model

        # start moving right away
        self.speed = self._sample_new_speed()

    def _sample_new_target(self):
        return Coordinates(
            random.uniform(0, self.x_dim),
            random.uniform(0, self.y_dim),
            self.coordinates.z  # keep z fixed (floor)
        )

    def _sample_new_speed(self):
        return random.uniform(self.min_speed, self.max_speed)

    def move(self, time, rounded=False):
        # If we are "at" the target (or extremely close), pick a new one
        if self.coordinates.calculate_distance(self.target) < 1e-6:
            self.target = self._sample_new_target()
            self.speed = self._sample_new_speed()

        # Direction from current position to target
        dx = self.target.x - self.coordinates.x
        dy = self.target.y - self.coordinates.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < 1e-9:
            return self.get_location(rounded=rounded)

        travel = self.speed * time

        if travel >= dist:
            new_x, new_y = self.target.x, self.target.y
        else:
            ratio = travel / dist
            new_x = self.coordinates.x + ratio * dx
            new_y = self.coordinates.y + ratio * dy

        # Keep inside bounds (clip)
        new_x = min(max(new_x, 0.0), self.x_dim)
        new_y = min(max(new_y, 0.0), self.y_dim)

        self.coordinates = Coordinates(new_x, new_y, self.coordinates.z)
        return self.get_location(rounded=rounded)
