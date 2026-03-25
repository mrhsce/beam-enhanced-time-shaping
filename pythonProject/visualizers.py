import pandas as pd

import matplotlib.pyplot as plt
import numpy as np


def visualize_satisfied_streams_per_coherence_interval(all_results, *, ax=None, title="Satisfied Streams throughout the time horizon",
                                show=True, save_path=None):
    """
    Plot the number of satisfied streams for each coherence interval.

    Parameters
    ----------
    all_results : list[dict]
        Output of run_BETS_multiple(). Each dict should contain:
        - "index": int
        - "satisfied_streams": list (or any iterable) of streams for that interval
    ax : matplotlib.axes.Axes | None
        Existing axes to draw on. If None, a new figure and axes are created.
    title : str
        Plot title.
    show : bool
        Whether to call plt.show() at the end (ignored if ax is provided and caller manages display).
    save_path : str | None
        If provided, saves the figure to this path.

    Returns
    -------
    (fig, ax) : tuple
        The matplotlib Figure and Axes used for the plot.
    """
    if not all_results:
        raise ValueError("all_results is empty; nothing to plot.")

    # Extract x (indices) and y (# satisfied streams)
    x = []
    y = []
    for rec in all_results:
        idx = rec.get("index")
        sats = rec.get("satisfied_streams", [])
        if idx is None:
            # Fallback to enumerating if 'index' is missing
            idx = len(x)
        x.append(idx)
        y.append(sats)

    # Sort by index to ensure monotonic x-axis if needed
    sort_order = sorted(range(len(x)), key=lambda i: x[i])
    x = [x[i] for i in sort_order]
    y = [y[i] for i in sort_order]

    created_fig = False
    if ax is None:
        fig, ax = plt.subplots(figsize=(7, 4))
        created_fig = True
    else:
        fig = ax.figure

    ax.plot(x, y, marker="o", linewidth=1.5)
    ax.set_title(title)
    ax.set_xlabel("Coherence Interval Index")
    ax.set_ylabel("# Satisfied Streams")
    ax.grid(True, linestyle="--", alpha=0.5)

    if save_path is not None:
        fig.savefig(save_path, bbox_inches="tight", dpi=150)

    if created_fig and show:
        plt.show()

    return fig, ax

