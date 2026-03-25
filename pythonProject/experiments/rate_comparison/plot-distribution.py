import os
import json
import matplotlib.pyplot as plt
import numpy as np


def load_json_files(execution_name, directory):
    # Find all JSON files in the directory that start with the execution_name
    files = [f for f in os.listdir(directory) if f.startswith(execution_name) and f.endswith('.json')]
    return files


def process_files(files, directory):
    all_active_ues_counts = []
    all_frames = []
    all_delays = []
    all_jitters = []
    all_queues = []
    for file in files:
        file_path = os.path.join(directory, file)
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Extract the "frames" values
        frames = [entry["frames"] for entry in data["history"]]
        flattened_frames = [frame for sublist in frames[500:] for frame in sublist if frame > 0]
        all_frames.extend(flattened_frames)

        # Extract the "user activity" values
        user_activity = [entry["user activity"] for entry in data["history"]]
        active_ues_counts = [sum(1 for ue in sublist if ue > 0) for sublist in user_activity[500:]]
        all_active_ues_counts.extend(active_ues_counts)

        # Extract the "average delay" values
        average_delays = [entry["average delay"] for entry in data["history"]]
        flattened_delays = [delay / 10 for sublist in average_delays[500:] for delay in sublist if delay > 0]
        all_delays.extend(flattened_delays)

        # Extract the "queue lengths" values
        queue_lengths = [entry["queue lengths"] for entry in data["history"]]
        flattened_lengths = [length for sublist in queue_lengths[500:] for length in sublist if length > 0]
        all_queues.extend(flattened_lengths)

        # Calculate jitter for each UE
        for delays in average_delays[500:]:
            if len(delays) > 1:
                for i in range(len(delays) - 1):
                    jitter = abs(delays[i + 1] - delays[i]) / 10  # Divide by 10 to convert from 10 ms to 1 ms
                    all_jitters.append(jitter)

    return all_frames, all_active_ues_counts, all_delays, all_jitters, all_queues


def plot_data(scenarios, directory, show_values=False, q1_q3_filter=False):
    data_types = ["frames", "active UEs", "delays", "jitters", "queues"]
    units = {
        "delays": "ms",
        "jitters": "ms",
    }
    all_data = {data_type: {} for data_type in data_types}

    for scenario in scenarios:
        execution_name = scenario['prefix']
        scenario_name = scenario['name']
        files = load_json_files(execution_name, directory)
        frames, active_ues_counts, delays, jitters, queues = process_files(files, directory)
        if frames:
            all_data["frames"][scenario_name] = frames
        if active_ues_counts:
            all_data["active UEs"][scenario_name] = active_ues_counts
        if delays:
            all_data["delays"][scenario_name] = delays
        if jitters:
            all_data["jitters"][scenario_name] = jitters
        if queues:
            all_data["queues"][scenario_name] = queues

    # Create directory if it does not exist
    if not os.path.exists('graphs'):
        os.makedirs('graphs')

    rate_sum_file = 'rate_sum.txt'
    file_exists = os.path.exists(rate_sum_file)

    with open(rate_sum_file, 'a') as file:
        for data_type, scenario_data in all_data.items():
            if not scenario_data:
                print(f"No valid {data_type} data available after filtering.")
                continue

            # Plot Violin plot and Box plot
            for plot_type in ['violin', 'box']:
                plt.figure(figsize=(10, 6))
                filtered_data = []
                labels = []

                for name, data in scenario_data.items():
                    q1 = np.percentile(data, 25)
                    q3 = np.percentile(data, 75)
                    if q1_q3_filter:
                        filtered_data.append([val for val in data if q1 <= val <= q3])
                    else:
                        filtered_data = data
                    labels.append(name)

                if plot_type == 'violin':
                    plt.violinplot(filtered_data, vert=False)
                    plt.xlabel(f'{data_type} {"(" + units[data_type] + ")" if data_type in units else ""}')
                    plt.title(f'Violin Plot of {data_type} (Filtered between Q1 and Q3)')
                    filename = f'graphs/violin_plot_{data_type}.png'
                else:
                    bp = plt.boxplot(filtered_data, vert=False, patch_artist=True)
                    plt.xlabel(f'{data_type} {"(" + units[data_type] + ")" if data_type in units else ""}')
                    plt.title(f'Box Plot of {data_type} (Filtered between Q1 and Q3)')
                    filename = f'graphs/box_plot_{data_type}.png'

                    # Append statistical characteristics to file if show_values is True
                    if show_values:
                        file.write(f'\n{data_type}:\n')
                        for i, (name, data) in enumerate(scenario_data.items()):
                            q1 = np.percentile(data, 25)
                            median = np.percentile(data, 50)
                            q3 = np.percentile(data, 75)
                            mean = np.mean(data)
                            min_val = np.min(data)
                            max_val = np.max(data)

                            file.write(f' {name} = [{round(min_val, 3)},{round(q1, 3)},{round(median, 3)},{round(mean, 3)},{round(q3, 3)},{round(max_val, 3)}]\n')

                            # Display values on the plot
                            plt.text(q1, i + 1.15, f'Q1: {q1:.2f}', horizontalalignment='center', fontsize=8, color='blue')
                            plt.text(median, i + 1.35, f'Median: {median:.2f}', horizontalalignment='center', fontsize=8, color='black')
                            plt.text(q3, i + 1.15, f'Q3: {q3:.2f}', horizontalalignment='center', fontsize=8, color='red')
                            plt.text(mean, i + 0.85, f'Mean: {mean:.2f}', horizontalalignment='center', fontsize=8, color='purple')

                plt.yticks(np.arange(1, len(labels) + 1), labels)
                plt.grid(True)
                plt.savefig(filename, dpi=300)
                plt.close()
                # plt.show()


