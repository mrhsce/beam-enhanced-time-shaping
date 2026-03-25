import gc
import math
import random

import numpy as np

from pythonProject.beamforming.digital_beamforming.zero_forcing import get_weighted_normalized_digital_beamformer
from pythonProject.helper_functions import time_it_cpu
from pythonProject.scheduler.hop_based_coherence_interval_aware_tst_scheduler import HopBasedCoherenceIntervalAwareTstScheduler
from pythonProject.ue_selection.non_cooperative import calculate_ue_bitrate_single_bs

class BETSEnabler:
    """
    Beam-Enhanced Time Shaping (BETS)

    In this version, BETS includes:
      - A reference to the environment (for nodes, links).
      - A list of TST streams.
      - A BET_Generator component for best-effort traffic.
      - channel_coherence_duration: The time interval (in seconds) after which
        channel conditions might change, prompting new beam/scheduling decisions.
      - channel_sensing_time: Time (in seconds) required to sense or measure the channel.
      - wireless_propagation_delay: Time (in milliseconds) for signals/frames to travel through the channel.

    All of these parameters can be used to drive beamforming updates, scheduling windows,
    or timing offsets in the run_time_shaping method.
    """

    def __init__(
            self,
            environment,
            streams,
            bet_generator,
            channel_coherence_duration=2.5,
            channel_sensing_time=0.1,
            wireless_propagation_delay=0.01,
            wired_link_constant_delay=0.04
    ):
        """
        Initialize the BETS object.

        :param environment: PhysicalEnvironment instance containing the network topology.
        :param streams: A list of TST Stream objects (time-sensitive traffic).
        :param bet_generator: An instance of BET_Generator for best-effort traffic.
        :param channel_coherence_duration: Time interval (seconds) after which
                                          channel conditions may be recalculated.
        :param channel_sensing_time: Time (seconds) spent sensing the channel
                                     before scheduling new transmissions.
        :param wireless_propagation_delay: Time (milliseconds) for frames/signals to propagate
                                  through the medium.
        """
        self.environment = environment
        self.streams = streams
        self.active_streams = streams
        self.bet_generator = bet_generator

        self.channel_coherence_duration = channel_coherence_duration
        self.channel_sensing_time = channel_sensing_time
        self.wired_link_constant_delay = wired_link_constant_delay
        self.wireless_propagation_delay = wireless_propagation_delay
        self.scheduler = HopBasedCoherenceIntervalAwareTstScheduler(environment.connection_manager, streams,
                                              wired_link_constant_delay=wired_link_constant_delay)
        self.current_time = 0

        # Initialize the decision variables to equal resource allocation
        for bs in self.environment.bss:
            self.set_spectrum_bands_by_percentage(bs, uplink_percentage=50, downlink_percentage=50)
            ue_list = self.environment.connection_manager.get_connected_ues(bs)
            if len(ue_list) > 0:
                self.set_beamweight_by_bs(bs, ue_list, [1 / len(ue_list)] * len(ue_list))
            else:
                bs.beamweight_manager.clear_all()

    #   ************************************** Initialization and objective evaluation**************************************

    def set_streams(self, streams):
        self.streams = streams

    def set_spectrum_bands_by_percentage(self, bs, uplink_percentage, downlink_percentage):
        bs.spectrum_manager.assign_bands(uplink_percentage, downlink_percentage)
        connected_ues = self.environment.connection_manager.get_connected_ues(bs)
        for ue in connected_ues:
            uplink = self.environment.connection_manager.get_link(ue, bs)
            uplink.bandwidth = bs.spectrum_manager.get_uplink_bandwidth()

            downlink = self.environment.connection_manager.get_link(bs, ue)
            downlink.bandwidth = bs.spectrum_manager.get_downlink_bandwidth()

    def set_spectrum_bands_by_downlink_bandwidth(self, bs, downlink_bandwidth):
        bs.spectrum_manager.assign_bands_by_downlink_bandwidth(downlink_bandwidth)
        connected_ues = self.environment.connection_manager.get_connected_ues(bs)
        for ue in connected_ues:
            uplink = self.environment.connection_manager.get_link(ue, bs)
            uplink.bandwidth = bs.spectrum_manager.get_uplink_bandwidth()

            downlink = self.environment.connection_manager.get_link(bs, ue)
            downlink.bandwidth = bs.spectrum_manager.get_downlink_bandwidth()

    def set_beamweight_by_bs(self, bs, ue_list, weights_list):
        for i, ue in enumerate(ue_list):
            bs.beamweight_manager.set_beamweight(ue, weights_list[i])
            uplink = self.environment.connection_manager.get_link(ue, bs)
            uplink.beamweight = weights_list[i]
            downlink = self.environment.connection_manager.get_link(bs, ue)
            downlink.beamweight = weights_list[i]

    def find_max_possible_beamweight(self, link):
        ue, bs = self.environment.connection_manager.get_ue_and_bs(link)
        # Always get the downlink between BS and UE
        downlink = self.environment.connection_manager.get_link(bs, ue)
        if not downlink:
            raise ValueError(f"No downlink found between BS {bs} and UE {ue}.")

        # Get all wireless downlinks from this BS
        bs_downlinks = [
            l for l in self.environment.connection_manager.find_connected_links(bs, outgoing=True)
            if l.link_type == "wireless"
        ]

        # Calculate the total current beamweight excluding the current link
        total_beamweight = sum(l.beamweight for l in bs_downlinks if l != downlink)

        max_increase = 1 - total_beamweight
        # If the increase exceeds 1, raise an error
        if max_increase > 1:
            raise ValueError(f"Beamweight increase exceeds the allowed limit: {max_increase}")

        return max_increase

    def is_beamweight_increase_possible(self, link, weight):
        max_possible_weight = self.find_max_possible_beamweight(link)
        return max_possible_weight >= weight

    def set_beamweight_by_link(self, link, weight):
        """
        Sets the beamweight for a given wireless link.

        :param link: The wireless link for which the beamweight is to be set.
        :param weight: The new beamweight value.
        """
        ue_bs_pair = self.environment.connection_manager.get_ue_and_bs(link)
        if not ue_bs_pair:
            raise ValueError(f"Invalid link: {link}. It must be a wireless link between a UE and a BS.")

        ue, bs = ue_bs_pair

        # Set beamweight in the beamweight manager
        bs.beamweight_manager.set_beamweight(ue, weight)

        # Update beamweight for both uplink and downlink
        uplink = self.environment.connection_manager.get_link(ue, bs)
        downlink = self.environment.connection_manager.get_link(bs, ue)

        if uplink:
            uplink.beamweight = weight
        if downlink:
            downlink.beamweight = weight

    def calculate_spectral_efficiency(self, bs, ue, channel_matrix):
        active_ues, active_ues_weights = bs.beamweight_manager.get_assigned_ues()
        active_ue_indices = [self.environment.find_ue_index(ue) for ue in active_ues]
        filtered_channel_matrix = channel_matrix[:, active_ue_indices]
        digital_precoding_matrix = get_weighted_normalized_digital_beamformer(filtered_channel_matrix,
                                                                              active_ues_weights)

        return calculate_ue_bitrate_single_bs(filtered_channel_matrix, digital_precoding_matrix, None,
                                              active_ues.index(ue))

    def calculate_links_bitrate(self, channel_matrices):
        # Calculates the bitrate of each link based on the channel matrix, beam weight and spectrum management
        # Output is a dictionary of {link, bitrate}
        links_bitrate = {}
        for downlink, uplink, bs, ue in self.environment.connection_manager.get_all_wireless_link_pairs():
            spectral_efficiency = self.calculate_spectral_efficiency(bs, ue, channel_matrices[
                self.environment.find_bs_index(bs)])
            links_bitrate[uplink] = spectral_efficiency * bs.spectrum_manager.get_uplink_bandwidth()
            links_bitrate[downlink] = spectral_efficiency * bs.spectrum_manager.get_downlink_bandwidth()

        return links_bitrate

    def calculate_bet_throughput_shortage(self, target_link, link_aggregate_instantaneous_bitrate, links_bitrate,
                                          satisfied_streams):
        # Calculates the difference between (total throughput - TST throughput) and (BET throughput)
        # The output is capacity (bits)
        total_available_throughput = links_bitrate[target_link] * (
                self.channel_coherence_duration - self.channel_sensing_time - self.wireless_propagation_delay)
        total_bet_throughput = target_link.bet_queue.get_length()
        total_tst_throughput = sum(
            link_aggregate_instantaneous_bitrate[target_link][stream]["total_throughput"]
            for stream in link_aggregate_instantaneous_bitrate[target_link]
            if stream in satisfied_streams
        )

        return max(total_tst_throughput + total_bet_throughput - total_available_throughput, 0)

    def check_stream_satisfiability(self, target_stream, link_aggregate_instantaneous_bitrate, links_bitrate):
        is_satisfied = True
        active_wireless_links = target_stream.get_active_wireless_links(self.environment, self.current_time,
                                                                        self.channel_coherence_duration,
                                                                        self.channel_sensing_time)
        for link in active_wireless_links:
            if target_stream not in link_aggregate_instantaneous_bitrate[link]:
                raise ValueError("Target stream not in the dictionary")
            if round(link_aggregate_instantaneous_bitrate[link][target_stream]["max_bitrate"], 3) > round(
                    links_bitrate[link], 3):
                is_satisfied = False
                break
        return is_satisfied

    def check_stream_robust_satisfiability(self, target_stream, link_aggregate_instantaneous_bitrate, sinr_collector):
        is_satisfied = True
        active_wireless_links = target_stream.get_active_wireless_links(self.environment, self.current_time,
                                                                        self.channel_coherence_duration,
                                                                        self.channel_sensing_time)
        for link in active_wireless_links:
            if target_stream not in link_aggregate_instantaneous_bitrate[link]:
                raise ValueError("Target stream not in the dictionary")
            ue, bs = self.environment.connection_manager.get_ue_and_bs(link)
            robust_link_sinr = sinr_collector.get_beamweight_scaled_robust_link_capacity(ue, target_stream.reliability, bs)
            robust_link_bitrate = link.bandwidth * np.log2(1.0 + robust_link_sinr)
            if round(link_aggregate_instantaneous_bitrate[link][target_stream]["max_bitrate"], 3) > round(
                    robust_link_bitrate, 3):
                is_satisfied = False
                break
        return is_satisfied

    def find_satisfied_streams(self, link_aggregate_instantaneous_bitrate, links_bitrate):
        satisfied_streams = []
        for stream in self.streams:
            if self.check_stream_satisfiability(stream, link_aggregate_instantaneous_bitrate, links_bitrate):
                satisfied_streams.append(stream)

        return satisfied_streams

    def find_robustly_satisfied_streams(self, link_aggregate_instantaneous_bitrate, sinr_collector):
        satisfied_streams = []
        for stream in self.streams:
            if self.check_stream_robust_satisfiability(stream, link_aggregate_instantaneous_bitrate, sinr_collector):
                satisfied_streams.append(stream)

        return satisfied_streams

    def find_sorted_unsatisfied_streams(self, link_aggregate_instantaneous_bitrate, links_bitrate):
        """
        Gathers all unsatisfied streams and sorts them in ascending order
        based on the maximum link_aggregate_instantaneous_bitrate they have
        across their wireless links.
        """
        unsatisfied_streams_info = []

        for stream in self.streams:
            # Check if the stream is unsatisfied
            if not self.check_stream_satisfiability(stream, link_aggregate_instantaneous_bitrate, links_bitrate):
                max_bitrate_for_stream = 0.0
                active_wireless_links = stream.get_active_wireless_links(self.environment, self.current_time,
                                                                         self.channel_coherence_duration,
                                                                         self.channel_sensing_time)
                # Find the maximum instantaneous bitrate across all wireless links in the path
                for link in active_wireless_links:
                    bitrate = link_aggregate_instantaneous_bitrate[link][stream]["max_bitrate"]
                    max_bitrate_for_stream = max(max_bitrate_for_stream, bitrate)

                unsatisfied_streams_info.append((stream, max_bitrate_for_stream))

        # Sort by the maximum bitrate in ascending order
        unsatisfied_streams_info.sort(key=lambda x: x[1])

        # Extract just the stream objects in sorted order
        sorted_unsatisfied_streams = [item[0] for item in unsatisfied_streams_info]
        return sorted_unsatisfied_streams

        # Sort the unsatisfied streams based on the minimum unsatisfied frame delay budget
        return unsatisfied_streams

    def find_robustly_sorted_unsatisfied_streams(self, link_aggregate_instantaneous_bitrate, sinr_collector):
        """
        Gathers all unsatisfied streams and sorts them in ascending order
        based on the maximum link_aggregate_instantaneous_bitrate they have
        across their wireless links.
        """
        unsatisfied_streams_info = []

        for stream in self.streams:
            # Check if the stream is unsatisfied
            if not self.check_stream_robust_satisfiability(stream, link_aggregate_instantaneous_bitrate, sinr_collector):
                max_bitrate_for_stream = 0.0
                active_wireless_links = stream.get_active_wireless_links(self.environment, self.current_time,
                                                                         self.channel_coherence_duration,
                                                                         self.channel_sensing_time)
                # Find the maximum instantaneous bitrate across all wireless links in the path
                for link in active_wireless_links:
                    bitrate = link_aggregate_instantaneous_bitrate[link][stream]["max_bitrate"]
                    max_bitrate_for_stream = max(max_bitrate_for_stream, bitrate)

                unsatisfied_streams_info.append((stream, max_bitrate_for_stream))

        # Sort by the maximum bitrate in ascending order
        unsatisfied_streams_info.sort(key=lambda x: x[1])

        # Extract just the stream objects in sorted order
        sorted_unsatisfied_streams = [item[0] for item in unsatisfied_streams_info]
        return sorted_unsatisfied_streams


    def evaluate_objective_function(self, link_aggregate_instantaneous_bitrate, links_bitrate):
        satisfied_streams = self.find_satisfied_streams(link_aggregate_instantaneous_bitrate, links_bitrate)
        bet_throughput_shortage = 0
        for link in self.environment.connection_manager.get_all_wireless_links():
            bet_throughput_shortage += self.calculate_bet_throughput_shortage(link,
                                                                              link_aggregate_instantaneous_bitrate,
                                                                              links_bitrate, satisfied_streams)

        return satisfied_streams, bet_throughput_shortage

    def get_current_status(self):
        """
        Return a snapshot of the current system status with:
          - beamweights per UE for each BS (keys are actual BS/UE objects)
          - bandwidth split (UL/DL) per BS (key is actual BS object)

        NOTE: Since keys are objects, this won't be JSON-serializable by default.
        """
        # -------- Beamweights per BS/UE (object keys) --------
        beamweights = {}
        for bs in self.environment.bss:
            ue_list, weights = bs.beamweight_manager.get_assigned_ues()
            beamweights[bs] = {ue: w for ue, w in zip(ue_list, weights)}

        # -------- Bandwidth split per BS (object keys) --------
        bandwidth_split = {}
        for bs in self.environment.bss:
            bandwidth_split[bs] = {
                "downlink_bandwidth": bs.spectrum_manager.get_downlink_bandwidth(),
                "uplink_bandwidth": bs.spectrum_manager.get_uplink_bandwidth(),
            }

        return beamweights, bandwidth_split

    #   ************************************************* BeamWeight Optimization*******************************************

    def find_beamweight_satisfiability_threshold(self, link_aggregate_instantaneous_bitrate, link_bitrates):
        # Go through the path of the stream and check what is the minimum needed beamweight for the satisfaction of the stream
        satisfiability_threshold = {}
        for stream in self.streams:
            active_wireless_links = stream.get_active_wireless_links(self.environment, self.current_time,
                                                                     self.channel_coherence_duration,
                                                                     self.channel_sensing_time)
            path_links = self.scheduler.get_stream_paths(stream)
            beamweight_per_link = {}
            for link in path_links:
                if link in active_wireless_links:
                    target_weight = 10
                    if link.bandwidth != 0:
                        current_spectral_efficiency = link_bitrates[link] / link.bandwidth
                        target_spectral_efficiency = link_aggregate_instantaneous_bitrate[link][stream][
                                                         "max_bitrate"] / link.bandwidth
                        if (target_spectral_efficiency < 1024):
                            current_SINR = math.exp2(current_spectral_efficiency) - 1
                            target_SINR = math.exp2(target_spectral_efficiency) - 1
                            if current_SINR != 0:
                                target_weight = target_SINR / current_SINR * link.beamweight

                    beamweight_per_link[link] = target_weight
                else:  # handle wired links or inactive streams
                    beamweight_per_link[link] = 0

            satisfiability_threshold[stream] = beamweight_per_link

        return satisfiability_threshold

    def find_robust_beamweight_satisfiability_threshold(self, link_aggregate_instantaneous_bitrate, sinr_collector):
        # Go through the path of the stream and check what is the minimum needed beamweight for the satisfaction of the stream
        satisfiability_threshold = {}
        for stream in self.streams:
            active_wireless_links = stream.get_active_wireless_links(self.environment, self.current_time,
                                                                     self.channel_coherence_duration,
                                                                     self.channel_sensing_time)
            path_links = self.scheduler.get_stream_paths(stream)
            beamweight_per_link = {}
            for link in path_links:
                if link in active_wireless_links:
                    target_weight = 10
                    if link.bandwidth != 0:
                        ue, _ = self.environment.connection_manager.get_ue_and_bs(link)
                        robust_link_sinr = sinr_collector.get_robust_link_capacity(ue, stream.reliability)
                        current_spectral_efficiency = np.log2(1.0 + robust_link_sinr)
                        target_spectral_efficiency = link_aggregate_instantaneous_bitrate[link][stream][
                                                         "max_bitrate"] / link.bandwidth
                        if (target_spectral_efficiency < 1024):
                            current_SINR = math.exp2(current_spectral_efficiency) - 1
                            target_SINR = math.exp2(target_spectral_efficiency) - 1
                            if current_SINR != 0:
                                target_weight = target_SINR / current_SINR * link.beamweight

                    beamweight_per_link[link] = target_weight
                else:  # handle wired links or inactive streams
                    beamweight_per_link[link] = 0

            satisfiability_threshold[stream] = beamweight_per_link

        return satisfiability_threshold

    def find_satisfied_streams_by_beamweight(self, streams, stream_satisfiability_beamweight_threshold):
        satisfied_streams = []

        for stream in streams:
            active_wireless_links = stream.get_active_wireless_links(self.environment, self.current_time,
                                                                     self.channel_coherence_duration,
                                                                     self.channel_sensing_time)
            for link in active_wireless_links:
                if link.beamweight < stream_satisfiability_beamweight_threshold[stream][link]:
                    break
            else:
                satisfied_streams.append(stream)

        return satisfied_streams

    def find_secondary_satisfiable_streams_by_beamweight(self, previously_satisfiable_streams,
                                                         stream_satisfiability_beamweight_threshold):
        # Ensure that all the links in the path of the stream have the capacity of increasing their weight for the satisfaction of the stream
        new_satisfiable_streams = []
        for stream in previously_satisfiable_streams:
            beamweight_backup = {}
            active_wireless_links = stream.get_active_wireless_links(self.environment, self.current_time,
                                                                     self.channel_coherence_duration,
                                                                     self.channel_sensing_time)
            for link in active_wireless_links:
                if link.beamweight < stream_satisfiability_beamweight_threshold[stream][link]:
                    if self.is_beamweight_increase_possible(link,
                                                            stream_satisfiability_beamweight_threshold[stream][link]):
                        beamweight_backup[link] = link.beamweight
                        self.set_beamweight_by_link(link, stream_satisfiability_beamweight_threshold[stream][link])
                    else:
                        break
            else:
                new_satisfiable_streams.append(stream)

            for link in beamweight_backup:
                self.set_beamweight_by_link(link, beamweight_backup[link])

        return new_satisfiable_streams

    def find_initial_satisfiable_streams_by_beamweight(self, stream_satisfiability_beamweight_threshold):
        satisfiable_streams = []
        for stream in self.streams:
            beamweight_per_link = stream_satisfiability_beamweight_threshold[stream]
            # First check every single one to find if anywhere there are more that one
            if not all(value <= 1 for value in beamweight_per_link.values()):
                continue

            # Then check if the sum of weight of the same BS is not greater than one
            # only checks the next link
            beamweight_per_link_list = list(beamweight_per_link)  # Convert keys to a list
            for i in range(len(beamweight_per_link_list) - 1):
                link = beamweight_per_link_list[i]
                next_link = beamweight_per_link_list[i + 1]

                # TODO this is temporary and for test, remove it later
                # Ensure path continuity
                if link.node2 != next_link.node1:
                    raise Exception("Error in the path!")

                # If two consecutive wireless links exceed beamweight sum > 1, discard the stream immediately
                if link.link_type == next_link.link_type == "wireless":
                    if beamweight_per_link[link] + beamweight_per_link[next_link] > 1:
                        break  # Stop checking and discard the stream
            else:
                # Only add to satisfiable streams if we never broke out of the loop
                satisfiable_streams.append(stream)

        return satisfiable_streams

    def evaluate_stream_while_satisfied(self, stream, previously_satisfiable_streams,
                                        stream_satisfiability_beamweight_threshold, tmp=True):
        """
        Temporarily increases the beamweights for the satisfaction of the given stream,
        calculates the newly satisfied and satisfiable streams, and reverts if needed.

        :param stream: The stream to evaluate.
        :param stream_satisfiability_beamweight_threshold: Dictionary containing beamweight
                                                           thresholds per stream.
        :param tmp: Boolean flag to indicate whether to revert changes after evaluation.
        :return: Tuple containing satisfied streams and satisfiable streams.
        """

        # Backup the current beamweights to revert if needed
        beamweight_backup = {}
        active_wireless_links = stream.get_active_wireless_links(self.environment, self.current_time,
                                                                 self.channel_coherence_duration,
                                                                 self.channel_sensing_time)
        for link in active_wireless_links:
            if link.beamweight < stream_satisfiability_beamweight_threshold[stream][link]:
                beamweight_backup[link] = link.beamweight
                self.set_beamweight_by_link(link, stream_satisfiability_beamweight_threshold[stream][link])

        # Identify satisfied and satisfiable streams
        satisfied_streams = self.find_satisfied_streams_by_beamweight(previously_satisfiable_streams,
                                                                      stream_satisfiability_beamweight_threshold)
        satisfiable_streams = self.find_secondary_satisfiable_streams_by_beamweight(previously_satisfiable_streams,
                                                                                    stream_satisfiability_beamweight_threshold)

        # Revert beamweight changes if tmp is True
        if tmp:
            for link in beamweight_backup:
                self.set_beamweight_by_link(link, beamweight_backup[link])

        return satisfied_streams, satisfiable_streams

    def greedy_stream_satisfier_by_beamweight(self, stream_satisfiability_beamweight_threshold):
        # This function in a greedy manner find an optimal stream to be satisfied each turn, it continues untill no satisfiable streams are remaining
        satisfiable_streams = self.find_initial_satisfiable_streams_by_beamweight(
            stream_satisfiability_beamweight_threshold)
        all_satisfied_streams = []

        while len(satisfiable_streams) > 0:
            satisfied_streams = []
            optimal_stream = None
            optimal_results = -2000
            for stream in satisfiable_streams:
                new_satisfied_streams, new_satisfiable_streams = self.evaluate_stream_while_satisfied(stream,
                                                                                                      satisfiable_streams,
                                                                                                      stream_satisfiability_beamweight_threshold)
                increase_in_satisfied = len(new_satisfied_streams) - len(satisfied_streams)
                decrease_in_satisfiability = len(satisfiable_streams) - len(new_satisfiable_streams)
                results = increase_in_satisfied - decrease_in_satisfiability
                if results > optimal_results:
                    optimal_stream = stream
                    optimal_results = results

            satisfied_streams, satisfiable_streams = self.evaluate_stream_while_satisfied(optimal_stream,
                                                                                          satisfiable_streams,
                                                                                          stream_satisfiability_beamweight_threshold,
                                                                                          False)
            # Remove streams from satisfiable_streams that are already in satisfied_streams
            satisfiable_streams = [stream for stream in satisfiable_streams if stream not in satisfied_streams]
            all_satisfied_streams.extend(satisfied_streams)

        return all_satisfied_streams

    def assign_remaining_beamweight_based_on_discrepancy(self, links_bitrate, link_aggregate_instantaneous_bitrate,
                                                         satisfied_streams):
        # TODO implement this function correctly
        """
        Adjusts beamweights for links that cannot currently support their best-effort (BET) traffic.
        Increases beamweight while ensuring that the total beamweight at each BS does not exceed 1.

        :param link_bitrates: A dictionary mapping links to their current bitrate values.
        """
        for link in self.environment.connection_manager.get_all_wireless_links():
            total_bet_throughput = link.bet_queue.get_length()
            total_tst_throughput = sum(
                link_aggregate_instantaneous_bitrate[link][stream]["total_throughput"]
                for stream in link_aggregate_instantaneous_bitrate[link]
                if stream in satisfied_streams
            )
            required_bitrate = (total_bet_throughput + total_tst_throughput) / (
                    self.channel_coherence_duration - self.channel_sensing_time - self.wireless_propagation_delay)
            if required_bitrate > links_bitrate[link]:
                # TODO handle the scenario where the beamweight of the link is zero
                current_spectral_efficiency = links_bitrate[link] / link.bandwidth
                target_spectral_efficiency = required_bitrate / link.bandwidth
                if (target_spectral_efficiency < 1024):
                    current_SINR = math.exp2(current_spectral_efficiency) - 1
                    target_SINR = math.exp2(target_spectral_efficiency) - 1
                    if link.beamweight == 0:
                        raise Exception("Beamweight is zero!")
                    target_weight = target_SINR / current_SINR * link.beamweight
                    max_possible_weight = self.find_max_possible_beamweight(link)
                    self.set_beamweight_by_link(link, min(target_weight, max_possible_weight))

    def assign_remaining_beamweight_equally(self, zero_link_strategy="allocation"):
        """
        Distributes the remaining beamweight equally among UEs in each BS.
        If no_zero_link is True, UEs with zero weight do not receive any extra beamweight.
        """
        for bs in self.environment.bss:
            ue_list, current_weights = bs.beamweight_manager.get_assigned_ues()
            remaining_weight = 1 - sum(current_weights)

            if remaining_weight > 0:
                new_weights = []
                if zero_link_strategy == "no_allocation":
                    non_zero_ues = [w for w in current_weights if w > 0]
                    if non_zero_ues:
                        new_weights = [
                            w + (remaining_weight / len(non_zero_ues)) if w > 0 else w
                            for w in current_weights
                        ]
                else:
                    new_weights = [w + (remaining_weight / len(ue_list)) for w in current_weights]

                self.set_beamweight_by_bs(bs, ue_list, new_weights)

    def assign_remaining_beamweight_proportionally(self, zero_link_strategy="equal_to_lowest"):
        """
        Distributes the remaining beamweight proportionally among UEs in each BS.
        If zero_link_strategy is "equal_to_lowest", zero-weight links receive the same allocation as the lowest-weighted UE.
        If zero_link_strategy is "no_allocation", zero-weight links receive no additional beamweight.

        :param zero_link_strategy: Strategy for zero-weight links: "equal_to_lowest" or "no_allocation"
        """
        for bs in self.environment.bss:
            ue_list, current_weights = bs.beamweight_manager.get_assigned_ues()
            remaining_weight = 1 - sum(current_weights)

            if remaining_weight > 0:
                non_zero_weights = [w for w in current_weights if w > 0]
                lowest_weight = min(non_zero_weights) if non_zero_weights else 0

                if zero_link_strategy == "equal_to_lowest" and lowest_weight > 0:
                    adjusted_weights = [w if w > 0 else lowest_weight for w in current_weights]
                else:  # "no_allocation" or default
                    adjusted_weights = [w for w in current_weights]

                total_adjusted_weight = sum(adjusted_weights)
                if total_adjusted_weight > 0:
                    new_weights = [current + (remaining_weight * (w / total_adjusted_weight)) for current, w in
                                   zip(current_weights, adjusted_weights)]
                else:
                    new_weights = current_weights  # No valid distribution

                self.set_beamweight_by_bs(bs, ue_list, new_weights)

    def assign_remaining_beamweight_inverse_proportional(self, zero_link_strategy="equal_to_highest"):
        """
        Distributes the remaining beamweight inversely proportional to the current weights of the UEs in each BS.
        If zero_link_strategy is "equal_to_highest", zero-weight links receive the highest remaining weight.
        If zero_link_strategy is "no_allocation", zero-weight links receive no additional beamweight.

        :param zero_link_strategy: Strategy for zero-weight links: "equal_to_highest" or "no_allocation"
        """
        for bs in self.environment.bss:
            ue_list, current_weights = bs.beamweight_manager.get_assigned_ues()
            remaining_weight = 1 - sum(current_weights)

            if remaining_weight > 0:
                inverse_weights = [1 / w if w > 0 else 0 for w in current_weights]

                if zero_link_strategy == "equal_to_highest":
                    max_inverse_weight = max(inverse_weights)
                    inverse_weights = [1 / w if w > 0 else max_inverse_weight for w in current_weights]

                total_inverse_weight = sum(inverse_weights)
                if total_inverse_weight > 0:
                    new_weights = [w + (remaining_weight * (inv_w / total_inverse_weight)) for w, inv_w in
                                   zip(current_weights, inverse_weights)]
                else:
                    new_weights = current_weights  # No valid distribution

                self.set_beamweight_by_bs(bs, ue_list, new_weights)

    def beamweight_optimization(self, link_aggregate_instantaneous_bitrate, channel_matrices,
                                rest_allocation_strategy="equal"):

        # Resetting the beamweight
        for bs in self.environment.bss:
            # Equal beamweight assignment among all the connected UEs
            ue_list = self.environment.connection_manager.get_connected_ues(bs)
            if len(ue_list) > 0:
                self.set_beamweight_by_bs(bs, ue_list, [1 / len(ue_list)] * len(ue_list))
            else:
                bs.beamweight_manager.clear_all()

        stream_satisfiability_beamweight_threshold = self.find_beamweight_satisfiability_threshold(
            link_aggregate_instantaneous_bitrate, self.calculate_links_bitrate(channel_matrices))

        # Zero out all beamweights for wireless links
        for link in self.environment.connection_manager.get_all_wireless_links(downlink=True):
            self.set_beamweight_by_link(link, 0)

        # Optimizing the streams
        resulted_satisfied_streams = self.greedy_stream_satisfier_by_beamweight(
            stream_satisfiability_beamweight_threshold)

        # bet_throughput_shortage = 0
        # for link in self.environment.connection_manager.get_all_wireless_links():
        #     bet_throughput_shortage += self.calculate_bet_throughput_shortage(link,
        #                                                                       link_aggregate_instantaneous_bitrate,
        #                                                                       self.calculate_links_bitrate(
        #                                                                           channel_matrices),
        #                                                                       resulted_satisfied_streams)
        # visualize_decision_variables(self.environment.bss, satisfied_streams, bet_throughput_shortage)

        # Allocate the remaining weights
        if rest_allocation_strategy == "equal":
            self.assign_remaining_beamweight_equally()
        if rest_allocation_strategy == "equal_no_zero":
            self.assign_remaining_beamweight_equally(zero_link_strategy="no_allocation")
        if rest_allocation_strategy == "proportional_equal_to_lowest":
            self.assign_remaining_beamweight_proportionally()
        if rest_allocation_strategy == "proportional_no_zero_link":
            self.assign_remaining_beamweight_proportionally(zero_link_strategy="no_allocation")
        if rest_allocation_strategy == "inverse_proportional_equal_to_highest":
            self.assign_remaining_beamweight_inverse_proportional()
        if rest_allocation_strategy == "inverse_proportional_no_zero_link":
            self.assign_remaining_beamweight_inverse_proportional(zero_link_strategy="no_allocation")
        if rest_allocation_strategy == "maximizing_BET":
            # TODO Implement this function
            self.assign_remaining_beamweight_based_on_discrepancy(self.calculate_links_bitrate(channel_matrices),
                                                                  link_aggregate_instantaneous_bitrate,
                                                                  resulted_satisfied_streams)
        beamweights = {}
        for bs in self.environment.bss:
            ue_list, weights = bs.beamweight_manager.get_assigned_ues()
            beamweights[bs] = {ue: w for ue, w in zip(ue_list, weights)}

        return beamweights, resulted_satisfied_streams

    def robust_beamweight_optimization(self, link_aggregate_instantaneous_bitrate, sinr_collector):

        # Resetting the beamweight
        for bs in self.environment.bss:
            # Equal beamweight assignment among all the connected UEs
            ue_list = self.environment.connection_manager.get_connected_ues(bs)
            if len(ue_list) > 0:
                self.set_beamweight_by_bs(bs, ue_list, [1 / len(ue_list)] * len(ue_list))
            else:
                bs.beamweight_manager.clear_all()

        stream_satisfiability_beamweight_threshold = self.find_robust_beamweight_satisfiability_threshold(
            link_aggregate_instantaneous_bitrate, sinr_collector)

        # Zero out all beamweights for wireless links
        for link in self.environment.connection_manager.get_all_wireless_links(downlink=True):
            self.set_beamweight_by_link(link, 0)

        # Optimizing the streams
        resulted_satisfied_streams = self.greedy_stream_satisfier_by_beamweight(
            stream_satisfiability_beamweight_threshold)


        self.assign_remaining_beamweight_equally()
        beamweights = {}
        for bs in self.environment.bss:
            ue_list, weights = bs.beamweight_manager.get_assigned_ues()
            beamweights[bs] = {ue: w for ue, w in zip(ue_list, weights)}

        return beamweights, resulted_satisfied_streams
    #   ************************************************* Spectrum Optimization*********************************************

    def find_spectrum_satisfiability_bandwidth(self, link_aggregate_instantaneous_bitrate, link_bitrates):
        """
        Determines the minimum spectrum bandwidth needed for each stream to be satisfied.

        :param link_aggregate_instantaneous_bitrate: Dictionary containing per-link aggregate bitrate information.
        :param link_bitrates: Dictionary containing the current bitrate per link.
        :return: Dictionary mapping each stream to the minimum required spectrum allocation per link.
        """
        stream_satisfiability_bandwidth = {}

        for stream in self.streams:
            active_wireless_links = stream.get_active_wireless_links(self.environment, self.current_time,
                                                                     self.channel_coherence_duration,
                                                                     self.channel_sensing_time)
            satisfiability_bandwidth_per_bs = {}
            for link in active_wireless_links:
                # Calculate the required bandwidth
                target_bandwidth = float('inf')
                if link_bitrates[link] != 0:
                    required_bitrate = link_aggregate_instantaneous_bitrate[link][stream]["max_bitrate"]
                    current_bandwidth = link.bandwidth
                    current_spectral_efficiency = link_bitrates[link] / current_bandwidth
                    target_bandwidth = required_bitrate / current_spectral_efficiency

                connected_ue, connected_bs = self.environment.connection_manager.get_ue_and_bs(link)
                link_type = self.environment.connection_manager.check_link_status(link)
                bandwidth_channels = (0, 0)
                if link_type == 'downlink':
                    bandwidth_channels = (target_bandwidth, 0)
                if link_type == 'uplink':
                    bandwidth_channels = (0, target_bandwidth)
                if connected_bs in satisfiability_bandwidth_per_bs:
                    previous_bandwidth_channels = satisfiability_bandwidth_per_bs[connected_bs]
                    satisfiability_bandwidth_per_bs[connected_bs] = (
                        max(previous_bandwidth_channels[0], bandwidth_channels[0]),
                        max(previous_bandwidth_channels[1], bandwidth_channels[1]))
                else:
                    satisfiability_bandwidth_per_bs[connected_bs] = bandwidth_channels

            stream_satisfiability_bandwidth[stream] = satisfiability_bandwidth_per_bs

        return stream_satisfiability_bandwidth

    def find_robust_spectrum_satisfiability_bandwidth(self, link_aggregate_instantaneous_bitrate, sinr_collector):
        stream_satisfiability_bandwidth = {}

        for stream in self.streams:
            active_wireless_links = stream.get_active_wireless_links(self.environment, self.current_time,
                                                                     self.channel_coherence_duration,
                                                                     self.channel_sensing_time)
            satisfiability_bandwidth_per_bs = {}
            for link in active_wireless_links:
                # Calculate the required bandwidth
                required_bitrate = link_aggregate_instantaneous_bitrate[link][stream]["max_bitrate"]
                ue, bs = self.environment.connection_manager.get_ue_and_bs(link)
                robust_link_sinr = sinr_collector.get_beamweight_scaled_robust_link_capacity(ue, stream.reliability, bs)
                current_spectral_efficiency = np.log2(1.0 + robust_link_sinr)
                target_bandwidth = required_bitrate / current_spectral_efficiency

                connected_ue, connected_bs = self.environment.connection_manager.get_ue_and_bs(link)
                link_type = self.environment.connection_manager.check_link_status(link)
                bandwidth_channels = (0, 0)
                if link_type == 'downlink':
                    bandwidth_channels = (target_bandwidth, 0)
                if link_type == 'uplink':
                    bandwidth_channels = (0, target_bandwidth)
                if connected_bs in satisfiability_bandwidth_per_bs:
                    previous_bandwidth_channels = satisfiability_bandwidth_per_bs[connected_bs]
                    satisfiability_bandwidth_per_bs[connected_bs] = (
                        max(previous_bandwidth_channels[0], bandwidth_channels[0]),
                        max(previous_bandwidth_channels[1], bandwidth_channels[1]))
                else:
                    satisfiability_bandwidth_per_bs[connected_bs] = bandwidth_channels

            stream_satisfiability_bandwidth[stream] = satisfiability_bandwidth_per_bs

        return stream_satisfiability_bandwidth


    def find_initial_satisfiable_streams_by_bandwidth(self, stream_satisfiability_bandwidth_threshold):
        """
        Identifies streams that can be initially satisfied based on spectrum bandwidth allocation.

        :param stream_satisfiability_bandwidth_threshold: Dictionary mapping each stream to the required
                                                          spectrum allocation per base station.
        :return: List of initially satisfiable streams.
        """
        satisfiable_streams = []
        downlink_bandwidth_range_per_bs = {}

        for stream in self.streams:
            for bs, (required_downlink_bw, required_uplink_bw) in stream_satisfiability_bandwidth_threshold[
                stream].items():
                if not bs.spectrum_manager.is_bandwidth_allocation_valid(required_downlink_bw, required_uplink_bw):
                    break
            else:
                satisfiable_streams.append(stream)
                for bs, (required_downlink_bw, required_uplink_bw) in stream_satisfiability_bandwidth_threshold[
                    stream].items():
                    downlink_bandwidth_range = bs.spectrum_manager.get_downlink_bandwidth_range(required_downlink_bw,
                                                                                                required_uplink_bw)
                    if not bs in downlink_bandwidth_range_per_bs:
                        downlink_bandwidth_range_per_bs[bs] = {}
                    downlink_bandwidth_range_per_bs[bs][stream] = downlink_bandwidth_range

        return satisfiable_streams, downlink_bandwidth_range_per_bs

    def find_bet_optimal_spectrum_point_and_set_it(self, optimal_range):
        # TODO: Implement this function.
        pass

    def greedy_stream_satisfier_by_bandwidth(self, stream_satisfiability_bandwidth_threshold):
        # TODO: Implement this function.

        satisfiable_streams = self.find_initial_satisfiable_streams_by_bandwidth(
            stream_satisfiability_bandwidth_threshold)

        self.find_bet_optimal_spectrum_point_and_set_it(optimal_range)

        return []

    def maximum_overlapping_stream_satisfier_by_bandwidth(
            self, stream_satisfiability_bandwidth_threshold
    ):
        """
        Finds the downlink range that covers the most number of stream downlink ranges (maximum intersection),
        picks the longest such maximum-intersection segment, then sets the middle of that segment as the
        bandwidth for the base station (BS). Finally, determines which streams are satisfied.

        :param stream_satisfiability_bandwidth_threshold: Dictionary mapping each stream to the required
                                                          spectrum allocation per base station.
        :return: List of satisfied streams.
        """
        # -- 1) Find streams that can be initially satisfied and their bandwidth ranges --
        satisfiable_streams, downlink_bandwidth_range_per_bs = (
            self.find_initial_satisfiable_streams_by_bandwidth(
                stream_satisfiability_bandwidth_threshold
            )
        )

        maximum_overlapping_ranges = {}

        # Iterate over each base station and find the longest max-intersection range
        for bs, stream_ranges in downlink_bandwidth_range_per_bs.items():

            # Collect all intervals (downlink ranges) for the current BS
            range_intervals = [stream_ranges[stream] for stream in stream_ranges]
            if not range_intervals:
                continue  # No intervals => skip

            # ------------------ BUILD EVENTS ------------------
            # We treat intervals [start, end] as inclusive. To handle this in a discrete
            # "sweep line" style, we create:
            #   (start, +1) for the start
            #   (end+1, -1) for the end, so that [start, end] coverage remains inclusive.
            events = []
            for start, end in range_intervals:
                events.append((start, +1))  # Start of interval
                events.append((end, -1))

            # Sort the events by time, ensuring starts (+1) come before ends (-1) when tied
            # (Although in this simple tuple sort, if times are equal, +1 < -1 by default)
            events.sort(key=lambda x: (x[0], -x[1]))

            # ------------------ FIRST PASS: FIND MAX INTERSECTION ------------------
            current_intersections = 0
            max_intersections = 0
            for _, effect in events:
                current_intersections += effect
                if current_intersections > max_intersections:
                    max_intersections = current_intersections

            # ---------------- SECOND PASS: COLLECT ALL MAX SEGMENTS ----------------
            # We'll track each continuous region where intersection == max_intersections.
            max_segments = []
            current_intersections = 0
            start_of_segment = None  # Where we enter a region of max intersection

            for i, (point, effect) in enumerate(events):
                prev_intersections = current_intersections
                current_intersections += effect

                # If we have just *entered* the max intersection level
                if prev_intersections < max_intersections and current_intersections == max_intersections:
                    start_of_segment = point

                # If we are leaving the max intersection level
                if prev_intersections == max_intersections and current_intersections < max_intersections:
                    # The max intersection region was [start_of_segment, point]
                    max_segments.append((start_of_segment, point))
                    start_of_segment = None

            # If the last event left us at max_intersections, we need to close that segment
            # at the largest possible endpoint from the intervals. This ensures we capture
            # any trailing region.
            if start_of_segment is not None:
                last_endpoint = max(end for (_, end) in range_intervals)
                max_segments.append((start_of_segment, last_endpoint))

            # ---------------- MERGE ANY OVERLAPPING MAX SEGMENTS ----------------
            # (In case multiple sub-ranges at max overlap are adjacent.)
            max_segments.sort()
            merged_segments = []
            for seg in max_segments:
                if not merged_segments:
                    merged_segments.append(seg)
                else:
                    prev_start, prev_end = merged_segments[-1]
                    curr_start, curr_end = seg
                    if curr_start <= prev_end + 1:  # Overlapping or adjacent
                        merged_segments[-1] = (prev_start, max(prev_end, curr_end))
                    else:
                        merged_segments.append(seg)

            # -------- PICK THE SINGLE LONGEST SEGMENT AT MAX INTERSECTION --------
            if merged_segments:
                longest_segment = max(merged_segments, key=lambda s: s[1] - s[0])
            else:
                # In edge cases where no intervals exist or no max segments,
                # fallback to a default single-point range
                longest_segment = (0, 0)

            maximum_overlapping_ranges[bs] = longest_segment

        return maximum_overlapping_ranges

    def spectrum_band_optimization(self, link_aggregate_instantaneous_bitrate, channel_matrices,
                                   optimum_point_strategy="middle"):
        optimal_point_name = []

        # Resetting the bandwidth
        for bs in self.environment.bss:
            # Equal spectrum assignment
            self.set_spectrum_bands_by_percentage(bs, uplink_percentage=50, downlink_percentage=50)

        stream_satisfiability_bandwidth_threshold = self.find_spectrum_satisfiability_bandwidth(
            link_aggregate_instantaneous_bitrate, self.calculate_links_bitrate(channel_matrices))

        # Find the maximum overlapping bandwidth ranges
        maximum_overlapping_ranges = self.maximum_overlapping_stream_satisfier_by_bandwidth(
            stream_satisfiability_bandwidth_threshold)

        # --------------- SET THE BS's SPECTRUM BAND ---------------
        for bs in self.environment.bss:
            if bs in maximum_overlapping_ranges:
                middle_point = (maximum_overlapping_ranges[bs][0] + maximum_overlapping_ranges[bs][1]) / 2.0
                self.set_spectrum_bands_by_downlink_bandwidth(bs, middle_point)

                if optimum_point_strategy == "min":
                    self.set_spectrum_bands_by_downlink_bandwidth(bs, maximum_overlapping_ranges[bs][0])

                if optimum_point_strategy == "random":
                    middle_point = random.uniform(maximum_overlapping_ranges[bs][0], maximum_overlapping_ranges[bs][1])
                    self.set_spectrum_bands_by_downlink_bandwidth(bs, middle_point)

                if optimum_point_strategy == "check_multiple":
                    satisfied_streams, bet_throughput_shortage = self.evaluate_objective_function(
                        link_aggregate_instantaneous_bitrate,
                        self.calculate_links_bitrate(channel_matrices))

                    candidates = [{"name": "min", "point": maximum_overlapping_ranges[bs][0], "result": 0},
                                  {"name": "q1", "point": (maximum_overlapping_ranges[bs][0] + middle_point) / 2,
                                   "result": 0},
                                  {"name": "middle", "point": middle_point, "result": bet_throughput_shortage},
                                  {"name": "q3", "point": (maximum_overlapping_ranges[bs][1] + middle_point) / 2,
                                   "result": 0},
                                  {"name": "max", "point": maximum_overlapping_ranges[bs][0], "result": 0}]

                    for point in candidates:
                        if point["name"] != "middle":
                            self.set_spectrum_bands_by_downlink_bandwidth(bs, point["point"])
                            throughput_shortage = 0
                            for link in self.environment.connection_manager.get_all_wireless_links():
                                throughput_shortage += self.calculate_bet_throughput_shortage(link,
                                                                                              link_aggregate_instantaneous_bitrate,
                                                                                              self.calculate_links_bitrate(
                                                                                                  channel_matrices),
                                                                                              satisfied_streams)
                            point["result"] = throughput_shortage

                    i = 0
                    # Select the point with the least throughput shortage
                    optimum_point = min(candidates, key=lambda x: x["result"])

                    optimal_point_name.append(optimum_point["name"])

                    # Set the spectrum band to the optimum point
                    self.set_spectrum_bands_by_downlink_bandwidth(bs, optimum_point["point"])

        bandwidth_split = {}
        for bs in self.environment.bss:
            bandwidth_split[bs] = {
                "downlink_bandwidth": bs.spectrum_manager.get_downlink_bandwidth(),
                "uplink_bandwidth": bs.spectrum_manager.get_uplink_bandwidth(),
            }

        bandwidth_satisfied_streams = self.find_satisfied_streams(link_aggregate_instantaneous_bitrate,
                                                                  self.calculate_links_bitrate(channel_matrices))

        return bandwidth_split, bandwidth_satisfied_streams

        #   ******************************************** Timing optimizer **********************************************

    def robust_spectrum_band_optimization(self, link_aggregate_instantaneous_bitrate, sinr_collector):
        optimal_point_name = []

        # Resetting the bandwidth
        for bs in self.environment.bss:
            # Equal spectrum assignment
            self.set_spectrum_bands_by_percentage(bs, uplink_percentage=50, downlink_percentage=50)

        stream_satisfiability_bandwidth_threshold = self.find_robust_spectrum_satisfiability_bandwidth(
            link_aggregate_instantaneous_bitrate, sinr_collector)

        # Find the maximum overlapping bandwidth ranges
        maximum_overlapping_ranges = self.maximum_overlapping_stream_satisfier_by_bandwidth(
            stream_satisfiability_bandwidth_threshold)

        # --------------- SET THE BS's SPECTRUM BAND ---------------
        for bs in self.environment.bss:
            if bs in maximum_overlapping_ranges:
                middle_point = (maximum_overlapping_ranges[bs][0] + maximum_overlapping_ranges[bs][1]) / 2.0
                self.set_spectrum_bands_by_downlink_bandwidth(bs, middle_point)

        bandwidth_split = {}
        for bs in self.environment.bss:
            bandwidth_split[bs] = {
                "downlink_bandwidth": bs.spectrum_manager.get_downlink_bandwidth(),
                "uplink_bandwidth": bs.spectrum_manager.get_uplink_bandwidth(),
            }

        bandwidth_satisfied_streams = self.find_robustly_satisfied_streams(link_aggregate_instantaneous_bitrate,
                                                                  sinr_collector)

        return bandwidth_split, bandwidth_satisfied_streams

        #   ******************************************** Timing optimizer **********************************************

    def calculate_frame_earliest_departure_time(self, start_time, payload_size, link_bitrate,
                                                link_instantaneous_demand):
        """
        Calculate the earliest time at which a frame of 'payload_size' bits can be completely transmitted,
        starting no earlier than 'start_time', given:
          - A link with total capacity of 'link_bitrate' bits per second,
          - A piecewise time series of the link's existing demand 'link_instantaneous_demand'.

        :param start_time: Earliest time we can start sending the frame (float).
        :param payload_size: Number of bits to send (int or float).
        :param link_bitrate: The raw maximum bits/second the link can carry if there is no other demand (float).
        :param link_instantaneous_demand: A list of (segment_start, segment_end, demand_bitrate) intervals (floats).
                                          Each interval means that, during [segment_start, segment_end),
                                          there's 'demand_bitrate' bps of other traffic on the link.
                                          The list is assumed to be sorted by segment_start.
        :return: The earliest time (float) that the frame is fully transmitted, or None if it cannot be
                 completed within the provided demand segments.
        """

        # We'll track how many bits remain to send.
        bits_left = payload_size

        # The "cursor" indicating how far we've progressed in time.
        current_time = start_time

        for (segment_start, segment_end, demand) in link_instantaneous_demand:
            # If this segment ends before our current_time, skip it.
            if segment_end <= current_time:
                continue

            # Determine the sub-interval we can use in this demand segment:
            # we can only start sending at max(current_time, segment_start).
            send_start = max(current_time, segment_start)
            send_end = segment_end  # We'll use as much as we can up to segment_end.

            if send_end <= send_start:
                # Zero or negative duration => no time to send in this segment
                continue

            # How much link capacity is actually left for this frame?
            # (If demand >= link_bitrate, there's no capacity left.)
            available_capacity = max(link_bitrate - demand, 0.0)  # bits/second

            if demand > link_bitrate:
                pass
                # raise ValueError("Demand is already more than link bitrate")

            if available_capacity <= 1e-12:
                # Effectively no capacity in this interval
                current_time = segment_end
                continue

            # Duration we can use in this interval
            duration = send_end - send_start  # seconds

            # How many bits can we push out in that duration at the available capacity?
            bits_can_send = available_capacity * duration

            if bits_can_send >= bits_left:
                # We can finish sending within this interval.
                # Figure out how long into this segment we need:
                time_needed = bits_left / available_capacity  # seconds
                departure_time = send_start + time_needed
                return departure_time
            else:
                # We'll only partially send the frame here.
                bits_left -= bits_can_send
                current_time = segment_end  # Move to the end of this segment and continue.

        # If we reach here, we never managed to send all bits_left using the intervals provided.
        # You might return None or float('inf'), depending on how you wish to handle "no solution."
        return None

    def edit_frame_schedule_to_satisfy(self, frame, path_links, satisfied_streams, links_bitrate,
                                       strategy="constant_wired_delay"):
        current_time = 0
        for link in path_links:
            if not link.future_queue.has_plan(frame):
                continue
            if current_time == 0:
                _, arrival_time, _ = link.future_queue.get_plan(frame)
                current_time = arrival_time
            if link.link_type == 'wired':
                if frame.creation_time + frame.delay_tolerance >= current_time + self.wired_link_constant_delay:
                    link.future_queue.edit_plan(frame, (current_time, current_time + self.wired_link_constant_delay))
                    current_time += self.wired_link_constant_delay
                else:
                    return False
            if link.link_type == 'wireless':
                link_aggregate_instantaneous_bitrate = link.future_queue.calculate_link_aggregate_instantaneous_bitrate(
                    self.current_time, self.current_time + self.channel_coherence_duration, self.channel_coherence_duration, self.channel_sensing_time,
                    self.wireless_propagation_delay, satisfied_streams)
                earliest_departure_time = self.calculate_frame_earliest_departure_time(current_time, frame.payload_size,
                                                                                       links_bitrate[link],
                                                                                       link_aggregate_instantaneous_bitrate)
                if earliest_departure_time is not None and frame.creation_time + frame.delay_tolerance >= earliest_departure_time + self.wireless_propagation_delay:
                    link.future_queue.edit_plan(frame, (current_time, earliest_departure_time))
                    current_time = earliest_departure_time + self.wireless_propagation_delay
                else:
                    return False
        return True

    def edit_frame_robust_schedule_to_satisfy(self, lcm_stream_period, frame, stream, path_links, satisfied_streams, sinr_collector):
        current_time = 0
        for link in path_links:
            if not link.future_queue.has_plan(frame):
                continue
            if current_time == 0:
                _, arrival_time, _ = link.future_queue.get_plan(frame)
                current_time = arrival_time
            if link.link_type == 'wired':
                if frame.creation_time + frame.delay_tolerance >= current_time + self.wired_link_constant_delay:
                    link.future_queue.edit_plan(frame, (current_time, current_time + self.wired_link_constant_delay))
                    current_time += self.wired_link_constant_delay
                else:
                    return False
            if link.link_type == 'wireless':
                link_aggregate_instantaneous_bitrate = link.future_queue.calculate_link_aggregate_instantaneous_bitrate(
                    0, lcm_stream_period, self.channel_coherence_duration, self.channel_sensing_time,
                    self.wireless_propagation_delay, satisfied_streams)
                ue, bs = self.environment.connection_manager.get_ue_and_bs(link)
                robust_link_sinr = sinr_collector.get_beamweight_scaled_robust_link_capacity(ue,
                                                                                             stream.reliability,
                                                                                             bs)
                robust_link_bitrate = link.bandwidth * np.log2(1.0 + robust_link_sinr)
                earliest_departure_time = self.calculate_frame_earliest_departure_time(current_time, frame.payload_size,
                                                                                       robust_link_bitrate,
                                                                                       link_aggregate_instantaneous_bitrate)
                if earliest_departure_time is not None and frame.creation_time + frame.delay_tolerance >= earliest_departure_time + self.wireless_propagation_delay:
                    link.future_queue.edit_plan(frame, (current_time, earliest_departure_time))
                    current_time = earliest_departure_time + self.wireless_propagation_delay
                else:
                    return False
        return True

    def find_unsatisfiable_frames(self, stream, path_links, satisfied_streams, links_bitrate):
        desired_streams = satisfied_streams.copy()
        desired_streams.append(stream)

        unsatisfiable_frames = set()
        for link in path_links:
            link_aggregate_instantaneous_bitrate = link.future_queue.calculate_stream_aggregate_instantaneous_bitrate(
                self.current_time, self.channel_coherence_duration, self.channel_sensing_time,
                self.wireless_propagation_delay, desired_streams)
            timeslots = []
            for elements in link_aggregate_instantaneous_bitrate:
                for slot in elements["time_series"]:
                    adjusted_start_time, adjusted_end_time, average_bitrate = slot
                    if average_bitrate > links_bitrate[link]:
                        timeslots.append((adjusted_start_time, adjusted_end_time))
            for timeslot in timeslots:
                unsatisfiable_frames.update(link.future_queue.get_active_frame(timeslot, stream))

        return unsatisfiable_frames

    def find_robustly_unsatisfiable_frames(self, lcm_stream_period, stream, path_links, satisfied_streams, sinr_collector):
        desired_streams = satisfied_streams.copy()
        desired_streams.append(stream)

        unsatisfiable_frames = set()
        for link in path_links:
            link_aggregate_instantaneous_bitrate = link.future_queue.calculate_stream_aggregate_instantaneous_bitrate(
                0, lcm_stream_period, self.channel_coherence_duration, self.channel_sensing_time,
                self.wireless_propagation_delay, desired_streams)
            timeslots = []
            for elements in link_aggregate_instantaneous_bitrate:
                for slot in elements["time_series"]:
                    adjusted_start_time, adjusted_end_time, average_bitrate = slot
                    ue, bs = self.environment.connection_manager.get_ue_and_bs(link)
                    robust_link_sinr = sinr_collector.get_beamweight_scaled_robust_link_capacity(ue, stream.reliability, bs)
                    robust_link_bitrate = link.bandwidth * np.log2(1.0 + robust_link_sinr)
                    if average_bitrate > robust_link_bitrate:
                        timeslots.append((adjusted_start_time, adjusted_end_time))
            for timeslot in timeslots:
                unsatisfiable_frames.update(link.future_queue.get_active_frame(timeslot, stream))

        return unsatisfiable_frames


    def timing_optimization(self, link_aggregate_instantaneous_bitrate, links_bitrate):
        # 1) Gather and sort unsatisfied streams
        sorted_unsatisfied_streams = self.find_sorted_unsatisfied_streams(
            link_aggregate_instantaneous_bitrate,
            links_bitrate
        )

        # Complete this
        satisfied_streams = [stream for stream in self.streams if stream not in sorted_unsatisfied_streams]

        # Find the unsatisfied frame for each stream
        for stream in sorted_unsatisfied_streams:
            satisfiable = True
            active_wireless_links = stream.get_active_wireless_links(self.environment, self.current_time,
                                                                     self.channel_coherence_duration,
                                                                     self.channel_sensing_time)
            unsatisfied_frames = self.find_unsatisfiable_frames(stream, active_wireless_links, satisfied_streams, links_bitrate)
            # Store the initial schedule of the stream here
            frame_plans_backup = {}
            for link in active_wireless_links:
                frame_plans_backup[link] = {}
                for frame in unsatisfied_frames:
                    if not link.future_queue.has_plan(frame):
                        continue
                    frame_plans_backup[link][frame] = link.future_queue.get_plan(frame)

            for frame in unsatisfied_frames:
                if not self.edit_frame_schedule_to_satisfy(frame, active_wireless_links, satisfied_streams, links_bitrate):
                    satisfiable = False
                    break
            if satisfiable:
                satisfied_streams.append(stream)
            else:
                # Revert the changes to the planning
                for link in active_wireless_links:
                    for frame in unsatisfied_frames:
                        if frame in frame_plans_backup[link]:
                            _, arrival_time, departure_time = frame_plans_backup[link][frame]
                            link.future_queue.edit_plan(frame, (arrival_time, departure_time))

        return satisfied_streams

        #   ********************************************************* BETS *****************************************************

    def robust_timing_optimization(self, lcm_stream_period, link_aggregate_instantaneous_bitrate, sinr_collector):
        # 1) Gather and sort unsatisfied streams
        sorted_unsatisfied_streams = self.find_robustly_sorted_unsatisfied_streams(
            link_aggregate_instantaneous_bitrate,
            sinr_collector
        )

        # Complete this
        satisfied_streams = [stream for stream in self.streams if stream not in sorted_unsatisfied_streams]

        # Find the unsatisfied frame for each stream
        for stream in sorted_unsatisfied_streams:
            satisfiable = True
            active_wireless_links = stream.get_active_wireless_links(self.environment, self.current_time,
                                                                     self.channel_coherence_duration,
                                                                     self.channel_sensing_time)
            unsatisfied_frames = self.find_robustly_unsatisfiable_frames(lcm_stream_period, stream, active_wireless_links, satisfied_streams, sinr_collector)
            # Store the initial schedule of the stream here
            frame_plans_backup = {}
            for link in active_wireless_links:
                frame_plans_backup[link] = {}
                for frame in unsatisfied_frames:
                    if not link.future_queue.has_plan(frame):
                        continue
                    frame_plans_backup[link][frame] = link.future_queue.get_plan(frame)

            for frame in unsatisfied_frames:
                if not self.edit_frame_robust_schedule_to_satisfy(lcm_stream_period, frame, stream, active_wireless_links, satisfied_streams, sinr_collector):
                    satisfiable = False
                    break
            if satisfiable:
                satisfied_streams.append(stream)
            else:
                # Revert the changes to the planning
                for link in active_wireless_links:
                    for frame in unsatisfied_frames:
                        if frame in frame_plans_backup[link]:
                            _, arrival_time, departure_time = frame_plans_backup[link][frame]
                            link.future_queue.edit_plan(frame, (arrival_time, departure_time))

        return satisfied_streams

        #   ********************************************************* BETS *****************************************************


    @time_it_cpu
    def execute_BETS_single_interval(self, channel_matrices, coherence_interval):
        reports = []
        print("Executing BETS_three_step")

        initial_link_bitrates = self.calculate_links_bitrate(channel_matrices)

        # Scheduled streams for timeslot
        self.scheduler.schedule_until(
            self.current_time + self.channel_coherence_duration,
            coherence_interval,
            self.channel_sensing_time
        )

        # Calculate the instantaneous bitrate for each link
        link_aggregate_instantaneous_bitrate = {}
        for link in self.environment.connection_manager.get_all_wireless_links():
            stream_link_max_bitrate = link.future_queue.calculate_stream_link_max_bitrate(
                self.current_time,
                self.channel_coherence_duration,
                self.channel_sensing_time,
                self.wireless_propagation_delay,
            )
            link_aggregate_instantaneous_bitrate[link] = stream_link_max_bitrate

        # Evaluating initial objective function
        satisfied_streams = self.find_satisfied_streams(
            link_aggregate_instantaneous_bitrate,
            initial_link_bitrates
        )

        beamweights, bandwidth_split = self.get_current_status()

        reports.append({
            "iteration": 0,
            "phase": "init",
            "beamweights": beamweights,
            "bandwidth_split": bandwidth_split,
            "TST": [s.name for s in satisfied_streams]
        })

        iteration_number = 0
        while True:
            iteration_number += 1
            previous_satisfied_streams = satisfied_streams

            # Running beamweight optimization
            beamweights, satisfied_streams = self.beamweight_optimization(
                link_aggregate_instantaneous_bitrate,
                channel_matrices
            )
            reports.append({
                "iteration": iteration_number,
                "phase": "post-beamweight",
                "TST": [s.name for s in satisfied_streams]
            })


            # Running spectrum band optimization
            bandwidth_split, satisfied_streams = self.spectrum_band_optimization(
                link_aggregate_instantaneous_bitrate,
                channel_matrices
            )
            reports.append({
                "iteration": iteration_number,
                "phase": "post-bandwidth",
                "TST": [s.name for s in satisfied_streams]
            })


            # Running timing optimization
            satisfied_streams = self.timing_optimization(
                link_aggregate_instantaneous_bitrate,
                self.calculate_links_bitrate(channel_matrices)
            )
            reports.append({
                "iteration": iteration_number,
                "phase": "post-timing",
                "TST": [s.name for s in satisfied_streams]
            })


            if len(satisfied_streams) <= len(previous_satisfied_streams):
                return satisfied_streams, beamweights, bandwidth_split, reports


    def robust_stream_admission(self, sinr_collector, lcm_stream_period, coherence_interval):
        admitted_streams = []

        # Initialize the decision variables
        for bs in self.environment.bss:
            self.set_spectrum_bands_by_percentage(bs, uplink_percentage=50, downlink_percentage=50)
            ue_list = self.environment.connection_manager.get_connected_ues(bs)
            if len(ue_list) > 0:
                self.set_beamweight_by_bs(bs, ue_list, [1 / len(ue_list)] * len(ue_list))
            else:
                bs.beamweight_manager.clear_all()

        # Scheduled streams for timeslot
        self.scheduler.schedule_until(
            lcm_stream_period,
            coherence_interval,
            self.channel_sensing_time
        )


        # Calculate the instantaneous bitrate for each link
        link_aggregate_instantaneous_bitrate = {}
        for link in self.environment.connection_manager.get_all_wireless_links():
            stream_link_max_bitrate = link.future_queue.calculate_stream_link_max_bitrate(
                self.current_time,
                self.current_time + lcm_stream_period,
                self.channel_coherence_duration,
                self.channel_sensing_time,
                self.wireless_propagation_delay,
            )
            link_aggregate_instantaneous_bitrate[link] = stream_link_max_bitrate

        # Evaluating initial objective function
        satisfied_streams = self.find_robustly_satisfied_streams(
            link_aggregate_instantaneous_bitrate,
            sinr_collector
        )

        print({
            "iteration": 0,
            "phase": "init",
            "count": len(satisfied_streams)
        })

        iteration_number = 0
        while True:
            iteration_number += 1
            previous_satisfied_streams = satisfied_streams

            # Running beamweight optimization
            beamweights, satisfied_streams = self.robust_beamweight_optimization(
                link_aggregate_instantaneous_bitrate,
                sinr_collector
            )

            print({
                "iteration": iteration_number,
                "phase": "post-beamweight",
                "count": len(satisfied_streams)
            })

            # Running spectrum band optimization
            bandwidth_split, satisfied_streams = self.robust_spectrum_band_optimization(
                link_aggregate_instantaneous_bitrate,
                sinr_collector
            )
            print({
                "iteration": iteration_number,
                "phase": "post-bandwidth",
                "count": len(satisfied_streams)
            })

            # Running timing optimization
            satisfied_streams = self.robust_timing_optimization(
                lcm_stream_period,
                link_aggregate_instantaneous_bitrate,
                sinr_collector
            )
            print({
                "iteration": iteration_number,
                "phase": "post-timing",
                "count": len(satisfied_streams)
            })

            if len(satisfied_streams) <= len(previous_satisfied_streams):
                return satisfied_streams


    def run_BETS(self, channel_matrices):
        # Initialize the decision variables
        for bs in self.environment.bss:
            self.set_spectrum_bands_by_percentage(bs, uplink_percentage=50, downlink_percentage=50)
            ue_list = self.environment.connection_manager.get_connected_ues(bs)
            if len(ue_list) > 0:
                self.set_beamweight_by_bs(bs, ue_list, [1 / len(ue_list)] * len(ue_list))
            else:
                bs.beamweight_manager.clear_all()

        # 1) Clear old FutureQueue plans (optional).
        # TODO ensure that this behavior is what you want in the stream serving phase
        for link in self.environment.connection_manager.links:
            link.future_queue.prune_queue_before_coherence_interval(self.current_time, self.channel_sensing_time)
            link.future_queue.prune_by_active_streams(self.streams)


        coherence_interval_results, time_taken, cpu_time_taken = self.execute_BETS_single_interval(channel_matrices)
        satisfied_streams, beamweights, bandwidth_split, reports = coherence_interval_results

        # --- Store results ---
        result = {
            "beamweights": beamweights,
            "bandwidth_split": bandwidth_split,
            "satisfied_streams": satisfied_streams,
            "start_time": self.current_time,
            "end_time": self.current_time + self.channel_coherence_duration,
            "time_taken": time_taken,
            "cpu_time_taken": cpu_time_taken
        }
        self.current_time += self.channel_coherence_duration

        return result
