import math

import numpy as np
from matplotlib import pyplot as plt

from pythonProject.helper_functions import load_dictionary, store


def plot_multiple_total_spectral_efficiency(scenarios, simulation_name, step=1):
    plt.figure(figsize=(12, 8))
    for scenario in scenarios:
        ue_se_history = [step['se'] for step in scenario['history']]
        time_steps = range(math.ceil(len(ue_se_history) / step))
        time_steps = [element * 10 * step for element in time_steps]
        total_se = []

        for ue_index in range(len(ue_se_history[0])):
            ue_se = [se[ue_index] for se in ue_se_history]
            total_se.append(ue_se[::step])

        total_se = np.sum(np.array(total_se), axis=0)
        style = scenario['style'] if 'style' in scenario else '--'
        plt.plot(time_steps, total_se, label=scenario['name'], linestyle=style)

    plt.title('Comparison of total Spectral Efficiency over Time')
    plt.xlabel('Time Step (ms)')
    plt.ylabel('Total Spectral Efficiency (b/s/Hz)')
    plt.legend()
    plt.grid(True)
    store(plt, f"{simulation_name}_total_spectral_efficiency.png")
    plt.close()


def plot_multiple_average_spectral_efficiency(scenarios, simulation_name, step=1):
    plt.figure(figsize=(12, 8))
    for scenario in scenarios:
        ue_se_history = [step['se'] for step in scenario['history']]
        time_steps = range(math.ceil(len(ue_se_history) / step))
        time_steps = [element * 10 * step for element in time_steps]
        total_se = []

        for ue_index in range(len(ue_se_history[0])):
            ue_se = [se[ue_index] for se in ue_se_history]
            total_se.append(ue_se[::step])

        total_se = np.sum(np.array(total_se), axis=0)
        style = scenario['style'] if 'style' in scenario else '--'
        plt.plot(time_steps, total_se, label=scenario['name'], linestyle=style)

    plt.title('Comparison of average Spectral Efficiency over Time')
    plt.xlabel('Time Step (ms)')
    plt.ylabel('Average Spectral Efficiency (b/s/Hz)')
    plt.legend()
    plt.grid(True)
    store(plt, f"{simulation_name}_total_spectral_efficiency.png")
    plt.close()


def plot_multiple_total_cumulative_packets(scenarios, simulation_name, step=1):
    plt.figure(figsize=(12, 8))
    for scenario in scenarios:
        ue_packets_sent_history = [entry['frames'] for entry in scenario['history']]

        # Calculate time steps considering the 'step' parameter for thinning
        time_steps = range(math.ceil(len(ue_packets_sent_history) / step))
        time_steps = [element * 10 * step for element in time_steps]  # Adjusting time step as per step parameter

        ue_packets_sent_history = np.array(ue_packets_sent_history).T[:, ::step]

        # Calculate cumulative packets sent for each scenario
        total_packets_sent = ue_packets_sent_history.sum(axis=0).cumsum()
        style = scenario['style'] if 'style' in scenario else '--'
        plt.plot(time_steps, total_packets_sent, label=scenario['name'], linestyle=style)

    plt.title('Comparison of Total Cumulative Packets Sent Over Time')
    plt.xlabel('Time Step (ms)')
    plt.ylabel('Cumulative Number of Frames Sent')
    plt.legend()
    plt.grid(True)
    store(plt, f"{simulation_name}_total_cumulative_packets_sent.png")
    plt.close()


def plot_multiple_total_cumulative_packets_dropped(scenarios, simulation_name, step=1):
    plt.figure(figsize=(12, 8))

    for scenario in scenarios:
        # Assuming each scenario contains a 'history' list with entries for 'dropped_frames'
        ue_packets_dropped_history = [entry['dropped_frames'] for entry in scenario['history']]
        time_steps = range(math.ceil(len(ue_packets_dropped_history) / step))
        time_steps = [element * 10 * step for element in time_steps]

        # Transpose and thin the data as necessary
        ue_packets_dropped_history = np.array(ue_packets_dropped_history).T[:, ::step]

        # Calculating and plotting the total cumulative packets dropped across all UEs in the scenario
        total_packets_dropped = ue_packets_dropped_history.sum(axis=0).cumsum()
        style = scenario['style'] if 'style' in scenario else '--'
        plt.plot(time_steps, total_packets_dropped, label=scenario['name'], linestyle=style)

    plt.title('Comparison of Cumulative Frames Dropped Over Time')
    plt.xlabel('Time Step (ms)')
    plt.ylabel('Cumulative Number of Frames Dropped')
    plt.legend()
    plt.grid(True)
    store(plt, f"{simulation_name}_total_cumulative_packets_dropped.png")
    plt.close()