def visualize_combined_improvement_and_runtime(results, title, include_runtime=False):
    """
    Creates a combined figure with two grouped bar charts:
    - Top row: Average Improvement (%)
    - Bottom row: Average Process Runtime (s) [optional]
    Grouped by stream count, bars grouped by scenario (in reversed order).
    """

    # =================== Customizable Parameters ===================
    font_title = 16
    font_label = 15
    font_ticks = 15
    font_legend = 15
    font_legend_title = 15
    font_bar_values = 10
    bar_value_offset_ratio = 10
    ci_line_width = 1.2
    ci_cap_thickness = 1.2
    ci_cap_size = 15
    # ===============================================================

    scenario_name_map = {
        "two_step_regular": "Two-Step",
        "two_step_plus_regular": "Two-Step-Plus",
        "three_step_regular": "Three-Step",
        "equal_allocation":"Equal allocation",
        "inverse_proportional_equal_to_highest_assignment": "Inverse proportional allocation",
        "no_allocation_assignment": "No allocation",
        "proportional_equal_to_lowest_assignment": "Proportional allocation",

        'uniform_src-dest': "Uniform",
        'inter-BS_src-dest': "Inter-BS",
        'intra-BS_src-dest': "Intra-BS",
        'common_source(1)_src-dest': "1 Common Source",
        'common_source(3)_src-dest': "3 Common Sources",
        'common_destination(1)_src-dest': "1 Common Destination",
        'common_destination(3)_src-dest': "3 Common Destinations",
    }

    scenario_order = [
        "no_allocation_assignment",
        "proportional_equal_to_lowest_assignment",
        "inverse_proportional_equal_to_highest_assignment",
        "equal_allocation",
        "two_step_regular",
        "two_step_plus_regular",
        "three_step_regular",

        'uniform_src-dest',
        'inter-BS_src-dest',
        'intra-BS_src-dest',
        'common_source(3)_src-dest',
        'common_source(1)_src-dest',
        'common_destination(3)_src-dest',
        'common_destination(1)_src-dest'
    ]

    stream_data = {}
    ci_improvement_data = {}
    ci_runtime_data = {}
    all_scenarios = set()

    for stream_count, entries in results.items():
        stream_data[stream_count] = {}
        ci_improvement_data[stream_count] = {}
        ci_runtime_data[stream_count] = {}
        for entry in entries:
            scenario = entry["scenario"]
            all_scenarios.add(scenario)
            stream_data[stream_count][scenario] = {
                "improvement": entry.get("Average Improvement", 0),
                "runtime": entry.get("Average Process Runtime", 0)
            }
            ci_improvement_data[stream_count][scenario] = entry.get("CI Improvement", 0)
            ci_runtime_data[stream_count][scenario] = entry.get("CI Process Runtime", 0)

    stream_counts = sorted(results.keys(), key=lambda x: int(x))
    scenarios = [s for s in scenario_order if s in all_scenarios]
    x = np.arange(len(stream_counts))
    bar_width = 0.8 / len(scenarios)

    # Choose subplot layout depending on whether to include runtime
    if include_runtime:
        fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, sharex=True, figsize=(12, 10), height_ratios=[1, 1])
    else:
        fig, ax1 = plt.subplots(nrows=1, ncols=1, figsize=(12, 8))
        ax2 = None  # Placeholder

    # Define unique hatches for each scenario
    hatch_patterns = ['/', '\\', '|', '-', '+', 'x', 'o', 'O', '.', '*']
    scenario_hatches = {scenario: hatch_patterns[i % len(hatch_patterns)] for i, scenario in enumerate(scenarios)}

    def plot_bars(ax, metric_key, ci_data_dict, ylabel, show_values=True):
        for i, scenario in enumerate(scenarios):
            offset = (i - (len(scenarios) - 1) / 2) * bar_width
            heights = [stream_data[sc].get(scenario, {}).get(metric_key, 0) for sc in stream_counts]
            errors = [ci_data_dict[sc].get(scenario, 0) for sc in stream_counts]

            label_name = scenario_name_map.get(scenario, scenario)

            bars = ax.bar(
                x + offset,
                heights,
                bar_width,
                label=label_name,
                # yerr=errors,
                hatch=scenario_hatches[scenario],  # ADD THIS LINE
                # color='white',  # Ensure colors don’t interfere in B/W
                # edgecolor='black',  # Black borders for clarity
                capsize=ci_cap_size,
                error_kw=dict(elinewidth=ci_line_width, capthick=ci_cap_thickness)
            )

            if show_values:
                for bar, value in zip(bars, heights):
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + bar_value_offset_ratio,
                        f"{int(value)}",
                        ha='center',
                        va='top',
                        fontsize=font_bar_values,
                        color='black'
                    )

        ax.set_ylabel(ylabel, fontsize=font_label)
        ax.grid(axis='y')
        ax.tick_params(axis='both', labelsize=font_ticks)

    # Plot improvement
    plot_bars(ax1, "improvement", ci_improvement_data, "Average Improvement (%)")
    ax1.legend(title="Scenario", fontsize=font_legend, title_fontsize=font_legend_title)

    # Plot runtime if included
    if include_runtime and ax2:
        plot_bars(ax2, "runtime", ci_runtime_data, "Average Runtime (s)")
        ax2.set_xlabel("Stream Count", fontsize=font_label)
        ax2.set_xticks(x)
        ax2.set_xticklabels(stream_counts, fontsize=font_ticks)
    else:
        ax1.set_xlabel("Stream Count", fontsize=font_label)
        ax1.set_xticks(x)
        ax1.set_xticklabels(stream_counts, fontsize=font_ticks)

    plt.tight_layout()
    if include_runtime:
        plt.subplots_adjust(hspace=0.05)
    plt.savefig(title + "_combined.png", dpi=300)
    plt.close()


