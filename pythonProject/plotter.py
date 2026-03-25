import os
import re
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

from helper_functions import load_dictionary, save_dictionary
from visualizers import visualize_process_runtime_bar_chart, visualize_combined_improvement_and_runtime, visualize_increased_satisfiability, visualize_iteration_count


def compute_confidence_interval(data, confidence=0.95):
    if not data or len(data) < 2:
        return 0.0
    array = np.array(data)
    sem = stats.sem(array)
    h = sem * stats.t.ppf((1 + confidence) / 2., len(array)-1)
    return round(h, 2)


def compute_overall_averages(aggregated_results):
    improvement_percentages = []
    initial_satisfied_list = []
    max_satisfied_list = []
    iteration_counts = []
    runtimes = []
    process_runtimes = []

    for result in aggregated_results:
        results_list = result.get("results", [])
        runtime = result.get("runtime")
        process_runtime = result.get("process_runtime")

        if runtime is not None:
            runtimes.append(runtime)
        if process_runtime is not None:
            process_runtimes.append(process_runtime)

        if not results_list:
            continue

        initial_phase = next((entry for entry in results_list if entry.get("phase") == "init"), None)
        if not initial_phase:
            continue

        TST_value = initial_phase.get("TST")
        initial_satisfied = len(TST_value) if isinstance(TST_value, list) else TST_value
        initial_satisfied_list.append(initial_satisfied)

        max_satisfied = max(
            len(entry.get("TST", 0)) if isinstance(entry.get("TST", 0), list) else entry.get("TST", 0)
            for entry in results_list
        )
        max_satisfied_list.append(max_satisfied)

        iteration_count = max(entry.get("iteration", 0) for entry in results_list)
        iteration_counts.append(iteration_count)

        improvement_percentage = ((max_satisfied - initial_satisfied) / initial_satisfied) * 100 if initial_satisfied > 0 else 0
        improvement_percentages.append(improvement_percentage)

    def mean_and_ci(data, round_digits=2):
        avg = round(np.mean(data), round_digits) if data else 0
        ci = compute_confidence_interval(data)
        return avg, ci

    avg_initial, ci_initial = mean_and_ci(initial_satisfied_list)
    avg_final, ci_final = mean_and_ci(max_satisfied_list)
    avg_improvement, ci_improvement = mean_and_ci(improvement_percentages)
    avg_iterations, ci_iterations = mean_and_ci(iteration_counts)
    avg_runtime, ci_runtime = mean_and_ci(runtimes, round_digits=3)
    avg_process_runtime, ci_process_runtime = mean_and_ci(process_runtimes, round_digits=3)

    return {
        "Average Initial Satisfied Streams": avg_initial,
        "CI Initial Satisfied Streams": ci_initial,
        "Average Final Satisfied Streams": avg_final,
        "CI Final Satisfied Streams": ci_final,
        "Average Improvement": avg_improvement,
        "CI Improvement": ci_improvement,
        "Average Iteration Count": avg_iterations,
        "CI Iteration Count": ci_iterations,
        "Average Runtime": avg_runtime,
        "CI Runtime": ci_runtime,
        "Average Process Runtime": avg_process_runtime,
        "CI Process Runtime": ci_process_runtime
    }


def group_results_by_stream_count(results):
    groups = {}
    pattern = re.compile(r'^(.*)_(\d+)_\(')

    for entry in results:
        filename = entry.get("filename", "")
        match = pattern.search(filename)
        if match:
            scenario = match.group(1)
            stream_count = match.group(2)
            new_entry = entry.copy()
            new_entry["scenario"] = scenario
            new_entry.pop("filename", None)
            groups.setdefault(stream_count, []).append(new_entry)
        else:
            print(f"Could not parse filename: {filename}")
    return groups


def aggregate_directory_results(directory):
    overall_results = []
    for filename in os.listdir(directory):
        if filename.endswith('.json') and filename != "results.json":
            filepath = os.path.join(directory, filename)
            try:
                aggregated_results = load_dictionary(filepath)
            except Exception as e:
                print(f"Error reading {filename}: {e}")
                continue

            averages = compute_overall_averages(aggregated_results)
            averages["filename"] = filename
            overall_results.append(averages)
    return overall_results




# Example usage
if __name__ == "__main__":
    experiment = 8
    address = ["output/structural/rest_beamweight", "output/structural/step_count", "output/structural/step_order",
               "output/scalability/BS_count", "output/scalability/UE_count", "output/scalability/stream_count",
               "output/stream_type/src_dest", "output/stream_type/other_params_2/similar", "output/stream_type/other_params_2/uniform"]
    titles = [" by beamweight", " by step_count", " by step order", "by BS count", "by UE count",
              "by stream count", "by stream src_dest", "by stream similar parameters", "by stream uniform parameters"]

    results = group_results_by_stream_count(aggregate_directory_results(address[experiment]))
    save_dictionary(results, file_name="results", output_directory=address[experiment])

    visualize_combined_improvement_and_runtime(load_dictionary(address[experiment] + "/results.json"), "Performance and Runtime Comparison Across Algorithm Variants at Different Stream Counts")
    # visualize_increased_satisfiability(load_dictionary(address[experiment] + "/results.json"), "Increase in satisfiability" + titles[experiment])
    # visualize_iteration_count(load_dictionary(address[experiment] + "/results.json"), "Iteration count" + titles[experiment])
    visualize_process_runtime_bar_chart(
        load_dictionary(address[experiment] + "/results.json"),
        "Process Runtime" + titles[experiment],
        filename="process_runtime" + titles[experiment].replace(" ", "_") + ".png"
    )