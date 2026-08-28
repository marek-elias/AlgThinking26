# Classroom Coding Instructions

## Repository structure

Assignment directories follow this naming convention:

```text
LNN-task_name/
```

* `NN` is the two-digit lecture number, such as `01`, `02`, or `12`.
* `task_name` describes the task.
* A lecture may contain several task directories.

Each task directory must have this structure:

```text
LNN-task_name/
├── main.py
├── data/
├── results/
└── additional files, if needed
```

The task requirements are:

* `main.py` contains the main executable solution.
* `data/` contains generated or reusable input data used by the task code.
* `results/` contains every generated plot, text file, table, report, or other output.
* Additional source or configuration files may be placed inside the task directory when needed.
* Do not place generated data outside the task’s `data/` directory.
* Do not place generated output outside the task’s `results/` directory.

## Student nickname

Every task’s `main.py` must contain the following constant near the beginning of the file, after imports and before the program logic:

```python
STUDENT_NICKNAME = "chosen_nickname"
```

Before creating, modifying, or running code for a task:

1. Inspect the task’s `main.py` for `STUDENT_NICKNAME`.

2. If it exists and contains a non-empty nickname, use it.

3. If it is missing or empty, inspect the other `LNN-task_name/main.py` files in the repository.

4. If they all contain the same non-empty nickname, use that nickname for the current task.

5. If no nickname can be determined, or conflicting nicknames are found, ask the student:

   `What nickname should be used for your work?`

6. Validate the nickname before using it:

   * Allow only letters, numbers, underscores, and hyphens.
   * Require between 1 and 30 characters.
   * Do not accept spaces, periods, slashes, or path components.

7. Hard-code the validated nickname in the current task’s `main.py`.

Use `STUDENT_NICKNAME` as the single source of the nickname. Do not repeat the nickname as another hard-coded string elsewhere in the program.

Do not change an existing non-empty nickname unless the student explicitly asks to change it.

## Output requirements

All generated output must be written into the current task’s `results/` directory.

Every generated result filename must begin with the student nickname.

Examples:

```text
results/<nickname>_plot.png
results/<nickname>_results.txt
results/<nickname>_table.csv
results/<nickname>_report.pdf
```

For example, if the nickname is `blue_fox`, valid filenames include:

```text
results/blue_fox_plot.png
results/blue_fox_results.txt
```

Text-based result files must also contain the following line:

```text
Student nickname: <nickname>
```

Do not overwrite or delete result files belonging to another nickname.

## Constructing paths in Python

Construct paths relative to the location of `main.py`, not relative to the shell’s current working directory.

Use this pattern:

```python
from pathlib import Path

STUDENT_NICKNAME = "chosen_nickname"

TASK_DIR = Path(__file__).resolve().parent
DATA_DIR = TASK_DIR / "data"
RESULTS_DIR = TASK_DIR / "results"
DATA_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
```

Construct result filenames using `STUDENT_NICKNAME`:

```python
text_output = RESULTS_DIR / f"{STUDENT_NICKNAME}_results.txt"
plot_output = RESULTS_DIR / f"{STUDENT_NICKNAME}_plot.png"
```

Example for writing a text result:

```python
text_output.write_text(
    f"Student nickname: {STUDENT_NICKNAME}\n"
    "Result: 42\n",
    encoding="utf-8",
)
```

Example for saving a Matplotlib plot:

```python
figure.savefig(
    RESULTS_DIR / f"{STUDENT_NICKNAME}_plot.png",
    dpi=150,
    bbox_inches="tight",
)
```

## Working on a task

When the student asks to work on a particular task:

1. Identify the corresponding `LNN-task_name/` directory.
2. Work only inside that task directory unless the student explicitly requests a shared repository change.
3. Ask for the nickname when it cannot be determined using the rules above.
4. Ensure that `main.py` contains the hard-coded `STUDENT_NICKNAME`.
5. Preserve the required `main.py`, `data/`, and `results/` structure.
6. Add extra files only when they are useful for the solution.
7. Keep the code readable and appropriate for a classroom submission.
8. Run `main.py` after making changes.
9. Fix errors encountered while running the program.
10. Verify that generated data files were created inside the task’s `data/` directory.
11. Verify that all expected output files were created inside the task’s `results/` directory.
12. Verify that every output filename begins with the correct nickname.
13. Verify that text-based results contain the nickname inside the file.

## Completion response

When the task is complete, report:

* The task directory that was used.
* The source files that were created or changed.
* The generated result files.
* The command used to run the solution.
* Whether the program completed successfully.
