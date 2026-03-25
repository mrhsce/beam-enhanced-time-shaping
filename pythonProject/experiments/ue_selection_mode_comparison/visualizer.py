import json
import matplotlib.pyplot as plt
import numpy as np

# Load data from the JSON file
with open('statistics.json', 'r') as file:
    data = json.load(file)

# Extracting data from the loaded JSON
frames = data['frames']
active_ues = data['active_ues']
delays = data['delays']
jitters = data['jitters']
queues = data['queues']


def create_bar_chart_with_values_and_ci(metric_data, ylabel, filename):
    hybrid_scenarios_complete = ["H-BM", "H-PFM", "H-QLM", "H-QPFM", "H-TK-BM", "H-TK-PFM", "H-TK-QPFM", "H-TK-QLM",
                                 "H-SA"]
    hybrid_scenarios = ["H-BM", "H-PFM", "H-QLM", "H-QPFM", "H-SA"]
    digital_scenarios_complete = ["D-BM", "D-PFM", "D-QLM", "D-QPFM", "D-TK-BM", "D-TK-PFM", "D-TK-QPFM", "D-TK-QLM",
                                  "D-SA"]
    digital_scenarios = ["D-BM", "D-PFM", "D-QLM", "D-QPFM", "D-SA"]

    metric_means = [metric_data[scenario][3] for scenario in digital_scenarios_complete]  # Mean values
    metric_stds = [metric_data[scenario][6] for scenario in digital_scenarios_complete]  # Standard deviations
    metric_counts = [metric_data[scenario][7] for scenario in digital_scenarios_complete]  # Sample counts
    print (metric_counts)

    # Calculate 95% confidence intervals
    metric_cis = [1.96 * (std / np.sqrt(count)) for std, count in zip(metric_stds, metric_counts)]

    x = np.arange(len(digital_scenarios_complete))  # the label locations
    width = 0.8  # the width of the bars

    fig, ax = plt.subplots(figsize=(15, 7))
    bars = ax.bar(x, metric_means, width, yerr=metric_cis, capsize=5, label='Mean Values')

    # Add some text for labels, and custom x-axis tick labels, etc.
    ax.set_ylabel(ylabel, fontsize=18)
    ax.set_xticks(x)
    ax.yaxis.set_tick_params(labelsize=18)
    ax.set_xticklabels(digital_scenarios_complete, fontsize=18)

    # Adding values on top of bars
    def add_values(bars):
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.2f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=14)

    add_values(bars)

    fig.tight_layout()

    plt.savefig(f'graphs/{filename}')
    plt.close()


# Create bar charts for each metric with values and confidence intervals on top of bars
# create_bar_chart_with_values_and_ci(frames, "Frames", "frames.png")
# create_bar_chart_with_values_and_ci(active_ues, "Active UEs", "active_ues.png")
create_bar_chart_with_values_and_ci(delays, "Delay (ms)", "delays.png")
# create_bar_chart_with_values_and_ci(jitters, "Jitters (ms)", "jitters.png")
# create_bar_chart_with_values_and_ci(queues, "Queue length", "queues.png")
