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

def plot_graphs(selected_modes=None, x_font_size=12, y_font_size=12, tick_font_size=10, legend_font_size=10):
    for data_name, data in data_dictionaries.items():
        plt.figure(figsize=(10, 6))

        for scenario, values in data.items():
            if selected_modes is None or scenario in selected_modes:
                bs_count = [2,4,8,16,32]
                values_at_rate = [values[rate][3] for rate in bs_count]  # Adjust if needed

                # Determine line style based on mode
                if scenario in digital_modes:
                    line_style = '--'  # Dashed line for digital modes
                elif scenario in hybrid_modes:
                    line_style = '-'   # Solid line for hybrid modes
                else:
                    line_style = '-'   # Default to solid line

                plt.plot(bs_count, values_at_rate, marker='o', linestyle=line_style, label=scenario)

        plt.xlabel('UE count', fontsize=x_font_size)
        plt.ylabel(labels[data_name][0], fontsize=y_font_size)
        plt.xticks(fontsize=tick_font_size)
        plt.yticks(fontsize=tick_font_size)
        plt.legend(fontsize=legend_font_size)
        plt.grid(True)
        plt.savefig(f'graphs/{data_name}_vs_bs_count.png')
        plt.close()

# Call the function with all modes and customizable font sizes
all_modes = digital_modes + hybrid_modes
plot_graphs(selected_modes=hybrid_modes, x_font_size=16, y_font_size=16, tick_font_size=14, legend_font_size=16)

# Example usage to include specific modes:
# plot_graphs(selected_modes=['H_QPFM', 'D_QPFM'], x_font_size=14, y_font_size=14, tick_font_size=12, legend_font_size=12)