def plot_multiple_average_packets_sent(scenarios, simulation_name, step=1):
    plt.figure(figsize=(12, 8))
    for scenario in scenarios:
        ue_packets_sent_history = [entry['frames'] for entry in scenario['history']]
        time_steps = range(math.ceil(len(ue_packets_sent_history) / step))
        time_steps = [element * 10 * step for element in time_steps]

        # Transpose and thin data as necessary
        ue_packets_sent_history = np.array(ue_packets_sent_history).T[:, ::step]

        # Calculate average packets sent for each scenario
        total_packets_sent = np.sum(ue_packets_sent_history, axis=0)
        average_packets_sent = total_packets_sent / len(ue_packets_sent_history)

        # Plotting the average packets sent for each scenario
        style = scenario['style'] if 'style' in scenario else '--'
        plt.plot(time_steps, average_packets_sent, label=scenario['name'], linestyle=style)

    plt.title('Comparison of Average Frames Sent Through Time')
    plt.xlabel('Time Step (ms)')
    plt.ylabel('Number of Frames Sent')
    plt.legend()
    plt.grid(True)
    store(plt, f"{simulation_name}_average_packets_sent.png")
    plt.close()


def plot_multiple_average_packets_dropped(scenarios, simulation_name, step=1):
    plt.figure(figsize=(12, 8))

    for scenario in scenarios:
        # Assuming each scenario contains a 'history' list with entries for 'dropped_frames'
        ue_packets_dropped_history = [entry['dropped_frames'] for entry in scenario['history']]
        time_steps = range(math.ceil(len(ue_packets_dropped_history) / step))
        time_steps = [element * 10 * step for element in time_steps]

        # Transpose and thin the data as necessary
        ue_packets_dropped_history = np.array(ue_packets_dropped_history).T[:, ::step]

        # Calculate average packets dropped for each scenario
        total_packets_dropped = np.sum(ue_packets_dropped_history, axis=0)
        average_packets_dropped = total_packets_dropped / len(ue_packets_dropped_history)

        # Plotting the average packets dropped for each scenario
        style = scenario['style'] if 'style' in scenario else '--'
        plt.plot(time_steps, average_packets_dropped, label=scenario["name"], linestyle=style)

    plt.title('Comparison of Average Frames Dropped Over Time')
    plt.xlabel('Time Step (ms)')
    plt.ylabel('Average Number of Frames Dropped')
    plt.legend()
    plt.grid(True)
    store(plt, f"{simulation_name}_average_packets_dropped.png")
    plt.close()


def plot_multiple_total_packets_sent(scenarios, simulation_name, step=1):
    plt.figure(figsize=(12, 8))
    for scenario in scenarios:
        ue_packets_sent_history = [entry['frames'] for entry in scenario['history']]
        time_steps = range(math.ceil(len(ue_packets_sent_history) / step))
        time_steps = [element * 10 * step for element in time_steps]

        # Transpose and thin data as necessary
        ue_packets_sent_history = np.array(ue_packets_sent_history).T[:, ::step]

        # Calculate average packets sent for each scenario
        total_packets_sent = np.sum(ue_packets_sent_history, axis=0)

        # Plotting the average packets sent for each scenario
        style = scenario['style'] if 'style' in scenario else '--'
        plt.plot(time_steps, total_packets_sent, label=scenario['name'], linestyle=style)

    plt.title('Comparison of Total Frames Sent Through Time')
    plt.xlabel('Time Step (ms)')
    plt.ylabel('Number of Frames Sent')
    plt.legend()
    plt.grid(True)
    store(plt, f"{simulation_name}_total_packets_sent.png")
    plt.close()


def plot_multiple_average_proportional_fairness(scenarios, simulation_name, step=1):
    plt.figure(figsize=(12, 8))
    for scenario in scenarios:
        ue_pf_history = [entry['pf'] for entry in scenario['history']]
        time_steps = range(math.ceil(len(ue_pf_history) / step))
        time_steps = [element * 10 * step for element in time_steps]

        # Transpose and thin the PF data as needed
        ue_pf_history = np.array(ue_pf_history).T[:, ::step]

        # Calculate average PF for each scenario
        average_pf = np.mean(ue_pf_history, axis=0)
        style = scenario['style'] if 'style' in scenario else '--'
        plt.plot(time_steps, average_pf, label=scenario['name'], linestyle=style)

    plt.title('Comparison of Average Proportional Fairness Over Time')
    plt.xlabel('Time Step (ms)')
    plt.ylabel('Proportional Fairness Metric')
    plt.legend()
    plt.grid(True)
    store(plt, f"{simulation_name}_average_proportional_fairness.png")
    plt.close()


