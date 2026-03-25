# Add the main module
import sys
from pathlib import Path

base_directory = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(base_directory))

import gc
import random

import numpy as np

from pythonProject.executions import run_simulation
from pythonProject.helper_functions import save_dictionary
from pythonProject.ue_selection.policies import UESelectionUtilityFunction, Policy, OperationMode, \
    UEAssignmentAlgorithm, SubcoherenceTimeAllocation


def prepare_and_run_simulations(base_dir, mode):
    random_seeds = [65138, 395312, 49702, 461537, 422912, 261942, 580533, 363150, 402538, 696981]
    utility_functions = [UESelectionUtilityFunction.BITRATE_MAXIMIZATION, UESelectionUtilityFunction.PF_MAXIMIZATION,
                         UESelectionUtilityFunction.QUEUE_LENGTH_MINIMIZATION,
                         UESelectionUtilityFunction.QUEUE_AWARE_PF_MAXIMIZATION]
    rfc_count = [2, 8, 16, 32]

    for count in rfc_count:
        for utility in utility_functions:
            for seed in random_seeds:
                random.seed(seed)
                np.random.seed(seed)
                policy = Policy(operation_mode=mode, utility_function=utility)
                (simulation_name, history, time_taken_array), time_taken = run_simulation(seed, 20000, 4*count, 4, count,
                                                                                          2, 2, policy=policy,
                                                                                          show_environment=False,
                                                                                          store_environment=False)

                time_taken_array.insert(0, time_taken)
                time_taken_array = [round(time, 3) for time in time_taken_array]
                save_dictionary({"time": time_taken_array, "history": history}, simulation_name)
                gc.collect()


# Main execution
if __name__ == "__main__":
    prepare_and_run_simulations('', OperationMode.NON_COOPERATIVE_HYBRID)
    prepare_and_run_simulations('', OperationMode.NON_COOPERATIVE_FULLY_DIGITAL)
