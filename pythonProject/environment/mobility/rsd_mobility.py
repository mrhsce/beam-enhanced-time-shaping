import random
import math
from .base import MobilityBase
from ..coordinates import Coordinates


class RSDMobility(MobilityBase):
    """
    Random Speed and Direction with 'run length' (move_on) in 2D.
    Logic ported from your original class.
    """

    def __init__(self, x_dim=120, y_dim=80, z_dim=10, coordinates=None):
        super().__init__(x_dim, y_dim, z_dim, coordinates, logic_name="RSD")
        self.theta = 0.0  # Movement angle in xy-plane
        self.phi = 0.0    # Elevation angle (unused in 2D)
        self.speed = 0.0
        self.move_on = 0

    def random_speed_and_direction_with_stop_2d(self, time):
        if self.move_on <= 0:
            # Original: move_on in [1/time, 5/time]
            # Guard against invalid randint bounds for large time steps.
            low = max(1, int(1 / time)) if time > 0 else 1
            high = max(low, int(5 / time)) if time > 0 else low + 1

            self.move_on = random.randint(low, high)
            self.speed = random.uniform(0.0, 1.38)

            theta_change = random.uniform(-math.pi / 2.0, math.pi / 2.0)
            self.theta = (self.theta + theta_change) % (2.0 * math.pi)

        dx = self.speed * time * math.cos(self.theta)
        dy = self.speed * time * math.sin(self.theta)

        new_x = self.coordinates.x + dx
        new_y = self.coordinates.y + dy
        new_z = self.coordinates.z  # keep on floor

        self.move_on -= 1
        return Coordinates(new_x, new_y, new_z), self.theta, 0.0, self.speed, self.move_on

    def move(self, time, rounded=False):
        while True:
            coordinates, theta, phi, speed, move_on = \
                self.random_speed_and_direction_with_stop_2d(time)

            if (0.0 <= coordinates.x <= self.x_dim and
                    0.0 <= coordinates.y <= self.y_dim and
                    0.0 <= coordinates.z <= self.z_dim):
                break

            # Out of bounds → force new direction
            self.move_on = 0

        self.coordinates = coordinates
        self.theta = theta
        self.phi = phi
        self.speed = speed
        self.move_on = move_on

        return self.get_location(rounded=rounded)