def plot_multiple_average_queue_length(scenarios, simulation_name, step=1):
    plt.figure(figsize=(12, 8))
    for scenario in scenarios:
        ue_queue_length_history = [entry['queue lengths'] for entry in scenario['history']]
        time_steps = range(math.ceil(len(ue_queue_length_history) / step))
        time_steps = [element * 10 * step for element in time_steps]

        # Transpose and thin the queue length data as needed
        ue_queue_length_history = np.array(ue_queue_length_history).T[:, ::step]

        # Calculate average queue length for each scenario
        average_queue_length = np.mean(ue_queue_length_history, axis=0)
        style = scenario['style'] if 'style' in scenario else '--'
        plt.plot(time_steps, average_queue_length, label=scenario['name'], linestyle=style)

    plt.title('Comparison of Average Queue Length Over Time')
    plt.xlabel('Time Step (ms)')
    plt.ylabel('Queue Length')
    plt.legend()
    plt.grid(True)
    store(plt, f"{simulation_name}_average_queue_length.png")
    plt.close()


def plot_multiple_user_activity(scenarios, simulation_name, step=1):
    plt.figure(figsize=(12, 8))
    for scenario in scenarios:
        user_activity_history = [entry['user activity'] for entry in scenario['history']]
        time_steps = range(math.ceil(len(user_activity_history) / step))
        time_steps = [element * 10 * step for element in time_steps]  # Adjusting time step as per step parameter

        user_activity_history = np.array(user_activity_history).T

        # Plotting total active users for each scenario
        total_active_users = np.sum(user_activity_history[:, ::step], axis=0)
        style = scenario['style'] if 'style' in scenario else '--'
        plt.plot(time_steps, total_active_users, label=scenario['name'], linestyle=style)

    plt.title('Comparison of User Activity Over Time')
    plt.xlabel('Time Step (ms)')
    plt.ylabel('Total Active Users')
    plt.legend()
    plt.grid(True)
    store(plt, f"{simulation_name}_total_user_activity.png")
    plt.close()


def plot_average_average_delay(scenarios, simulation_name, step=1):
    plt.figure(figsize=(12, 8))
    for scenario in scenarios:
        ue_delay_history = [entry['average delay'] for entry in scenario['history']]
        time_steps = range(math.ceil(len(ue_delay_history) / step))
        time_steps = [element * 10 * step for element in time_steps]

        ue_delay_history = np.array(ue_delay_history).T[:, ::step]  # Thinning the data

        # Calculate the average of average delays for each scenario
        average_average_delay = np.mean(ue_delay_history, axis=0)
        style = scenario['style'] if 'style' in scenario else '--'
        plt.plot(time_steps, average_average_delay, label=scenario['name'], linestyle=style)

    plt.title('Comparison of of Average Delays Over Time')
    plt.xlabel('Time Step (ms)')
    plt.ylabel('Average Delay (ms)')
    plt.legend()
    plt.grid(True)
    store(plt, f"{simulation_name}_average_average_delay.png")
    plt.close()


def plot_from_json(scenarios, name, step):
    # Load the history for each scenario from a JSON file
    for scenario in scenarios:
        scenario['history'] = load_dictionary(f"output/{scenario['address']}")

    # Call each plotting function
    plot_multiple_total_spectral_efficiency(scenarios, name, step)
    plot_multiple_average_spectral_efficiency(scenarios, name, step)
    plot_multiple_total_cumulative_packets(scenarios, name, step)
    plot_multiple_average_packets_sent(scenarios, name, step)
    # plot_multiple_total_cumulative_packets_dropped(scenarios, name, step)
    # plot_multiple_average_packets_dropped(scenarios, name, step)
    plot_multiple_total_packets_sent(scenarios, name, step)
    plot_multiple_average_proportional_fairness(scenarios, name, step)
    plot_multiple_average_queue_length(scenarios, name, step)
    plot_multiple_user_activity(scenarios, name, step)
    plot_average_average_delay(scenarios, name, step)

# Example usage:
