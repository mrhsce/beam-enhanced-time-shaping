from matplotlib import pyplot as plt
import numpy as np

import matplotlib.pyplot as plt
import numpy as np

def visualize_decision_variables(bss, satisfied_streams, resource_misuse):
    """
    Visualizes the decision variables (beamweights and spectrum assignment) for all BSs in a single chart,
    along with the number of satisfied streams and resource misuse.

    :param bss: List of BS (base station) objects.
    :param satisfied_streams: List of streams that are satisfied.
    :param resource_misuse: Total resource misuse value.
    """
    fig, ax1 = plt.subplots(figsize=(14, 10))

    # Collect data for visualization
    bs_labels = []
    beamweight_data = []
    beamweight_segments = []
    spectrum_segments = []

    for bs in bss:
        bs_labels.append(f"BS {bs.id}")

        # Beamweights: Weight distribution among active UEs
        active_ues, active_weights = bs.beamweight_manager.get_active_ues()
        beamweight_segments.append((active_ues, active_weights))

        # Spectrum Assignment: Uplink and downlink bandwidths
        uplink_bandwidth = bs.spectrum_manager.get_uplink_bandwidth()
        downlink_bandwidth = bs.spectrum_manager.get_downlink_bandwidth()
        spectrum_segments.append([uplink_bandwidth, downlink_bandwidth])

    x = np.arange(len(bs_labels))  # Positions for the bars
    bar_width = 0.35
    margin = 0.05  # Small margin between the columns

    # Create a secondary y-axis for spectrum allocation
    ax2 = ax1.twinx()

    # Spectrum allocation bars
    for i, (uplink, downlink) in enumerate(spectrum_segments):
        ax2.bar(x[i] + bar_width / 2 + margin, uplink, width=bar_width, label="Uplink" if i == 0 else "", color='darkorange')
        ax2.bar(x[i] + bar_width / 2 + margin, downlink, width=bar_width, bottom=uplink,
                label="Downlink" if i == 0 else "", color='forestgreen')

    # Beamweights bars
    for i, (ues, weights) in enumerate(beamweight_segments):
        bottom = 0
        for ue, weight in zip(ues, weights):
            ax1.bar(x[i] - bar_width / 2 - margin, weight, width=bar_width, bottom=bottom,
                    color=f"C{ue.id % 10}", label=None)
            ax1.text(x[i] - bar_width / 2 - margin, bottom + weight / 2, f"UE {ue.id}", ha='center', va='center', fontsize=8, color='white')
            bottom += weight

    # Add BS labels and titles
    ax1.set_xticks(x)
    ax1.set_xticklabels(bs_labels)
    ax1.set_ylabel("Beamweights", color='black')
    ax2.set_ylabel("Spectrum Allocation (Hz)", color='black')
    ax1.set_title("Decision Variables per BS: Beamweights and Spectrum Allocation")

    # Legends for clarity
    handles2, labels2 = ax2.get_legend_handles_labels()
    by_label2 = dict(zip(labels2, handles2))
    ax2.legend(by_label2.values(), by_label2.keys(), loc="upper left", fontsize=10)

    # Show grid for clarity
    ax1.grid(axis='y', linestyle='--', alpha=0.7)

    # Add overall performance metrics below the chart in a single line
    fig.text(0.5, 0.01, f"Satisfied Streams: {len(satisfied_streams)}    |    Throughput shortage: {resource_misuse:.2f}",
             ha='center', fontsize=14, color="black", fontweight='bold')

    plt.tight_layout(rect=[0, 0.03, 1, 1])
    plt.show()


