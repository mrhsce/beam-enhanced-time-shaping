import numpy as np

from pythonProject.helper_functions import time_it
from pythonProject.ue_selection.policies import Policy, DigitalBeamformingTechnique

def get_weighted_normalized_digital_beamformer(channel_matrix, ue_weights, analog_precoding_matrix=None, total_power=1):
    """
    Design a Zero Forcing beamformer with weighted power allocation,
    including the effect of an analog beamformer.

    :param channel_matrix: Effective channel matrix G(M).
    :param ue_weights: Weights for each user (should sum to 1).
    :param analog_precoding_matrix: Optional analog beamforming matrix.
    :param total_power: Total transmit power.
    :return: Weighted and normalized digital beamformer F*_BB(M).
    """

    ue_weights = np.array(ue_weights)
    # Validate UE weights
    if np.any((ue_weights < 0) | (ue_weights > 1)):
        raise ValueError("Each UE weight must be between 0 and 1.")

    if round(np.sum(ue_weights),6) > 1:
        raise ValueError("UE weights must sum to at most 1.")

    # Calculate effective channel matrix
    effective_channel_matrix = np.conj(channel_matrix.T)
    if analog_precoding_matrix is not None:
        effective_channel_matrix = effective_channel_matrix @ analog_precoding_matrix

    # Number of data streams/users
    data_stream_count = channel_matrix.shape[1]

    # Step 2: Calculate F_BB(M) based on the formula given
    G_H = np.conj(effective_channel_matrix.T)  # Hermitian transpose of G
    try:
        # Attempt to invert the matrix directly
        F_BB = G_H @ np.linalg.inv(effective_channel_matrix @ G_H)
    except np.linalg.LinAlgError:
        # Fallback to pseudoinverse if inversion fails
        print("Matrix is singular, using pseudoinverse.")
        F_BB = G_H @ np.linalg.pinv(effective_channel_matrix @ G_H)

    # Step 3: Normalize each digital beamforming vector in F_BB(M) with respect to F_RF
    F_BB_star = np.zeros_like(F_BB, dtype=np.complex128)
    for i in range(data_stream_count):
        # The beamforming vector for the ith user
        f_BB_i = F_BB[:, i]

        # Scale considering the analog beamformer (if provided)
        normalizer = f_BB_i
        if analog_precoding_matrix is not None:
            normalizer = analog_precoding_matrix @ normalizer

        # Calculate normalization factor based on UE weights
        norm_factor = np.sqrt((total_power * ue_weights[i]) / np.linalg.norm(normalizer)**2)
        F_BB_star[:, i] = f_BB_i * norm_factor

    return F_BB_star


def get_normalized_digital_beamformer(channel_matrix, analog_precoding_matrix=None, total_power=1):
    """
    Design a Zero Forcing beamformer having equal power allocation,
    including the effect of an analog beamformer.

    :param channel_matrix: Effective channel matrix G(M).
    :param analog_precoding_matrix: Analog beamforming matrix.
    :param total_power: Total transmit power.
    :return: Normalized digital beamformer F*_BB(M).
    """

    # caluclating effective channel matrix
    effective_channel_matrix = np.conj(channel_matrix.T)
    if analog_precoding_matrix is not None:
        effective_channel_matrix = effective_channel_matrix @ analog_precoding_matrix

    # Number of data streams/users
    data_stream_count = channel_matrix.shape[1]

    # Step 2: Calculate F_BB(M) based on the formula given
    G_H = np.conj(effective_channel_matrix.T)  # Hermitian transpose of G
    try:
        # Attempt to invert the matrix directly
        F_BB = G_H @ np.linalg.inv(effective_channel_matrix @ G_H)
    except np.linalg.LinAlgError:
        # Fallback to pseudoinverse if inversion fails
        print("Matrix is singular, using pseudoinverse.")
        F_BB = G_H @ np.linalg.pinv(effective_channel_matrix @ G_H)

    # Step 3: Normalize each digital beamforming vector in F_BB(M) with respect to F_RF
    F_BB_star = np.zeros_like(F_BB, dtype=np.complex128)
    for i in range(data_stream_count):
        # The beamforming vector needs to be scaled considering the analog beamformer
        normalizer = f_BB_i = F_BB[:, i]
        # We use the analog beamformer here in the normalization
        if analog_precoding_matrix is not None:
            normalizer = analog_precoding_matrix @ normalizer

        norm_factor = np.sqrt(total_power / data_stream_count) / np.linalg.norm(normalizer)
        F_BB_star[:, i] = f_BB_i * norm_factor

    return F_BB_star


@time_it
def non_cooperative_digital_beamformer(channel_matrices, analog_precoding_matrices, policy: Policy,
                                       user_activity_matrix,
                                       assignment_matrix, total_power=1):
    BS_count, num_antennas, num_users = channel_matrices.shape
    digital_precoding_matrices = []

    for bs_index in range(BS_count):
        # Identify active users for the current BS
        active_user_indices = np.where(user_activity_matrix[bs_index, :])[0]

        if len(active_user_indices) > 0:
            # Filter channel and analog precoding matrices for active users
            filtered_channel_matrix = channel_matrices[bs_index][:, active_user_indices]

            # Get the indices of all users assigned to this BS
            assigned_user_indices = np.where(assignment_matrix[bs_index])[0]

            active_user_order_index = [np.where(assigned_user_indices == element)[0][0] for element in
                                       active_user_indices]

            # Compute the digital beamformer for the filtered matrices
            analog_precoding_matrix = None
            if analog_precoding_matrices is not None:
                analog_precoding_matrix = analog_precoding_matrices[bs_index]
                if policy.digital_beamforming_technique == DigitalBeamformingTechnique.ZERO_FORCING_DYNAMIC_RF_CHAIN:
                    analog_precoding_matrix = analog_precoding_matrix[:, active_user_order_index]
            digital_precoding_matrix = get_normalized_digital_beamformer(filtered_channel_matrix,
                                                                         analog_precoding_matrix, total_power)

            digital_precoding_matrices.append(digital_precoding_matrix)
        else:
            # If no users are active for this BS, append an empty matrix
            digital_precoding_matrices.append(np.array([]))

    return digital_precoding_matrices
