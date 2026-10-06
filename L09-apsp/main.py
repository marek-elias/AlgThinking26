"""Starter scaffold for the all pairs shortest paths"""

import random
import networkx as nx
import matplotlib
from pathlib import Path


TASK_DIR = Path(__file__).resolve().parent
DATA_DIR = TASK_DIR / "data"
RESULTS_DIR = TASK_DIR / "results"
DATA_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    """Run the all pairs shortest path experiment once it is implemented."""
    pass

if __name__ == "__main__":
    main()