# Main execution
scenarios = [
        {'prefix': '(0.3)Digital-GREEDY-BITRATE_MAXIMIZATION-30000,4,5,20', 'name': 'D-BM(0.3)'},
        {'prefix': '(0.3)Digital-GREEDY-PF_MAXIMIZATION-30000,4,5,20', 'name': 'D-PFM(0.3)'},
        {'prefix': '(0.3)Digital-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-30000,4,5,20', 'name': 'D-QPFM(0.3)'},
        {'prefix': '(0.3)Digital-GREEDY-QUEUE_LENGTH_MINIMIZATION-30000,4,5,20', 'name': 'D-QLM(0.3)'},
        {'prefix': '(0.3)Hybrid-GREEDY-BITRATE_MAXIMIZATION-30000,4,5,20', 'name': 'H-BM(0.3)'},
        {'prefix': '(0.3)Hybrid-GREEDY-PF_MAXIMIZATION-30000,4,5,20', 'name': 'H-PFM(0.3)'},
        {'prefix': '(0.3)Hybrid-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-30000,4,5,20', 'name': 'H-QPFM(0.3)'},
        {'prefix': '(0.3)Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-30000,4,5,20', 'name': 'H-QLM(0.3)'},
        {'prefix': '(0.7)Digital-GREEDY-BITRATE_MAXIMIZATION-30000,4,5,20', 'name': 'D-BM(0.7)'},
        {'prefix': '(0.7)Digital-GREEDY-PF_MAXIMIZATION-30000,4,5,20', 'name': 'D-PFM(0.7)'},
        {'prefix': '(0.7)Digital-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-30000,4,5,20', 'name': 'D-QPFM(0.7)'},
        {'prefix': '(0.7)Digital-GREEDY-QUEUE_LENGTH_MINIMIZATION-30000,4,5,20', 'name': 'D-QLM(0.7)'},
        {'prefix': '(0.7)Hybrid-GREEDY-BITRATE_MAXIMIZATION-30000,4,5,20', 'name': 'H-BM(0.7)'},
        {'prefix': '(0.7)Hybrid-GREEDY-PF_MAXIMIZATION-30000,4,5,20', 'name': 'H-PFM(0.7)'},
        {'prefix': '(0.7)Hybrid-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-30000,4,5,20', 'name': 'H-QPFM(0.7)'},
        {'prefix': '(0.7)Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-30000,4,5,20', 'name': 'H-QLM(0.7)'},
        {'prefix': 'Digital-GREEDY-BITRATE_MAXIMIZATION-30000,4,5,20', 'name': 'D-BM(1)'},
        {'prefix': 'Digital-GREEDY-PF_MAXIMIZATION-30000,4,5,20', 'name': 'D-PFM(1)'},
        {'prefix': 'Digital-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-30000,4,5,20', 'name': 'D-QPFM(1)'},
        {'prefix': 'Digital-GREEDY-QUEUE_LENGTH_MINIMIZATION-30000,4,5,20', 'name': 'D-QLM(1)'},
        {'prefix': 'Hybrid-GREEDY-BITRATE_MAXIMIZATION-30000,4,5,20', 'name': 'H-BM(1)'},
        {'prefix': 'Hybrid-GREEDY-PF_MAXIMIZATION-30000,4,5,20', 'name': 'H-PFM(1)'},
        {'prefix': 'Hybrid-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-30000,4,5,20', 'name': 'H-QPFM(1)'},
        {'prefix': 'Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-30000,4,5,20', 'name': 'H-QLM(1)'},
        {'prefix': '(1.7)Digital-GREEDY-BITRATE_MAXIMIZATION-30000,4,5,20', 'name': 'D-BM(1.7)'},
        {'prefix': '(1.7)Digital-GREEDY-PF_MAXIMIZATION-30000,4,5,20', 'name': 'D-PFM(1.7)'},
        {'prefix': '(1.7)Digital-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-30000,4,5,20', 'name': 'D-QPFM(1.7)'},
        {'prefix': '(1.7)Digital-GREEDY-QUEUE_LENGTH_MINIMIZATION-30000,4,5,20', 'name': 'D-QLM(1.7)'},
        {'prefix': '(1.7)Hybrid-GREEDY-BITRATE_MAXIMIZATION-30000,4,5,20', 'name': 'H-BM(1.7)'},
        {'prefix': '(1.7)Hybrid-GREEDY-PF_MAXIMIZATION-30000,4,5,20', 'name': 'H-PFM(1.7)'},
        {'prefix': '(1.7)Hybrid-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-30000,4,5,20', 'name': 'H-QPFM(1.7)'},
        {'prefix': '(1.7)Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-30000,4,5,20', 'name': 'H-QLM(1.7)'},
        {'prefix': '(3)Digital-GREEDY-BITRATE_MAXIMIZATION-30000,4,5,20', 'name': 'D-BM(3)'},
        {'prefix': '(3)Digital-GREEDY-PF_MAXIMIZATION-30000,4,5,20', 'name': 'D-PFM(3)'},
        {'prefix': '(3)Digital-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-30000,4,5,20', 'name': 'D-QPFM(3)'},
        {'prefix': '(3)Digital-GREEDY-QUEUE_LENGTH_MINIMIZATION-30000,4,5,20', 'name': 'D-QLM(3)'},
        {'prefix': '(3)Hybrid-GREEDY-BITRATE_MAXIMIZATION-30000,4,5,20', 'name': 'H-BM(3)'},
        {'prefix': '(3)Hybrid-GREEDY-PF_MAXIMIZATION-30000,4,5,20', 'name': 'H-PFM(3)'},
        {'prefix': '(3)Hybrid-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-30000,4,5,20', 'name': 'H-QPFM(3)'},
        {'prefix': '(3)Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-30000,4,5,20', 'name': 'H-QLM(3)'},
    ]

