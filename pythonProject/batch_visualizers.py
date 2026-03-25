import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import matplotlib.pyplot as plt

from pythonProject.visualizers import visualize_satisfied_streams_per_coherence_interval


def _load_runs_by_seed(json_path: Path) -> Dict[int, List[dict]]:
    """
    Load a JSON file whose top-level is a list of objects:
      { "seed": <int>, "results": [ {...}, {...}, ... ] }
    Returns a dict: seed -> results_list
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    runs = {}
    for entry in data:
        seed = entry.get("seed")
        results = entry.get("results", [])
        if seed is None:
            continue
        runs[seed] = results
    return runs

def _coerce_to_path(p) -> Path:
    """Allow file path with or without .json extension."""
    p = Path(p)
    if p.suffix.lower() != ".json":
        alt = p.with_suffix(".json")
        if alt.exists():
            return alt
    return p

def visualize_all_seeds_stacked(
    file_50,
    file_100,
    file_150,
    *,
    save_dir: Optional[str] = "plots_per_seed",
    show: bool = True,
    dpi: int = 300,
    figsize=(9, 8),
    suptitle_fmt: str = "Seed {seed} — Satisfied Streams per Coherence Interval",
):
    """
    Create one figure per seed with three stacked subplots:
    (top) 50 streams, (middle) 100 streams, (bottom) 150 streams.

    Parameters
    ----------
    file_50, file_100, file_150 : str | Path
        Paths to the three JSON result files (with or without the .json suffix).
    save_dir : str | None
        If provided, save one PNG per seed to this directory.
    show : bool
        Whether to display the figures via plt.show() at the end.
    dpi : int
        DPI for saved figures.
    figsize : tuple
        Figure size in inches.
    suptitle_fmt : str
        Suptitle format string; will receive 'seed' via str.format().

    Returns
    -------
    figures : Dict[int, plt.Figure]
        Mapping seed -> created matplotlib Figure.
    """
    # Make paths resilient to missing ".json" suffix
    file_50 = _coerce_to_path(file_50)
    file_100 = _coerce_to_path(file_100)
    file_150 = _coerce_to_path(file_150)

    # Load data, grouped by seed
    runs_50 = _load_runs_by_seed(file_50)
    runs_100 = _load_runs_by_seed(file_100)
    runs_150 = _load_runs_by_seed(file_150)

    # Union of all seeds across files
    all_seeds = sorted(set(runs_50) | set(runs_100) | set(runs_150))

    if save_dir is not None:
        Path(save_dir).mkdir(parents=True, exist_ok=True)

    figures = {}

    for seed in all_seeds:
        # Prepare figure with 3 rows, shared x if possible
        fig, axes = plt.subplots(
            nrows=3, ncols=1, figsize=figsize, sharex=True, constrained_layout=True
        )

        # For consistent ordering top->bottom
        panels = [
            ("50 streams", runs_50.get(seed)),
            ("100 streams", runs_100.get(seed)),
            ("150 streams", runs_150.get(seed)),
        ]

        for ax, (label, results) in zip(axes, panels):
            if results is None or len(results) == 0:
                # No data for this seed/file: draw an empty panel with a note
                ax.set_title(f"{label} — no data for seed {seed}")
                ax.set_xlabel("Coherence Interval Index")
                ax.set_ylabel("# Satisfied Streams")
                ax.grid(True, linestyle="--", alpha=0.5)
                continue

            # Use your existing single-seed visualizer for each panel
            visualize_satisfied_streams_per_coherence_interval(
                results,
                ax=ax,
                title=label,
                show=False,
                save_path=None,
            )

        fig.suptitle(suptitle_fmt.format(seed=seed))
        figures[seed] = fig

        if save_dir is not None:
            out_name = f"seed_{seed}_50_100_150.png"
            out_path = os.path.join(save_dir, out_name)
            fig.savefig(out_path, dpi=dpi, bbox_inches="tight")

    if show:
        plt.show()

    return figures


# Assuming your helper exists in scope:
# def visualize_satisfied_streams_per_coherence_interval(...): ...

figs = visualize_all_seeds_stacked(
    "output/bets_multiple_real_csi_50.json",   # or "bets_multiple_50.json"
    "output/bets_multiple_real_csi_100.json",
    "output/bets_multiple_real_csi_150.json",
    save_dir="output",  # change or set to None to skip saving
    show=False
)
