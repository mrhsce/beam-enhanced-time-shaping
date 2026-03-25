
def build_concurrency_time_series(streams_intervals):
    """
    Given a list of intervals from multiple streams, each in the form:
      [(start, end, bitrate), (start, end, bitrate), ...]
    returns a piecewise function (list of intervals) that describes
    the total concurrent bitrate at each sub-interval in time,
    where concurrency is non-zero.

    The output is a list of intervals:
      [(start, end, total_bitrate_in_that_time), ...]
    sorted by start.
    """
    if not streams_intervals:
        return []

    # 1) Build a list of 'events' for line sweeping:
    #    For each interval (s, e, b), we create:
    #      - (s, +b) to indicate that from 's' onward, concurrency goes up by 'b'
    #      - (e, -b) to indicate that from 'e' onward, concurrency goes down by 'b'
    events = []
    for (s, e, b) in streams_intervals:
        events.append((s, +b))
        events.append((e, -b))

    # 2) Sort events by (time, then -delta) so that additions occur before subtractions
    events.sort(key=lambda x: (x[0], -x[1]))

    # 3) Sweep over the events to build concurrency intervals
    concurrency_time_series = []
    current_bitrate = 0
    last_time = None

    for (time, delta) in events:
        if last_time is not None and time > last_time:
            # We have an interval [last_time, time) with concurrency = current_bitrate
            if current_bitrate != 0:
                concurrency_time_series.append((last_time, time, current_bitrate))
        # Update concurrency for the next segment
        current_bitrate += delta
        last_time = time

    return concurrency_time_series


def build_full_concurrency_time_series(streams_intervals, min_time=None, max_time=None):
    """
    Variation of build_concurrency_time_series that ensures we cover the entire
    range [min_time, max_time] with intervals, inserting zero-bitrate intervals
    where needed so that the timeline is fully covered from min_time to max_time.

    If min_time or max_time is None, we derive them from the intervals.
    """
    if not streams_intervals:
        return []

    # Determine overall min and max time if not explicitly given
    times = []
    for s, e, _ in streams_intervals:
        times.append(s)
        times.append(e)

    if min_time is None:
        min_time = min(times)
    if max_time is None:
        max_time = max(times)

    # 1) Build concurrency intervals (only where concurrency != 0)
    partial = build_concurrency_time_series(streams_intervals)
    # partial is sorted by start

    # 2) Insert leading/trailing zero intervals and fill any gaps with zero
    full = []
    prev_end = min_time

    for (cs, ce, cb) in partial:
        # If there's a gap between prev_end and cs, fill it with (prev_end, cs, 0)
        if cs > prev_end:
            full.append((prev_end, cs, 0))
            prev_end = cs

        # Now add the concurrency interval from cs to ce
        if ce > prev_end:
            full.append((cs, ce, cb))
            prev_end = ce

    # If there's space after the last concurrency interval up to max_time, fill with zero
    if prev_end < max_time:
        full.append((prev_end, max_time, 0))

    # Remove intervals of length 0 just in case
    full = [(s, e, b) for (s, e, b) in full if e > s]

    return full


def merge_intervals(stream_intervals, concurrency_intervals):
    """
    Given:
      - stream_intervals = [(start_s, end_s, bitrate_s), ...]
      - concurrency_intervals = [(start_c, end_c, bitrate_c), ...], which is
        typically a 'full coverage' concurrency timeline from min to max time
        with no gaps (some intervals may have zero bitrate).

    Return a new list of intervals that covers the overlapping time
    of the stream with concurrency, where each sub-interval has
      total_bitrate = stream_bitrate + concurrency_bitrate.

    Intervals are only created where the stream is actually playing.
    """
    i_s = 0
    i_c = 0
    len_s = len(stream_intervals)
    len_c = len(concurrency_intervals)

    result = []

    while i_s < len_s and i_c < len_c:
        s_s, e_s, b_s = stream_intervals[i_s]
        s_c, e_c, b_c = concurrency_intervals[i_c]

        # Find overlap in time
        start_overlap = max(s_s, s_c)
        end_overlap = min(e_s, e_c)

        if start_overlap < end_overlap:
            # Overlapping region => sum the bitrates
            result.append((start_overlap, end_overlap, b_s + b_c))

        # Move whichever interval ends first
        if e_s < e_c:
            i_s += 1
        elif e_c < e_s:
            i_c += 1
        else:
            # They end at the same time
            i_s += 1
            i_c += 1

    return result


