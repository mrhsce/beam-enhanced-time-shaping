from pythonProject.environment.mobility import Mobility
from pythonProject.nodes.node import Node


class UE(Node):
    def __init__(self, coordinates, mobility_logic="lanegraph"):
        """
        User Equipment (UE) node.

        :param coordinates: Initial coordinates of the UE.
        """
        super().__init__(coordinates, node_type="UE")
        self.mobility = Mobility(coordinates=coordinates, logic=mobility_logic)

    def move(self, time):
        """
        Move the UE based on its mobility model.

        :param time: Time increment for the movement, the unit is second.
        """
        self.coordinates = self.mobility.move(time)

    def set_location(self, coordinates):
        """
        Override the set_location method to also update the mobility model.
        """
        super().set_location(coordinates)
        self.mobility.set_coordinates(coordinates)