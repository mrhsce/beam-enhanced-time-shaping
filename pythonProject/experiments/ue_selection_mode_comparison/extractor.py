import os
import json
import numpy as np


def load_json_files(execution_name, directory):
    # Find all JSON files in the directory that start with the execution_name
    files = [f for f in os.listdir(directory) if f.startswith(execution_name) and f.endswith('.json')]
    return files


def process_files(files, directory):
    all_data = {
        'frames': [],
        'active_ues': [],
        'delays': [],
        'jitters': [],
        'queues': []
    }

    file_stats = {}

    for file in files:
        file_path = os.path.join(directory, file)
        with open(file_path, 'r') as f:
            data = json.load(f)

        scenario_data = {
            'frames': [],
            'active_ues': [],
            'delays': [],
            'jitters': [],
            'queues': []
        }

        # Extract the "frames" values
        frames = [entry["frames"] for entry in data["history"]]
        flattened_frames = [frame for sublist in frames[500:] for frame in sublist]
        scenario_data['frames'].extend(flattened_frames)

        # Extract the "user activity" values
        user_activity = [entry["user activity"] for entry in data["history"]]
        active_ues_counts = [sum(1 for ue in sublist if ue > 0) for sublist in user_activity[500:]]
        scenario_data['active_ues'].extend(active_ues_counts)

        # Extract the "average delay" values
        average_delays = [entry["average delay"] for entry in data["history"]]
        flattened_delays = [delay / 10 for sublist in average_delays[500:] for delay in sublist]
        scenario_data['delays'].extend(flattened_delays)

        # Extract the "queue lengths" values
        queue_lengths = [entry["queue lengths"] for entry in data["history"]]
        flattened_lengths = [length for sublist in queue_lengths[500:] for length in sublist]
        scenario_data['queues'].extend(flattened_lengths)

        # Calculate jitter for each UE
        for delays in average_delays[500:]:
            if len(delays) > 1:
                for i in range(len(delays) - 1):
                    jitter = abs(delays[i + 1] - delays[i]) / 10  # Divide by 10 to convert from 10 ms to 1 ms
                    scenario_data['jitters'].append(jitter)

        for key in all_data:
            all_data[key].append(scenario_data[key])

        file_key = file.split('.')[1]
        file_stats[file_key] = calculate_statistics(scenario_data)

    return all_data, file_stats


def calculate_statistics(data):
    stats = {}
    for key, values in data.items():
        if values:
            if isinstance(values[0], list):
                all_values = [val for sublist in values for val in sublist]
            else:
                all_values = values
            stats[key] = [
                round(float(np.min(all_values)), 3),
                round(float(np.percentile(all_values, 25)), 3),
                round(float(np.median(all_values)), 3),
                round(float(np.mean(all_values)), 3),
                round(float(np.percentile(all_values, 75)), 3),
                round(float(np.max(all_values)), 3),
                round(float(np.std(all_values)), 3),
                int(len(all_values))
            ]
    return stats


def save_statistics_to_file(scenarios, directory):
    data_types = ["frames", "active_ues", "delays", "jitters", "queues"]
    all_stats = {data_type: {} for data_type in data_types}
    file_stats = {data_type: {} for data_type in data_types}

    for scenario in scenarios:
        execution_name = scenario['prefix']
        scenario_name = scenario['name']
        files = load_json_files(execution_name, directory)
        scenario_data, scenario_file_stats = process_files(files, directory)

        for key in all_stats:
            all_stats[key][scenario_name] = calculate_statistics({key: scenario_data[key]})[key]

        for file_key, stats in scenario_file_stats.items():
            for key in file_stats:
                if scenario_name not in file_stats[key]:
                    file_stats[key][scenario_name] = {}
                file_stats[key][scenario_name][file_key] = stats[key]

    # Save statistics to JSON file
    stats_file = 'statistics.json'
    with open(stats_file, 'w') as file:
        json.dump(all_stats, file, indent=4)

    # Save file statistics to JSON file
    file_stats_file = 'file_statistics.json'
    with open(file_stats_file, 'w') as file:
        json.dump(file_stats, file, indent=4)


# Main execution
# TODO: STA and RND has been exchanged
digital_scenarios = [
        {'prefix': 'Digital-GREEDY-BITRATE_MAXIMIZATION-50000,4,5,20(1)', 'name': 'D-BM'},
        {'prefix': 'Digital-GREEDY-PF_MAXIMIZATION-50000,4,5,20(1)', 'name': 'D-PFM'},
        {'prefix': 'Digital-GREEDY-QUEUE_LENGTH_MINIMIZATION-50000,4,5,20(1)', 'name': 'D-QLM'},
        {'prefix': 'Digital-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-50000,4,5,20(1)', 'name': 'D-QPFM'},
        {'prefix': 'Digital-ADAPTIVE_TOP_K-BITRATE_MAXIMIZATION-40000,4,5,20(1)', 'name': 'D-TK-BM'},
        {'prefix': 'Digital-ADAPTIVE_TOP_K-PF_MAXIMIZATION-40000,4,5,20(1)', 'name': 'D-TK-PFM'},
        {'prefix': 'Digital-ADAPTIVE_TOP_K-QUEUE_AWARE_PF_MAXIMIZATION-40000,4,5,20(1)', 'name': 'D-TK-QPFM'},
        {'prefix': 'Digital-ADAPTIVE_TOP_K-QUEUE_LENGTH_MINIMIZATION-40000,4,5,20(1)', 'name': 'D-TK-QLM'},
        {'prefix': 'Digital-SERVING_ALL-QUEUE_AWARE_PF_MAXIMIZATION-40000,4,5,20(1)', 'name': 'D-SA'}
    ]

hybrid_scenarios = [
        {'prefix': 'Hybrid-GREEDY-BITRATE_MAXIMIZATION-50000,4,5,20(1)', 'name': 'H-BM'},
        {'prefix': 'Hybrid-GREEDY-PF_MAXIMIZATION-50000,4,5,20(1)', 'name': 'H-PFM'},
        {'prefix': 'Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-50000,4,5,20(1)', 'name': 'H-QLM'},
        {'prefix': 'Hybrid-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-50000,4,5,20(1)', 'name': 'H-QPFM'},
        {'prefix': 'Hybrid-ADAPTIVE_TOP_K-BITRATE_MAXIMIZATION-40000,4,5,20(1)', 'name': 'H-TK-BM'},
        {'prefix': 'Hybrid-ADAPTIVE_TOP_K-PF_MAXIMIZATION-40000,4,5,20(1)', 'name': 'H-TK-PFM'},
        {'prefix': 'Hybrid-ADAPTIVE_TOP_K-QUEUE_AWARE_PF_MAXIMIZATION-40000,4,5,20(1)', 'name': 'H-TK-QPFM'},
        {'prefix': 'Hybrid-ADAPTIVE_TOP_K-QUEUE_LENGTH_MINIMIZATION-40000,4,5,20(1)', 'name': 'H-TK-QLM'},
        {'prefix': 'Hybrid-SERVING_ALL-QUEUE_AWARE_PF_MAXIMIZATION-40000,4,5,20(1)', 'name': 'H-SA'}
    ]

directory = 'output'  # Directory where the JSON files are stored

save_statistics_to_file(digital_scenarios + hybrid_scenarios, directory)