scenarios_qpfm_hybrid = [
    # {'prefix': '(0.3)Digital-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-30000,4,5,20', 'name': 'D-QPFM(0.3)'},
    {'prefix': '(0.3)Hybrid-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-30000,4,5,20', 'name': 'H-QPFM(0.3)'},
    # {'prefix': '(0.7)Digital-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-30000,4,5,20', 'name': 'D-QPFM(0.7)'},
    {'prefix': '(0.7)Hybrid-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-30000,4,5,20', 'name': 'H-QPFM(0.7)'},
    # {'prefix': '(1.7)Digital-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-30000,4,5,20', 'name': 'D-QPFM(1.7)'},
    {'prefix': 'Hybrid-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-50000,4,5,20(1)', 'name': 'H-QPFM(1)'},
    # {'prefix': 'Digital-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-50000,4,5,20(1)', 'name': 'D-QPFM(1)'},
    {'prefix': '(1.7)Hybrid-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-30000,4,5,20', 'name': 'H-QPFM(1.7)'},
    # {'prefix': '(3)Digital-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-30000,4,5,20', 'name': 'D-QPFM(3)'},
    {'prefix': '(3)Hybrid-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-30000,4,5,20', 'name': 'H-QPFM(3)'},
]

scenarios_qpfm_digital = [
    {'prefix': '(0.3)Digital-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-30000,4,5,20', 'name': 'D-QPFM(0.3)'},
    # {'prefix': '(0.3)Hybrid-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-30000,4,5,20', 'name': 'H-QPFM(0.3)'},
    {'prefix': '(0.7)Digital-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-30000,4,5,20', 'name': 'D-QPFM(0.7)'},
    # {'prefix': '(0.7)Hybrid-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-30000,4,5,20', 'name': 'H-QPFM(0.7)'},
    {'prefix': 'Digital-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-50000,4,5,20(1)', 'name': 'D-QPFM(1)'},
    # {'prefix': 'Hybrid-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-50000,4,5,20(1)', 'name': 'H-QPFM(1)'},
    {'prefix': '(1.7)Digital-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-30000,4,5,20', 'name': 'D-QPFM(1.7)'},
    # {'prefix': '(1.7)Hybrid-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-30000,4,5,20', 'name': 'H-QPFM(1.7)'},
    {'prefix': '(3)Digital-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-30000,4,5,20', 'name': 'D-QPFM(3)'},
    # {'prefix': '(3)Hybrid-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-30000,4,5,20', 'name': 'H-QPFM(3)'},
]

