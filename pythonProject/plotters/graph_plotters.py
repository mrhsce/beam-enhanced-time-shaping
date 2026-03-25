import math

import matplotlib.pyplot as plt
import numpy as np

from pythonProject.helper_functions import store


def plot_spectral_efficiency(channel_history, simulation_name, step=1, directory=None):
    plt.figure(figsize=(12, 8))
    ue_se_history = [step['se'] for step in channel_history]

    # Calculate time steps considering the 'step' parameter for thinning
    time_steps = range(math.ceil(len(ue_se_history) / step))
    time_steps = [element * 10 * step for element in time_steps]  # Assuming time step is 10 ms

    total_se = []

    for ue_index in range(len(ue_se_history[0])):
        ue_se = [se[ue_index] for se in ue_se_history]
        thinned_ue_se = ue_se[::step]  # Thinning the data as per the step parameter
        plt.plot(time_steps, thinned_ue_se, label=f'UE {ue_index + 1}')

        total_se.append(thinned_ue_se)  # Collecting the thinned data for total SE

    total_se = np.sum(np.array(total_se), axis=0)
    plt.plot(time_steps, total_se, label='Total SE', linewidth=2, linestyle='--')

    plt.title('Spectral Efficiency over Time')
    plt.xlabel('Time Step (ms)')
    plt.ylabel('Spectral Efficiency (b/s/Hz)')
    plt.legend()
    plt.grid(True)
    store(plt, f"{simulation_name}_spectral_efficiency.png", directory)
    plt.close()


def plot_user_activity(channel_history, simulation_name, step=1, directory=None):
    plt.figure(figsize=(12, 8))
    user_activity_history = [step['user activity'] for step in channel_history]

    # Calculate time steps considering the 'step' parameter for thinning
    time_steps = range(math.ceil(len(user_activity_history) / step))
    time_steps = [element * 10 * step for element in time_steps]  # Assuming time step is 10 ms

    user_activity_history = np.array(user_activity_history).T

    # Plotting each user equipment's (UE) activity with the applied thinning
    for ue_index, activity in enumerate(user_activity_history):
        thinned_activity = activity[::step]  # Thinning the data as per the step parameter
        plt.plot(time_steps, thinned_activity, label=f'UE {ue_index + 1}')

    # Summing up the user activities for the 'Total Active Users' plot with thinned data
    total_active_users = np.sum(user_activity_history[:, ::step], axis=0)
    plt.plot(time_steps, total_active_users, label='Total Active Users', linewidth=2, linestyle='--')

    plt.title('User Activity over Time')
    plt.xlabel('Time Step (ms)')
    plt.ylabel('Activity Status')
    plt.legend()
    plt.grid(True)
    store(plt, f"{simulation_name}_user_activity.png", directory)
    plt.close()


def plot_average_delay(channel_history, simulation_name, step=1, directory=None):
    plt.figure(figsize=(12, 8))
    ue_delay_history = [step['average delay'] for step in channel_history]

    # Calculate time steps considering the 'step' parameter for thinning
    time_steps = range(math.ceil(len(ue_delay_history) / step))
    time_steps = [element * 10 * step for element in time_steps]  # Assuming time step is 10 ms

    ue_delay_history = np.array(ue_delay_history).T

    # Plotting each user equipment's (UE) delay with the applied thinning
    for ue_index, delay in enumerate(ue_delay_history):
        thinned_delay = delay[::step]  # Thinning the data as per the step parameter
        plt.plot(time_steps, thinned_delay, label=f'UE {ue_index + 1}')

    # Calculating the average delay for the 'Average Delay (All UEs)' plot with thinned data
    average_delay = np.mean(ue_delay_history[:, ::step], axis=0)
    plt.plot(time_steps, average_delay, label='Average Delay (All UEs)', linewidth=2, linestyle='--')

    plt.title('Average Delay over Time')
    plt.xlabel('Time Step (ms)')
    plt.ylabel('Average Delay (ms)')
    plt.legend()
    plt.grid(True)
    store(plt, f"{simulation_name}_average_delay.png", directory)
    plt.close()


def plot_proportional_fairness(channel_history, simulation_name, step=1, directory=None):
    plt.figure(figsize=(12, 8))
    ue_pf_history = [step['pf'] for step in channel_history]
    time_steps = range(math.ceil(len(ue_pf_history) / step))
    time_steps = [element * 10 * step for element in time_steps]
    ue_pf_history = np.array(ue_pf_history).T[:, ::step]

    for ue_index, pf in enumerate(ue_pf_history):
        plt.plot(time_steps, pf, label=f'UE {ue_index + 1}')

    average_pf = np.mean(ue_pf_history, axis=0)
    plt.plot(time_steps, average_pf, label='Average PF (All UEs)', linewidth=2, linestyle='--')

    plt.title('Proportional Fairness (PF) over Time')
    plt.xlabel('Time Step (ms)')
    plt.ylabel('Proportional Fairness Metric')
    plt.legend()
    plt.grid(True)
    store(plt, f"{simulation_name}_proportional_fairness.png", directory)
    plt.close()


def plot_queue_length(channel_history, simulation_name, step=1, directory=None):
    plt.figure(figsize=(12, 8))
    ue_queue_length_history = [step['queue lengths'] for step in channel_history]
    time_steps = range(math.ceil(len(ue_queue_length_history) / step))
    time_steps = [element * 10 * step for element in time_steps]
    ue_queue_length_history = np.array(ue_queue_length_history).T[:, ::step]

    for ue_index, queue_length in enumerate(ue_queue_length_history):
        plt.plot(time_steps, queue_length, label=f'UE {ue_index + 1}')

    average_queue_length = np.mean(ue_queue_length_history, axis=0)
    plt.plot(time_steps, average_queue_length, label='Average Queue Length (All UEs)', linewidth=2, linestyle='--')

    plt.title('Queue Length over Time')
    plt.xlabel('Time Step (ms)')
    plt.ylabel('Queue Length')
    plt.legend()
    plt.grid(True)
    store(plt, f"{simulation_name}_queue_length.png", directory)
    plt.close()


