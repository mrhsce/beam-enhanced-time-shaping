from .random_mobility import RandomMobility
from .rsd_mobility import RSDMobility
from .lane_graph_mobility import LaneGraphMobility


class Mobility:
    """
    Public-facing class that preserves your original interface:
    - get_location
    - set_coordinates
    - set_logic
    - move

    Internally delegates to a concrete mobility implementation.
    """

    def __init__(self, x_dim=120, y_dim=80, z_dim=10,
                 coordinates=None, logic="lanegraph", **kwargs):
        self.x_dim = x_dim
        self.y_dim = y_dim
        self.z_dim = z_dim
        self._impl = None

        self.set_logic(logic, coordinates=coordinates, **kwargs)

    def get_location(self, rounded=False):
        return self._impl.get_location(rounded=rounded)

    def set_coordinates(self, coordinates):
        return self._impl.set_coordinates(coordinates)

    def set_logic(self, logic, coordinates=None, **kwargs):
        logic = (logic or "RSD").strip().lower()

        # Preserve current coordinates if caller didn't provide them
        if coordinates is None and self._impl is not None:
            coordinates = self._impl.coordinates

        if logic == "random":
            self._impl = RandomMobility(self.x_dim, self.y_dim, self.z_dim, coordinates)
        elif logic == "rsd":
            self._impl = RSDMobility(self.x_dim, self.y_dim, self.z_dim, coordinates)
        elif logic in ("lanegraph", "lane", "graph"):
            self._impl = LaneGraphMobility(self.x_dim, self.y_dim, self.z_dim, coordinates, **kwargs)
        else:
            raise ValueError(f"Unknown mobility logic: {logic}")

    def move(self, time, rounded=False):
        return self._impl.move(time, rounded=rounded)