scenarios_qlm_hybrid = [
    # {'prefix': '(0.3)Digital-GREEDY-QUEUE_LENGTH_MINIMIZATION-30000,4,5,20', 'name': 'D-QLM(0.3)'},
    {'prefix': '(0.3)Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-30000,4,5,20', 'name': 'H-QLM(0.3)'},
    # {'prefix': '(0.7)Digital-GREEDY-QUEUE_LENGTH_MINIMIZATION-30000,4,5,20', 'name': 'D-QLM(0.7)'},
    {'prefix': '(0.7)Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-30000,4,5,20', 'name': 'H-QLM(0.7)'},
    # {'prefix': '(1.7)Digital-GREEDY-QUEUE_LENGTH_MINIMIZATION-30000,4,5,20', 'name': 'D-QLM(1.7)'},
    {'prefix': 'Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-50000,4,5,20(1)', 'name': 'H-QLM(1)'},
    # {'prefix': 'Digital-GREEDY-QUEUE_LENGTH_MINIMIZATION-50000,4,5,20(1)', 'name': 'D-QLM(1)'},
    {'prefix': '(1.7)Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-30000,4,5,20', 'name': 'H-QLM(1.7)'},
    # {'prefix': '(3)Digital-GREEDY-QUEUE_LENGTH_MINIMIZATION-30000,4,5,20', 'name': 'D-QLM(3)'},
    {'prefix': '(3)Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-30000,4,5,20', 'name': 'H-QLM(3)'},
]

