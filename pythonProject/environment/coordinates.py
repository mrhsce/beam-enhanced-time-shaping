import math


class Coordinates:
    def __init__(self, x, y, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def calculate_distance(self, other_coordinates):
        """Euclidean distance to another set of coordinates."""
        return math.sqrt(
            (self.x - other_coordinates.x) ** 2 +
            (self.y - other_coordinates.y) ** 2 +
            (self.z - other_coordinates.z) ** 2
        )

    def calculate_manhattan_distance(self, other_coordinates, extended_percentage=0):
        """
        Manhattan distance to another set of coordinates,
        optionally extended by a percentage.
        """
        distance = (
            abs(self.x - other_coordinates.x) +
            abs(self.y - other_coordinates.y) +
            abs(self.z - other_coordinates.z)
        )
        if extended_percentage > 0:
            distance *= (1 + extended_percentage / 100.0)
        return distance

    def copy(self):
        return Coordinates(self.x, self.y, self.z)

    def __repr__(self):
        return f"Coordinates(x={self.x:.3f}, y={self.y:.3f}, z={self.z:.3f})"
