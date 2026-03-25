import os
import re
import matplotlib.pyplot as plt
import numpy as np

from helper_functions import load_dictionary, save_dictionary
from visualizers import visualize_improvement, visualize_increased_satisfiability, visualize_iteration_count

group_count = 2

def compute_overall_averages(aggregated_results):
    improvement_percentages = []
    iteration_counts = []
    runtimes = []
    process_runtimes = []

    easy_counts = []
    medium_counts = []
    hard_counts = []

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

        # Find best result with most satisfied streams
        best_entry = max(
            results_list,
            key=lambda entry: len(entry.get("TST", [])) if isinstance(entry.get("TST", []), list) else 0
        )

        best_TST = best_entry.get("TST", [])
        if not isinstance(best_TST, list):
            continue

        # Count by group
        easy = sum(1 for s in best_TST if s.startswith("Easy"))
        medium = sum(1 for s in best_TST if s.startswith("Moderate"))
        hard = sum(1 for s in best_TST if s.startswith("Hard"))

        easy_counts.append(easy)
        medium_counts.append(medium)
        hard_counts.append(hard)

        # Initial TST for improvement calculation
        initial_phase = next((entry for entry in results_list if entry.get("phase") == "init"), None)
        if initial_phase:
            initial_TST = initial_phase.get("TST", [])
            initial_count = len(initial_TST) if isinstance(initial_TST, list) else 0
            improvement = ((len(best_TST) - initial_count) / initial_count) * 100 if initial_count > 0 else 0
            improvement_percentages.append(improvement)

        iteration_count = max(entry.get("iteration", 0) for entry in results_list)
        iteration_counts.append(iteration_count)

    avg_improvement = sum(improvement_percentages) / len(improvement_percentages) if improvement_percentages else 0
    avg_iterations = sum(iteration_counts) / len(iteration_counts) if iteration_counts else 0
    avg_runtime = sum(runtimes) / len(runtimes) if runtimes else 0
    avg_process_runtime = sum(process_runtimes) / len(process_runtimes) if process_runtimes else 0

    avg_easy = sum(easy_counts) / len(easy_counts) if easy_counts else 0
    avg_medium = sum(medium_counts) / len(medium_counts) if medium_counts else 0
    avg_hard = sum(hard_counts) / len(hard_counts) if hard_counts else 0

    return {
        "Average Easy Satisfied": round(avg_easy, 2),
        "Average Moderate Satisfied": round(avg_medium, 2),
        "Average Hard Satisfied": round(avg_hard, 2),
        "Average Improvement": round(avg_improvement, 2),
        "Average Iteration Count": round(avg_iterations, 2),
        "Average Runtime": round(avg_runtime, 3),
        "Average Process Runtime": round(avg_process_runtime, 3),
        # "Easy Counts": easy_counts,
        # "Medium Counts": medium_counts,
        # "Hard Counts": hard_counts
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

def visualize_process_runtime_bar_chart(grouped_results, title="Average Process Runtime per Stream Count", filename="average_process_runtime.png"):
    """
    Creates a grouped bar chart of average process runtime per stream count,
    grouped by scenario (subject), and saves it using a title-based filename.
    """
    stream_counts = sorted(grouped_results.keys(), key=lambda x: int(x))
    scenarios = set()

    for entries in grouped_results.values():
        for entry in entries:
            scenarios.add(entry.get("scenario", "unknown"))
    scenarios = sorted(list(scenarios))

    data = []
    for scenario in scenarios:
        row = []
        for stream_count in stream_counts:
            entries = grouped_results.get(stream_count, [])
            runtimes = [entry.get("Average Process Runtime", 0) for entry in entries if entry.get("scenario") == scenario]
            avg_runtime = sum(runtimes) / len(runtimes) if runtimes else 0
            row.append(avg_runtime)
        data.append(row)

    x = np.arange(len(stream_counts))
    width = 0.8 / len(scenarios)

    plt.figure(figsize=(12, 6))
    for i, (scenario, runtime_row) in enumerate(zip(scenarios, data)):
        plt.bar(x + i * width, runtime_row, width, label=scenario)

    plt.xlabel("Stream Count")
    plt.ylabel("Average Process Runtime (s)")
    plt.title(title)
    plt.xticks(x + width * (len(scenarios) - 1) / 2, stream_counts)
    plt.legend(title="Scenario")
    plt.grid(axis="y")
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

# Example usage
if __name__ == "__main__":
    experiment = 1
    address = ["output/stream_type/other_params_2/two_groups", "output/stream_type/other_params_2/three_groups"]
    titles = ["by stream two groups", "by stream three groups"]

    results = group_results_by_stream_count(aggregate_directory_results(address[experiment]))
    save_dictionary(results, file_name="results", output_directory=address[experiment])

    visualize_improvement(load_dictionary(address[experiment] + "/results.json"), "Improvement" + titles[experiment])
    visualize_increased_satisfiability(load_dictionary(address[experiment] + "/results.json"), "Increase in satisfiability" + titles[experiment])
    visualize_iteration_count(load_dictionary(address[experiment] + "/results.json"), "Iteration count" + titles[experiment])
    visualize_process_runtime_bar_chart(
        load_dictionary(address[experiment] + "/results.json"),
        "Process Runtime" + titles[experiment],
        filename="process_runtime" + titles[experiment].replace(" ", "_") + ".png"
    )
