import random
import math
from .base import MobilityBase
from ..coordinates import Coordinates

# Static thresholds (can be easily adjusted)
MIN_STATIONS = 1  # Allow for stationary robots (at least 1 station)
MAX_STATIONS = 5
MIN_RADIUS = 5
MAX_RADIUS = 20
MIN_TIME_AT_STATION = 1
MAX_TIME_AT_STATION = 5
MIN_SPEED = 0.5
MAX_SPEED = 1


class LaneGraphMobility(MobilityBase):
    """
    LaneGraphMobility simulates a robot's movement through a network of stations.
    The stations are located within a specified radius from an initial starting point.
    The robot randomly picks stations to visit, spends random time at each,
    and then moves to the next station. The robot can also remain stationary at a single station.
    """

    def __init__(self, x_dim=120, y_dim=80, z_dim=10, coordinates=None):
        super().__init__(x_dim, y_dim, z_dim, coordinates, logic_name="LaneGraph")

        self.speed = random.uniform(MIN_SPEED, MAX_SPEED)
        self.current_station = None
        self.time_spent = 0.0  # seconds remaining at current station
        self.nodes = {}
        self.edges = {}

        # Movement target state
        self.target_station = None

        # Initialize stations and infer if robot is stationary
        self._initialize_stations()

    def _initialize_stations(self):
        """
        Initializes the stations and their positions within the radius.
        Randomly selects a number of stations within the threshold radius.
        """
        # Keep exactly as you requested:
        num_stations = random.randint(MIN_STATIONS, MAX_STATIONS + 1)

        radius = random.uniform(MIN_RADIUS, MAX_RADIUS)
        self.stations = []

        # Generate stations within a radius of the initial position
        for _ in range(num_stations):
            while True:  # Keep trying until we get valid coordinates within bounds
                angle = random.uniform(0, 2 * math.pi)
                x = self.coordinates.x + radius * math.cos(angle)
                y = self.coordinates.y + radius * math.sin(angle)

                # Accept only in-bounds points (no clipping)
                if 0 <= x <= self.x_dim and 0 <= y <= self.y_dim:
                    z = self.coordinates.z  # Keep z-level same (floor)
                    self.stations.append(Coordinates(x, y, z))
                    break

        # Start at the first station
        self.current_station = self.stations[0]
        self.coordinates = Coordinates(self.current_station.x, self.current_station.y, self.current_station.z)

        self.time_spent = random.uniform(MIN_TIME_AT_STATION, MAX_TIME_AT_STATION)

        # If only one station, the robot stays at that station indefinitely
        self.stationary = (len(self.stations) == 1)

        # No target yet
        self.target_station = None

    def _select_next_station(self):
        """Select next station uniformly at random among stations != current_station."""
        remaining = [s for s in self.stations if s is not self.current_station]
        return random.choice(remaining) if remaining else None

    def _path_to_station(self, start, end):
        """
        Placeholder for graph/path planning.
        For now: direct line segment.
        """
        return [start, end]

    def move(self, time, rounded=False):
        """
        Move the robot:
        - If stationary: always stays at its only station.
        - If dwelling: counts down time_spent.
        - Else: move toward a chosen next station using current coordinates (not station coords).
        """
        if self.stationary:
            return self.get_location(rounded)

        # dwell time at current station
        if self.time_spent > 0:
            self.time_spent = max(0.0, self.time_spent - time)
            return self.get_location(rounded)

        # choose a target if we don't have one
        if self.target_station is None:
            self.target_station = self._select_next_station()
            if self.target_station is None:
                # should not happen if len(stations)>1, but keep safe
                return self.get_location(rounded)

        # (optional placeholder call; not used yet)
        _ = self._path_to_station(self.current_station, self.target_station)

        # Move toward target using CURRENT position (this fixes the "move once then stop" issue)
        dx = self.target_station.x - self.coordinates.x
        dy = self.target_station.y - self.coordinates.y
        dist = math.hypot(dx, dy)

        if dist < 1e-9:
            # arrived (or extremely close)
            self.coordinates = Coordinates(self.target_station.x, self.target_station.y, self.coordinates.z)
            self.current_station = self.target_station
            self.target_station = None
            self.time_spent = random.uniform(MIN_TIME_AT_STATION, MAX_TIME_AT_STATION)
            return self.get_location(rounded)

        travel = self.speed * time  # distance you can move this step

        if travel >= dist:
            # arrive this step
            self.coordinates = Coordinates(self.target_station.x, self.target_station.y, self.coordinates.z)
            self.current_station = self.target_station
            self.target_station = None
            self.time_spent = random.uniform(MIN_TIME_AT_STATION, MAX_TIME_AT_STATION)
            return self.get_location(rounded)

        # partial move
        ratio = travel / dist
        new_x = self.coordinates.x + ratio * dx
        new_y = self.coordinates.y + ratio * dy

        # keep in bounds (should already be, but safe)
        if new_x < 0.0:
            new_x = 0.0
        elif new_x > self.x_dim:
            new_x = float(self.x_dim)

        if new_y < 0.0:
            new_y = 0.0
        elif new_y > self.y_dim:
            new_y = float(self.y_dim)

        self.coordinates = Coordinates(new_x, new_y, self.coordinates.z)
        return self.get_location(rounded)
