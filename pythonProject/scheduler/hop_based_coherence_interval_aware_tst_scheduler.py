class HopBasedCoherenceIntervalAwareTstScheduler:
    def __init__(self, connection_manager, streams, wired_link_constant_delay=0.04):
        self.connection_manager = connection_manager
        self.streams = streams
        self.wired_link_constant_delay = wired_link_constant_delay

    @staticmethod
    def _interval_index(t, interval_len):
        return int(t // interval_len)

    @staticmethod
    def _interval_bounds(idx, interval_len):
        s = idx * interval_len
        return s, s + interval_len

    @staticmethod
    def _wireless_window(interval_start, interval_end, sensing):
        return interval_start + sensing, interval_end

    def _place_wireless_hop_within_coherence(self, *,
                                             desired_start,
                                             hop_dur,
                                             interval_len,
                                             channel_sensing_interval):
        """
        Place a wireless hop fully inside a single coherence interval’s wireless window.

        - If hop fits entirely within current interval → keep it.
        - If it crosses into next → decide whether to keep in current or move to next
          by comparing:
              (coherence_end - arrival_time)  vs.  (departure_time - coherence_end - sensing)
          i.e., whether more of the hop lies in the current interval or the next one
          (accounting for sensing in the next).
        - Trim hop if needed to fit inside chosen interval.
        """
        idx = self._interval_index(desired_start, interval_len)
        departure = desired_start + hop_dur

        while True:
            # --- Current interval ---
            i_start, i_end = self._interval_bounds(idx, interval_len)
            w_start, w_end = self._wireless_window(i_start, i_end, channel_sensing_interval)
            arrival = max(desired_start, w_start)

            # --- Case 1: fits fully inside current wireless window ---
            if departure <= w_end:
                return arrival, departure

            # --- Case 2: crosses into next interval ---

            # Next interval window
            n_idx = idx + 1
            n_start, n_end = self._interval_bounds(n_idx, interval_len)
            nw_start, nw_end = self._wireless_window(n_start, n_end, channel_sensing_interval)

            # Time available in next interval (after sensing)
            # Using your condition:
            # if (coherence_end - arrival_time) >= (departure_time - coherence_end - sensing)
            # → more time in current
            left_side = (i_end - arrival)
            right_side = min(interval_len - channel_sensing_interval, departure - i_end - channel_sensing_interval)

            if left_side >= right_side:
                # More time lies in current → trim hop to end of current interval
                trimmed_departure = min(departure, w_end)
                return arrival, trimmed_departure
            else:
                # More time lies in next → shift hop start to next interval after sensing
                arrival_next = max(desired_start, nw_start)
                departure_next = min(departure, nw_end)
                return arrival_next, departure_next

    # --------- path utility ---------
    def get_stream_paths(self, stream):
        return self.connection_manager.find_path(
            start_node=stream.source,
            end_node=stream.destination
        )

    # --------- main scheduling ---------
    def schedule_until(self, end_time, channel_coherence_interval, channel_sensing_interval):
        """
        Coherence interval = L = (end_time - start_time), tiled from start_time forward.
        - Wireless hops: must be fully contained within a single interval's wireless window
          [interval_start + channel_sensing_interval, interval_end).
        - Wired hops: can transmit anytime (including sensing), and MAY span interval boundaries.
        """

        for stream in self.streams:
            path_links = self.get_stream_paths(stream)

            # Wired / wireless counts
            wired_links = [link for link in path_links if getattr(link, "link_type", "wired") == "wired"]
            wireless_links = [link for link in path_links if getattr(link, "link_type", "wired") == "wireless"]
            num_wired = len(wired_links)
            num_wireless = len(wireless_links)

            # Wired fixed delay budget subtracts from latency
            remaining_latency = stream.latency_tolerance - (num_wired * self.wired_link_constant_delay)
            if remaining_latency < -1e-9:
                raise ValueError(
                    f"Stream='{stream.name}' has insufficient latency after wired delay subtraction."
                )

            # Distribute remaining latency across wireless hops (evenly)
            wireless_link_time = (remaining_latency / num_wireless) if num_wireless > 0 else 0.0

            # Per-hop allocations in path order
            link_time_allocations = [
                (self.wired_link_constant_delay if getattr(link, "link_type", "wired") == "wired"
                 else wireless_link_time)
                for link in path_links
            ]

            # Create frames
            new_frames = stream.create_tst_frames_until(end_time)

            for frame in new_frames:
                current_time = frame.creation_time

                for link_idx, link in enumerate(path_links):
                    hop_dur = link_time_allocations[link_idx]
                    link_type = getattr(link, "link_type", "wired")

                    if link_type == "wireless":
                        # Wireless: must fit wholly inside one interval's wireless window
                        arrival_time, departure_time = self._place_wireless_hop_within_coherence(
                            desired_start=current_time,
                            hop_dur=hop_dur,
                            interval_len=channel_coherence_interval,
                            channel_sensing_interval=channel_sensing_interval
                        )
                    else:
                        # Wired: no confinement; can start immediately and span intervals or sensing
                        arrival_time = current_time
                        departure_time = current_time + hop_dur

                    # Enqueue plan
                    link.future_queue.add_plan(
                        stream=stream,
                        frame_queue_plan=(frame, arrival_time, departure_time)
                    )

                    current_time = departure_time

                # End-to-end latency check
                total_transit_time = current_time - frame.creation_time
                if round(total_transit_time, 6) > round(stream.latency_tolerance, 6):
                    raise ValueError(
                        f"Frame {frame} in stream='{stream.name}' exceeded latency tolerance by "
                        f"{total_transit_time - stream.latency_tolerance:.6f} seconds."
                    )