def visualize_streams(streams, start, end, color_map):
    """
    Visualize each TST stream's frame creation times over 'duration',
    using the provided color_map to ensure consistent coloring.
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    for i, stream in enumerate(streams):
        # We'll create TST frames for the specified duration, from time=0
        frames = stream.get_tst_frame_among(start, end)
        frame_times = [frame.creation_time for frame in frames]
        stream_color = color_map[stream.name]
        ax.scatter(frame_times, [i + 1] * len(frame_times), label=stream.name, color=stream_color)

    ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("Stream")
    ax.set_yticks(range(1, len(streams) + 1))
    ax.set_yticklabels([stream.name for stream in streams])
    ax.set_title("TST Stream Frame Creation Times")
    ax.legend()
    plt.grid(True)
    plt.show()


def create_gantt_chart(environment, color_map):
    """
    Gantt chart from the environment's link.future_queue data,
    labeling each link as "Link <index>".
    """
    fig, ax = plt.subplots(figsize=(12, 8))

    link_schedules = {}
    for link in environment.connection_manager.links:
        link_schedules[link] = []
        for plan_dict in link.future_queue.plans:
            sname = plan_dict["stream"]  # e.g., "Stream_1", "Stream_2", or "BET"
            frame, arrival, departure = plan_dict["frame_queue_plan"]
            link_schedules[link].append((arrival, departure, sname, frame))

    link_list = list(link_schedules.keys())
    y_positions = {link: idx for idx, link in enumerate(link_list)}

    offset = 0.15  # Offset for overlapping streams within the same link
    for link in link_list:
        y = y_positions[link]
        current_stream_offsets = {}  # Track offsets for streams

        for (arrival, departure, stream, frame) in link_schedules[link]:
            color = color_map.get(stream.name, "black")
            stream_offset = current_stream_offsets.get(stream, 0)
            y_with_offset = y + stream_offset
            ax.hlines(
                y=y_with_offset,
                xmin=arrival,
                xmax=departure,
                color=color,
                linewidth=3,
                alpha=0.8,
            )

            # Adjust the offset for overlapping streams
            current_stream_offsets[stream] = stream_offset + offset

    ax.set_yticks(range(len(link_list)))
    ax.set_yticklabels([f"{link.name}" for link in link_list])
    ax.set_xlabel("Time (seconds)")
    ax.set_title("Gantt Chart of Scheduled Frames (TST)")
    ax.grid(True)
    plt.tight_layout()
    plt.show()

def build_stream_color_map(streams):
    """
    Build a dictionary that assigns each TST stream a color from a colormap
    in a consistent, reproducible order.
    """
    import matplotlib.pyplot as plt

    sorted_streams = sorted(streams, key=lambda s: s.name)
    cmap = plt.get_cmap("tab10")
    color_map = {}

    for i, stream in enumerate(sorted_streams):
        color_map[stream.name] = cmap(i % cmap.N)

    return color_map


def visualize_bet_queue_sizes(environment):
    """
    Display a bar chart of how many BET frames are in the bet_queue of each link.

    :param environment: A PhysicalEnvironment instance with a ConnectionManager.
    """
    import matplotlib.pyplot as plt

    # Collect the links from the ConnectionManager
    link_list = environment.connection_manager.links

    # We'll label each link as "Link <index>: node1->node2"
    link_labels = [
        f"{idx}"
        for idx, link in enumerate(link_list)
    ]

    # Gather the number of frames in the BET queue for each link
    bet_queue_sizes = [len(link.bet_queue) for link in link_list]

    # Create the bar chart
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(range(len(bet_queue_sizes)), bet_queue_sizes, color="lightblue")

    # Label the bars
    ax.set_xticks(range(len(bet_queue_sizes)))
    ax.set_xticklabels(link_labels, rotation=30, ha='right')  # rotate labels if they're long
    ax.set_ylabel("Number of Frames in BET Queue")
    ax.set_title("BET Queue Sizes per Link")
    plt.tight_layout()
    plt.show()


def visualize_stream_status(all_streams, satisfied_streams, step_label="Optimization Step"):
    """
    Visualizes the status of all streams using a 2D grid representation, highlighting which ones are satisfied.

    :param all_streams: List of all streams in the system.
    :param satisfied_streams: List of streams that are currently satisfied.
    :param step_label: Label for the current optimization step.
    """
    num_streams = len(all_streams)
    grid_size = int(np.ceil(np.sqrt(num_streams)))  # Create a square grid

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlim(0, grid_size)
    ax.set_ylim(0, grid_size)

    for i, stream in enumerate(all_streams):
        row = i // grid_size
        col = i % grid_size
        color = 'green' if stream in satisfied_streams else 'red'
        ax.add_patch(plt.Rectangle((col, grid_size - row - 1), 1, 1, color=color))
        ax.text(col + 0.5, grid_size - row - 0.5, stream.name, ha='center', va='center', fontsize=8, color='white')

    ax.set_title(f"Stream Satisfaction Status - {step_label}")

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='green', label='Satisfied Streams'),
        Patch(facecolor='red', label='Unsatisfied Streams')
    ]
    ax.legend(handles=legend_elements, loc='lower right')

    plt.show()