def visualize_improvement(results, title):
    """
    Creates a grouped bar chart with 95% confidence intervals for average improvement,
    grouping by stream count instead of scenario.
    """
    # Reorganize the data: outer key is stream count
    stream_data = {}
    ci_data = {}
    all_scenarios = set()

    for stream_count, entries in results.items():
        stream_data[stream_count] = {}
        ci_data[stream_count] = {}
        for entry in entries:
            scenario = entry["scenario"]
            improvement = entry.get("Average Improvement", 0)
            ci = entry.get("CI Improvement", 0)
            stream_data[stream_count][scenario] = improvement
            ci_data[stream_count][scenario] = ci
            all_scenarios.add(scenario)

    stream_counts = sorted(results.keys(), key=lambda x: int(x))
    scenarios = sorted(all_scenarios)

    # Build data for each scenario across stream counts
    avg_data = {
        sc: [stream_data[sc].get(scenario, 0) for scenario in scenarios]
        for sc in stream_counts
    }
    ci_error_data = {
        sc: [ci_data[sc].get(scenario, 0) for scenario in scenarios]
        for sc in stream_counts
    }

    x = np.arange(len(stream_counts))  # positions for stream count groups
    bar_width = 0.8 / len(scenarios)

    fig, ax = plt.subplots(figsize=(10, 6))

    for i, scenario in enumerate(scenarios):
        offset = (i - (len(scenarios) - 1) / 2) * bar_width
        heights = [avg_data[sc][i] for sc in stream_counts]
        errors = [ci_error_data[sc][i] for sc in stream_counts]

        ax.bar(x + offset, heights, width=bar_width, label=scenario, yerr=errors, capsize=5)

    ax.set_xlabel("Stream Count")
    ax.set_ylabel("Average Improvement (%)")
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(stream_counts)
    ax.legend(title="Scenario", fontsize=8)
    ax.grid(axis='y')

    plt.tight_layout()
    plt.savefig(title + "_by_stream.png", dpi=300)
    plt.close()

def visualize_process_runtime_bar_chart(
    grouped_results,
    title="Average Process Runtime per Stream Count",
    filename="average_process_runtime.png"
):
    """
    Creates a grouped bar chart of average process runtime per stream count,
    grouped by scenario (subject), with 95% confidence intervals as error bars.
    """
    stream_counts = sorted(grouped_results.keys(), key=lambda x: int(x))
    scenarios = sorted({entry.get("scenario", "unknown") for entries in grouped_results.values() for entry in entries})

    avg_data = []
    ci_data = []

    for scenario in scenarios:
        avg_row = []
        ci_row = []
        for stream_count in stream_counts:
            entries = grouped_results.get(stream_count, [])
            for entry in entries:
                if entry.get("scenario") == scenario:
                    avg_runtime = entry.get("Average Process Runtime", 0)
                    ci = entry.get("CI Process Runtime", 0)
                    break
            else:
                avg_runtime = 0
                ci = 0
            avg_row.append(avg_runtime)
            ci_row.append(ci)
        avg_data.append(avg_row)
        ci_data.append(ci_row)

    x = np.arange(len(stream_counts))
    width = 0.8 / len(scenarios)

    plt.figure(figsize=(12, 6))
    for i, (scenario, avg_row, ci_row) in enumerate(zip(scenarios, avg_data, ci_data)):
        plt.bar(x + i * width, avg_row, width, label=scenario, yerr=ci_row, capsize=5)

    plt.xlabel("Stream Count")
    plt.ylabel("Average Process Runtime (s)")
    plt.title(title)
    plt.xticks(x + width * (len(scenarios) - 1) / 2, stream_counts)
    plt.legend(title="Scenario")
    plt.grid(axis="y")
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()


