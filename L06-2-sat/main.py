"""Estimate a graph's minimum cut with Karger's randomized algorithm."""

import csv
import math
import random
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection


STUDENT_NICKNAME = "Jarek"

TASK_DIR = Path(__file__).resolve().parent
DATA_DIR = TASK_DIR / "data"
RESULTS_DIR = TASK_DIR / "results"
DATA_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Experiment settings for a graph with a sparse planted cut between two dense
# halves. Vertices 0--99 form A and vertices 100--199 form B.
NUMBER_OF_VERTICES = 200
INTERNAL_EDGE_PROBABILITY = 0.50
NUMBER_OF_CROSS_EDGES = 20
TARGET_FAILURE_PROBABILITY = 0.01
GRAPH_SEED = 20260922
TRIAL_SEED = 20260923

Edge = tuple[int, int]


def generate_partitioned_graph(
    number_of_vertices: int,
    internal_edge_probability: float,
    number_of_cross_edges: int,
    rng: random.Random,
) -> list[Edge]:
    """Generate two dense equal parts joined by a few random edges."""
    if number_of_vertices < 4 or number_of_vertices % 2 != 0:
        raise ValueError("The graph must have an even number of at least 4 vertices.")
    if not 0.0 <= internal_edge_probability <= 1.0:
        raise ValueError("The edge probability must be between 0 and 1.")

    part_size = number_of_vertices // 2
    possible_cross_edges = part_size * part_size
    if not 1 <= number_of_cross_edges <= min(50, possible_cross_edges):
        raise ValueError("The number of cross edges must be between 1 and 50.")

    edges: list[Edge] = []
    for part_start in (0, part_size):
        part_end = part_start + part_size
        for first in range(part_start, part_end):
            for second in range(first + 1, part_end):
                if rng.random() < internal_edge_probability:
                    edges.append((first, second))

    cross_edge_candidates = [
        (first, second)
        for first in range(part_size)
        for second in range(part_size, number_of_vertices)
    ]
    edges.extend(rng.sample(cross_edge_candidates, number_of_cross_edges))
    return sorted(edges)


def build_adjacency_masks(
    number_of_vertices: int, graph_edges: list[Edge]
) -> list[int]:
    """Represent each vertex's neighbors as a bit mask for fast cut counting."""
    adjacency_masks = [0] * number_of_vertices
    for first, second in graph_edges:
        adjacency_masks[first] |= 1 << second
        adjacency_masks[second] |= 1 << first
    return adjacency_masks


def karger_trial(
    number_of_vertices: int,
    graph_edges: list[Edge],
    adjacency_masks: list[int],
    rng: random.Random,
) -> int:
    """Run one Karger contraction trial and return the resulting cut size.

    Disjoint-set components represent supervertices. Sampling an original
    edge and rejecting it when both endpoints are already in one component is
    equivalent to removing self-loops while retaining all parallel edges.
    """
    parents = list(range(number_of_vertices))
    component_sizes = [1] * number_of_vertices
    number_of_components = number_of_vertices
    number_of_edges = len(graph_edges)

    def find(vertex: int) -> int:
        while parents[vertex] != vertex:
            parents[vertex] = parents[parents[vertex]]
            vertex = parents[vertex]
        return vertex

    while number_of_components > 2:
        first, second = graph_edges[rng.randrange(number_of_edges)]
        first_root = find(first)
        second_root = find(second)
        if first_root == second_root:  # This edge is currently a self-loop.
            continue

        if component_sizes[first_root] < component_sizes[second_root]:
            first_root, second_root = second_root, first_root
        parents[second_root] = first_root
        component_sizes[first_root] += component_sizes[second_root]
        number_of_components -= 1

    # Build one final supervertex as a bit mask, then count its edges to the
    # other supervertex using fast integer bit operations.
    first_root = find(0)
    first_side = 0
    for vertex in range(number_of_vertices):
        if find(vertex) == first_root:
            first_side |= 1 << vertex
    all_vertices = (1 << number_of_vertices) - 1
    second_side = all_vertices ^ first_side
    if first_side.bit_count() > second_side.bit_count():
        first_side, second_side = second_side, first_side

    cut_size = 0
    while first_side:
        vertex_bit = first_side & -first_side
        vertex = vertex_bit.bit_length() - 1
        cut_size += (adjacency_masks[vertex] & second_side).bit_count()
        first_side ^= vertex_bit
    return cut_size