def merge_equal_bitrate_subintervals(intervals):
    """
    Given a sorted list of intervals (start, end, bitrate),
    merges any adjacent intervals that have the same bitrate
    and are directly contiguous.

    Example:
      [(0,2,2), (2,3,2), (3,5,1)] => [(0,3,2), (3,5,1)]
    """
    if not intervals:
        return []

    # Ensure intervals are sorted by start time
    intervals = sorted(intervals, key=lambda x: x[0])

    merged = []
    current_start, current_end, current_bitrate = intervals[0]

    for i in range(1, len(intervals)):
        s, e, b = intervals[i]
        if b == current_bitrate and s == current_end:
            # Extend the current interval
            current_end = e
        else:
            # Save the current interval
            merged.append((current_start, current_end, current_bitrate))
            # Start a new one
            current_start, current_end, current_bitrate = s, e, b

    # Append the final interval
    merged.append((current_start, current_end, current_bitrate))

    return merged


def compute_aggregate_instantaneous_bitrates_global_sorting(
        instantaneous_bitrates,
        visualization=False,
):
    """
    Global-sorting-based aggregation of instantaneous bitrate requirements.
    Visualization added WITHOUT changing any logic or functionality.
    """

    import matplotlib.pyplot as plt

    n = len(instantaneous_bitrates)

    aggregated_results = []

    # Keep a cumulative list of intervals from all previous streams
    all_prev_intervals = []

    for i in range(n):
        entry = instantaneous_bitrates[i]
        stream_id = entry["stream"]
        time_series = entry["time_series"]  # list of (start, end, bitrate)

        # 1) Build concurrency from all previous streams
        if all_prev_intervals:
            tmin = min(s for s, _, _ in time_series)
            tmax = max(e for _, e, _ in time_series)
            concurrency_full = build_full_concurrency_time_series(
                all_prev_intervals, min_time=tmin, max_time=tmax
            )
        else:
            concurrency_full = []

        # 2) Merge concurrency with this stream
        if concurrency_full:
            aggregated_series = merge_intervals(time_series, concurrency_full)
        else:
            aggregated_series = list(time_series)

        # 3) Merge adjacent sub-intervals that share the same bitrate
        aggregated_series = merge_equal_bitrate_subintervals(aggregated_series)

        # 4) Update max bitrate
        if aggregated_series:
            new_max = max(b for (_, _, b) in aggregated_series)
        else:
            new_max = 0

        aggregated_results.append({
            "stream": stream_id,
            "time_series": aggregated_series,
            "max_bitrate": new_max,
            "total_throughput": entry["total_throughput"]
        })

        # 5) Add ORIGINAL intervals for future concurrency
        all_prev_intervals.extend(time_series)

    # ------------------------------------------------------------
    # Visualization (global fixed ordering)
    # ------------------------------------------------------------
    if visualization:
        fig, ax = plt.subplots(figsize=(12, 4))

        # Fixed global order = input order
        streams = [e["stream"] for e in instantaneous_bitrates]
        series_map = {e["stream"]: e["time_series"] for e in instantaneous_bitrates}

        # Build global slot boundaries
        boundaries = set()
        for ts in series_map.values():
            for s, e, _ in ts:
                boundaries.add(s)
                boundaries.add(e)

        boundaries = sorted(boundaries)
        slots = [(boundaries[i], boundaries[i + 1]) for i in range(len(boundaries) - 1)]

        # Helper: instantaneous bitrate in slot
        def bitrate_in_slot(ts, slot):
            t0, t1 = slot
            for s, e, b in ts:
                if s <= t0 and t1 <= e:
                    return b
            return 0.0

        cmap = plt.get_cmap("tab10")
        colors = {s: cmap(i % 10) for i, s in enumerate(streams)}

        # Draw stacked rectangles with FIXED order
        for slot in slots:
            t0, t1 = slot
            bottom = 0.0

            for s in streams:
                br = bitrate_in_slot(series_map[s], slot)
                if br == 0:
                    continue

                ax.fill_between(
                    [t0, t1],
                    [bottom, bottom],
                    [bottom + br, bottom + br],
                    color=colors[s],
                    edgecolor="black",
                    linewidth=0.3,
                    alpha=0.9
                )
                bottom += br

        ax.set_xlabel("Time")
        ax.set_ylabel("Bitrate")
        ax.set_title("Global-sorting stacked instantaneous bitrate")
        ax.grid(True, axis="y", linestyle="--", alpha=0.4)

        plt.tight_layout()
        plt.show()

    return aggregated_results


