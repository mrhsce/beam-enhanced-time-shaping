import matplotlib.pyplot as plt
import numpy as np
import os
import json

# Load statistics from JSON file
statistics_file = 'statistics.json'
with open(statistics_file, 'r') as file:
    statistics_data = json.load(file)

# Ensure the output directory exists
output_dir = 'graphs'
os.makedirs(output_dir, exist_ok=True)

def calculate_confidence_interval(mean, std, n, confidence=0.95):
    z_score = 1.96  # Z-score for 95% confidence interval
    margin_of_error = z_score * (std / np.sqrt(n))
    return mean - margin_of_error, mean + margin_of_error

def plot_metric(metric_data, metric_name, ylabel, output_file, font_sizes):
    # Extract the mean values and standard deviations for each scenario and its extended version
    mean_values = {key: value[3] for key, value in metric_data.items()}
    std_values = {key: value[6] for key, value in metric_data.items()}
    n_values = {key: value[7] for key, value in metric_data.items()}

    # Scenarios and their extended versions
    scenarios = ['D-QPFM', 'D-QLM', 'H-QPFM', 'H-QLM']
    all_labels = [label for pair in zip(scenarios, [s + "-S" for s in scenarios]) for label in pair]

    # Values to plot
    values_to_plot = [mean_values[label] for label in all_labels]

    # Calculate the confidence intervals
    yerr = [
        (mean_values[label] - calculate_confidence_interval(mean_values[label], std_values[label], n_values[label])[0],
         calculate_confidence_interval(mean_values[label], std_values[label], n_values[label])[1] - mean_values[label])
        for label in all_labels
    ]

    # Calculate the percentage of improvement
    improvements = []
    for i in range(0, len(values_to_plot), 2):
        without_s = values_to_plot[i]
        with_s = values_to_plot[i + 1]
        improvement = ((without_s - with_s) / without_s) * 100
        improvements.append(improvement)

    x = np.arange(len(scenarios))  # the label locations
    width = 0.35  # the width of the bars

    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot the bars
    bars1 = ax.bar(x - width / 2, values_to_plot[0::2], width, label='Without Multi-precoder',
                   yerr=np.array(yerr[0::2]).T, capsize=5)
    bars2 = ax.bar(x + width / 2, values_to_plot[1::2], width, label='With Multi-precoder',
                   yerr=np.array(yerr[1::2]).T, capsize=5)

    # Add some text for labels, title, and custom x-axis tick labels, etc.
    ax.set_xlabel('Scenarios', fontsize=font_sizes['axis_label'])
    ax.set_ylabel(ylabel, fontsize=font_sizes['axis_label'])
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios, fontsize=font_sizes['tick_labels'])
    ax.tick_params(axis='y', labelsize=font_sizes['tick_labels'])
    ax.legend(fontsize=font_sizes['legend'])

    # Add percentage improvement text above bars
    for i in range(len(improvements)):
        height = max(bars1[i].get_height(), bars2[i].get_height())
        ax.text(x[i], height, f'{improvements[i]:.2f}%', ha='center', va='bottom', fontsize=font_sizes['text'])

    fig.tight_layout()
    plt.savefig(os.path.join(output_dir, output_file))
    plt.close(fig)

# Define font sizes
font_sizes = {
    'axis_label': 16,
    'tick_labels': 14,
    'legend': 16,
    'text': 14
}

# Plot and save each metric
plot_metric(statistics_data['delays'], 'delay', 'Delay (ms)', 'delays_comparison.png', font_sizes)
plot_metric(statistics_data['jitters'], 'jitter', 'Jitter (ms)', 'jitters_comparison.png', font_sizes)
plot_metric(statistics_data['queues'], 'queue length', 'Queue Length', 'queues_comparison.png', font_sizes)

print("Graphs have been saved in the 'graphs' directory.")
