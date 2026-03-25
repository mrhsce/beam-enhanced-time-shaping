import numpy as np

from pythonProject.beamforming.digital_beamforming.zero_forcing import get_normalized_digital_beamformer
from pythonProject.ue_selection.policies import UESelectionUtilityFunction, Policy, DigitalBeamformingTechnique


# This is a helper function that will calculate the SINR (Signal-to-Interference-plus-Noise Ratio) for a given user i
def calculate_sinr(i, H, F_B, sigma_square=1.00e-12):
    # Signal Power Calculation
    numerator = np.abs(H[i] @ F_B[:, i]) ** 2

    # Interference Power Calculation
    # Sum the power of all other streams directed to other users (excluding user i)
    interference_power = sum(
        np.abs(H[i] @ F_B[:, j]) ** 2 for j in range(H.shape[0]) if j != i
    )

    # SINR Calculation for user i
    sinr = numerator / (interference_power + sigma_square)

    return sinr


# This is the primary function that calculates the bitrate for all users based on the provided formula
def calculate_weighted_bitrate(channel_matrix, analog_precoding_matrix, digital_precoding_matrix,
                               policy: UESelectionUtilityFunction,
                               user_activity, cumulative_data_rates, queue_lengths, noise_power=1.00e-12):
    # Initialize bitrate result dictionary
    user_bitrates = {}

    # caluclating effective channel matrix
    effective_channel_matrix = np.conj(channel_matrix.T)
    if analog_precoding_matrix is not None:
        effective_channel_matrix = effective_channel_matrix @ analog_precoding_matrix

    # Calculate bitrate for all the assigned users
    order = 0
    for i in range(len(user_activity)):
        if user_activity[i]:
            sinr = calculate_sinr(order, effective_channel_matrix, digital_precoding_matrix, noise_power)

            if policy == UESelectionUtilityFunction.BITRATE_MAXIMIZATION:
                user_bitrates[order] = np.log2(1 + sinr)
            elif policy == UESelectionUtilityFunction.PF_MAXIMIZATION:
                user_bitrates[order] = np.log(np.log2(1 + sinr) / cumulative_data_rates[i])
                # user_bitrates[order] = np.log2(1 + sinr) / cumulative_data_rates[i]
            elif policy == UESelectionUtilityFunction.QUEUE_LENGTH_MINIMIZATION:
                user_bitrates[order] = np.log2(1 + sinr) * queue_lengths[i]
            elif policy == UESelectionUtilityFunction.QUEUE_AWARE_PF_MAXIMIZATION:
                user_bitrates[order] = np.log(np.log2(1 + sinr) / cumulative_data_rates[i]) * queue_lengths[i]
            order += 1

    return sum(user_bitrates.values())


def greedy_bs_user_selection(channel_matrix, analog_precoding_matrix, policy,
                             cumulative_data_rates, queue_lengths, n_max=None):
    I = channel_matrix.shape[1]  # Total number of users

    if n_max is None:
        n_max = I

    M = set()  # Initialize M as an empty set
    Q_M = -np.inf  # Initialize Q(M) to negative infinity

    while len(M) < n_max:
        best_user = None

        # Iterate over all users not in M
        for i in range(I):
            if i not in M:
                user_activity = np.array([user in M or user == i for user in range(I)])
                filtered_channel_matrix = channel_matrix[:, user_activity]
                filtered_analog_precoding_matrix = analog_precoding_matrix
                if filtered_analog_precoding_matrix is not None:
                    if policy.digital_beamforming_technique == DigitalBeamformingTechnique.ZERO_FORCING_DYNAMIC_RF_CHAIN:
                        filtered_analog_precoding_matrix = filtered_analog_precoding_matrix[:, user_activity]

                digital_precoding_matrix = get_normalized_digital_beamformer(filtered_channel_matrix,
                                                                             filtered_analog_precoding_matrix, 1)
                current_Q = calculate_weighted_bitrate(filtered_channel_matrix, filtered_analog_precoding_matrix,
                                                       digital_precoding_matrix, policy.utility_function, user_activity,
                                                       cumulative_data_rates, queue_lengths)

                # Check if adding the current user improves Q(M)
                if current_Q > Q_M:
                    Q_M = current_Q
                    best_user = i

        # If no improvement is possible, break the loop
        if best_user is None:
            break

        # Update the set M and Q(M) with the best user found in this iteration
        M.add(best_user)
    return M
