from enum import Enum, auto
import numpy
from pythonProject.helper_functions import generate_lognormal, generate_uniform, generate_complex_gaussian
import numpy as np

azimuth_lower_bound = 0
azimuth_higher_bound = 2 * numpy.pi

elevation_lower_bound = 0
elevation_higher_bound = numpy.pi / 2


class PathType(Enum):
    OUT = auto()
    LOS = auto()
    NLOS = auto()


def determine_type(distance):
    """
    Determine the type based on the given distance.

    Parameters:
    distance (float): Distance in meters.

    Returns:
    PathType: The determined type (PathType.OUT, PathType.LOS, or PathType.NLOS).
    """
    # Constants from the formulas
    a_out = 0.0334  # in meters^-1
    b_out = 5.2
    a_los = 0.0149  # in meters^-1

    # Calculate P_out
    P_out = max(0, 1 - np.exp(-a_out * distance + b_out))

    # Calculate P_LOS
    P_LOS = (1 - P_out) * np.exp(-a_los * distance)

    # Calculate P_NLOS
    P_NLOS = 1 - P_out - P_LOS

    # Define the categories
    categories = [PathType.OUT, PathType.LOS, PathType.NLOS]
    probabilities = [P_out, P_LOS, P_NLOS]

    # Choose a category based on the defined probabilities
    chosen_type = np.random.choice(categories, p=probabilities)

    return chosen_type


# Function to calculate the path loss based on the path type and distance
def calculate_path_loss(distance, path_type):
    # Path loss calculation constants for LOS and NLOS
    path_loss_params = {
        PathType.LOS: {'alpha': 61.4, 'beta': 2, 'sigma': 5.8},
        PathType.NLOS: {'alpha': 72.0, 'beta': 2.92, 'sigma': 8.7}
    }

    if path_type == PathType.OUT:
        return float('inf')

    # Retrieve parameters for the given path type
    params = path_loss_params[path_type]

    # Calculate the path loss
    return params['alpha'] + 10 * params['beta'] * np.log10(distance) + generate_lognormal(0, params['sigma'] ** 2)


def calculate_cluster_power():
    # Constants given in the formula
    r_t = 2.8
    zeta = 4.0

    # Drawing a sample from a uniform distribution U[0, 1]
    U_k = generate_uniform(0, 1)

    # Drawing a sample from a normal distribution N(0, zeta^2)
    Z_k = generate_lognormal(0, zeta ** 2)

    # Calculating gamma_k according to the formula
    return U_k ** (r_t - 1) * 10 ** (-0.1 * Z_k)


def generate_mmwave_path_cluster(distance):
    cluster_type = determine_type(distance)
    path_loss = calculate_path_loss(distance, cluster_type)
    power_fraction = calculate_cluster_power()
    azimuth = generate_uniform(azimuth_lower_bound, azimuth_higher_bound)
    elevation = generate_uniform(elevation_lower_bound, elevation_higher_bound)
    small_scale_fading = generate_complex_gaussian(0, power_fraction * 10 ** (-0.1 * path_loss))

    return cluster_type, azimuth, elevation, small_scale_fading


class Cluster:
    def __init__(self, distance):
        self.cluster_type = determine_type(distance)
        self.path_loss = calculate_path_loss(distance, self.cluster_type)
        self.power_fraction = calculate_cluster_power()
        self.azimuth = generate_uniform(azimuth_lower_bound, azimuth_higher_bound)
        self.elevation = generate_uniform(elevation_lower_bound, elevation_higher_bound)
        # TODO: If multiple paths per cluster has been implemented this should change
        self.small_scale_fading = generate_complex_gaussian(0, self.power_fraction * 10 ** (-0.1 * self.path_loss))
        self.paths = []  # Array to store paths associated with the cluster

    def add_path(self, path_instance):
        self.paths.append(path_instance)

    def small_scale_fading_effect(self):
        self.small_scale_fading = generate_complex_gaussian(0, self.power_fraction * 10 ** (-0.1 * self.path_loss))

    def __str__(self):
        return f"Cluster Type: {self.cluster_type}\n" \
               f"Path Loss: {self.path_loss}\n" \
               f"Power Fraction: {self.power_fraction}\n" \
               f"Azimuth: {self.azimuth}\n" \
               f"Elevation: {self.elevation}\n" \
               f"Small Scale Fading: {self.small_scale_fading}"
