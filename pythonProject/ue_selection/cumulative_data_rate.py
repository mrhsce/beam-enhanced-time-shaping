import numpy as np


class CumulativeDataRates:
    def __init__(self, number_of_users):
        # Initialize the cumulative data rate (Ri) for each user to one, using numpy ndarray
        self.cumulative_data_rates = np.ones(number_of_users)
        self.delta = 0.1  # This is a constant that might be defined elsewhere in the system

    def update(self, bitrates):
        # bitrates is a numpy array of the current bitrate for each user (ri(T))
        # The formula is vectorized for efficient computation
        self.cumulative_data_rates = (1 - self.delta) * self.cumulative_data_rates + self.delta * bitrates

    def get_cumulative_data_rates(self, decimals=None):
        # Return the current cumulative data rates
        if decimals is not None:
            return [round(rate, decimals) for rate in self.cumulative_data_rates]
        else:
            return self.cumulative_data_rates
