import json

import numpy as np
import matplotlib.pyplot as plt
from pythonProject.beamforming.digital_beamforming.zero_forcing import get_weighted_normalized_digital_beamformer
import os

from pythonProject.environment.antenna_array import URPA


class SINRDataCollector:
    def __init__(self, environment, num_coherence_intervals=10000, coherence_interval_duration=10, output_directory='./output'):
        self.environment = environment
        self.num_coherence_intervals = num_coherence_intervals
        self.sinr_list_all_intervals = []
        self.output_directory = output_directory
        self.coherence_interval_duration = coherence_interval_duration
        self._sinr_db_sorted_per_ue = {}

    def collect_data(self):
        """
        Collect SINR data over multiple coherence intervals.

        Returns
        -------
        sinr_list_all_intervals : list
            A list of SINR values collected for all UEs across all intervals.
        """

        for i in range(self.num_coherence_intervals):
            if i % int(100/self.coherence_interval_duration) == 0:
                self.environment.generate_path_clusters_matrix()

            # Move UEs and apply short-term fading
            self.environment.move_ues(self.coherence_interval_duration / 1000)
            self.environment.short_term_fading_effect_on_path_clusters()

            # Generate channel matrices for this interval
            channel_matrices = self.environment.generate_channel_matrices(URPA)

            # Compute SINR for the UEs in this interval
            sinr_dict = self.compute_sinr(channel_matrices)
            self.sinr_list_all_intervals.append(list(sinr_dict.values()))  # Append only SINR values

            if i % 1000 == 0 and i != 0:
                print(f"Finished {int(i/1000)}k channel realizations.")

        self.precompute_sinr_cdfs()
        return self.sinr_list_all_intervals

    def compute_sinr(self, channel_matrices, noise_power=1.00e-12):
        """
        Compute the SINR for each UE given the current channel matrices.

        Parameters
        ----------
        channel_matrices : np.ndarray
            Shape (num_bs, num_antennas, num_ues). The channel matrix for each BS and UE.
        noise_power : float, optional
            Noise power to be used in SINR calculation (default: 1.0).

        Returns
        -------
        sinr_dict : dict
            A dictionary mapping UE identifiers to their corresponding SINR values.
        """
        sinr_dict = {}

        # Iterate over each base station (BS)
        for bs in self.environment.bss:
            bs_idx = self.environment.find_bs_index(bs)

            # Get the channel matrix for the current BS
            channel_matrix = channel_matrices[bs_idx]

            # Get the assigned UEs and their weights for beamforming
            active_ues, active_ues_weights = bs.beamweight_manager.get_assigned_ues()
            active_ue_indices = [self.environment.find_ue_index(ue) for ue in active_ues]
            filtered_channel_matrix = channel_matrix[:, active_ue_indices]

            # Digital precoding matrix calculation
            digital_precoding_matrix = get_weighted_normalized_digital_beamformer(filtered_channel_matrix, active_ues_weights)

            # Loop over each UE assigned to this BS
            for ue_idx, ue in enumerate(active_ues):
                # Compute the SINR for this UE
                sinr = self.calculate_ue_bitrate_single_bs(filtered_channel_matrix, digital_precoding_matrix, None, ue_idx, noise_power)
                sinr_dict[ue.id] = sinr  # Map SINR to the corresponding UE

        sorted_sinr_dict = {k: v for k, v in sorted(sinr_dict.items())}

        return sorted_sinr_dict

    def calculate_ue_bitrate_single_bs(self, channel_matrix, digital_precoding_matrix, analog_precoding_matrix, ue, noise_power=1.00e-12):
        interference_power = 0

        effective_channel_matrix_serving = np.conj(channel_matrix[:, [ue]].T)
        if analog_precoding_matrix is not None:
            effective_channel_matrix_serving = effective_channel_matrix_serving @ analog_precoding_matrix

        signal_power = np.abs(effective_channel_matrix_serving @ digital_precoding_matrix[:, ue]) ** 2

        # Calculate interference power from other users at the same BS only
        for j in range(channel_matrix.shape[1]):
            if j != ue:
                interference_power += np.abs(effective_channel_matrix_serving @ digital_precoding_matrix[:, j]) ** 2

        # SINR calculation
        sinr = signal_power / (interference_power + noise_power)
        return sinr.item()

    def save_data(self, file_url='sinr_data.json'):
        """
        Save the SINR data to a file in JSON format.
        """
        # Ensure the output directory exists
        if not os.path.exists(self.output_directory):
            os.makedirs(self.output_directory)

        with open(file_url, 'w') as f:
            json.dump(self.sinr_list_all_intervals, f)
        print(f"Saved SINR data to {file_url}")

    def precompute_sinr_cdfs(self):
        """
        Precompute and cache sorted SINR samples (in dB) per UE index.
        Works with loaded JSON data: List[List[sinr]].
        """
        if not self.sinr_list_all_intervals:
            raise RuntimeError("No SINR data available. Load or collect data first.")

        sinr_per_ue = {}

        for sinr_list in self.sinr_list_all_intervals:
            for ue_idx, sinr in enumerate(sinr_list):
                if ue_idx not in sinr_per_ue:
                    sinr_per_ue[ue_idx] = []
                sinr_per_ue[ue_idx].append(sinr)

        # Convert to dB and sort
        for ue_idx, sinr_values in sinr_per_ue.items():
            sinr_values = np.array(sinr_values)
            sinr_db = 10 * np.log10(sinr_values + 1e-12)
            self._sinr_db_sorted_per_ue[ue_idx] = np.sort(sinr_db)

    def load_data(self, file_url='sinr_data.json'):
        """
        Load the SINR data from a file.
        """
        with open(file_url, 'r') as f:
            self.sinr_list_all_intervals = json.load(f)
            self.num_coherence_intervals = len(self.sinr_list_all_intervals)
        self.precompute_sinr_cdfs()
        print(f"Loaded SINR data from {file_url}")

    def get_robust_link_capacity(self, ue, reliability):
        """
        Return robust SINR based on empirical CDF.
        Reliability = P(SINR >= γ).

        Example:
            reliability = 95 → 5% outage SINR
        """
        if ue.id not in self._sinr_db_sorted_per_ue:
            raise KeyError(f"SINR CDF not available for UE {ue.id}")

        sinr_db_sorted = self._sinr_db_sorted_per_ue[ue.id]
        n = len(sinr_db_sorted)

        # Target outage probability
        outage_prob = 1.0 - reliability / 100.0

        # Index for empirical quantile
        idx = int(np.floor(outage_prob * n))
        idx = np.clip(idx, 0, n - 1)

        robust_sinr_db = sinr_db_sorted[idx]

        # Convert back to linear scale
        robust_sinr_linear = 10 ** (robust_sinr_db / 10)

        return robust_sinr_linear

    def get_beamweight_scaled_robust_link_capacity(self, ue, reliability, bs):
        """
        Return beamweight-scaled robust SINR for a UE under ZF.

        Assumptions:
        - Stored SINR was collected with equal power allocation.
        - Zero-forcing ⇒ only signal power scales with beamweight.
        - Noise + interference remain unchanged.

        Parameters
        ----------
        ue : UE object
        reliability : float
            Reliability in percent (e.g., 95 → 5% outage SINR)
        bs : BS object
            Base station serving the UE

        Returns
        -------
        scaled_robust_sinr_linear : float
            Beamweight-scaled robust SINR (linear scale)
        """

        # Step 1: get robust SINR under equal power allocation
        robust_sinr_equal = self.get_robust_link_capacity(ue, reliability)

        # Step 2: fetch current beamweights at this BS
        ue_list, weights = bs.beamweight_manager.get_assigned_ues()

        if ue not in ue_list:
            raise KeyError(f"UE {ue.id} is not assigned to BS {bs.id}")

        # Step 3: extract UE beamweight
        weight_map = {u: w for u, w in zip(ue_list, weights)}
        w_ue = weight_map[ue]

        # Step 4: compute equal-allocation weight
        num_ues = len(ue_list)
        w_equal = 1.0 / num_ues

        # Step 5: scale SINR (linear domain)
        scaling_factor = w_ue / w_equal
        scaled_robust_sinr = robust_sinr_equal * scaling_factor

        return scaled_robust_sinr

    def plot_sinr_distribution(self, bin_count=100):
        """
        Plot the SINR distribution across all UEs and coherence intervals and save the plot.
        """
        # Create a dictionary to hold the SINR values for each UE across all intervals
        sinr_dict_ue = {}

        # Collect the SINR values for each UE across all intervals
        for sinr_dict in self.sinr_list_all_intervals:
            sinr_list = list(sinr_dict)  # Convert dict_values to a list

            for ue_idx, sinr_value in enumerate(sinr_list):
                # Using UE index as a key, accumulate SINR values
                if ue_idx not in sinr_dict_ue:
                    sinr_dict_ue[ue_idx] = []
                sinr_dict_ue[ue_idx].append(sinr_value)

        # Plotting a separate histogram for each UE and saving the plots to files
        for ue_id, sinr_values in sinr_dict_ue.items():
            plt.figure(figsize=(10, 6))  # Create a new figure for each UE

            # Log-transform the SINR values (only if they are positive)
            sinr_values_log = 10 * np.log10(np.array(sinr_values) + 1e-12)  # Adding a small constant to avoid log(0)

            # Get the counts, bin edges, and patches
            counts, bin_edges, patches = plt.hist(sinr_values_log, bins=bin_count, alpha=0.7)

            # Get the number of samples (data points)
            n_samples = len(sinr_values)

            # Calculate the bin width (assuming equal-width bins)
            bin_width = bin_edges[1] - bin_edges[0]

            # Normalize the counts (frequency)
            normalized_counts = counts / n_samples * 100

            # Clear the previous plot and re-plot with normalized counts
            plt.clf()  # Clear the previous plot

            # Plot the normalized histogram
            plt.bar(bin_edges[:-1], normalized_counts, width=bin_width, alpha=0.7, align='edge')

            plt.title(f'SINR Distribution for UE {ue_id} (Log Scale)')
            plt.xlabel('SINR (dB)')
            plt.ylabel('Probability (%)')  # This will now show the normalized density
            plt.grid(True)

            # Ensure the output directory exists
            if not os.path.exists(self.output_directory):
                os.makedirs(self.output_directory)

            # Save the plot to a file
            plot_filename = f'{self.output_directory}/sinr_distribution_ue_{ue_id}.png'
            plt.savefig(plot_filename, format='png')
            plt.close()  # Close the figure to avoid display

