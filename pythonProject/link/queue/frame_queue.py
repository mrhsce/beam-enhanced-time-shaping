class FrameQueue:
    def __init__(self, queue_type):
        """
        Initialize a FrameQueue instance.
        This class manages a queue of frames with basic functionalities.

        :param queue_type: The type of frames the queue will manage (e.g., "TST" or "BET").
        """
        self.frames = []  # List to hold frames
        self.queue_type = queue_type

    def add_frame(self, frame):
        """
        Add a frame to the queue.

        :param frame: The frame to add.
        """
        self.frames.append(frame)

    def remove_frame(self, frame):
        """
        Remove a specific frame from the queue if it exists.

        :param frame: The frame to remove.
        """
        if frame in self.frames:
            self.frames.remove(frame)

    def clear(self):
        """
        Clear all frames from the queue.
        """
        self.frames.clear()

    def __len__(self):
        """
        Get the total payload of all frames in the queue.

        :return: The total payload of all frames in the queue.
        """
        return sum(frame.payload_size for frame in self.frames)

    def get_length(self):
        """
        Get the total payload of all frames in the queue.

        :return: The total payload of all frames in the queue.
        """
        return sum(frame.payload_size for frame in self.frames)


    def __repr__(self):
        """
        Return a string representation of the queue.

        :return: A string showing the queue type, the number of frames, and their details.
        """
        return f"FrameQueue(Type: {self.queue_type}, Frames: {len(self.frames)})"