import math

import numpy as np

# Constants
DX = 0.5  # distance between elements in x direction
DY = 0.5  # distance between elements in y direction
NX = 12  # number of elements in x direction
NY = 5  # number of elements in y direction
FREQUENCY = 28e9  # example frequency in Hertz (28 GHz)
SPEED_OF_LIGHT = 3e8  # speed of light in meters per second

# Calculate the wavelength from the frequency
WAVELENGTH = SPEED_OF_LIGHT / FREQUENCY


def get_steering_vector(elevation, azimuth):
    # Calculate the wavenumber
    k = 2 * np.pi / WAVELENGTH

    # Calculate the steering vectors for each dimension
    vx = np.exp(1j * k * DX * np.arange(NX) * np.sin(elevation) * np.cos(azimuth))
    vy = np.exp(1j * k * DY * np.arange(NY) * np.sin(elevation) * np.sin(azimuth))

    # Calculate the steering vector for the array
    a = np.kron(vx, vy)  # Kronecker product of vx and vy to form the URPA steering vector

    return a


def generate_codebook(azimuth_range, elevation_range, azimuth_sample_count=NX, elevation_sample_count=NY):
    # Sampling steering angles
    azimuth_samples = np.linspace(azimuth_range[0], azimuth_range[1], azimuth_sample_count)
    elevation_samples = np.linspace(elevation_range[0], elevation_range[1], elevation_sample_count)

    # Initialize the codebook
    codebook = np.zeros((azimuth_sample_count, elevation_sample_count, NX * NY), dtype=complex)

    for i_azimuth, azimuth in enumerate(azimuth_samples):
        for i_elevation, elevation in enumerate(elevation_samples):
            a = get_steering_vector(elevation, azimuth) * 1 / math.sqrt(NX * NY)

            # Calculate the conjugate of the vector a
            conjugate_a = np.conjugate(a)

            codebook[i_azimuth, i_elevation, :] = conjugate_a

    return codebook
