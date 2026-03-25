import json
import numpy as np
import matplotlib.pyplot as plt


def load_statistics(file_path):
    with open(file_path, 'r') as file:
        stats = json.load(file)
    return stats


def plot_delays(stats, confidence_level=0.99, include_confidence_interval=True):
    scenarios = list(stats['delays'].keys())
    means = []
    errors = []

    if include_confidence_interval:
        # Select the z-value based on the confidence level
        if confidence_level == 0.99:
            z_value = 2.576
        elif confidence_level == 0.95:
            z_value = 1.96
        else:
            raise ValueError("Unsupported confidence level. Use 0.95 or 0.99.")

    # Calculate mean and confidence interval for each scenario
    for scenario in scenarios:
        mean_delay = stats['delays'][scenario][3]
        means.append(mean_delay)

        if include_confidence_interval:
            std_delay = stats['delays'][scenario][6]
            count = stats['delays'][scenario][7]
            # Confidence interval = z * (std / sqrt(n))
            ci = z_value * (std_delay / np.sqrt(count))
            errors.append(ci)
        else:
            errors.append(0)  # No error bars if confidence interval is not included

    # Plotting
    x_pos = np.arange(len(scenarios))

    plt.figure(figsize=(12, 6))
    plt.bar(x_pos, means, yerr=errors if include_confidence_interval else None, alpha=0.7, capsize=10,
            color='skyblue', edgecolor='black')
    plt.xlabel('Scenarios', fontsize=12)
    plt.ylabel('Mean Delay (ms)', fontsize=12)
    title = 'Comparison of Scenarios in Terms of Delay'
    if include_confidence_interval:
        title += f' with {int(confidence_level * 100)}% Confidence Interval'
    plt.title(title, fontsize=14)
    plt.xticks(x_pos, scenarios, rotation=45, ha='right')
    plt.tight_layout()
    plt.grid(axis='y')

    # Save the plot
    filename = 'delay_comparison'
    if include_confidence_interval:
        filename += f'_with_{int(confidence_level * 100)}_confidence_interval'
    filename += '.png'
    plt.savefig(filename, dpi=300)
    plt.show()


# Main execution
stats_file_path = 'statistics.json'
stats = load_statistics(stats_file_path)
plot_delays(stats, confidence_level=0.99, include_confidence_interval=True)