def visualize_optimal_points(results):
    """
    Function to visualize the frequency of different optimal points as a bar chart.

    Args:
    - results (list of dicts): The results generated from run_BETS function.
    """
    # Extract relevant data
    optimal_points_data = [entry for entry in results if "optimal_points_name" in entry]

    # Check if there are any results to visualize
    if not optimal_points_data:
        print("No optimal points data found in results.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(optimal_points_data)

    # Explode the list of optimal point names
    df_exploded = df.explode("optimal_points_name")

    # Count the frequency of each optimal point name
    optimal_point_counts = df_exploded["optimal_points_name"].value_counts()

    # Plot the bar chart
    plt.figure(figsize=(8, 5))
    optimal_point_counts.plot(kind="bar", color="c", alpha=0.7)
    plt.xlabel("Optimal Point Name")
    plt.ylabel("Frequency")
    plt.title("Frequency of Optimal Points")
    plt.xticks(rotation=45)
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    # Show the plot
    plt.show()


def report_improvement(aggregated_results):
    """
    Prints the improvement in satisfied streams for each seed by comparing the initial phase
    with the maximum satisfied streams achieved in all iterations and calculates the improvement percentage.
    Also calculates the average improvement percentage, average initial satisfied streams,
    average final satisfied streams, and average iteration count across all seeds.

    Args:
    - aggregated_results (list of dicts): The aggregated results from multiple seed runs.
    """
    improvement_percentages = []
    initial_satisfied_list = []
    max_satisfied_list = []
    iteration_counts = []

    for result in aggregated_results:
        seed = result["seed"]
        results = result["results"]

        if not results:
            print(f"Seed {seed}: No results found.")
            continue

        # Extract initial satisfied streams
        initial_phase = next((entry for entry in results if entry["phase"] == "init"), None)
        if not initial_phase:
            print(f"Seed {seed}: No initial phase found.")
            continue

        initial_satisfied = len(initial_phase["TST"]) if isinstance(initial_phase["TST"], list) else initial_phase["TST"]
        initial_satisfied_list.append(initial_satisfied)

        # Extract the maximum satisfied streams achieved in any iteration
        max_satisfied = max(
            len(entry["TST"]) if isinstance(entry["TST"], list) else entry["TST"]
            for entry in results
        )
        max_satisfied_list.append(max_satisfied)

        # Count total iterations
        iteration_count = max(entry["iteration"] for entry in results)
        iteration_counts.append(iteration_count)

        # Calculate improvement percentage
        improvement_percentage = ((max_satisfied - initial_satisfied) / initial_satisfied) * 100 if initial_satisfied > 0 else 0
        improvement_percentages.append(improvement_percentage)

        # Print the comparison
        print(f"Seed {seed}: {initial_satisfied} -> {max_satisfied}, Iterations: {iteration_count}, Improvement: {improvement_percentage:.2f}%")

    # Calculate and print the averages
    avg_improvement = sum(improvement_percentages) / len(improvement_percentages) if improvement_percentages else 0
    avg_initial_satisfied = sum(initial_satisfied_list) / len(initial_satisfied_list) if initial_satisfied_list else 0
    avg_max_satisfied = sum(max_satisfied_list) / len(max_satisfied_list) if max_satisfied_list else 0
    avg_iteration_count = sum(iteration_counts) / len(iteration_counts) if iteration_counts else 0

    print("\nOverall Averages:")
    print(f"Average Initial Satisfied Streams: {avg_initial_satisfied:.2f}")
    print(f"Average Final Satisfied Streams: {avg_max_satisfied:.2f}")
    print(f"Average Improvement: {avg_improvement:.2f}%")
    print(f"Average Iteration Count: {avg_iteration_count:.2f}")




def visualize_increased_satisfiability(results, title):
    """
    Given a results dictionary of the form:
    {
      "100": [
        { "Average Initial Satisfied Streams": ..., "Average Final Satisfied Streams": ..., "scenario": "scenario_name", ... },
         ...
      ],
      "150": [ ... ],
      "50": [ ... ]
    }

    This function creates a grouped bar chart where:
      - The x-axis represents scenario names.
      - For each scenario, a group of bars is drawn for each stream count (50, 100, 150).
      - The y-axis represents the increase in the number of satisfied streams,
        computed as (Average Final Satisfied Streams - Average Initial Satisfied Streams).
    """
    # Aggregate the data by scenario.
    # Map each scenario to a dictionary {stream_count: increase in satisfied streams}
    scenario_data = {}
    for stream_count, entries in results.items():
        for entry in entries:
            scenario = entry["scenario"]
            initial = entry["Average Initial Satisfied Streams"]
            final = entry["Average Final Satisfied Streams"]
            increase = final - initial  # Increase in the number of satisfied streams
            if scenario not in scenario_data:
                scenario_data[scenario] = {}
            scenario_data[scenario][stream_count] = increase

    # Get a sorted list of scenario names.
    scenarios = list(scenario_data.keys())
    # Get a sorted list of stream counts (as strings), sorted numerically.
    stream_counts = sorted(results.keys(), key=lambda x: int(x))

    # Build the data for each scenario for each stream count.
    # If a scenario doesn't have a value for a given stream count, default to 0.
    data = {
        scenario: [scenario_data[scenario].get(sc, 0) for sc in stream_counts]
        for scenario in scenarios
    }

    # Set up the bar chart.
    x = np.arange(len(scenarios))  # positions for each scenario group on the x-axis
    bar_width = 0.2
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot each stream count as a set of bars.
    for i, sc in enumerate(stream_counts):
        # Calculate horizontal offset for each stream count's bars.
        offset = (i - (len(stream_counts) - 1) / 2) * bar_width
        increases = [data[scenario][i] for scenario in scenarios]
        ax.bar(x + offset, increases, width=bar_width, label=f"Stream Count {sc}")

    # Formatting the chart.
    ax.set_xlabel("Scenario")
    ax.set_ylabel("Increase in Satisfied Streams")
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios, fontsize=7)
    ax.legend(title="Stream Count")

    plt.tight_layout()
    plt.savefig(title + ".png", dpi=300)

