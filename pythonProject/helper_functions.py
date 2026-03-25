import json
import os
import time
from functools import reduce
from math import gcd

import numpy as np


def time_it(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        time_taken = end_time - start_time
        return result, time_taken

    return wrapper

def time_it_cpu(func):
    def wrapper(*args, **kwargs):
        start_process_time = time.process_time()
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        end_process_time = time.process_time()
        time_taken = end_time - start_time
        cpu_time_taken = end_process_time - start_process_time
        return result, time_taken, cpu_time_taken

    return wrapper

def store(plotter, name, directory=None):
    if directory is None:
        directory = 'output'
        if not os.path.exists(directory):
            os.makedirs(directory)
    plotter.savefig(f"{directory}/{name}", dpi=300)


def save_dictionary(channel_history, file_name='channel_history', output_directory='output'):
    if output_directory is not None and not os.path.exists(output_directory):
        os.makedirs(output_directory)

    def convert(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        raise TypeError("Object of type '%s' is not JSON serializable" % type(obj).__name__)

    with open(f"{output_directory + '/' if output_directory is not None else ''}{file_name}.json", 'w') as file:
        json.dump(channel_history, file, default=convert, indent=2)

    print(
        f"The data was successfully saved to {output_directory + '/' if output_directory is not None else ''}{file_name}.json")


def load_dictionary(file_path='output/channel_history.json'):
    with open(file_path, 'r') as file:
        return json.load(file)


def generate_complex_gaussian(mean, variance):
    real_part = np.random.normal(mean, np.sqrt(variance) / 2)
    imag_part = np.random.normal(mean, np.sqrt(variance) / 2)
    complex_number = real_part + 1j * imag_part
    return complex_number


def generate_gaussian(mean, variance):
    return np.random.normal(mean, np.sqrt(variance))


def generate_lognormal(mean, variance):
    return np.random.lognormal(mean, np.sqrt(variance))


def generate_uniform(lower_bound, upper_bound):
    return np.random.uniform(lower_bound, upper_bound)


def calculate_coherence_time(speed_kmh, frequency_ghz):
    """
    Calculate the coherence time for a given speed and frequency.

    Parameters:
    speed_kmh (float): The relative speed in kilometers per hour.
    frequency_ghz (float): The carrier frequency in gigahertz.

    Returns:
    float: The coherence time in seconds.
    """
    # Constants
    c = 3e8  # Speed of light in m/s

    # Convert speed from km/h to m/s
    speed_ms = speed_kmh * 1000 / 3600

    # Convert frequency from GHz to Hz
    frequency_hz = frequency_ghz * 1e9

    # Calculate Doppler spread
    fd = speed_ms * frequency_hz / c

    # Calculate and return coherence time
    coherence_time = 1 / fd
    return coherence_time

def lcm(a: int, b: int) -> int:
    return a * b // gcd(a, b)

def lcm_list(values):
    return reduce(lcm, values)

def compute_lcm_of_streams_and_coherence(streams, coherence_interval_ms: int) -> int:
    """
    Compute LCM of all stream periodic cycles and the channel coherence interval.

    :param streams: list of Stream objects
    :param coherence_interval_ms: coherence interval in milliseconds
    :return: LCM in milliseconds
    """
    stream_cycles_ms = [
        int(round(stream.periodic_cycle))
        for stream in streams
    ]

    # print("Stream periodic cycles:", stream_cycles_ms)
    # print("Coherence interval (ms):", coherence_interval_ms)

    return lcm_list(stream_cycles_ms + [coherence_interval_ms])

