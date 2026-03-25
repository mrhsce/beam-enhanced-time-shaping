import os
import json
import matplotlib.pyplot as plt
import numpy as np

def load_json_files(execution_name, directory):
    # Find all JSON files in the directory that start with the execution_name
    files = [f for f in os.listdir(directory) if f.startswith(execution_name) and f.endswith('.json')]
    return files

def process_execution_times(files, directory, bs_count=4):
    ue_association = []
    beam_sweeping = []
    ue_selection = []
    digital_beamforming = []

    for file in files:
        file_path = os.path.join(directory, file)
        with open(file_path, 'r') as f:
            data = json.load(f)
        # Extract the "time" element at the beginning of the JSON file
        times = data["time"]
        if len(times) > 4:
            ue_association.append(times[1])
            beam_sweeping.append(times[2])
            ue_selection.append(times[3] / bs_count)
            digital_beamforming.append(times[4] / bs_count)
    return ue_association, beam_sweeping, ue_selection, digital_beamforming

def extract_execution_length(prefix):
    parts = prefix.split('-')
    for part in parts:
        if ',' in part:
            number_str = part.split(',')[0]
            if number_str.isdigit():
                return int(number_str)
    return None

def plot_execution_times(scenarios, directory, bs_count=4, show_values=False):
    scenario_averages_total = {}
    scenario_averages_stepwise = {}

    for scenario in scenarios:
        execution_name = scenario['prefix']
        scenario_name = scenario['name']
        files = load_json_files(execution_name, directory)
        ue_association, beam_sweeping, ue_selection, digital_beamforming = process_execution_times(files, directory, bs_count)
        if ue_association and beam_sweeping and ue_selection and digital_beamforming:
            scenario_averages_total[scenario_name] = {
                'UE Association': np.mean(ue_association),
                'Beam Sweeping': np.mean(beam_sweeping),
                'UE Selection': np.mean(ue_selection),
                'Digital Beamforming': np.mean(digital_beamforming)
            }

            execution_length = extract_execution_length(execution_name)
            if execution_length:
                scenario_averages_stepwise[scenario_name] = {
                    'UE Association': (np.mean(ue_association) / (execution_length / 1000)) * 1000,
                    'Beam Sweeping': (np.mean(beam_sweeping) / (execution_length / 100)) * 1000,
                    'UE Selection': (np.mean(ue_selection) / (execution_length / 10)) * 1000,
                    'Digital Beamforming': (np.mean(digital_beamforming) / (execution_length / 10)) * 1000
                }

    # Plot bar chart for average execution times
    if scenario_averages_total:
        labels = list(scenario_averages_total.keys())
        ue_association_means = [scenario_averages_total[label]['UE Association'] for label in labels]
        beam_sweeping_means = [scenario_averages_total[label]['Beam Sweeping'] for label in labels]
        ue_selection_means = [scenario_averages_total[label]['UE Selection'] for label in labels]
        digital_beamforming_means = [scenario_averages_total[label]['Digital Beamforming'] for label in labels]

        x = np.arange(len(labels))  # the label locations
        width = 0.2  # the width of the bars

        fig, ax = plt.subplots(figsize=(12, 6))
        rects1 = ax.bar(x - 1.5 * width, ue_association_means, width, label='UE Association')
        rects2 = ax.bar(x - 0.5 * width, beam_sweeping_means, width, label='Beam Sweeping')
        rects3 = ax.bar(x + 0.5 * width, ue_selection_means, width, label='UE Selection')
        rects4 = ax.bar(x + 1.5 * width, digital_beamforming_means, width, label='Digital Beamforming')

        if show_values:
            def add_labels(rects):
                for rect in rects:
                    height = rect.get_height()
                    ax.annotate(f'{height:.2f}',
                                xy=(rect.get_x() + rect.get_width() / 2, height),
                                xytext=(0, 3),  # 3 points vertical offset
                                textcoords="offset points",
                                ha='center', va='bottom')

            add_labels(rects1)
            add_labels(rects2)
            add_labels(rects3)
            add_labels(rects4)

        # Add some text for labels, title and custom x-axis tick labels, etc.
        ax.set_xlabel('Scenario')
        ax.set_ylabel('Average Execution Time (s)')
        ax.set_title('Average Total Execution Time by Mode')
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()

        fig.tight_layout()
        plt.grid(True)
        # plt.show()

        # Save the figure with a DPI of 300
        if not os.path.exists('graphs'):
            os.makedirs('graphs')
        fig.savefig(os.path.join('graphs', 'average_total_execution_times.png'), dpi=300)

    # Plot bar chart for stepwise execution times
    if scenario_averages_stepwise:
        labels = list(scenario_averages_stepwise.keys())
        ue_association_means = [scenario_averages_stepwise[label]['UE Association'] for label in labels]
        beam_sweeping_means = [scenario_averages_stepwise[label]['Beam Sweeping'] for label in labels]
        ue_selection_means = [scenario_averages_stepwise[label]['UE Selection'] for label in labels]
        digital_beamforming_means = [scenario_averages_stepwise[label]['Digital Beamforming'] for label in labels]

        x = np.arange(len(labels))  # the label locations
        width = 0.2  # the width of the bars

        fig, ax = plt.subplots(figsize=(12, 6))
        rects1 = ax.bar(x - 1.5 * width, ue_association_means, width, label='UE Association')
        rects2 = ax.bar(x - 0.5 * width, beam_sweeping_means, width, label='Beam Sweeping')
        rects3 = ax.bar(x + 0.5 * width, ue_selection_means, width, label='UE Selection')
        rects4 = ax.bar(x + 1.5 * width, digital_beamforming_means, width, label='Digital Beamforming')

        if show_values:
            def add_labels(rects):
                for rect in rects:
                    height = rect.get_height()
                    ax.annotate(f'{height:.2f}',
                                xy=(rect.get_x() + rect.get_width() / 2, height),
                                xytext=(0, 3),  # 3 points vertical offset
                                textcoords="offset points",
                                ha='center', va='bottom')

            add_labels(rects1)
            add_labels(rects2)
            add_labels(rects3)
            add_labels(rects4)

        # Add some text for labels, title and custom x-axis tick labels, etc.
        ax.set_xlabel('Scenario')
        ax.set_ylabel('Average Stepwise Execution Time (ms)')
        ax.set_title('Average Stepwise Execution Time by Mode')
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()

        fig.tight_layout()
        plt.grid(True)
        # plt.show()

        # Save the figure with a DPI of 300
        if not os.path.exists('graphs'):
            os.makedirs('graphs')
        fig.savefig(os.path.join('graphs', 'average_stepwise_execution_times.png'), dpi=300)