scenarios_qlm_digital = [
    {'prefix': '(0.3)Digital-GREEDY-QUEUE_LENGTH_MINIMIZATION-30000,4,5,20', 'name': 'D-QLM(0.3)'},
    # {'prefix': '(0.3)Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-30000,4,5,20', 'name': 'H-QLM(0.3)'},
    {'prefix': '(0.7)Digital-GREEDY-QUEUE_LENGTH_MINIMIZATION-30000,4,5,20', 'name': 'D-QLM(0.7)'},
    # {'prefix': '(0.7)Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-30000,4,5,20', 'name': 'H-QLM(0.7)'},
    {'prefix': 'Digital-GREEDY-QUEUE_LENGTH_MINIMIZATION-50000,4,5,20(1)', 'name': 'D-QLM(1)'},
    # {'prefix': 'Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-50000,4,5,20(1)', 'name': 'H-QLM(1)'},
    {'prefix': '(1.7)Digital-GREEDY-QUEUE_LENGTH_MINIMIZATION-30000,4,5,20', 'name': 'D-QLM(1.7)'},
    # {'prefix': '(1.7)Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-30000,4,5,20', 'name': 'H-QLM(1.7)'},
    {'prefix': '(3)Digital-GREEDY-QUEUE_LENGTH_MINIMIZATION-30000,4,5,20', 'name': 'D-QLM(3)'},
    # {'prefix': '(3)Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-30000,4,5,20', 'name': 'H-QLM(3)'},
]

scenarios_bm_hybrid = [
    # {'prefix': '(0.3)Digital-GREEDY-BITRATE_MAXIMIZATION-30000,4,5,20', 'name': 'D-BM(0.3)'},
    {'prefix': '(0.3)Hybrid-GREEDY-BITRATE_MAXIMIZATION-30000,4,5,20', 'name': 'H-BM(0.3)'},
    # {'prefix': '(0.7)Digital-GREEDY-BITRATE_MAXIMIZATION-30000,4,5,20', 'name': 'D-BM(0.7)'},
    {'prefix': '(0.7)Hybrid-GREEDY-BITRATE_MAXIMIZATION-30000,4,5,20', 'name': 'H-BM(0.7)'},
    # {'prefix': '(1.7)Digital-GREEDY-BITRATE_MAXIMIZATION-30000,4,5,20', 'name': 'D-BM(1.7)'},
    {'prefix': 'Hybrid-GREEDY-BITRATE_MAXIMIZATION-50000,4,5,20(1)', 'name': 'H-BM(1)'},
    # {'prefix': 'Digital-GREEDY-BITRATE_MAXIMIZATION-50000,4,5,20(1)', 'name': 'D-BM(1)'},
    {'prefix': '(1.7)Hybrid-GREEDY-BITRATE_MAXIMIZATION-30000,4,5,20', 'name': 'H-BM(1.7)'},
    # {'prefix': '(3)Digital-GREEDY-BITRATE_MAXIMIZATION-30000,4,5,20', 'name': 'D-BM(3)'},
    {'prefix': '(3)Hybrid-GREEDY-BITRATE_MAXIMIZATION-30000,4,5,20', 'name': 'H-BM(3)'},
]

scenarios_bm_digital = [
    {'prefix': '(0.3)Digital-GREEDY-BITRATE_MAXIMIZATION-30000,4,5,20', 'name': 'D-BM(0.3)'},
    # {'prefix': '(0.3)Hybrid-GREEDY-BITRATE_MAXIMIZATION-30000,4,5,20', 'name': 'H-BM(0.3)'},
    {'prefix': '(0.7)Digital-GREEDY-BITRATE_MAXIMIZATION-30000,4,5,20', 'name': 'D-BM(0.7)'},
    # {'prefix': '(0.7)Hybrid-GREEDY-BITRATE_MAXIMIZATION-30000,4,5,20', 'name': 'H-BM(0.7)'},
    {'prefix': 'Digital-GREEDY-BITRATE_MAXIMIZATION-50000,4,5,20(1)', 'name': 'D-BM(1)'},
    # {'prefix': 'Hybrid-GREEDY-BITRATE_MAXIMIZATION-50000,4,5,20(1)', 'name': 'H-BM(1)'},
    {'prefix': '(1.7)Digital-GREEDY-BITRATE_MAXIMIZATION-30000,4,5,20', 'name': 'D-BM(1.7)'},
    # {'prefix': '(1.7)Hybrid-GREEDY-BITRATE_MAXIMIZATION-30000,4,5,20', 'name': 'H-BM(1.7)'},
    {'prefix': '(3)Digital-GREEDY-BITRATE_MAXIMIZATION-30000,4,5,20', 'name': 'D-BM(3)'},
    # {'prefix': '(3)Hybrid-GREEDY-BITRATE_MAXIMIZATION-30000,4,5,20', 'name': 'H-BM(3)'},
]