def visualize_iteration_count(results, title):
    """
    Given a results dictionary of the form:
    {
      "100": [
        { "Average Iteration Count": ..., "scenario": "scenario_name", ... },
         ...
      ],
      "150": [ ... ],
      "50": [ ... ]
    }

    This function creates a grouped bar chart where:
      - The x-axis represents scenario names.
      - For each scenario, a group of bars is drawn for each stream count (50, 100, 150).
      - The y-axis represents the average iteration count.
    """
    # Aggregate data by scenario.
    # Create a dictionary mapping scenario name -> {stream_count: average iteration count}
    scenario_data = {}
    for stream_count, entries in results.items():
        for entry in entries:
            scenario = entry["scenario"]
            iteration_count = entry["Average Iteration Count"]
            if scenario not in scenario_data:
                scenario_data[scenario] = {}
            scenario_data[scenario][stream_count] = iteration_count

    # Get the list of scenarios and sorted stream counts.
    scenarios = list(scenario_data.keys())
    stream_counts = sorted(results.keys(), key=lambda x: int(x))

    # Build the data for each scenario for each stream count.
    # If a scenario doesn't have a value for a given stream count, default to 0.
    data = {
        scenario: [scenario_data[scenario].get(sc, 0) for sc in stream_counts]
        for scenario in scenarios
    }

    # Set up the bar chart.
    x = np.arange(len(scenarios))  # positions for each scenario on the x-axis
    bar_width = 0.2
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot each stream count as a set of bars.
    for i, sc in enumerate(stream_counts):
        offset = (i - (len(stream_counts) - 1) / 2) * bar_width
        iteration_counts = [data[scenario][i] for scenario in scenarios]
        ax.bar(x + offset, iteration_counts, width=bar_width, label=f"Stream Count {sc}")

    # Formatting the chart.
    ax.set_xlabel("Scenario")
    ax.set_ylabel("Average Iteration Count")
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios, fontsize=7)
    ax.legend(title="Stream Count")

    plt.tight_layout()
    plt.savefig(title + ".png", dpi=300)
