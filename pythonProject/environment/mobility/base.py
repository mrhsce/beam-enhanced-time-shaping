import random
from abc import ABC, abstractmethod

from pythonProject.environment.coordinates import Coordinates


class MobilityBase(ABC):
    """
    Abstract base for all mobility models.
    All subclasses must implement move().
    """

    def __init__(self, x_dim=120, y_dim=80, z_dim=10, coordinates=None, logic_name="Base"):
        self.x_dim = x_dim
        self.y_dim = y_dim
        self.z_dim = z_dim
        self.logic = logic_name

        if coordinates is None:
            self.coordinates = Coordinates(
                random.uniform(0, x_dim),
                random.uniform(0, y_dim),
                random.uniform(0, z_dim)
            )
        else:
            self.coordinates = coordinates

    # --------- interface methods you want to keep ----------

    def get_location(self, rounded=False):
        """Return current location (optionally rounded to ints)."""
        if rounded:
            return Coordinates(round(self.coordinates.x),
                               round(self.coordinates.y),
                               round(self.coordinates.z))
        return self.coordinates.copy()

    def set_coordinates(self, coordinates):
        """Set current coordinates."""
        self.coordinates = coordinates
        return self.coordinates

    def set_logic(self, logic):
        """
        Optional: subclasses rarely need this.
        The main Mobility wrapper will switch the implementation.
        """
        self.logic = logic

    @abstractmethod
    def move(self, time, rounded=False):
        """Advance the mobility model by `time` seconds."""
        raise NotImplementedError
