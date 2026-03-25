from pythonProject.plotters.graph_plotters import plot_spectral_efficiency, plot_user_activity, plot_average_delay, \
    plot_proportional_fairness, plot_queue_length, plot_packets_sent, plot_cumulative_packets_sent, plot_packets_dropped, plot_cumulative_packets_dropped
from pythonProject.plotters.mobility_video import visualize_movement_and_save


def simulation_report(channel_history, name, step=1, vidoe=True, directory=None):
    plot_spectral_efficiency(channel_history, name, step, directory)
    plot_user_activity(channel_history, name, step, directory)
    plot_average_delay(channel_history, name, step, directory)
    plot_proportional_fairness(channel_history, name, step, directory)
    plot_queue_length(channel_history, name, step, directory)
    plot_packets_sent(channel_history, name, step, directory)
    plot_cumulative_packets_sent(channel_history, name, step, directory)
    # plot_packets_dropped(channel_history, name, step, directory)
    # plot_cumulative_packets_dropped(channel_history, name, step, directory)

    if vidoe:
        visualize_movement_and_save(channel_history, name, directory)

