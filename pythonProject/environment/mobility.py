import random
import math


class Coordinates:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def calculate_distance(self, other_coordinates):
        """Calculate the Euclidean distance to another set of coordinates."""
        distance = math.sqrt((self.x - other_coordinates.x) ** 2 +
                             (self.y - other_coordinates.y) ** 2 +
                             (self.z - other_coordinates.z) ** 2)
        return distance

    def calculate_manhattan_distance(self, other_coordinates, extended_percentage=0):
        """
        Calculate the Manhattan distance to another set of coordinates,
        with an optional extended percentage.

        Args:
            other_coordinates (Coordinates): The other coordinates.
            extended_percentage (float): Percentage to extend the distance (default is 0).

        Returns:
            float: The adjusted Manhattan distance.
        """
        distance = (abs(self.x - other_coordinates.x) +
                    abs(self.y - other_coordinates.y) +
                    abs(self.z - other_coordinates.z))

        # Apply the extended percentage if it's greater than 0
        if extended_percentage > 0:
            distance *= (1 + extended_percentage / 100)

        return distance


class Mobility:
    def __init__(self, x_dim=120, y_dim=80, z_dim=10, coordinates=None):
        self.x_dim, self.y_dim, self.z_dim = x_dim, y_dim, z_dim
        self.theta = 0  # Movement angle in xy-plane
        self.phi = 0  # Elevation angle
        self.speed = 0
        self.move_on = 0
        self.logic = 'RSD'
        if coordinates is None:
            self.coordinates = Coordinates(random.randint(0, x_dim), random.randint(0, y_dim), random.randint(0, z_dim))
        else:
            self.coordinates = coordinates

    def get_location(self, rounded=False):
        return Coordinates(round(self.coordinates.x), round(self.coordinates.y),
                           round(self.coordinates.z)) if rounded else Coordinates(self.coordinates.x,
                                                                                  self.coordinates.y,
                                                                                  self.coordinates.z)

    def set_coordinates(self, coordinates):
        self.coordinates = coordinates
        return self.coordinates

    def set_logic(self, logic):
        self.logic = logic

    def move(self, time, rounded=False):
        coordinates, theta, phi, speed, move_on = self.coordinates, self.theta, self.phi, self.speed, self.move_on

        if self.logic == 'Random':
            x, y = self.random()
        if self.logic == 'RSD':
            while True:
                coordinates, theta, phi, speed, move_on = self.random_speed_and_direction_with_stop_2d(time)
                if self.x_dim > coordinates.x >= 0 and self.y_dim > coordinates.y >= 0 and self.z_dim > coordinates.z >= 0:
                    break
                self.move_on = 0

        self.coordinates, self.theta, self.phi, self.speed, self.move_on = coordinates, theta, phi, speed, move_on
        return Coordinates(round(self.coordinates.x), round(self.coordinates.y),
                           round(self.coordinates.z)) if rounded else Coordinates(self.coordinates.x,
                                                                                  self.coordinates.y,
                                                                                  self.coordinates.z)

    def random_speed_and_direction_with_stop(self, time):
        if self.move_on == 0:
            self.move_on = random.randint(int(0.1 / time), int(0.5 / time))
            self.speed = random.uniform(0, 1.38)
            theta_change = random.uniform(-math.pi, math.pi)
            self.theta = (self.theta + theta_change) % (2 * math.pi)
            phi_change = random.uniform(-math.pi / 2, math.pi / 2)
            self.phi = (self.phi + phi_change) % math.pi

        dx = self.speed * time * math.cos(self.theta) * math.sin(self.phi)
        dy = self.speed * time * math.sin(self.theta) * math.sin(self.phi)
        dz = self.speed * time * math.cos(self.phi)
        new_x = self.coordinates.x + dx
        new_y = self.coordinates.y + dy
        new_z = self.coordinates.z  #+ dz

        self.move_on -= 1

        return Coordinates(new_x, new_y, new_z), self.theta, self.phi, self.speed, self.move_on

    def random_speed_and_direction_with_stop_2d(self, time):
        if self.move_on == 0:
            self.move_on = random.randint(int(1 / time), int(5 / time))
            self.speed = random.uniform(0, 1.38)
            theta_change = random.uniform(-math.pi / 2, math.pi / 2)
            self.theta = (self.theta + theta_change) % (2 * math.pi)

        dx = self.speed * time * math.cos(self.theta)
        dy = self.speed * time * math.sin(self.theta)
        new_x = self.coordinates.x + dx
        new_y = self.coordinates.y + dy
        new_z = self.coordinates.z

        self.move_on -= 1

        return Coordinates(new_x, new_y, new_z), self.theta, 0, self.speed, self.move_on
