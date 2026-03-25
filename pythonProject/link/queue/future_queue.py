import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from pythonProject.link.queue.helper import compute_aggregate_instantaneous_bitrates_per_slot_sorting, \
    compute_aggregate_instantaneous_bitrates_global_sorting


class FutureQueue:
    def __init__(self):
        """
        Initialize a FutureQueue instance.
        This class manages a list of future traffic plans.
        Each plan includes a stream and a list of frame details (frame, arrival time, departure time).
        """
        self.plans = []  # List to hold future traffic plans

    def add_plan(self, stream, frame_queue_plan):
        """
        Add a traffic plan to the future queue.

        :param stream: The stream associated with the plan.
        :param frame_queue_plan: A list of tuples (frame, arrival_time, departure_time).
        """
        self.plans.append({"stream": stream, "frame_queue_plan": frame_queue_plan})

    def get_plan(self, frame):
        """
        Retrieve the traffic plan that contains the given frame.

        :param frame: The frame to search for.
        :return: A dictionary containing the stream and frame queue plan if found, else None.
        """
        for plan in self.plans:
            existing_frame, arrival_time, departure_time = plan["frame_queue_plan"]
            if existing_frame == frame:
                return plan["frame_queue_plan"]  # Return the entire plan containing the frame

        return None  # Return None if the frame is not found

    def has_plan(self, frame) -> bool:
        """
        Check whether a traffic plan exists for the given frame.

        :param frame: The frame to search for.
        :return: True if a plan containing this frame exists, False otherwise.
        """
        for plan in self.plans:
            existing_frame, _, _ = plan["frame_queue_plan"]
            if existing_frame == frame:
                return True
        return False

    def edit_plan(self, frame, new_times):
        """
        Edit the arrival and departure time of a specific frame.

        :param frame: The frame to be updated.
        :param new_times: A tuple (new_arrival, new_departure) with updated times.
        :return: True if the update was successful, False otherwise.
        """
        new_arrival, new_departure = new_times

        for plan in self.plans:
            existing_frame, arrival_time, departure_time = plan["frame_queue_plan"]
            if existing_frame == frame:
                # Update the arrival and departure times
                plan["frame_queue_plan"] = (existing_frame, new_arrival, new_departure)
                return True  # Successfully updated
        return False  # Frame not found

    @staticmethod
    def visualize_bitrate_time_series(
            time_series,
            current_time,
            channel_coherence_duration,
            channel_sensing_time,
            propagation_delay
    ):
        """
        Visualize the instantaneous bitrate time series with rectangles for bitrate intervals.
        Only add the propagation delay to intervals whose end_time does not immediately match
        the start_time of the next interval, or if it's the last interval.

        :param time_series: A list of tuples (start_time, end_time, bitrate).
        :param current_time: The current time in the system.
        :param channel_coherence_duration: Duration of the channel coherence period.
        :param channel_sensing_time: Time required for channel sensing before transmission.
        :param propagation_delay: Time required for data propagation through the link.
        """
        if not time_series:
            print("No valid frames to visualize.")
            return

        fig, ax = plt.subplots(figsize=(12, 6))

        # Highlight channel sensing period (from current_time to current_time + channel_sensing_time)
        sensing_start = current_time
        sensing_end = current_time + channel_sensing_time
        ax.axvspan(sensing_start, sensing_end, color='red', alpha=0.3, label="Channel Sensing Period")

        # Plot each bitrate interval
        for i, (start_time, end_time, bitrate) in enumerate(time_series):
            # Draw a rectangle for the bitrate interval
            rect = Rectangle(
                (start_time, 0),  # Bottom-left corner: (x=start_time, y=0)
                end_time - start_time,  # Width in time
                bitrate,  # Height corresponds to bitrate
                facecolor='blue',
                edgecolor='black',
                alpha=0.7,
                label=f"Bitrate: {bitrate:.2f} bps"
            )
            ax.add_patch(rect)

            # Decide if we should highlight the propagation delay period for this interval
            # 1. If it's the last interval in the list, OR
            # 2. If this interval does NOT end exactly where the next one begins.
            if i == len(time_series) - 1:
                # It's the last interval; always highlight
                propagation_start = end_time
                propagation_end = end_time + propagation_delay
                ax.axvspan(propagation_start, propagation_end, color='green', alpha=0.3,
                           label="Propagation Delay Period")
            else:
                # Check the next interval's start_time
                next_start_time = time_series[i + 1][0]
                if abs(next_start_time - end_time) > 1e-12:  # or simply next_start_time != end_time
                    # There's a gap, so we highlight the propagation delay
                    propagation_start = end_time
                    propagation_end = end_time + propagation_delay
                    ax.axvspan(propagation_start, propagation_end, color='green', alpha=0.3,
                               label="Propagation Delay Period")

        # Highlight the boundary of the channel coherence window
        coherence_end = current_time + channel_coherence_duration
        ax.axvline(x=coherence_end, color='black', linestyle='--', label="End of Coherence Window")

        # Customize the plot
        ax.set_title("Instantaneous Bitrate Over Time", fontsize=16)
        ax.set_xlabel("Time", fontsize=14)
        ax.set_ylabel("Bitrate (bps)", fontsize=14)

        # X-axis limits: just a bit before current_time and after coherence_end
        ax.set_xlim([current_time - 1, coherence_end + 1])

        # Y-axis limit: a bit larger than the max bitrate
        max_bitrate = max([bitrate for _, _, bitrate in time_series])
        ax.set_ylim([0, max_bitrate * 1.2])

        ax.grid(alpha=0.3)

        # Deduplicate legend labels
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        # ax.legend(by_label.values(), by_label.keys(), loc="upper right")

        plt.tight_layout()
        plt.show()

    def get_active_frame_of_stream(self, stream, coherence_start, coherence_duration, channel_sensing_time):
        """
        Check if any frame belonging to `stream` is still active before the coherence end,
        using the same overlap condition logic as used elsewhere in the system.

        A frame is considered active if:
          1. departure_time > coherence_end  (extends beyond the window)
          2. arrival_time < coherence_end < departure_time and
             (coherence_end - arrival_time) <= (departure_time - coherence_end - channel_sensing_time)

        :param stream: Stream to check.
        :param coherence_end: End of current coherence interval.
        :param channel_sensing_time: Channel sensing duration.
        :return: True if the stream has any active frame, False otherwise.
        """
        coherence_end = coherence_start + coherence_duration
        active_frames = []
        for plan in self.plans:
            if plan["stream"] != stream:
                continue

            frame, arrival_time, departure_time = plan["frame_queue_plan"]

            if departure_time < coherence_start:
                continue

            # Case 1: Frame is sent before coherence window
            if departure_time <= coherence_end:
                active_frames.append(plan)

            # Case 2: Frame overlaps
            if arrival_time < coherence_end <= departure_time:
                if (coherence_end - arrival_time) >= (departure_time - coherence_end - channel_sensing_time):
                    active_frames.append(plan)

        return active_frames

    def has_active_frame_of_stream(self, stream, coherence_start, coherence_duration, channel_sensing_time) -> bool:
        """
        Check if any frame belonging to `stream` is still active before the coherence end,
        using the same overlap condition logic as used elsewhere in the system.

        A frame is considered active if:
          1. departure_time > coherence_end  (extends beyond the window)
          2. arrival_time < coherence_end < departure_time and
             (coherence_end - arrival_time) <= (departure_time - coherence_end - channel_sensing_time)

        :param stream: Stream to check.
        :param coherence_end: End of current coherence interval.
        :param channel_sensing_time: Channel sensing duration.
        :return: True if the stream has any active frame, False otherwise.
        """
        coherence_end = coherence_start + coherence_duration
        for plan in self.plans:
            if plan["stream"] != stream:
                continue

            frame, arrival_time, departure_time = plan["frame_queue_plan"]

            if departure_time < coherence_start:
                continue

            # Case 1: Frame is sent before coherence window
            if departure_time <= coherence_end:
                return True

            # Case 2: Frame overlaps
            if arrival_time < coherence_end <= departure_time:
                if (coherence_end - arrival_time) >= (departure_time - coherence_end - channel_sensing_time):
                    return True

        return False

    def prune_queue_before_coherence_interval(
            self,
            coherence_interval_start_time: float,
            channel_sensing_time: float,
    ) -> int:
        """
        Remove frames that were already served before the new coherence interval.

        A frame is removed if:
          1. departure_time < current_time  (completely finished), or
          2. arrival_time < current_time < departure_time and
             (current_time - arrival_time) <= (departure_time - current_time - channel_sensing_time)

        :param coherence_interval_start_time: Start of the new coherence interval.
        :param channel_sensing_time: Sensing time before transmission.
        :return: Number of frames removed.
        """
        current_time = coherence_interval_start_time
        removed = 0

        # Iterate backwards to safely remove from list in-place
        for i in range(len(self.plans) - 1, -1, -1):
            frame, arrival_time, departure_time = self.plans[i]["frame_queue_plan"]

            # --- removal conditions ---
            if departure_time <= current_time:
                # fully finished before current interval
                del self.plans[i]
                removed += 1
                continue

            if arrival_time < current_time <= departure_time:
                if (current_time - arrival_time) >= (departure_time - current_time - channel_sensing_time):
                    # overlaps but mostly belongs to previous window
                    del self.plans[i]
                    removed += 1
                    continue

        return removed

    def prune_by_active_streams(self, streams_list) -> int:
        """
        Keep only the traffic plans belonging to the given active streams.
        Remove all other plans.

        :param streams_list: List of active stream objects.
        :return: Number of plans removed.
        """
        removed = 0

        # Iterate backwards to safely remove from list in-place
        for i in range(len(self.plans) - 1, -1, -1):
            if self.plans[i]["stream"] not in streams_list:
                del self.plans[i]
                removed += 1

        return removed

    def calculate_stream_instantaneous_bitrate_single_coherence_interval(self, stream, start_time, channel_coherence_duration,
                                                                         channel_sensing_time,
                                                                         propagation_delay):
        """
        Calculate the instantaneous bitrate of a specific stream as a time series of (start_time, end_time, bitrate),
        ensuring that if multiple frames overlap in time, their bitrates are summed in that overlap region.

        :param stream: The stream for which to calculate the instantaneous bitrate.
        :param start_time: The current time in the system.
        :param channel_coherence_duration: The duration for which the channel remains coherent (usable).
        :param channel_sensing_time: The time required for channel sensing before transmission.
        :param propagation_delay: The time required for the data to propagate through the link.
        :return: (time_series, total_throughput):
                 time_series is a list of tuples (start_time, end_time, summed_bitrate) with no overlap.
                 total_throughput is the sum of all frame payloads (bits) that fall within the coherence window.
        """
        # This list will hold intervals (start, end, bitrate) for each qualifying frame
        frame_intervals = []
        total_throughput = 0.0
        if stream.name == "Stream_8":
            i = 0

        # The coherence window is [current_time, coherence_end_time)
        coherence_end_time = start_time + channel_coherence_duration

        # Scan all plans for this stream
        for plan in self.plans:
            if plan["stream"] != stream:
                continue

            # If plan["frame_queue_plan"] has multiple frames, iterate them.
            # Here, it looks like there's only one for demonstration, but you can adapt as needed.
            frame, arrival_time, departure_time = plan["frame_queue_plan"]

            # Next interval frames
            if arrival_time >= coherence_end_time:
                continue

            # previous interval frames
            if departure_time <= start_time:
                continue

            # Border-case frames - case 4
            if arrival_time < coherence_end_time <= departure_time:
                if (coherence_end_time - arrival_time) < (departure_time - coherence_end_time - channel_sensing_time):
                    continue

            # 2) Adjust times for channel sensing
            adjusted_start_time = max (arrival_time, start_time + channel_sensing_time)

            # Subtract propagation time at the end
            adjusted_end_time = min(departure_time - propagation_delay, coherence_end_time - propagation_delay)

            # 3) Ensure valid transmission window
            if adjusted_end_time < adjusted_start_time:
                # Force a tiny interval => effectively infinite bitrate
                adjusted_end_time = adjusted_start_time + 1e-12
                avg_bitrate = float('inf')
                print(stream.name + " is impossible (transmission window < 0).")
            else:
                payload_size = frame.payload_size
                total_throughput += payload_size
                duration = adjusted_end_time - adjusted_start_time
                avg_bitrate = payload_size / duration if duration > 0 else float('inf')

            # Accumulate the interval for later merging
            frame_intervals.append((adjusted_start_time, adjusted_end_time, avg_bitrate))

        # -----------------------------
        # Merge intervals to avoid overlap
        # -----------------------------
        if not frame_intervals:
            return [], total_throughput  # No intervals => no time series

        # Step A: Convert each (start, end, rate) into “events”
        #         +rate at start, -rate at end
        events = []
        for (start, end, rate) in frame_intervals:
            events.append((start, rate))  # at 'start', add 'rate'
            events.append((end, -rate))  # at 'end', remove 'rate'

        # Step B: Sort events by time
        #         If times are equal, we add first, remove second => sum is correct
        events.sort(key=lambda x: (x[0], -x[1]))

        # Step C: Sweep through events, building a piecewise constant function
        merged_time_series = []
        current_bitrate = 0.0
        current_start_time = None

        for i in range(len(events)):
            event_time, delta_bitrate = events[i]

            # If we're starting a new piece, set the current_start_time
            if current_start_time is None:
                current_start_time = event_time
                current_bitrate += delta_bitrate
                continue

            # We have an interval [current_start_time, event_time) with a constant 'current_bitrate'
            if event_time > current_start_time:
                # Only record if the bitrate is non-trivial
                if current_bitrate > 1e-12:
                    merged_time_series.append((current_start_time, event_time, current_bitrate))
                current_start_time = event_time

            # Update the current bitrate by the event delta
            current_bitrate += delta_bitrate

        # At the end, there's no further interval to store because we've used event boundaries
        # If you prefer to store an open-ended final interval, you could do it here.

        return merged_time_series, total_throughput

    def calculate_stream_instantaneous_bitrate(
            self,
            stream,
            start_time,
            end_time,
            channel_coherence_duration,
            channel_sensing_time,
            propagation_delay
    ):
        merged_series = []
        total_throughput = 0.0

        t = start_time
        while t < end_time:
            ts, tp = self.calculate_stream_instantaneous_bitrate_single_coherence_interval(
                stream=stream,
                start_time=t,
                channel_coherence_duration=channel_coherence_duration,
                channel_sensing_time=channel_sensing_time,
                propagation_delay=propagation_delay,
            )

            merged_series.extend(ts)
            total_throughput += tp

            t += channel_coherence_duration

        return merged_series, total_throughput

    def calculate_stream_aggregate_instantaneous_bitrate(self, start_time, end_time, channel_coherence_duration, channel_sensing_time,
                                                         propagation_delay, satisfied_streams=None, visualization=False):
        """
                Calculate and aggregate the instantaneous bitrate for all streams or only the satisfied ones.

                :param start_time: The current time in the system.
                :param end_time: The end time in the system.
                :param channel_coherence_duration: The duration for which the channel remains coherent (usable).
                :param channel_sensing_time: The time required for channel sensing before transmission.
                :param propagation_delay: The time required for the data to propagate through the link.
                :param visualization: Boolean, if True, visualize time series.
                :param satisfied_streams: Optional list of streams to consider; if None, all streams are considered.
                :return: A sorted list of dictionaries with keys `stream`, `max_bitrate`, and `total_throughput`.
                """

        # Get the list of streams, filtered by satisfied_streams if provided
        all_streams = self.get_stream_lists()
        streams = [stream for stream in all_streams if (satisfied_streams is None or stream in satisfied_streams)]

        instantaneous_bitrates = []

        # Process each stream that satisfies the condition
        for stream in streams:
            # Calculate the instantaneous bitrate time series for the stream
            time_series, total_throughput = self.calculate_stream_instantaneous_bitrate(
                stream,
                start_time,
                end_time,
                channel_coherence_duration,
                channel_sensing_time,
                propagation_delay
            )

            # Calculate the maximum bitrate from the time series
            max_bitrate = max((entry[2] for entry in time_series), default=0)

            # Append the information to the list
            instantaneous_bitrates.append({
                "stream": stream,
                "time_series": time_series,
                "max_bitrate": max_bitrate,
                "total_throughput": total_throughput
            })

        # Sort the list by max_bitrate in ascending order
        sorted_bitrates = sorted(instantaneous_bitrates, key=lambda x: x["max_bitrate"])

        aggregated_instantaneous_bitrates = compute_aggregate_instantaneous_bitrates_global_sorting(sorted_bitrates, visualization)

        return aggregated_instantaneous_bitrates

    def calculate_link_aggregate_instantaneous_bitrate(
            self,
            start_time,
            end_time,
            channel_coherence_duration,
            channel_sensing_time,
            propagation_delay,
            streams=None,
            visualization=False
    ):
        """
        Produce a single merged time series that reflects the sum of all streams'
        instantaneous bitrates over time, within the given coherence window.

        :param start_time: The current time in the system.
        :param end_time: The end time in the system.
        :param channel_coherence_duration: The duration for which the channel remains usable.
        :param channel_sensing_time: The time required for channel sensing before transmission.
        :param propagation_delay: The time required for data to propagate through the link.
        :param streams: Optional list of streams to consider; if None, all streams are considered.
        :param visualization: If True, visualize the resulting aggregate time series.
        :return: A list of (start_time, end_time, bitrate_sum) intervals reflecting the
                 total instantaneous bitrate demand across all streams.
        """

        # Retrieve all distinct streams
        all_streams = self.get_stream_lists()

        # Filter streams if a specific subset is provided
        if streams is not None:
            selected_streams = [stream for stream in all_streams if stream in streams]
        else:
            selected_streams = all_streams

        # 1) Gather intervals from each stream
        all_events = []  # will hold tuples of (time, rate_change)

        # For each stream, calculate its instantaneous bitrate intervals and transform them into events
        for stream in selected_streams:
            time_series, _ = self.calculate_stream_instantaneous_bitrate(
                stream,
                start_time,
                end_time,
                channel_coherence_duration,
                channel_sensing_time,
                propagation_delay
            )

            # Convert each (start, end, rate) into two events: +rate at start, -rate at end
            for (start, end, rate) in time_series:
                all_events.append((start, rate))  # at 'start' time, total demand goes up by rate
                all_events.append((end, -rate))  # at 'end' time, total demand goes down by rate

        # 2) Sort events by their time
        all_events.sort(key=lambda x: x[0])  # sort by the time coordinate

        # 3) Sweep over events, summing up bitrates
        merged_time_series = []
        current_bitrate = 0.0
        current_start = None

        for i, (event_time, rate_change) in enumerate(all_events):
            # If we have not started an interval yet, initialize one at this event_time
            if current_start is None:
                current_start = event_time

            # Before applying this event, we close out the interval from current_start to event_time
            if event_time > current_start:
                # Record the interval with the current bitrate from [current_start, event_time]
                # (Provided current_bitrate > 0, else no real demand in that window)
                if current_bitrate > 1e-12:
                    merged_time_series.append((current_start, event_time, current_bitrate))
                # Move the "start" pointer forward
                current_start = event_time

            # Now apply the rate change
            current_bitrate += rate_change

        # 4) Optional: If you want to clamp any intervals to the coherence window
        # (from current_time to current_time + channel_coherence_duration), you can do it here
        # or slice off intervals outside that range.

        # 5) Visualize if requested
        if visualization:
            self.visualize_bitrate_time_series(
                merged_time_series,
                start_time,
                channel_coherence_duration,
                channel_sensing_time,
                propagation_delay
            )

        return merged_time_series

    def calculate_stream_link_max_bitrate(self, start_time, end_time, channel_coherence_duration, channel_sensing_time,
                                          propagation_delay, visualization=False):

        aggregated_instantaneous_bitrates = self.calculate_stream_aggregate_instantaneous_bitrate(start_time, end_time, channel_coherence_duration, channel_sensing_time,
                                                                                                  propagation_delay, None, visualization)

        # Prepare a dict mapping each stream to its max bitrate and total throughput
        stream_to_max_bitrate = {
            entry["stream"]: {"max_bitrate": entry["max_bitrate"], "total_throughput": entry["total_throughput"]}
            for entry in aggregated_instantaneous_bitrates
        }

        return stream_to_max_bitrate

    def clear(self):
        """
        Clear all traffic plans from the future queue.
        """
        self.plans.clear()

    def get_active_frame(self, timeslot, stream=None):
        """
        Retrieve all frames that were planned for transmission within the given timeslot.

        :param timeslot: A tuple (start_time, end_time) defining the time range.
        :param stream: (Optional) If provided, only return frames belonging to this stream.
        :return: A list of tuples (stream, frame, arrival_time, departure_time) for active frames.
        """
        start_time, end_time = timeslot
        active_frames = []

        for plan in self.plans:
            plan_stream = plan["stream"]
            frame_queue_plan = plan["frame_queue_plan"]

            # If a specific stream is provided, filter by it
            if stream is not None and plan_stream != stream:
                continue

            frame, arrival_time, departure_time = frame_queue_plan
            # Check if the frame's active period overlaps with the given timeslot
            if departure_time >= start_time and arrival_time <= end_time:
                active_frames.append(frame)

        return active_frames

    def get_stream_lists(self):
        """
        Retrieve all distinct streams from the plans in the future queue.

        :return: A list of unique stream names.
        """
        return list({plan["stream"] for plan in self.plans})

    def __len__(self):
        """
        Get the number of traffic plans in the queue.

        :return: The number of traffic plans in the queue.
        """
        return len(self.plans)

    def __repr__(self):
        """
        Return a string representation of the future queue.

        :return: A string showing the number of plans and their details.
        """
        return f"FutureQueue(Plans: {len(self.plans)})"
