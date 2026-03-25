# Add the main module
import sys
from pathlib import Path

base_directory = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(base_directory))

import gc
import os
import random

import numpy as np

from pythonProject.executions import run_simulation
from pythonProject.helper_functions import save_dictionary
from pythonProject.ue_selection.policies import UESelectionUtilityFunction, Policy, OperationMode, \
    UEAssignmentAlgorithm, SubcoherenceTimeAllocation


def prepare_and_run_simulations(base_dir, mode):
    random_seeds = [654321, 987654, 192837, 564738, 102938, 746281, 374829, 192837, 473829, 384756]
    sub_allocation = [SubcoherenceTimeAllocation.FIXED_SIZE_SPECULATIVE, SubcoherenceTimeAllocation.NONE]
    rates = [0.3, 0.7, 1.7, 3]
    rfc_count = [2, 8, 16, 32]
    bs_count = [(2, 2, 1), (8, 4, 2), (16, 4, 4), (32, 8, 4)]

    for sub_allocation in sub_allocation:
        for rate in rates:
            for seed in random_seeds:
                random.seed(seed)
                np.random.seed(seed)
                policy = Policy(operation_mode=mode, subcoherence_time_allocation=sub_allocation,
                                frame_injection_rate=rate)
                (simulation_name, history, time_taken_array), time_taken = run_simulation(seed, 10000, 20, 4, 5,
                                                                                          2, 2, policy=policy,
                                                                                          show_environment=False,
                                                                                          store_environment=False)

                time_taken_array.insert(0, time_taken)
                time_taken_array = [round(time, 3) for time in time_taken_array]
                save_dictionary({"time": time_taken_array, "history": history}, f'({rate})' + simulation_name)
                gc.collect()
        for count in rfc_count:
            for seed in random_seeds:
                random.seed(seed)
                np.random.seed(seed)
                policy = Policy(operation_mode=mode, subcoherence_time_allocation=sub_allocation)
                (simulation_name, history, time_taken_array), time_taken = run_simulation(seed, 10000, 4 * count, 4,
                                                                                          count,
                                                                                          2, 2, policy=policy,
                                                                                          show_environment=False,

                                                                                          store_environment=False)

                time_taken_array.insert(0, time_taken)
                time_taken_array = [round(time, 3) for time in time_taken_array]
                save_dictionary({"time": time_taken_array, "history": history}, simulation_name)
                gc.collect()
        for count in bs_count:
            for seed in random_seeds:
                random.seed(seed)
                np.random.seed(seed)
                policy = Policy(operation_mode=mode, subcoherence_time_allocation=sub_allocation)
                (simulation_name, history, time_taken_array), time_taken = run_simulation(seed, 10000, 5 * count[0],
                                                                                          count[0], 5,
                                                                                          count[1], count[2],
                                                                                          policy=policy,
                                                                                          show_environment=False,
                                                                                          store_environment=False)

                time_taken_array.insert(0, time_taken)
                time_taken_array = [round(time, 3) for time in time_taken_array]
                save_dictionary({"time": time_taken_array, "history": history}, simulation_name)
                gc.collect()


# Main execution
if __name__ == "__main__":
    prepare_and_run_simulations('', OperationMode.NON_COOPERATIVE_HYBRID)
    # prepare_and_run_simulations('', OperationMode.NON_COOPERATIVE_FULLY_DIGITAL)
