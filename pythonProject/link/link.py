from pythonProject.link.queue.frame_queue import FrameQueue
from pythonProject.link.queue.future_queue import FutureQueue


class Link:
    counter = 0  # Class-level counter to track link IDs
    def __init__(self, source, destination, link_type):
        """
        Initialize a Link instance.

        :param node1: The source node of the link.
        :param node1: The destination node of the link.
        :param link_type: The type of the link (wired or wireless).
        :param latency: The latency of the link in milliseconds.
        :param throughput: The throughput of the link in Mbps.
        """
        self.node1 = source
        self.node2 = destination
        self.link_type = link_type
        self.beamweight = 0
        self.bandwidth = 0

        # Generate a unique name for the link
        Link.counter += 1
        self.name = f"Link-{Link.counter}"

        # Queues for frames
        self.tsn_queue = FrameQueue(queue_type="TST")
        self.bet_queue = FrameQueue(queue_type="BET")

        # Future queue for scheduling traffic
        self.future_queue = FutureQueue()

    def __repr__(self):
        """
        Return a string representation of the link.

        :return: A string representation showing the link's details and its queues.
        """
        return (f"Link(Name: {self.name}, Source: {self.node1}, Destination: {self.node2}, "
                f"Beamweight: {self.beamweight}, Bandwidth: {self.bandwidth}, Type: {self.link_type}, "
                f"TSN Queue: {len(self.tsn_queue)} frames, BET Queue: {len(self.bet_queue)} frames)")