def required_number_of_trials(
    number_of_vertices: int, target_failure_probability: float
) -> int:
    """Return trials needed to make Karger's failure bound at most the target."""
    if not 0.0 < target_failure_probability < 1.0:
        raise ValueError("The target failure probability must be between 0 and 1.")

    # One Karger trial finds a particular minimum cut with probability at
    # least 2 / (n * (n - 1)).
    success_lower_bound = 2.0 / (
        number_of_vertices * (number_of_vertices - 1)
    )
    return math.ceil(
        math.log(target_failure_probability)
        / math.log1p(-success_lower_bound)
    )


def save_graph(graph_edges: list[Edge]) -> Path:
    """Save the generated graph so the exact experiment input is reusable."""
    graph_path = DATA_DIR / "graph_edges.csv"
    with graph_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(["vertex_1", "vertex_2"])
        writer.writerows(graph_edges)
    return graph_path


def save_graph_plot(number_of_vertices: int, graph_edges: list[Edge]) -> Path:
    """Draw the two dense parts and highlight their sparse connecting edges."""
    part_size = number_of_vertices // 2
    positions: dict[int, tuple[float, float]] = {}
    for part_index, part_start in enumerate((0, part_size)):
        center_x = -1.15 if part_index == 0 else 1.15
        for offset in range(part_size):
            angle = math.pi / 2 - 2 * math.pi * offset / part_size
            positions[part_start + offset] = (
                center_x + 0.88 * math.cos(angle),
                0.88 * math.sin(angle),
            )

    part_a_segments = []
    part_b_segments = []
    cross_segments = []
    for first, second in graph_edges:
        segment = [positions[first], positions[second]]
        if first < part_size and second < part_size:
            part_a_segments.append(segment)
        elif first >= part_size and second >= part_size:
            part_b_segments.append(segment)
        else:
            cross_segments.append(segment)

    figure, axis = plt.subplots(figsize=(12, 6.5))
    axis.add_collection(
        LineCollection(part_a_segments, colors="#4472C4", linewidths=0.35, alpha=0.08)
    )
    axis.add_collection(
        LineCollection(part_b_segments, colors="#E17C3A", linewidths=0.35, alpha=0.08)
    )
    axis.add_collection(
        LineCollection(cross_segments, colors="#C44E52", linewidths=1.5, alpha=0.8)
    )

    for part_start, color, label in (
        (0, "#4472C4", "Part A"),
        (part_size, "#E17C3A", "Part B"),
    ):
        vertices = range(part_start, part_start + part_size)
        axis.scatter(
            [positions[vertex][0] for vertex in vertices],
            [positions[vertex][1] for vertex in vertices],
            s=18,
            color=color,
            edgecolor="white",
            linewidth=0.25,
            zorder=2,
            label=label,
        )

    axis.plot([], [], color="#C44E52", linewidth=1.5, label="Cross edge")
    axis.text(-1.15, 1.08, "A (100 vertices)", ha="center", fontsize=12, weight="bold")
    axis.text(1.15, 1.08, "B (100 vertices)", ha="center", fontsize=12, weight="bold")
    axis.set_title(
        f"Planted-partition graph: {number_of_vertices} vertices, "
        f"{len(graph_edges)} edges, {NUMBER_OF_CROSS_EDGES} cross edges",
        fontsize=15,
        pad=18,
    )
    axis.legend(loc="lower center", ncols=3, frameon=True)
    axis.set_aspect("equal")
    axis.set_xlim(-2.2, 2.2)
    axis.set_ylim(-1.12, 1.22)
    axis.axis("off")
    figure.tight_layout()

    plot_path = RESULTS_DIR / f"{STUDENT_NICKNAME}_graph.png"
    figure.savefig(plot_path, dpi=180, bbox_inches="tight")
    plt.close(figure)
    return plot_path


def save_trial_results(cut_sizes: list[int]) -> Path:
    """Save every observed cut size in a text-based CSV result."""
    trial_path = RESULTS_DIR / f"{STUDENT_NICKNAME}_trial_cuts.csv"
    with trial_path.open("w", newline="", encoding="utf-8") as output_file:
        output_file.write(f"Student nickname: {STUDENT_NICKNAME}\n")
        writer = csv.writer(output_file)
        writer.writerow(["trial", "cut_size"])
        writer.writerows(enumerate(cut_sizes, start=1))
    return trial_path


