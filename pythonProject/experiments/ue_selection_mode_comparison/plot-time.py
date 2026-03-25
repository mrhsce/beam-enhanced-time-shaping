import os
import json
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats


def load_json_files(execution_name, directory):
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


def calculate_confidence_intervals(data, confidence=0.95):
    if len(data) > 1:
        mean = np.mean(data)
        se = stats.sem(data)
        interval = se * stats.t.ppf((1 + confidence) / 2., len(data) - 1)
        return mean, interval
    else:
        return np.mean(data), 0


def plot_execution_times(scenarios, directory, bs_count=4, show_values=False):
    scenario_averages_total = {}
    scenario_averages_stepwise = {}

    for scenario in scenarios:
        execution_name = scenario['prefix']
        scenario_name = scenario['name']
        files = load_json_files(execution_name, directory)
        ue_association, beam_sweeping, ue_selection, digital_beamforming = process_execution_times(files, directory,
                                                                                                   bs_count)
        if ue_association and beam_sweeping and ue_selection and digital_beamforming:
            ue_association_mean, ue_association_ci = calculate_confidence_intervals(ue_association)
            beam_sweeping_mean, beam_sweeping_ci = calculate_confidence_intervals(beam_sweeping)
            ue_selection_mean, ue_selection_ci = calculate_confidence_intervals(ue_selection)
            digital_beamforming_mean, digital_beamforming_ci = calculate_confidence_intervals(digital_beamforming)

            scenario_averages_total[scenario_name] = {
                'UE Association': (ue_association_mean, ue_association_ci),
                'Beam Sweeping': (beam_sweeping_mean, beam_sweeping_ci),
                'UE Selection': (ue_selection_mean, ue_selection_ci),
                'Digital Beamforming': (digital_beamforming_mean, digital_beamforming_ci)
            }

            execution_length = extract_execution_length(execution_name)
            if execution_length:
                scenario_averages_stepwise[scenario_name] = {
                    'UE Association': ((ue_association_mean / (execution_length / 1000)) * 1000,
                                       (ue_association_ci / (execution_length / 1000)) * 1000),
                    'Beam Sweeping': ((beam_sweeping_mean / (execution_length / 100)) * 1000,
                                      (beam_sweeping_ci / (execution_length / 100)) * 1000),
                    'UE Selection': ((ue_selection_mean / (execution_length / 10)) * 1000,
                                     (ue_selection_ci / (execution_length / 10)) * 1000),
                    'Digital Beamforming': ((digital_beamforming_mean / (execution_length / 10)) * 1000,
                                            (digital_beamforming_ci / (execution_length / 10)) * 1000)
                }

    if scenario_averages_total:
        labels = list(scenario_averages_total.keys())
        ue_association_means = [scenario_averages_total[label]['UE Association'][0] for label in labels]
        ue_association_cis = [scenario_averages_total[label]['UE Association'][1] for label in labels]
        beam_sweeping_means = [scenario_averages_total[label]['Beam Sweeping'][0] for label in labels]
        beam_sweeping_cis = [scenario_averages_total[label]['Beam Sweeping'][1] for label in labels]
        ue_selection_means = [scenario_averages_total[label]['UE Selection'][0] for label in labels]
        ue_selection_cis = [scenario_averages_total[label]['UE Selection'][1] for label in labels]
        digital_beamforming_means = [scenario_averages_total[label]['Digital Beamforming'][0] for label in labels]
        digital_beamforming_cis = [scenario_averages_total[label]['Digital Beamforming'][1] for label in labels]

        x = np.arange(len(labels))
        width = 0.2

        fig, ax = plt.subplots(figsize=(12, 6))
        rects1 = ax.bar(x - 1.5 * width, ue_association_means, width, yerr=ue_association_cis, label='UE Association',
                        capsize=5)
        rects2 = ax.bar(x - 0.5 * width, beam_sweeping_means, width, yerr=beam_sweeping_cis, label='Beam Sweeping',
                        capsize=5)
        rects3 = ax.bar(x + 0.5 * width, ue_selection_means, width, yerr=ue_selection_cis, label='UE Selection',
                        capsize=5)
        rects4 = ax.bar(x + 1.5 * width, digital_beamforming_means, width, yerr=digital_beamforming_cis,
                        label='Digital Beamforming', capsize=5)

        if show_values:
            def add_labels(rects):
                for rect in rects:
                    height = rect.get_height()
                    ax.annotate(f'{height:.2f}',
                                xy=(rect.get_x() + rect.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha='center', va='bottom')

            add_labels(rects1)
            add_labels(rects2)
            add_labels(rects3)
            add_labels(rects4)

        ax.set_xlabel('Scenario', fontsize=16)
        ax.set_ylabel('Average Execution Time (s)', fontsize=16)
        ax.set_title('Average Total Execution Time by Mode', fontsize=18)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=14)
        ax.legend(fontsize=14, loc='center right')

        fig.tight_layout()
        plt.grid(True)

        if not os.path.exists('graphs'):
            os.makedirs('graphs')
        fig.savefig(os.path.join('graphs', 'average_total_execution_times.png'), dpi=300)

    if scenario_averages_stepwise:
        labels = list(scenario_averages_stepwise.keys())
        ue_association_means = [scenario_averages_stepwise[label]['UE Association'][0] for label in labels]
        ue_association_cis = [scenario_averages_stepwise[label]['UE Association'][1] for label in labels]
        beam_sweeping_means = [scenario_averages_stepwise[label]['Beam Sweeping'][0] for label in labels]
        beam_sweeping_cis = [scenario_averages_stepwise[label]['Beam Sweeping'][1] for label in labels]
        ue_selection_means = [scenario_averages_stepwise[label]['UE Selection'][0] for label in labels]
        ue_selection_cis = [scenario_averages_stepwise[label]['UE Selection'][1] for label in labels]
        digital_beamforming_means = [scenario_averages_stepwise[label]['Digital Beamforming'][0] for label in labels]
        digital_beamforming_cis = [scenario_averages_stepwise[label]['Digital Beamforming'][1] for label in labels]

        x = np.arange(len(labels))
        width = 0.2

        fig, ax = plt.subplots(figsize=(12, 6))
        rects1 = ax.bar(x - 1.5 * width, ue_association_means, width, yerr=ue_association_cis, label='UE Association',
                        capsize=5)
        rects2 = ax.bar(x - 0.5 * width, beam_sweeping_means, width, yerr=beam_sweeping_cis, label='Beam Sweeping',
                        capsize=5)
        rects3 = ax.bar(x + 0.5 * width, ue_selection_means, width, yerr=ue_selection_cis, label='UE Selection',
                        capsize=5)
        rects4 = ax.bar(x + 1.5 * width, digital_beamforming_means, width, yerr=digital_beamforming_cis,
                        label='Digital Beamforming', capsize=5)

        if show_values:
            def add_labels(rects):
                for rect in rects:
                    height = rect.get_height()
                    ax.annotate(f'{height:.2f}',
                                xy=(rect.get_x() + rect.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha='center', va='bottom')

            add_labels(rects1)
            add_labels(rects2)
            add_labels(rects3)
            add_labels(rects4)

        ax.set_xlabel('Scenario', fontsize=16)
        ax.set_ylabel('Average Stepwise Execution Time (ms)', fontsize=16)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=14)
        ax.legend(fontsize=14, loc='center right')

        fig.tight_layout()
        plt.grid(True)

        if not os.path.exists('graphs'):
            os.makedirs('graphs')
        fig.savefig(os.path.join('graphs', 'average_stepwise_execution_times.png'), dpi=300)


# Main execution
if __name__ == "__main__":
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
    directory = 'output'
    bs_count = 4

    plot_execution_times(hybrid_scenarios, directory, bs_count, show_values=True)
