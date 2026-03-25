from pythonProject.traffic.tst_frame import TST_Frame


class Stream:
    def __init__(self, name, periodic_cycle, frame_payload, latency_tolerance, jitter_tolerance, reliability, source, destination, start_time=0):
        """
        Initialize a Stream instance with reliability parameter.

        :param name: The name of the stream.
        :param periodic_cycle: The periodic cycle of the stream in seconds.
        :param frame_payload: The payload size for each frame in bits.
        :param latency_tolerance: The maximum acceptable latency in seconds.
        :param jitter_tolerance: The maximum acceptable jitter in seconds.
        :param source: The source node of the stream.
        :param destination: The destination node of the stream.
        :param reliability: The percentage of frames that should meet their target within a time window.
        :param start_time: The time when the stream starts (default is 0).
        """
        self.name = name
        self.periodic_cycle = periodic_cycle
        self.frame_payload = frame_payload
        self.latency_tolerance = latency_tolerance
        self.jitter_tolerance = jitter_tolerance
        self.source = source
        self.destination = destination
        self.reliability = reliability  # Reliability as a percentage
        self.next_creation_time = start_time  # Tracks the next frame creation time
        self.created_frames = []  # List to store all created frames, only for visualization purposes

    def get_active_wireless_links(self, environment, coherence_start, coherence_duration, channel_sensing_time):
        """
        Retrieve all active frames of this stream from all links' future queues
        within the given coherence interval.

        :param environment: The environment containing the connection_manager and its links.
        :param coherence_start: Start time of the coherence interval.
        :param coherence_duration: Duration of the coherence interval.
        :param channel_sensing_time: Channel sensing time.
        :return: List of active frames belonging to this stream.
        """
        active_links = []
        coherence_end = coherence_start + coherence_duration

        for link in environment.connection_manager.links:
            if link.link_type == 'wireless':
                frames = link.future_queue.get_active_frame_of_stream(self, coherence_start, coherence_duration, channel_sensing_time)
                if len(frames) > 0:
                    active_links.append(link)
        return active_links

    def get_active_frames(self, environment, coherence_start, coherence_duration, channel_sensing_time):
        """
        Retrieve all active frames of this stream from all links' future queues
        within the given coherence interval.

        :param environment: The environment containing the connection_manager and its links.
        :param coherence_start: Start time of the coherence interval.
        :param coherence_duration: Duration of the coherence interval.
        :param channel_sensing_time: Channel sensing time.
        :return: List of active frames belonging to this stream.
        """
        active_frames = []
        for link in environment.connection_manager.links:
            if link.link_type == 'wireless':
                frames = link.future_queue.get_active_frame_of_stream(self, coherence_start, coherence_duration, channel_sensing_time)
                if len(frames) > 0:
                    active_frames += frames
        return active_frames

    def has_active_wireless_frame(self, environment, coherence_start, coherence_duration, channel_sensing_time):
        """
        Check if this stream has any active frame on any link before the coherence_end.
        """
        for link in environment.connection_manager.links:
            if link.link_type == 'wireless' and link.future_queue.has_active_frame_of_stream(self, coherence_start, coherence_duration, channel_sensing_time):
                return True
        return False

    def create_tst_frame(self, creation_time):
        """
        Create a TST_Frame based on the given creation time.

        :param creation_time: The time at which the frame is created.
        :return: A TST_Frame instance.
        """
        self.next_creation_time = creation_time + self.periodic_cycle  # Update the next creation time
        frame = TST_Frame(payload_size=self.frame_payload,
                          source_node=self.source,
                          destination_node=self.destination,
                          creation_time=creation_time,
                          stream=self.name,
                          delay_tolerance=self.latency_tolerance)
        self.created_frames.append(frame)  # Keep track of the created frame
        return frame

    def create_tst_frames_until(self, end_time):
        """
        Create TST_Frame instances until a specified end time.

        :param end_time: The end time until which TST_Frame instances will be created.
        :return: A list of TST_Frame instances.
        """
        frames = []
        current_time = self.next_creation_time

        while current_time < end_time:
            frames.append(self.create_tst_frame(creation_time=current_time))
            current_time = self.next_creation_time

        return frames

    def get_tst_frame_among(self, start_time, end_time):
        """
        Retrieve frames created within a specified time range.

        :param start_time: The start time of the range.
        :param end_time: The end time of the range.
        :return: A list of TST_Frame instances created within the time range.
        """
        return [frame for frame in self.created_frames if start_time <= frame.creation_time <= end_time]


    def __repr__(self):
        """Return a string representation of the stream."""
        return (f"Stream(Name: {self.name}, Source: {self.source}, Destination: {self.destination}, "
                f"Periodic Cycle: {self.periodic_cycle}s, "
                f"Payload: {self.frame_payload} bytes, Latency Tolerance: {self.latency_tolerance}s, "
                f"Jitter Tolerance: {self.jitter_tolerance}s, Reliability: {self.reliability}%, "
                f"Next Creation Time: {self.next_creation_time})")