def save_distribution_plot(cut_sizes: list[int]) -> Path:
    """Plot the empirical frequency and cumulative distribution of cut sizes."""
    frequencies = Counter(cut_sizes)
    cut_values = sorted(frequencies)
    cumulative_probabilities: list[float] = []
    running_total = 0
    for cut_value in cut_values:
        running_total += frequencies[cut_value]
        cumulative_probabilities.append(running_total / len(cut_sizes))

    figure, (frequency_axis, cumulative_axis) = plt.subplots(
        1, 2, figsize=(12, 4.8)
    )

    frequency_axis.hist(
        cut_sizes, bins=40, color="#4472C4", edgecolor="white", linewidth=0.4
    )
    frequency_axis.axvline(
        min(cut_sizes), color="#C44E52", linestyle="--", label="Smallest cut found"
    )
    frequency_axis.set_title("Distribution of cuts from Karger trials")
    frequency_axis.set_xlabel("Cut size")
    frequency_axis.set_ylabel("Number of trials")
    frequency_axis.grid(axis="y", alpha=0.25)
    frequency_axis.legend()

    cumulative_axis.step(
        cut_values,
        cumulative_probabilities,
        where="post",
        color="#C44E52",
        linewidth=2,
    )
    cumulative_axis.scatter(cut_values, cumulative_probabilities, color="#C44E52")
    cumulative_axis.set_title("Empirical cumulative distribution")
    cumulative_axis.set_xlabel("Cut size")
    cumulative_axis.set_ylabel("Proportion with this cut or smaller")
    cumulative_axis.set_ylim(0.0, 1.05)
    cumulative_axis.grid(alpha=0.25)

    figure.suptitle(
        f"Karger's randomized minimum-cut experiment ({len(cut_sizes)} trials)"
    )
    figure.tight_layout()

    plot_path = RESULTS_DIR / f"{STUDENT_NICKNAME}_cut_distribution.png"
    figure.savefig(plot_path, dpi=160, bbox_inches="tight")
    plt.close(figure)
    return plot_path


def save_summary(
    graph_edges: list[Edge], cut_sizes: list[int], number_of_trials: int
) -> Path:
    """Save a short human-readable summary of the experiment."""
    frequencies = Counter(cut_sizes)
    best_cut = min(cut_sizes)
    summary_path = RESULTS_DIR / f"{STUDENT_NICKNAME}_results.txt"
    summary_path.write_text(
        f"Student nickname: {STUDENT_NICKNAME}\n"
        "Karger's randomized minimum-cut experiment\n"
        f"Vertices: {NUMBER_OF_VERTICES}\n"
        f"Vertices in each part: {NUMBER_OF_VERTICES // 2}\n"
        f"Within-part edge probability: {INTERNAL_EDGE_PROBABILITY}\n"
        f"Planted cut size (cross edges): {NUMBER_OF_CROSS_EDGES}\n"
        f"Original edges: {len(graph_edges)}\n"
        f"Target upper bound on failure probability: "
        f"{TARGET_FAILURE_PROBABILITY:.2%}\n"
        f"Trials: {number_of_trials}\n"
        f"Smallest cut found: {best_cut}\n"
        f"Trials finding the smallest observed cut: {frequencies[best_cut]}\n"
        f"Observed cut frequencies: {dict(sorted(frequencies.items()))}\n",
        encoding="utf-8",
    )
    return summary_path


def main() -> None:
    """Generate a graph, run enough Karger trials, and save the results."""
    graph_rng = random.Random(GRAPH_SEED)
    graph_edges = generate_partitioned_graph(
        NUMBER_OF_VERTICES,
        INTERNAL_EDGE_PROBABILITY,
        NUMBER_OF_CROSS_EDGES,
        graph_rng,
    )
    adjacency_masks = build_adjacency_masks(NUMBER_OF_VERTICES, graph_edges)
    graph_path = save_graph(graph_edges)
    graph_plot_path = save_graph_plot(NUMBER_OF_VERTICES, graph_edges)

    number_of_trials = required_number_of_trials(
        NUMBER_OF_VERTICES, TARGET_FAILURE_PROBABILITY
    )
    trial_rng = random.Random(TRIAL_SEED)
    cut_sizes = [
        karger_trial(NUMBER_OF_VERTICES, graph_edges, adjacency_masks, trial_rng)
        for _ in range(number_of_trials)
    ]

    trial_path = save_trial_results(cut_sizes)
    plot_path = save_distribution_plot(cut_sizes)
    summary_path = save_summary(graph_edges, cut_sizes, number_of_trials)

    print(f"Graph data: {graph_path}")
    print(f"Graph plot: {graph_plot_path}")
    print(f"Trial data: {trial_path}")
    print(f"Distribution plot: {plot_path}")
    print(f"Summary: {summary_path}")
    print(f"Smallest cut found: {min(cut_sizes)}")


if __name__ == "__main__":
    main()
