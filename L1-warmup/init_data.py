"""Create reusable input arrays for the warmup timing experiment."""

import ast
from collections.abc import Iterable
from pathlib import Path
from pprint import pformat
from random import randint
from re import fullmatch


TASK_DIR = Path(__file__).resolve().parent
DATA_DIR = TASK_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

N = 1000
K = [5, 10, 50, 100, 500, 1000]


def validate_array_parameters(n: int, k: int) -> None:
    """Check that the requested random array parameters are valid."""

    if not isinstance(n, int):
        raise TypeError("n must be an integer")
    if not isinstance(k, int):
        raise TypeError("k must be an integer")
    if n < 0:
        raise ValueError("n must be non-negative")
    if k < 0:
        raise ValueError("k must be non-negative")


def data_module_path(student_nickname: str) -> Path:
    """Return the Python data module path for this student's arrays."""

    if fullmatch(r"[A-Za-z0-9_-]{1,30}", student_nickname) is None:
        raise ValueError(
            "student_nickname must contain 1-30 letters, numbers, "
            "underscores, or hyphens"
        )

    return DATA_DIR / f"arrays_{student_nickname}.py"


def array_variable_name(k: int) -> str:
    """Return the importable variable name used for the array with bound k."""

    return f"Arr_{k}"


def initialize_random_array(n: int, k: int, student_nickname: str) -> list[int]:
    """Generate an array and save it in an importable Python data module."""

    return initialize_all_arrays(n, [k], student_nickname)[k]


def initialize_all_arrays(
    n: int,
    k_values: Iterable[int],
    student_nickname: str,
) -> dict[int, list[int]]:
    """Generate and save arrays for all requested k values."""

    requested_k_values = list(k_values)
    for k in requested_k_values:
        validate_array_parameters(n, k)

    path = data_module_path(student_nickname)
    arrays_by_k, metadata_by_k = read_arrays_module(path)
    generated_arrays = {}

    for k in requested_k_values:
        arr = [randint(0, k) for _ in range(n)]
        arrays_by_k[k] = arr
        metadata_by_k[k] = {"n": n, "k": k}
        generated_arrays[k] = arr

    write_arrays_module(path, arrays_by_k, metadata_by_k)

    return generated_arrays


def read_student_nickname_from_main() -> str:
    """Read STUDENT_NICKNAME from main.py as the single nickname source."""

    main_path = TASK_DIR / "main.py"
    tree = ast.parse(main_path.read_text(encoding="utf-8"), filename=str(main_path))
    student_nickname = _read_literal_assignment(tree, "STUDENT_NICKNAME", "")

    if not isinstance(student_nickname, str):
        raise ValueError("STUDENT_NICKNAME in main.py must be a string")
    if fullmatch(r"[A-Za-z0-9_-]{1,30}", student_nickname) is None:
        raise ValueError(
            "STUDENT_NICKNAME in main.py must contain 1-30 letters, numbers, "
            "underscores, or hyphens"
        )

    return student_nickname


def load_initialized_array(k: int, student_nickname: str) -> list[int]:
    """Load an array previously saved for the given k."""

    if not isinstance(k, int):
        raise TypeError("k must be an integer")
    if k < 0:
        raise ValueError("k must be non-negative")

    path = data_module_path(student_nickname)
    arrays_by_k, _metadata_by_k = read_arrays_module(path)

    if k not in arrays_by_k:
        raise KeyError(f"No saved array found for k={k} in {path}")

    return arrays_by_k[k]


def read_arrays_module(path: Path) -> tuple[dict[int, list[int]], dict[int, dict[str, int]]]:
    """Read array dictionaries from a generated Python data module."""

    if not path.exists():
        return {}, {}

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    arrays_by_k = _read_literal_assignment(tree, "ARRAYS_BY_K", {})
    metadata_by_k = _read_literal_assignment(tree, "ARRAY_METADATA_BY_K", {})

    return _validate_arrays_by_k(arrays_by_k), _validate_metadata_by_k(metadata_by_k)


def write_arrays_module(
    path: Path,
    arrays_by_k: dict[int, list[int]],
    metadata_by_k: dict[int, dict[str, int]],
) -> None:
    """Write all saved arrays as a directly importable Python module."""

    lines = [
        '"""Generated input arrays for L1-warmup."""',
        "",
        f"ARRAY_METADATA_BY_K = {pformat(metadata_by_k, sort_dicts=True)}",
        f"ARRAYS_BY_K = {pformat(arrays_by_k, sort_dicts=True)}",
        "",
    ]

    for k in sorted(arrays_by_k):
        lines.append(f"{array_variable_name(k)} = ARRAYS_BY_K[{k}]")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _read_literal_assignment(
    tree: ast.Module,
    variable_name: str,
    default: object,
) -> object:
    for statement in tree.body:
        if not isinstance(statement, ast.Assign):
            continue
        has_variable_name = any(
            isinstance(target, ast.Name) and target.id == variable_name
            for target in statement.targets
        )
        if has_variable_name:
            return ast.literal_eval(statement.value)

    return default


def _validate_arrays_by_k(value: object) -> dict[int, list[int]]:
    if not isinstance(value, dict):
        raise ValueError("ARRAYS_BY_K must be a dictionary")

    arrays_by_k = {}
    for k, arr in value.items():
        if not isinstance(k, int) or k < 0:
            raise ValueError("ARRAYS_BY_K keys must be non-negative integers")
        if not isinstance(arr, list) or any(not isinstance(item, int) for item in arr):
            raise ValueError("ARRAYS_BY_K values must be lists of integers")
        arrays_by_k[k] = arr

    return arrays_by_k


def _validate_metadata_by_k(value: object) -> dict[int, dict[str, int]]:
    if not isinstance(value, dict):
        raise ValueError("ARRAY_METADATA_BY_K must be a dictionary")

    metadata_by_k = {}
    for k, metadata in value.items():
        if not isinstance(k, int) or k < 0:
            raise ValueError("ARRAY_METADATA_BY_K keys must be non-negative integers")
        if not isinstance(metadata, dict):
            raise ValueError("ARRAY_METADATA_BY_K values must be dictionaries")
        if metadata.get("k") != k:
            raise ValueError("ARRAY_METADATA_BY_K entries must include their matching k")
        if not isinstance(metadata.get("n"), int) or metadata["n"] < 0:
            raise ValueError("ARRAY_METADATA_BY_K entries must include a non-negative n")
        metadata_by_k[k] = {"n": metadata["n"], "k": metadata["k"]}

    return metadata_by_k


def main() -> None:
    """Generate the configured reusable arrays."""

    student_nickname = read_student_nickname_from_main()
    generated_arrays = initialize_all_arrays(N, K, student_nickname)
    path = data_module_path(student_nickname)
    generated_k_values = ", ".join(str(k) for k in sorted(generated_arrays))

    print(f"Wrote arrays for k = {generated_k_values} to {path}")


if __name__ == "__main__":
    main()