# Main execution
if __name__ == "__main__":
    scenarios_hybrid = [
        {'prefix': 'Hybrid-GREEDY-BITRATE_MAXIMIZATION-20000,16,5,80', 'name': 'H-BM(16)'},
        {'prefix': 'Hybrid-GREEDY-BITRATE_MAXIMIZATION-20000,2,5,10', 'name': 'H-BM(2)'},
        {'prefix': 'Hybrid-GREEDY-BITRATE_MAXIMIZATION-20000,32,5,160', 'name': 'H-BM(32)'},
        {'prefix': 'Hybrid-GREEDY-BITRATE_MAXIMIZATION-20000,8,5,40', 'name': 'H-BM(8)'},
        {'prefix': 'Hybrid-GREEDY-BITRATE_MAXIMIZATION-50000,4,5,20(1)', 'name': 'H-BM(4)'},
        {'prefix': 'Hybrid-GREEDY-PF_MAXIMIZATION-20000,16,5,80', 'name': 'H-PFM(16)'},
        {'prefix': 'Hybrid-GREEDY-PF_MAXIMIZATION-20000,2,5,10', 'name': 'H-PFM(2)'},
        {'prefix': 'Hybrid-GREEDY-PF_MAXIMIZATION-20000,32,5,160', 'name': 'H-PFM(32)'},
        {'prefix': 'Hybrid-GREEDY-PF_MAXIMIZATION-20000,8,5,40', 'name': 'H-PFM(8)'},
        {'prefix': 'Hybrid-GREEDY-PF_MAXIMIZATION-50000,4,5,20(1)', 'name': 'H-PFM(4)'},
        {'prefix': 'Hybrid-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-20000,16,5,80', 'name': 'H-QPFM(16)'},
        {'prefix': 'Hybrid-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-20000,2,5,10', 'name': 'H-QPFM(2)'},
        {'prefix': 'Hybrid-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-20000,32,5,160', 'name': 'H-QPFM(32)'},
        {'prefix': 'Hybrid-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-20000,8,5,40', 'name': 'H-QPFM(8)'},
        {'prefix': 'Hybrid-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-50000,4,5,20(1)', 'name': 'H-QPFM(4)'},
        {'prefix': 'Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-20000,16,5,80', 'name': 'H-QLM(16)'},
        {'prefix': 'Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-20000,2,5,10', 'name': 'H-QLM(2)'},
        {'prefix': 'Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-20000,32,5,160', 'name': 'H-QLM(32)'},
        {'prefix': 'Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-20000,8,5,40', 'name': 'H-QLM(8)'},
        {'prefix': 'Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-50000,4,5,20(1)', 'name': 'H-QLM(4)'},
    ]

    highest_comparison_hybrid = [
        {'prefix': 'Hybrid-GREEDY-BITRATE_MAXIMIZATION-20000,32,5,160', 'name': 'H-BM(32)'},
        {'prefix': 'Hybrid-GREEDY-PF_MAXIMIZATION-20000,32,5,160', 'name': 'H-PFM(32)'},
        {'prefix': 'Hybrid-GREEDY-QUEUE_AWARE_PF_MAXIMIZATION-20000,32,5,160', 'name': 'H-QPFM(32)'},
        {'prefix': 'Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-20000,32,5,160', 'name': 'H-QLM(32)'},
    ]

    hybrid_qlm = [
        {'prefix': 'Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-20000,2,5,10', 'name': 'H-QLM(2)'},
        {'prefix': 'Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-50000,4,5,20(1)', 'name': 'H-QLM(4)'},
        {'prefix': 'Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-20000,8,5,40', 'name': 'H-QLM(8)'},
        {'prefix': 'Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-20000,16,5,80', 'name': 'H-QLM(16)'},
        {'prefix': 'Hybrid-GREEDY-QUEUE_LENGTH_MINIMIZATION-20000,32,5,160', 'name': 'H-QLM(32)'},
    ]

    directory = 'output'  # Directory where the JSON files are stored
    bs_count = 4  # Default BS count

    plot_execution_times(hybrid_qlm, directory, bs_count, show_values=True)
