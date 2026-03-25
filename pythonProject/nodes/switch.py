from pythonProject.nodes.node import Node


class Switch(Node):
    def __init__(self, coordinates):
        """
        Switch node.

        :param coordinates: Coordinates of the Switch.
        """
        super().__init__(coordinates, node_type="Switch")