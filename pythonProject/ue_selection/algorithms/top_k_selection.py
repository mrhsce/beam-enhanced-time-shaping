import numpy as np

from pythonProject.beamforming.digital_beamforming.zero_forcing import get_normalized_digital_beamformer
from pythonProject.ue_selection.algorithms.greedy_selection import calculate_weighted_bitrate
from pythonProject.ue_selection.policies import DigitalBeamformingTechnique


def adaptive_top_k_bs_user_selection(channel_matrix, analog_precoding_matrix, policy,
                                     cumulative_data_rates, queue_lengths, n_max=None):
    I = channel_matrix.shape[1]  # Total number of users
    if n_max is None:
        n_max = I

    # Step 1: Calculate the individual bitrate for each UE without interference
    bitrates = {}
    for i in range(I):
        user_activity = np.array([user == i for user in range(I)])
        filtered_channel_matrix = channel_matrix[:, user_activity]
        filtered_analog_precoding_matrix = analog_precoding_matrix
        if filtered_analog_precoding_matrix is not None:
            if policy.digital_beamforming_technique == DigitalBeamformingTechnique.ZERO_FORCING_DYNAMIC_RF_CHAIN:
                filtered_analog_precoding_matrix = filtered_analog_precoding_matrix[:, user_activity]
        digital_precoding_matrix = get_normalized_digital_beamformer(filtered_channel_matrix,
                                                                     filtered_analog_precoding_matrix, 1)
        bitrates[i] = calculate_weighted_bitrate(filtered_channel_matrix, filtered_analog_precoding_matrix,
                                                 digital_precoding_matrix, policy.utility_function, user_activity,
                                                 cumulative_data_rates, queue_lengths)
    # Step 2: Sort the UEs based on the calculated bitrates
    sorted_users = sorted(bitrates, key=bitrates.get, reverse=True)

    # Step 3 and 4: Select top-k UEs, calculate the combined performance, and determine the best set
    best_performance = -np.inf
    best_set = None

    for k in range(1, n_max + 1):
        selected_users = sorted_users[:k]
        user_activity = [user in selected_users for user in range(I)]
        filtered_channel_matrix = channel_matrix[:, user_activity]
        filtered_analog_precoding_matrix = None
        if filtered_analog_precoding_matrix is not None:
            if policy.digital_beamforming_technique == DigitalBeamformingTechnique.ZERO_FORCING_DYNAMIC_RF_CHAIN:
                analog_precoding_matrix = analog_precoding_matrix[:, user_activity]
        digital_precoding_matrix = get_normalized_digital_beamformer(filtered_channel_matrix,
                                                                     filtered_analog_precoding_matrix, 1)
        performance = calculate_weighted_bitrate(filtered_channel_matrix, filtered_analog_precoding_matrix,
                                                 digital_precoding_matrix, policy.utility_function, user_activity,
                                                 cumulative_data_rates, queue_lengths)
        if performance > best_performance:
            best_performance = performance
            best_set = selected_users

    return best_set if best_set is not None else []
