import os
import json
import numpy as np

def load_json_files(execution_name, directory):
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

        if "history" in data:
            history = data["history"]
        else:
            continue

        frames = [entry.get("frames", []) for entry in history]
        flattened_frames = [frame for sublist in frames[500:] for frame in sublist]
        scenario_data['frames'].extend(flattened_frames)

        user_activity = [entry.get("user activity", []) for entry in history]
        active_ues_counts = [sum(1 for ue in sublist if ue > 0) for sublist in user_activity[500:]]
        scenario_data['active_ues'].extend(active_ues_counts)

        average_delays = [entry.get("average delay", []) for entry in history]
        flattened_delays = [delay / 10 for sublist in average_delays[500:] for delay in sublist]
        scenario_data['delays'].extend(flattened_delays)

        queue_lengths = [entry.get("queue lengths", []) for entry in history]
        flattened_lengths = [length for sublist in queue_lengths[500:] for length in sublist]
        scenario_data['queues'].extend(flattened_lengths)

        for delays in average_delays[500:]:
            if len(delays) > 1:
                for i in range(len(delays) - 1):
                    jitter = abs(delays[i + 1] - delays[i]) / 10
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
            if all_values:
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
            else:
                stats[key] = [None] * 8
        else:
            stats[key] = [None] * 8
    return stats

def extract_rate(name):
    # Extract the rate from the name
    try:
        rate_str = name.split('(')[-1][:-1]
        return float(rate_str)
    except ValueError:
        return 1.0  # Default rate if not specified

def save_statistics_to_file(scenarios, directory):
    data_types = ["frames", "active_ues", "delays", "jitters", "queues"]
    all_stats = {data_type: {} for data_type in data_types}
    file_stats = {data_type: {} for data_type in data_types}

    formatted_data = {data_type: {} for data_type in data_types}

    for scenario in scenarios:
        execution_name = scenario['prefix']
        scenario_name = scenario['name']
        rate = extract_rate(scenario_name)  # Extract rate from name
        files = load_json_files(execution_name, directory)
        scenario_data, scenario_file_stats = process_files(files, directory)

        for key in all_stats:
            if key in scenario_data:
                stats = calculate_statistics({key: scenario_data[key]})[key]
                setup_name = scenario_name.split('(')[0]
                if setup_name not in formatted_data[key]:
                    formatted_data[key][setup_name] = {}
                formatted_data[key][setup_name][rate] = stats

    with open('statistics.json', 'w') as file:
        json.dump(formatted_data, file, indent=4)

    for file_key, stats in scenario_file_stats.items():
        for key in file_stats:
            if scenario_name not in file_stats[key]:
                file_stats[key][scenario_name] = {}
            file_stats[key][scenario_name][file_key] = stats[key]

    with open('file_statistics.json', 'w') as file:
        json.dump(file_stats, file, indent=4)

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
        {'prefix': 'Digital-GREEDY-BITRATE_MAXIMIZATION-50000,4,5,20(1)', 'name': 'D-BM(1)'},
        {'prefix': 'Digital-GREEDY-PF_MAXIMIZATION-50000,4,5,20(1)', 'name': 'D-PFM(1)'},
        {'prefix': 'Digital-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-50000,4,5,20(1)', 'name': 'D-QPFM(1)'},
        {'prefix': 'Digital-GREEDY-QUEUE_LENGTH_MINIMIZATION-50000,4,5,20(1)', 'name': 'D-QLM(1)'},
        {'prefix': 'Hybrid-GREEDY-BITRATE_MAXIMIZATION-50000,4,5,20(1)', 'name': 'H-BM(1)'},
        {'prefix': 'Hybrid-GREEDY-PF_MAXIMIZATION-50000,4,5,20(1)', 'name': 'H-PFM(1)'},
        {'prefix': 'Hybrid-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-50000,4,5,20(1)', 'name': 'H-QPFM(1)'},
        {'prefix': 'Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-50000,4,5,20(1)', 'name': 'H-QLM(1)'},
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

directory = 'output'  # Directory where the JSON files are stored

save_statistics_to_file(scenarios, directory)
