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
    UEAssignmentAlgorithm


def prepare_and_run_simulations(base_dir, mode):
    random_seeds = [65138, 395312, 49702, 461537, 422912, 261942, 580533, 363150, 402538, 696981]
    ue_assignment_algorithms = [UEAssignmentAlgorithm.CHANNEL_BASED_STABLE_MARRIAGE_STATIC]
    prefix = ["STA"]
    rfc_count = [2, 4, 8, 16, 32]
    bs_count = [(2, 2, 1), (4, 2, 2), (8, 4, 2), (16, 4, 4), (32, 8, 4)]
    for i, algorithm in enumerate(ue_assignment_algorithms):
        for count in rfc_count:
            for seed in random_seeds:
                random.seed(seed)
                np.random.seed(seed)
                policy = Policy(operation_mode=mode, ue_assignment_algorithm=algorithm)
                (simulation_name, history, time_taken_array), time_taken = run_simulation(seed, 20000, 4 * count, 4,
                                                                                          count,
                                                                                          2, 2, policy=policy,
                                                                                          show_environment=False,
                                                                                          store_environment=False)

                time_taken_array.insert(0, time_taken)
                time_taken_array = [round(time, 3) for time in time_taken_array]
                save_dictionary({"time": time_taken_array, "history": history}, prefix[i] + "-" +simulation_name)
                gc.collect()
        for count in bs_count:
            for seed in random_seeds:
                random.seed(seed)
                np.random.seed(seed)
                policy = Policy(operation_mode=mode, ue_assignment_algorithm=algorithm)
                (simulation_name, history, time_taken_array), time_taken = run_simulation(seed, 20000, 5 * count[0],
                                                                                          count[0], 5,
                                                                                          count[1], count[2],
                                                                                          policy=policy,
                                                                                          show_environment=False,
                                                                                          store_environment=False)

                time_taken_array.insert(0, time_taken)
                time_taken_array = [round(time, 3) for time in time_taken_array]
                save_dictionary({"time": time_taken_array, "history": history}, prefix[i] + "-" + simulation_name)
                gc.collect()


# Main execution
if __name__ == "__main__":
    prepare_and_run_simulations("", OperationMode.NON_COOPERATIVE_HYBRID)
    prepare_and_run_simulations("", OperationMode.NON_COOPERATIVE_FULLY_DIGITAL)
