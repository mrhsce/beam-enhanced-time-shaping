import numpy as np

from pythonProject.ue_selection.policies import DigitalBeamformingTechnique


# This is a helper function that will calculate the SINR (Signal-to-Interference-plus-Noise Ratio) for a given user i
def calculate_sinr(i, H, F_B, user_activity, sigma_square):
    # Signal Power Calculation
    numerator = np.abs(H[i] @ F_B[:, i]) ** 2

    # Interference Power Calculation
    # Sum the power of all other streams directed to other users (excluding user i)
    interference_power = sum(
        np.abs(H[i] @ F_B[:, j]) ** 2 for j in range(H.shape[0]) if j != i and user_activity[j]
    )

    # SINR Calculation for user i
    sinr = numerator / (interference_power + sigma_square)

    return sinr


def calculate_actual_ue_bitrate(channel_matrices, analog_precoding_matrices, digital_precoding_matrices, policy,
                                user_activity_matrix, assignment_matrix, ue, noise_power=1.00e-12):
    L, num_antennas, K = channel_matrices.shape
    signal_power = 0
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

    # Calculate interference power from all other users at all BSs
    for j in range(K):
        if j != ue:
            j_active_bs_indices = np.where(user_activity_matrix[:, j])[0]
            if len(j_active_bs_indices) > 0:
                # Consider interference only from active users
                j_serving_bs = j_active_bs_indices[0]

                j_assigned_user_indices = np.where(assignment_matrix[j_serving_bs])[0]

                j_active_user_indices = np.where(user_activity_matrix[j_serving_bs, :])[0]
                j_users_order_in_analog_beamformer = [np.where(j_assigned_user_indices == element)[0][0] for element in
                                                      j_active_user_indices]
                j_users_order_in_digital_beamformer = [np.where(j_active_user_indices == j)[0][0]]

                j_effective_channel_matrix_serving = np.conj(channel_matrices[j_serving_bs][:, [ue]].T)
                if analog_precoding_matrices is not None:
                    j_analog_precoding_matrix = analog_precoding_matrices[j_serving_bs]
                    if policy.digital_beamforming_technique == DigitalBeamformingTechnique.ZERO_FORCING_DYNAMIC_RF_CHAIN:
                        j_analog_precoding_matrix = j_analog_precoding_matrix[:, j_users_order_in_analog_beamformer]
                    j_effective_channel_matrix_serving = j_effective_channel_matrix_serving @ j_analog_precoding_matrix

                interference_power += np.abs(
                    j_effective_channel_matrix_serving @ digital_precoding_matrices[j_serving_bs][:,
                                                         j_users_order_in_digital_beamformer]) ** 2

    # SINR calculation
    sinr = signal_power / (interference_power + noise_power)

    # Bitrate calculation for the UE
    bitrate = np.log2(1 + sinr[0][0])
    return bitrate


def calculate_actual_ue_bitrates(channel_matrices, analog_precoding_matrices, digital_precoding_matrices, policy,
                                 user_activity_matrix, assignment_matrix, decimals=4):
    num_users = channel_matrices.shape[2]  # Assuming the channel_matrices shape is [BS_count, num_antennas, num_users]
    bitrates_array = np.zeros(num_users)

    for ue in range(num_users):
        bitrates_array[ue] = round(calculate_actual_ue_bitrate(channel_matrices, analog_precoding_matrices,
                                                               digital_precoding_matrices, policy, user_activity_matrix,
                                                               assignment_matrix, ue), decimals)

    return bitrates_array
