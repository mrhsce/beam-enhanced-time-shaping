class Node:
    counters = {"UE": 0, "BS": 0, "Switch": 0}  # Class-level counters for each type
    def __init__(self, coordinates, node_type):
        """
        Base class for all node types.

        :param coordinates: Coordinates of the node.
        :param node_type: Type of the node (e.g., "UE", "BS", "Switch").
        """
        self.coordinates = coordinates
        self.node_type = node_type

        # Assign a unique ID based on the node type
        if node_type not in Node.counters:
            raise ValueError(f"Unknown node type: {node_type}")
        self.id = Node.counters[node_type]
        Node.counters[node_type] += 1

    def set_location(self, coordinates):
        """
        Update the node's coordinates.

        :param coordinates: New coordinates to set.
        """
        self.coordinates = coordinates

    def __str__(self):
        """
        Return a string representation of the node.
        """
        return f"{self.node_type} {self.id}"

    def __repr__(self):
        """
        Return a detailed string representation for debugging.
        """
        return f"{self.node_type}(id={self.id}, coordinates={self.coordinates})"