scenarios_pfm_hybrid = [
    # {'prefix': '(0.3)Digital-GREEDY-PF_MAXIMIZATION-30000,4,5,20', 'name': 'D-PFM(0.3)'},
    {'prefix': '(0.3)Hybrid-GREEDY-PF_MAXIMIZATION-30000,4,5,20', 'name': 'H-PFM(0.3)'},
    # {'prefix': '(0.7)Digital-GREEDY-PF_MAXIMIZATION-30000,4,5,20', 'name': 'D-PFM(0.7)'},
    {'prefix': '(0.7)Hybrid-GREEDY-PF_MAXIMIZATION-30000,4,5,20', 'name': 'H-PFM(0.7)'},
    # {'prefix': '(1.7)Digital-GREEDY-PF_MAXIMIZATION-30000,4,5,20', 'name': 'D-PFM(1.7)'},
    {'prefix': 'Hybrid-GREEDY-PF_MAXIMIZATION-50000,4,5,20(1)', 'name': 'H-PFM(1)'},
    # {'prefix': 'Digital-GREEDY-PF_MAXIMIZATION-50000,4,5,20(1)', 'name': 'D-PFM(1)'},
    {'prefix': '(1.7)Hybrid-GREEDY-PF_MAXIMIZATION-30000,4,5,20', 'name': 'H-PFM(1.7)'},
    # {'prefix': '(3)Digital-GREEDY-PF_MAXIMIZATION-30000,4,5,20', 'name': 'D-PFM(3)'},
    {'prefix': '(3)Hybrid-GREEDY-PF_MAXIMIZATION-30000,4,5,20', 'name': 'H-PFM(3)'},
]

scenarios_pfm_digital = [
    {'prefix': '(0.3)Digital-GREEDY-PF_MAXIMIZATION-30000,4,5,20', 'name': 'D-PFM(0.3)'},
    # {'prefix': '(0.3)Hybrid-GREEDY-PF_MAXIMIZATION-30000,4,5,20', 'name': 'H-PFM(0.3)'},
    {'prefix': '(0.7)Digital-GREEDY-PF_MAXIMIZATION-30000,4,5,20', 'name': 'D-PFM(0.7)'},
    # {'prefix': '(0.7)Hybrid-GREEDY-PF_MAXIMIZATION-30000,4,5,20', 'name': 'H-PFM(0.7)'},
    {'prefix': 'Digital-GREEDY-PF_MAXIMIZATION-50000,4,5,20(1)', 'name': 'D-PFM(1)'},
    # {'prefix': 'Hybrid-GREEDY-PF_MAXIMIZATION-50000,4,5,20(1)', 'name': 'H-PFM(1)'},
    {'prefix': '(1.7)Digital-GREEDY-PF_MAXIMIZATION-30000,4,5,20', 'name': 'D-PFM(1.7)'},
    # {'prefix': '(1.7)Hybrid-GREEDY-PF_MAXIMIZATION-30000,4,5,20', 'name': 'H-PFM(1.7)'},
    {'prefix': '(3)Digital-GREEDY-PF_MAXIMIZATION-30000,4,5,20', 'name': 'D-PFM(3)'},
    # {'prefix': '(3)Hybrid-GREEDY-PF_MAXIMIZATION-30000,4,5,20', 'name': 'H-PFM(3)'},
]

directory = 'output'  # Directory where the JSON files are stored
# plot_data(scenarios_qpfm_hybrid, directory, show_values=True, q1_q3_filter=False)

for i in [scenarios_qpfm_hybrid, scenarios_qpfm_digital, scenarios_qlm_hybrid, scenarios_qlm_digital, scenarios_bm_hybrid, scenarios_bm_digital, scenarios_pfm_hybrid, scenarios_pfm_digital]:
    plot_data(i, directory, show_values=True, q1_q3_filter=True)
    print("One done")
