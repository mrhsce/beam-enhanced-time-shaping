import math

import numpy as np

from pythonProject.environment.channel_model.cluster import Cluster

# Constants for a chosen scenario (Urban Micro - UMi)
num_clusters = 5  # Example cluster number
num_rays_per_cluster = 20  # Rays per cluster
frequency = 28e9  # Frequency (28 GHz)
wavelength = 3e8 / frequency  # Wavelength
AoD_spread = 10  # Degrees, example angular spread for AoD


def calculate_channel_matrices(path_clusters_matrix, antenna_array):
    channel_matrices = np.zeros(
        (len(path_clusters_matrix), antenna_array.NX * antenna_array.NY, len(path_clusters_matrix[0])), dtype=complex)
    for bs_index, bs_path_clusters in enumerate(path_clusters_matrix):
        for ue_index, path_clusters in enumerate(bs_path_clusters):
            for path_cluster in path_clusters:
                steering_vector = antenna_array.get_steering_vector(path_cluster.elevation, path_cluster.azimuth)
                channel_matrices[bs_index, :, ue_index] += path_cluster.small_scale_fading * steering_vector
            channel_matrices[bs_index, :, ue_index] = channel_matrices[bs_index, :, ue_index] / math.sqrt(len(path_clusters))

    return channel_matrices


def generate_path_clusters(distance_matrix):
    path_clusters_matrix = []
    for bs_index, bs_distances in enumerate(distance_matrix):
        path_clusters_matrix.append([])
        for ue_index, distance in enumerate(bs_distances):
            path_clusters_matrix[bs_index].append([])
            for cluster_index in range(num_clusters):
                path_clusters_matrix[bs_index][ue_index].append(Cluster(distance))
    return path_clusters_matrix