def plot_packets_sent(channel_history, simulation_name, step=1, directory=None):
    plt.figure(figsize=(12, 8))
    ue_packets_sent_history = [step['frames'] for step in channel_history]
    time_steps = range(math.ceil(len(ue_packets_sent_history) / step))
    time_steps = [element * 10 * step for element in time_steps]
    ue_packets_sent_history = np.array(ue_packets_sent_history).T[:, ::step]

    for ue_index, packets in enumerate(ue_packets_sent_history):
        plt.plot(time_steps, packets, label=f'UE {ue_index + 1}')

    total_packets_sent = np.sum(ue_packets_sent_history, axis=0)
    average_packets_sent = total_packets_sent / len(ue_packets_sent_history)
    plt.plot(time_steps, average_packets_sent, label='Average Packets Sent (per UE)', linewidth=2, linestyle=':')

    plt.title('Packets Sent over Time')
    plt.xlabel('Time Step (ms)')
    plt.ylabel('Number of Frames Sent')
    plt.legend()
    plt.grid(True)
    store(plt, f"{simulation_name}_packets_sent.png", directory)
    plt.close()


def plot_packets_dropped(channel_history, simulation_name, step=1, directory=None):
    plt.figure(figsize=(12, 8))
    ue_packets_dropped_history = [step['dropped_frames'] for step in channel_history]
    time_steps = range(math.ceil(len(ue_packets_dropped_history) / step))
    time_steps = [element * 10 * step for element in time_steps]
    ue_packets_dropped_history = np.array(ue_packets_dropped_history).T[:, ::step]

    for ue_index, packets in enumerate(ue_packets_dropped_history):
        plt.plot(time_steps, packets, label=f'UE {ue_index + 1}')

    total_packets_dropped = np.sum(ue_packets_dropped_history, axis=0)
    average_packets_sent = total_packets_dropped / len(ue_packets_dropped_history)
    plt.plot(time_steps, average_packets_sent, label='Average Packets dropped', linewidth=2, linestyle=':')

    plt.title('Frames Dropped over Time')
    plt.xlabel('Time Step (ms)')
    plt.ylabel('Number of Frames Dropped')
    plt.legend()
    plt.grid(True)
    store(plt, f"{simulation_name}_packets_dropped.png", directory)
    plt.close()


def plot_cumulative_packets_dropped(channel_history, simulation_name, step=1, directory=None):
    plt.figure(figsize=(12, 8))
    ue_packets_dropped_history = [step['dropped_frames'] for step in channel_history]

    # Calculate time steps considering the 'step' parameter for thinning
    time_steps = range(math.ceil(len(ue_packets_dropped_history) / step))
    time_steps = [element * 10 * step for element in time_steps]  # Adjusting time step as per step parameter

    ue_packets_dropped_history = np.array(ue_packets_dropped_history).T[:, ::step]

    # Plotting the cumulative packets sent by each UE
    for ue_index, packets in enumerate(ue_packets_dropped_history):
        plt.plot(time_steps, packets.cumsum(), label=f'UE {ue_index + 1}')

    # Calculating and plotting the total and average packets sent
    total_packets_dropped = ue_packets_dropped_history.sum(axis=0).cumsum()
    average_packets_sent = total_packets_dropped / len(ue_packets_dropped_history)
    plt.plot(time_steps, average_packets_sent, label='Average Packets Dropped (per UE)', linewidth=2, linestyle=':')

    plt.title('Cumulative Frames Dropped over Time')
    plt.xlabel('Time Step (ms)')
    plt.ylabel('Cumulative Number of Frames Dropped')
    plt.legend()
    plt.grid(True)
    store(plt, f"{simulation_name}_cumulative_packets_dropped.png", directory)
    plt.close()


def plot_cumulative_packets_sent(channel_history, simulation_name, step=1, directory=None):
    plt.figure(figsize=(12, 8))
    ue_packets_sent_history = [step['frames'] for step in channel_history]

    # Calculate time steps considering the 'step' parameter for thinning
    time_steps = range(math.ceil(len(ue_packets_sent_history) / step))
    time_steps = [element * 10 * step for element in time_steps]  # Adjusting time step as per step parameter

    ue_packets_sent_history = np.array(ue_packets_sent_history).T[:, ::step]

    # Plotting the cumulative packets sent by each UE
    for ue_index, packets in enumerate(ue_packets_sent_history):
        plt.plot(time_steps, packets.cumsum(), label=f'UE {ue_index + 1}')

    # Calculating and plotting the total and average packets sent
    total_packets_sent = ue_packets_sent_history.sum(axis=0).cumsum()
    average_packets_sent = total_packets_sent / len(ue_packets_sent_history)
    plt.plot(time_steps, average_packets_sent, label='Average Packets Sent (per UE)', linewidth=2, linestyle=':')

    plt.title('Cumulative Packets Sent over Time')
    plt.xlabel('Time Step (ms)')
    plt.ylabel('Cumulative Number of Frames Sent')
    plt.legend()
    plt.grid(True)
    store(plt, f"{simulation_name}_cumulative_packets_sent.png", directory)
    plt.close()
