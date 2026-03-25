from pythonProject.traffic.frame import Frame


class TST_Frame(Frame):
    def __init__(self, payload_size, source_node, destination_node, creation_time, stream, arrival_time=None, delay_tolerance=None):
        """
        Initialize a TST_Frame instance. Always has a type of "TST".

        :param payload_size: The size of the payload in bytes.
        :param source_node: The source node of the frame.
        :param destination_node: The destination node of the frame.
        :param creation_time: The time the frame is created.
        :param stream: The stream this frame belongs to.
        :param arrival_time: The time the frame arrives at its destination. Defaults to None.
        :param delay_tolerance: The maximum acceptable delay for the frame. Defaults to None.
        """
        super().__init__(frame_type="TST", payload_size=payload_size, source_node=source_node, destination_node=destination_node, creation_time=creation_time, arrival_time=arrival_time, delay_tolerance=delay_tolerance)
        self.stream = stream

    def __repr__(self):
        """Return a string representation of the TST frame."""
        return (f"TST_Frame(Payload Size: {self.payload_size} bytes, Source: {self.source_node}, "
                f"Destination: {self.destination_node}, Creation Time: {self.creation_time}, "
                f"Arrival Time: {self.arrival_time}, Delay Tolerance: {self.delay_tolerance}, Stream: {self.stream})")

    def to_dict(self):
        """
        Convert the TST frame to a dictionary representation.

        :return: A dictionary containing TST frame details.
        """
        frame_dict = super().to_dict()
        frame_dict["stream"] = self.stream
        return frame_dict