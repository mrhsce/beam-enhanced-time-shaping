import json
import numpy as np
import matplotlib.pyplot as plt


def load_statistics(file_path):
    with open(file_path, 'r') as file:
        stats = json.load(file)
    return stats


def create_bar_chart_three_groups_with_values(stats, metric, title, ylabel, filename, include_ci=False):
    scenarios = ["SM-D", "SM-H", "STA-D", "STA-H", "RND-D", "RND-H"]
    metric_means = [stats[metric][scenario][3] for scenario in scenarios]  # Mean values

    # Grouping data
    group1 = metric_means[:2]
    group2 = metric_means[2:4]
    group3 = metric_means[4:]

    x = np.arange(len(group1))  # the label locations
    width = 0.2  # the width of the bars

    fig, ax = plt.subplots()

    if include_ci:
        errors = [1.96 * (stats[metric][scenario][6] / np.sqrt(stats[metric][scenario][7])) for scenario in scenarios]
        group1_errors = errors[:2]
        group2_errors = errors[2:4]
        group3_errors = errors[4:]
        bars1 = ax.bar(x - width, group1, width, label='Stable marriage', yerr=group1_errors, capsize=5)
        bars2 = ax.bar(x + width, group2, width, label='Static', yerr=group2_errors, capsize=5)
        bars3 = ax.bar(x, group3, width, label='Random', yerr=group3_errors, capsize=5)
    else:
        bars1 = ax.bar(x - width, group1, width, label='Stable marriage')
        bars2 = ax.bar(x + width, group2, width, label='Static')
        bars3 = ax.bar(x, group3, width, label='Random')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel(ylabel)
    # ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(['Digital', 'Hybrid'])
    ax.legend()

    # Adding values on top of bars
    def add_values(bars):
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.2f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom')

    add_values(bars1)
    add_values(bars2)
    add_values(bars3)

    fig.tight_layout()

    plt.savefig(f'graphs/{filename}')
    plt.close()


# Main execution
stats_file_path = 'statistics.json'
stats = load_statistics(stats_file_path)

# Create bar charts for each metric with three groups and values on top of bars
# create_bar_chart_three_groups_with_values(stats, 'frames', "Comparison of Frames sent Across Scenarios", "Frames", "frames.png", include_ci=False)
create_bar_chart_three_groups_with_values(stats, 'active_ues', "Comparison of Active UEs Across Scenarios", "Active UEs", "active_ues.png", include_ci=True)
create_bar_chart_three_groups_with_values(stats, 'delays', "Comparison of Delays Across Scenarios", "Delays(ms)", "delays.png", include_ci=True)
# create_bar_chart_three_groups_with_values(stats, 'jitters', "Comparison of Jitters Across Scenarios", "Jitters(ms)", "jitters.png", include_ci=True)
# create_bar_chart_three_groups_with_values(stats, 'queues', "Comparison of Queues Across Scenarios", "Queue length", "queues.png", include_ci=True)
