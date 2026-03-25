class Frame:
    def __init__(self, frame_type, payload_size, source_node, destination_node, creation_time, arrival_time=None, delay_tolerance=None):
        """
        Initialize a Frame instance.

        :param frame_type: The type of frame (TST or BET).
        :param payload_size: The size of the payload in bytes.
        :param source_node: The source node of the frame.
        :param destination_node: The destination node of the frame.
        :param creation_time: The time the frame is created.
        :param arrival_time: The time the frame arrives at its destination. Defaults to None.
        :param delay_tolerance: The maximum acceptable delay for the frame. Defaults to None.
        """
        self.frame_type = frame_type
        self.payload_size = payload_size
        self.source_node = source_node
        self.destination_node = destination_node
        self.creation_time = creation_time
        self.arrival_time = arrival_time
        self.delay_tolerance = delay_tolerance

    def __repr__(self):
        """Return a string representation of the frame."""
        return (f"Frame(Type: {self.frame_type}, Payload Size: {self.payload_size} bytes, "
                f"Source: {self.source_node}, Destination: {self.destination_node}, "
                f"Creation Time: {self.creation_time}, Arrival Time: {self.arrival_time}, "
                f"Delay Tolerance: {self.delay_tolerance})")

    def to_dict(self):
        """
        Convert the frame to a dictionary representation.

        :return: A dictionary containing frame details.
        """
        return {
            "frame_type": self.frame_type,
            "payload_size": self.payload_size,
            "source_node": self.source_node,
            "destination_node": self.destination_node,
            "creation_time": self.creation_time,
            "arrival_time": self.arrival_time,
            "delay_tolerance": self.delay_tolerance,
        }

    def update_arrival_time(self, new_arrival_time):
        """
        Update the arrival time of the frame.

        :param new_arrival_time: The new arrival time to set.
        """
        self.arrival_time = new_arrival_time

    def calculate_delay(self):
        """
        Calculate the delay experienced by the frame.

        :return: The delay in seconds or None if arrival_time is not set.
        """
        if self.arrival_time is not None:
            return self.arrival_time - self.creation_time
        return None