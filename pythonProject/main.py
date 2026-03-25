import random
import numpy as np

from pythonProject.bets_enabler.bets_enabler import BETSEnabler
from pythonProject.environment.antenna_array import URPA
from pythonProject.environment.physical_environment import PhysicalEnvironment
from pythonProject.helper_functions import compute_lcm_of_streams_and_coherence
from pythonProject.sinr_data_collector import SINRDataCollector
from pythonProject.traffic.tst_stream import Stream


# =========================
# Configuration & Constants
# =========================

# Constants
BS_COUNT = 4
BS_ROW = 2
BS_COLUMN = 2
UE_COUNT = 32
AIR_PROPAGATION_DELAY = 0.01
WIRED_LINK_CONSTANT_DELAY = 0.04
TOTAL_BANDWIDTH = 5000 # because latency is in ms this is Kb and should be multiplied to 1000 also if
                        # the payload is in bytes instead of bits this also should be multiplied to 8
GUARD_BAND = 50

COHERENCE_INTERVAL_DURATION_MS = 10
SEED = 100

NUM_COHERENCE_INTERVALS = 25_000
STREAM_COUNT = 150


random.seed(SEED)
np.random.seed(SEED)


# =========================
# Setup helpers
# =========================

def setup_environment() -> PhysicalEnvironment:
    environment = PhysicalEnvironment()

    environment.evenly_spread_switches_over_the_ceiling(1, 0.3, 1, 1)
    environment.evenly_spread_bs_over_the_ceiling(BS_COUNT, 0.3, BS_ROW, BS_COLUMN,
                                                  TOTAL_BANDWIDTH, GUARD_BAND)
    environment.connect_bss_to_switch()

    environment.randomly_spread_ue_over_ue_plane(UE_COUNT, 1)
    environment.connect_ues_to_closest_bs()

    return environment


def generate_streams(environment: PhysicalEnvironment, stream_count: int):
    streams = []

    for j in range(stream_count):
        source, destination = random.sample(environment.ues, 2)
        periodic_cycle = random.choice([1, 2, 3, 4, 5, 6, 8, 12, 15, 20])

        streams.append(
            Stream(
                name=f"Stream_{j}",
                periodic_cycle=periodic_cycle,
                frame_payload=random.randint(2000, 5000),
                latency_tolerance=periodic_cycle,
                jitter_tolerance=0.1 * random.randint(1, 3),
                reliability=random.randint(90, 99),
                source=source,
                destination=destination,
                start_time=random.randint(0, 10),
            )
        )

    return streams


def setup_bets_enabler(environment, streams):
    return BETSEnabler(
        environment=environment,
        streams=streams,
        bet_generator=None,
        channel_coherence_duration=COHERENCE_INTERVAL_DURATION_MS,
        channel_sensing_time=0.1,
        wireless_propagation_delay=AIR_PROPAGATION_DELAY,
        wired_link_constant_delay=WIRED_LINK_CONSTANT_DELAY,
    )


def admit_streams(enabler, environment, streams):
    sinr_collector = SINRDataCollector(environment)
    sinr_collector.load_data("./sinr_data_100_(10)_new_mobility.json")

    lcm_hyperperiod = compute_lcm_of_streams_and_coherence(
        streams,
        COHERENCE_INTERVAL_DURATION_MS,
    )

    admitted_streams = enabler.robust_stream_admission(
        sinr_collector,
        lcm_hyperperiod,
        COHERENCE_INTERVAL_DURATION_MS
    )

    enabler.set_streams(admitted_streams)


# =========================
# Main simulation loop
# =========================

def main():
    environment = setup_environment()
    streams = generate_streams(environment, STREAM_COUNT)
    enabler = setup_bets_enabler(environment, streams)

    admit_streams(enabler, environment, streams)

    results = []

    for i in range(NUM_COHERENCE_INTERVALS):
        if i % int(100 / COHERENCE_INTERVAL_DURATION_MS) == 0:
            environment.generate_path_clusters_matrix()

        environment.move_ues(COHERENCE_INTERVAL_DURATION_MS / 1000)
        environment.short_term_fading_effect_on_path_clusters()

        channel_matrices = environment.generate_channel_matrices(URPA)
        result = enabler.run_BETS(channel_matrices)

        results.append(result)
        print(f"Finished {i}th channel realizations.")

    # Evaluation intentionally unchanged / not implemented


if __name__ == "__main__":
    main()