def compute_aggregate_instantaneous_bitrates_per_slot_sorting(
        instantaneous_bitrates,
        visualization=False,
):
    """
    Slot-based aggregation of instantaneous bitrate requirements with
    slot-wise sorting and stacked time visualization.
    """

    import matplotlib.pyplot as plt

    # ------------------------------------------------------------
    # 0. Extract streams and time series
    # ------------------------------------------------------------
    streams = [e["stream"] for e in instantaneous_bitrates]
    series_map = {e["stream"]: e["time_series"] for e in instantaneous_bitrates}

    # ------------------------------------------------------------
    # 1. Build global slot boundaries
    # ------------------------------------------------------------
    boundaries = set()
    for ts in series_map.values():
        for s, e, _ in ts:
            boundaries.add(s)
            boundaries.add(e)

    boundaries = sorted(boundaries)
    slots = [(boundaries[i], boundaries[i + 1]) for i in range(len(boundaries) - 1)]

    # Helper: instantaneous bitrate of a stream in a slot
    def bitrate_in_slot(ts, slot):
        t0, t1 = slot
        for s, e, b in ts:
            if s <= t0 and t1 <= e:
                return b
        return 0.0

    # ------------------------------------------------------------
    # 2. Slot-based aggregation
    # ------------------------------------------------------------
    aggregated_series_per_stream = {s: [] for s in streams}
    max_aggregated_bitrate = {s: 0.0 for s in streams}

    for slot in slots:
        t0, t1 = slot

        # instantaneous rates
        slot_rates = []
        for s in streams:
            br = bitrate_in_slot(series_map[s], slot)
            slot_rates.append((s, br))

        # slot-wise sorting (low demand = higher priority)
        slot_rates.sort(key=lambda x: x[1])

        cumulative = 0.0
        for s, br in slot_rates:
            cumulative += br

            aggregated_series_per_stream[s].append((t0, t1, cumulative))
            max_aggregated_bitrate[s] = max(
                max_aggregated_bitrate[s], cumulative
            )

    # ------------------------------------------------------------
    # 3. Visualization (single global figure)
    # ------------------------------------------------------------
    if visualization:
        fig, ax = plt.subplots(figsize=(12, 4))

        cmap = plt.get_cmap("tab10")
        colors = {s: cmap(i % 10) for i, s in enumerate(streams)}

        for slot in slots:
            t0, t1 = slot

            # instantaneous bitrate per stream
            slot_rates = []
            for s in streams:
                br = bitrate_in_slot(series_map[s], slot)
                slot_rates.append((s, br))

            slot_rates.sort(key=lambda x: x[1])

            bottom = 0.0
            for s, br in slot_rates:
                if br == 0:
                    continue

                ax.fill_between(
                    [t0, t1],
                    [bottom, bottom],
                    [bottom + br, bottom + br],
                    color=colors[s],
                    edgecolor="black",
                    linewidth=0.3,
                    alpha=0.9
                )
                bottom += br

        ax.set_xlabel("Time")
        ax.set_ylabel("Bitrate")
        ax.set_title("Slot-based sorted stacked instantaneous bitrate")
        ax.grid(True, axis="y", linestyle="--", alpha=0.4)

        plt.tight_layout()
        plt.show()

    # ------------------------------------------------------------
    # 4. Merge adjacent intervals with equal bitrate
    # ------------------------------------------------------------
    def merge_equal_intervals(ts):
        if not ts:
            return []

        merged = [ts[0]]
        for s, e, b in ts[1:]:
            ps, pe, pb = merged[-1]
            if b == pb and s == pe:
                merged[-1] = (ps, e, pb)
            else:
                merged.append((s, e, b))
        return merged

    # ------------------------------------------------------------
    # 5. Final output
    # ------------------------------------------------------------
    results = []
    for entry in instantaneous_bitrates:
        s = entry["stream"]

        merged_series = merge_equal_intervals(
            aggregated_series_per_stream[s]
        )

        results.append({
            "stream": s,
            "time_series": merged_series,
            "max_bitrate": max_aggregated_bitrate[s],
            "total_throughput": entry["total_throughput"]
        })

    # Sort by satisfiability threshold
    results.sort(key=lambda x: x["max_bitrate"])

    return results


