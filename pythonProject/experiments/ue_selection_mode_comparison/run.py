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
    UEAssignmentAlgorithm, SubcoherenceTimeAllocation, UESelectionAlgorithm


def prepare_and_run_simulations(base_dir, mode):
    random_seeds = [65138, 395312, 49702, 461537, 422912, 261942, 580533, 363150, 402538, 696981]
    utility_functions = [UESelectionUtilityFunction.BITRATE_MAXIMIZATION, UESelectionUtilityFunction.PF_MAXIMIZATION,
                         UESelectionUtilityFunction.QUEUE_LENGTH_MINIMIZATION,
                         UESelectionUtilityFunction.QUEUE_AWARE_PF_MAXIMIZATION]

    for utility in utility_functions:
        for seed in random_seeds:
            random.seed(seed)
            np.random.seed(seed)
            policy = Policy(operation_mode=mode, utility_function=utility, ue_selection_algorithm=UESelectionAlgorithm.ADAPTIVE_TOP_K,
                            frame_injection_rate=1)
            (simulation_name, history, time_taken_array), time_taken = run_simulation(seed, 40000, 20, 4, 5,
                                                                                      2, 2, policy=policy,
                                                                                      show_environment=False,
                                                                                      store_environment=False)

            time_taken_array.insert(0, time_taken)
            time_taken_array = [round(time, 3) for time in time_taken_array]
            save_dictionary({"time": time_taken_array, "history": history}, simulation_name)
            gc.collect()
    for seed in random_seeds:
        random.seed(seed)
        np.random.seed(seed)
        policy = Policy(operation_mode=mode, ue_selection_algorithm=UESelectionAlgorithm.SERVING_ALL,
                        frame_injection_rate=1)
        (simulation_name, history, time_taken_array), time_taken = run_simulation(seed, 40000, 20, 4, 5,
                                                                                  2, 2, policy=policy,
                                                                                  show_environment=False,
                                                                                  store_environment=False)

        time_taken_array.insert(0, time_taken)
        time_taken_array = [round(time, 3) for time in time_taken_array]
        save_dictionary({"time": time_taken_array, "history": history}, simulation_name)
        gc.collect()

# Main execution
if __name__ == "__main__":
    random_seed = 11490
    random.seed(random_seed)
    np.random.seed(random_seed)

    output_dir = "output/"

    base_hybrid = output_dir + "hybrid"
    base_digital = output_dir + "digital"

    prepare_and_run_simulations(base_hybrid, OperationMode.NON_COOPERATIVE_HYBRID)
    prepare_and_run_simulations(base_digital, OperationMode.NON_COOPERATIVE_FULLY_DIGITAL)
