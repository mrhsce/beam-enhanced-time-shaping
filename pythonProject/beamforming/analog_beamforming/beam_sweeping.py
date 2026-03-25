import numpy as np

from pythonProject.helper_functions import time_it


def fully_connected_full_sweeping(channel_matrix, codebook):
    num_antennas, num_users = channel_matrix.shape
    azimuth_sample_count, elevation_sample_count = codebook.shape[0], codebook.shape[1]

    analog_precoding_matrix = np.zeros((num_antennas, num_users), dtype=complex)

    for user_index in range(num_users):
        best_beam_index = (0,0)
        best_gain = 0

        for azimuth_index in range(azimuth_sample_count):
            for elevation_index in range(elevation_sample_count):
                beam = codebook[azimuth_index, elevation_index, :].reshape(-1, 1)
                gain = np.abs(channel_matrix.conj().T[user_index] @ beam)

                if gain > best_gain:
                    best_gain = gain
                    best_beam_index = (azimuth_index, elevation_index)

        analog_precoding_matrix[:, user_index] = codebook[best_beam_index[0], best_beam_index[1], :]

    return analog_precoding_matrix # antenna x ue_count

@time_it
def non_cooperative_fully_connected_full_sweeping(channel_matrices, assignment_matrix, codebook):
    BS_count, num_antennas, num_users = channel_matrices.shape

    # Initialize a list to hold analog precoding matrices for flexibility
    analog_precoding_matrices_list = []

    for bs_index in range(BS_count):
        # Filter the channel matrix for the current BS based on the user assignment
        active_user_indices = np.where(assignment_matrix[bs_index, :] == 1)[0]

        if len(active_user_indices) > 0:
            filtered_channel_matrix = channel_matrices[bs_index][:, active_user_indices]
            # Call the original function for each BS with its filtered channel matrix
            precoding_matrix = fully_connected_full_sweeping(filtered_channel_matrix, codebook)

            analog_precoding_matrices_list.append(precoding_matrix)
        else:
            # If no users are active for this BS, append an empty matrix
            analog_precoding_matrices_list.append(np.array([]))

    return np.array(analog_precoding_matrices_list)