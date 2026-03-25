import numpy as np

from pythonProject.helper_functions import time_it
from pythonProject.ue_selection.algorithms.greedy_selection import greedy_bs_user_selection
from pythonProject.ue_selection.algorithms.top_k_selection import adaptive_top_k_bs_user_selection
from pythonProject.ue_selection.policies import Policy, UESelectionAlgorithm, DigitalBeamformingTechnique


@time_it
def perform_user_selection(channel_matrices, analog_precoding_matrices, policy: Policy, assignment_matrix,
                           cumulative_data_rates, queue_lengths):
    BS_count, num_antennas, num_users = channel_matrices.shape
    user_activity_matrix = np.zeros((BS_count, num_users), dtype=bool)

    for bs_index in range(BS_count):
        # Identify users assigned to this BS
        assigned_user_indices = np.where(assignment_matrix[bs_index, :] == 1)[0]
        if len(assigned_user_indices) == 0:
            continue  # Skip this BS if no users are assigned

        # Extract the channel matrix and analog precoding matrix for the assigned users
        filtered_channel_matrix = channel_matrices[bs_index][:, assigned_user_indices]
        filtered_analog_precoding_matrix = None
        if analog_precoding_matrices is not None:
            filtered_analog_precoding_matrix = analog_precoding_matrices[bs_index]
        filtered_cumulative_data_rates = cumulative_data_rates[assigned_user_indices]
        filtered_queue_lengths = queue_lengths[assigned_user_indices]

        # Apply the greedy user selection for the filtered matrices
        if policy.ue_selection_algorithm == UESelectionAlgorithm.GREEDY:
            selected_users = greedy_bs_user_selection(filtered_channel_matrix,
                                                      filtered_analog_precoding_matrix,
                                                      policy,
                                                      filtered_cumulative_data_rates, filtered_queue_lengths)
        elif policy.ue_selection_algorithm == UESelectionAlgorithm.ADAPTIVE_TOP_K:
            selected_users = adaptive_top_k_bs_user_selection(filtered_channel_matrix,
                                                              filtered_analog_precoding_matrix,
                                                              policy,
                                                              filtered_cumulative_data_rates, filtered_queue_lengths)
        elif policy.ue_selection_algorithm == UESelectionAlgorithm.SERVING_ALL:
            selected_users = list(range(len(assigned_user_indices)))

            # Update the user activity matrix based on selected users
        for user_index in selected_users:
            actual_user_index = assigned_user_indices[user_index]  # Map back to original user index
            user_activity_matrix[bs_index, actual_user_index] = True

    return user_activity_matrix

def calculate_ue_bitrate_single_bs(channel_matrix, digital_precoding_matrix, analog_precoding_matrix, ue, noise_power=1.00e-12):
    interference_power = 0

    effective_channel_matrix_serving = np.conj(channel_matrix[:, [ue]].T)
    if analog_precoding_matrix is not None:
        # if policy.digital_beamforming_technique == DigitalBeamformingTechnique.ZERO_FORCING_DYNAMIC_RF_CHAIN:
        #     analog_precoding_matrix = analog_precoding_matrix[:, users_order_in_analog_beamformer]
        effective_channel_matrix_serving = effective_channel_matrix_serving @ analog_precoding_matrix

    signal_power = np.abs(
        effective_channel_matrix_serving @ digital_precoding_matrix[:, ue]) ** 2

    # Calculate interference power from other users at the same BS only
    for j in range(channel_matrix.shape[1]):
        if j != ue:
            interference_power += np.abs(
                effective_channel_matrix_serving @ digital_precoding_matrix[:, j]) ** 2

    # SINR calculation
    sinr = signal_power / (interference_power + noise_power)

    # Bitrate calculation for the UE
    bitrate = np.log2(1 + sinr[0])
    return bitrate

def calculate_ue_bitrate_no_interbs(channel_matrices, analog_precoding_matrices, digital_precoding_matrices, policy,
                                    user_activity_matrix, assignment_matrix, ue, noise_power=1.00e-12):
    interference_power = 0

    # Check if the UE is active and served by any BS
    related_bs_indices = np.where(user_activity_matrix[:, ue])[0]
    if len(related_bs_indices) == 0:
        # The UE is not active and not served by any BS, return bitrate of zero
        return 0

    # Calculate signal power for the serving BS
    serving_bs = related_bs_indices[0]

    # Get the indices of all users assigned to this BS
    assigned_user_indices = np.where(assignment_matrix[serving_bs])[0]

    active_user_indices = np.where(user_activity_matrix[serving_bs, :])[0]
    users_order_in_analog_beamformer = [np.where(assigned_user_indices == element)[0][0] for element in
                                        active_user_indices]
    users_order_in_digital_beamformer = [np.where(active_user_indices == ue)[0][0]]

    effective_channel_matrix_serving = np.conj(channel_matrices[serving_bs][:, [ue]].T)
    if analog_precoding_matrices is not None:
        analog_precoding_matrix = analog_precoding_matrices[serving_bs]
        if policy.digital_beamforming_technique == DigitalBeamformingTechnique.ZERO_FORCING_DYNAMIC_RF_CHAIN:
            analog_precoding_matrix = analog_precoding_matrix[:, users_order_in_analog_beamformer]
        effective_channel_matrix_serving = effective_channel_matrix_serving @ analog_precoding_matrix

    signal_power = np.abs(
        effective_channel_matrix_serving @ digital_precoding_matrices[serving_bs][:,
                                           users_order_in_digital_beamformer]) ** 2

    # Calculate interference power from other users at the same BS only
    for j in active_user_indices:
        if j != ue:
            j_users_order_in_digital_beamformer = [np.where(active_user_indices == j)[0][0]]
            interference_power += np.abs(
                effective_channel_matrix_serving @ digital_precoding_matrices[serving_bs][:,
                                                   j_users_order_in_digital_beamformer]) ** 2

    # SINR calculation
    sinr = signal_power / (interference_power + noise_power)

    # Bitrate calculation for the UE
    bitrate = np.log2(1 + sinr[0][0])
    return bitrate


def calculate_ue_bitrates_no_interbs(channel_matrices, analog_precoding_matrices, digital_precoding_matrices, policy,
                                     user_activity_matrix, assignment_matrix, decimals=4):
    num_users = channel_matrices.shape[2]
    bitrates_array = np.zeros(num_users)

    for ue in range(num_users):
        bitrates_array[ue] = round(calculate_ue_bitrate_no_interbs(channel_matrices, analog_precoding_matrices,
                                                                   digital_precoding_matrices, policy,
                                                                   user_activity_matrix,
                                                                   assignment_matrix, ue), decimals)

    return bitrates_array
