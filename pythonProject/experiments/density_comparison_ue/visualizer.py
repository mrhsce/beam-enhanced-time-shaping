import matplotlib.pyplot as plt
import os
from data import active_ues, delays, jitters, queues, frames

# Combine all your data dictionaries into a single dictionary
data_dictionaries = {
    'active_ues': active_ues,
    'delay': delays,
    'jitter': jitters,
    'queue': queues,
    'frames': frames
}

# Create the 'graphs' directory if it doesn't exist
os.makedirs('graphs', exist_ok=True)

# Define labels and units for each type of data
labels = {
    'active_ues': ('Number of Active UEs', 'Number of Active UEs vs Injection Rate for Different Scenarios'),
    'delay': ('Delay (ms)', 'Latency (ms) vs Injection Rate for Different Scenarios'),
    'jitter': ('Jitter (ms)', 'Jitter (ms) vs Injection Rate for Different Scenarios'),
    'queue': ('Queue Length', 'Queue Length vs Injection Rate for Different Scenarios'),
    'frames': ('Number of Frames', 'Number of Frames vs Injection Rate for Different Scenarios')
}

# Define digital and hybrid modes
digital_modes = ['D_QPFM', 'D_QLM', 'D_BM', 'D_PFM']
hybrid_modes = ['H_QPFM', 'H_QLM', 'H_BM', 'H_PFM']


def plot_graphs(selected_modes=None, xlabel_fontsize=12, ylabel_fontsize=12, xtick_fontsize=10, ytick_fontsize=10,
                legend_fontsize=10):
    for data_name, data in data_dictionaries.items():
        plt.figure(figsize=(10, 6))

        for scenario, values in data.items():
            if selected_modes is None or scenario in selected_modes:
                ue_count = [8, 20, 32, 64, 128]
                ue_count_limited = [8, 20, 32, 64, 128]
                values_at_rate = [values[rate][3] for rate in ue_count_limited]  # Adjust if needed

                # Determine line style based on mode
                if scenario in digital_modes:
                    line_style = '--'  # Dashed line for digital modes
                elif scenario in hybrid_modes:
                    line_style = '-'  # Solid line for hybrid modes
                else:
                    line_style = '-'  # Default to solid line

                plt.plot(ue_count_limited, values_at_rate, marker='o', linestyle=line_style, label=scenario)

        plt.xlabel('UE count', fontsize=xlabel_fontsize)
        plt.ylabel(labels[data_name][0], fontsize=ylabel_fontsize)

        # Customize tick font sizes
        plt.xticks(fontsize=xtick_fontsize)
        plt.yticks(fontsize=ytick_fontsize)

        # Remove the graph title
        # plt.title(labels[data_name][1])  # Commented out to remove the title

        # Customize legend font size
        plt.legend(fontsize=legend_fontsize)

        plt.grid(True)
        plt.savefig(f'graphs/{data_name}_vs_ue_count.png')
        plt.close()


# Call the function with all modes
all_modes = digital_modes + hybrid_modes
plot_graphs(selected_modes=all_modes, xlabel_fontsize=16, ylabel_fontsize=16, xtick_fontsize=14, ytick_fontsize=14,
            legend_fontsize=14)

# Example usage to include specific modes:
# plot_graphs(selected_modes=['H_QPFM', 'D_QPFM'])
