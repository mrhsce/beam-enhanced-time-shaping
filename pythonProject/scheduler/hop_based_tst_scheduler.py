class HopBasedTstScheduler:
    def __init__(self, connection_manager, streams, wired_link_constant_delay=0.04, wired_link_coefficient=1,
                 wireless_link_coefficient=5):
        """
        Initialize the HopBasedTstScheduler with a connection manager and a list of TST streams.

        :param connection_manager: An instance of ConnectionManager to find paths between nodes.
        :param streams: A list of Stream objects (TST streams) to be scheduled.
        """
        self.connection_manager = connection_manager
        self.streams = streams
        self.wired_link_coefficient = wired_link_coefficient
        self.wireless_link_coefficient = wireless_link_coefficient
        self.wired_link_constant_delay = wired_link_constant_delay

        # A dict to store scheduling details like:
        # { frame_object: [ (link, arrival_time, departure_time), ... ], ... }

    def get_stream_paths(self, stream):
        # Find the path between the source and destination nodes for the given stream.
        return self.connection_manager.find_path(
            start_node=stream.source,
            end_node=stream.destination
        )

    def schedule_until(self, end_time, scheduler_strategy="static_coefficients", links_bitrate=None):
        """
        Schedule TST frames for all known streams until the given end_time based on different strategies.

        :param end_time: Time duration (seconds) until which new frames will be generated.
        :param scheduler_strategy:
            ["static_coefficients", "static_coefficients_constant_wired_delay",
            "channel_based_coefficients_constant_wired_delay"]
        :param links_bitrate: Dictionary mapping each wireless link to its bitrate (used in channel-based strategy).
        :raises SchedulingError: If any condition required for scheduling is not met.
        """

        for stream in self.streams:
            path_links = self.get_stream_paths(stream)
            if not path_links:
                raise ValueError(f"No path found for stream='{stream.name}'. Skipping scheduling.")

            if stream.latency_tolerance is None or stream.latency_tolerance <= 0:
                raise ValueError(f"Stream='{stream.name}' has no valid latency_tolerance. Skipping.")

            # Determine wired and wireless links
            wired_links = [link for link in path_links if link.link_type == "wired"]
            wireless_links = [link for link in path_links if link.link_type == "wireless"]
            num_wired = len(wired_links)
            num_wireless = len(wireless_links)

            if scheduler_strategy == "static_coefficients":
                # Use predefined coefficients
                link_coefficients = [
                    self.wired_link_coefficient if link.link_type == "wired" else self.wireless_link_coefficient
                    for link in path_links
                ]
                total_coefficient = sum(link_coefficients)

                if total_coefficient == 0:
                    raise ValueError(f"Stream='{stream.name}' has zero total coefficient. Skipping.")

                link_time_allocations = [
                    stream.latency_tolerance * (coeff / total_coefficient)
                    for coeff in link_coefficients
                ]

            elif scheduler_strategy == "static_coefficients_constant_wired_delay":
                # Subtract fixed delay from latency tolerance
                remaining_latency = stream.latency_tolerance - (num_wired * self.wired_link_constant_delay)

                if remaining_latency <= 0:
                    raise ValueError(
                        f"Stream='{stream.name}' has insufficient latency after wired delay subtraction.")

                if num_wireless > 0:
                    wireless_link_time = remaining_latency / num_wireless
                else:
                    wireless_link_time = 0  # No wireless links to distribute time

                link_time_allocations = [
                    self.wired_link_constant_delay if link.link_type == "wired" else wireless_link_time
                    for link in path_links
                ]

            elif scheduler_strategy == "channel_based_coefficients_constant_wired_delay":
                if links_bitrate is None:
                    raise ValueError(f"Stream='{stream.name}' requires links_bitrate for channel-based strategy.")

                remaining_latency = stream.latency_tolerance - (num_wired * self.wired_link_constant_delay)
                if remaining_latency <= 0:
                    raise ValueError(
                        f"Stream='{stream.name}' has insufficient latency after wired delay subtraction.")

                # Compute inverse of bitrate for wireless links
                wireless_bitrates = [links_bitrate.get(link, 0) for link in wireless_links]

                inverse_bitrates = [1 / bitrate if bitrate > 0 else float('inf') for bitrate in wireless_bitrates]
                total_inverse_bitrate = sum(inverse_bitrates)

                # Assign time inversely proportional to bitrate
                wireless_link_time_allocations = [
                    remaining_latency * (inv_bitrate / total_inverse_bitrate) for inv_bitrate in inverse_bitrates
                ]

                # Assign final link allocations
                link_time_allocations = []
                wireless_idx = 0
                for link in path_links:
                    if link.link_type == "wired":
                        link_time_allocations.append(self.wired_link_constant_delay)
                    else:
                        link_time_allocations.append(wireless_link_time_allocations[wireless_idx])
                        wireless_idx += 1

            else:
                raise ValueError(f"Unknown scheduling strategy: {scheduler_strategy}.")

            # Create frames for this stream over the specified duration
            new_frames = stream.create_tst_frames_until(end_time)

            for frame in new_frames:
                current_time = frame.creation_time
                for link_idx, link in enumerate(path_links):
                    link_alloc_time = link_time_allocations[link_idx]

                    arrival_time = current_time
                    departure_time = current_time + link_alloc_time

                    link.future_queue.add_plan(
                        stream=stream,
                        frame_queue_plan=(frame, arrival_time, departure_time)
                    )


                    current_time = departure_time

                total_transit_time = current_time - frame.creation_time
                if round(total_transit_time, 5) > round(stream.latency_tolerance, 5):
                    raise ValueError(
                        f"Frame {frame} in stream='{stream.name}' exceeded latency tolerance by "
                        f"{total_transit_time - stream.latency_tolerance:.3f} seconds."
                    )

        # self.print_schedule_details()