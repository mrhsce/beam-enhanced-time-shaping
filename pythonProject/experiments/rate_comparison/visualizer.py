import json
import matplotlib.pyplot as plt
import os

with open('statistics.json', 'r') as file:
    data = json.load(file)

# Combine all your data dictionaries into a single dictionary
data_dictionaries = {
    'delay': data['delays'],
    'jitter': data['jitters'],
}

# Create the 'graphs' directory if it doesn't exist
os.makedirs('graphs', exist_ok=True)

# Define labels and units for each type of data
labels = {
    'delay': ('Delay (ms)', 'Delay (ms) vs Injection Rate for Different Scenarios'),
    'jitter': ('Jitter (ms)', 'Jitter (ms) vs Injection Rate for Different Scenarios'),
}

# Define digital and hybrid modes
digital_modes = ['D-QPFM', 'D-QLM', 'D-BM', 'D-PFM']
hybrid_modes = ['H-QPFM', 'H-QLM', 'H-BM', 'H-PFM']

def plot_graphs(selected_modes=None, xlabel_fontsize=12, ylabel_fontsize=12, ytick_fontsize=10, legend_fontsize=10):
    for data_name, data in data_dictionaries.items():
        plt.figure(figsize=(10, 6))

        for scenario, values in data.items():
            if selected_modes is None or scenario in selected_modes:
                injection_rates = ["0.3", "0.7", "1.0", "1.7", "3.0"]
                injection_rates_limited = ["0.3", "0.7", "1.0", "1.7"]
                values_at_rate = [values[rate][3] for rate in injection_rates_limited]  # Adjust if needed

                # Determine line style based on mode
                if scenario in digital_modes:
                    line_style = '--'  # Dashed line for digital modes
                elif scenario in hybrid_modes:
                    line_style = '-'   # Solid line for hybrid modes
                else:
                    line_style = '-'   # Default to solid line

                plt.plot(injection_rates_limited, values_at_rate, marker='o', linestyle=line_style, label=scenario)

        plt.xlabel('Injection Rate (average SE in b/s/Hz per UE)', fontsize=xlabel_fontsize)
        plt.ylabel(labels[data_name][0], fontsize=ylabel_fontsize)
        plt.xticks(fontsize=ytick_fontsize)
        plt.yticks(fontsize=ytick_fontsize)
        plt.legend(fontsize=legend_fontsize)
        plt.grid(True)
        plt.savefig(f'graphs/{data_name}_vs_injection_rate_limited.png')
        plt.close()

# Call the function with all modes and custom font sizes
all_modes = digital_modes + hybrid_modes
plot_graphs(selected_modes=all_modes, xlabel_fontsize=16, ylabel_fontsize=16, ytick_fontsize=14, legend_fontsize=16)
