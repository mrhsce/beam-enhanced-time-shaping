import matplotlib.pyplot as plt
import numpy as np
import os

# Import data from data_density_ue.py
from data_density_ue import delays, jitters, queues

# Ensure the output directory exists
output_dir = 'graphs'
os.makedirs(output_dir, exist_ok=True)

def plot_metric(metric_data, metric_name, ylabel, output_file):
    # Extract UE counts
    ue_counts = list(metric_data['H_QPFM'].keys())

    # Scenarios and their extended versions
    scenarios = ['H_QPFM']
    scenarios_m = ['H_QPFM_M']

    fig, ax = plt.subplots(figsize=(10, 6))

    for scenario, scenario_m in zip(scenarios, scenarios_m):
        mean_values = {ue: metric_data[scenario][ue][3] for ue in ue_counts}
        mean_values_m = {ue: metric_data[scenario_m][ue][3] for ue in ue_counts}

        values_to_plot = [mean_values[ue] for ue in ue_counts]
        values_to_plot_m = [mean_values_m[ue] for ue in ue_counts]

        x = np.arange(len(ue_counts))  # the label locations
        width = 0.35  # the width of the bars

        bars1 = ax.bar(x - width/2, values_to_plot, width, label=f'{scenario} Without Multi-precoder')
        bars2 = ax.bar(x + width/2, values_to_plot_m, width, label=f'{scenario} With Multi-precoder')

        # Calculate the percentage of improvement
        improvements = []
        for ue in ue_counts:
            without_s = mean_values[ue]
            with_s = mean_values_m[ue]
            improvement = ((without_s - with_s) / without_s) * 100
            improvements.append(improvement)

        # Add percentage improvement text above bars
        for i in range(len(improvements)):
            height = max(bars1[i].get_height(), bars2[i].get_height())
            ax.text(x[i], height, f'{improvements[i]:.2f}%', ha='center', va='bottom')

    # Add some text for labels, title, and custom x-axis tick labels, etc.
    ax.set_xlabel('UE Count')
    ax.set_ylabel(ylabel)
    ax.set_title(f'Comparison of Average {metric_name.capitalize()} with and without Multi-precoder')
    ax.set_xticks(x)
    ax.set_xticklabels(ue_counts)
    ax.legend()

    fig.tight_layout()
    plt.savefig(os.path.join(output_dir, output_file))
    plt.close(fig)

# Plot and save each metric
plot_metric(delays, 'delay', 'Delay (ms)', 'delays_comparison_density_ue.png')
plot_metric(jitters, 'jitter', 'Jitter (ms)', 'jitters_comparison_density_ue.png')
plot_metric(queues, 'queue length', 'Queue Length', 'queues_comparison_density_ue.png')

print("Graphs have been saved in the 'graphs' directory.")
