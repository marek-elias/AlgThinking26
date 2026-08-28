#!/usr/bin/env python3
"""Prepare a task's result files for Microsoft Forms upload."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from urllib.parse import urlparse


URL_FILENAME = "microsoft_form_url.txt"
TEXT_RESULT_SUFFIXES = {
    ".csv",
    ".html",
    ".json",
    ".md",
    ".svg",
    ".tex",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}


def main() -> None:
    args = parse_args()
    task_dir = args.task_dir.resolve()

    if not task_dir.is_dir():
        raise SystemExit(f"Task directory does not exist: {task_dir}")

    if args.url is not None:
        write_form_url(task_dir, args.url)

    summary = build_upload_summary(task_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect result files and form URL for a task upload."
    )
    parser.add_argument("task_dir", type=Path)
    parser.add_argument(
        "--url",
        help=f"Save this Microsoft Form URL to {URL_FILENAME} before preparing.",
    )
    return parser.parse_args()


def build_upload_summary(task_dir: Path) -> dict[str, object]:
    results_dir = task_dir / "results"
    form_url = read_form_url(task_dir)
    nickname = read_student_nickname(task_dir / "main.py")
    result_files = sorted(path for path in results_dir.rglob("*") if path.is_file())
    warnings = []

    if form_url is None:
        warnings.append(f"Missing {URL_FILENAME}")
    elif not looks_like_microsoft_form_url(form_url):
        warnings.append("Configured URL does not look like a Microsoft Forms URL")

    if not results_dir.is_dir():
        warnings.append("Missing results/ directory")
    elif not result_files:
        warnings.append("No files found under results/")

    if nickname is None:
        warnings.append("Could not read STUDENT_NICKNAME from main.py")
    else:
        for path in result_files:
            if not path.name.startswith(f"{nickname}_"):
                warnings.append(
                    f"Result filename does not begin with nickname: {path.name}"
                )
            if path.suffix.lower() in TEXT_RESULT_SUFFIXES:
                text = path.read_text(encoding="utf-8", errors="replace")
                if f"Student nickname: {nickname}" not in text:
                    warnings.append(
                        f"Text result lacks nickname line: {path.relative_to(task_dir)}"
                    )

    return {
        "task_dir": str(task_dir),
        "form_url": form_url,
        "url_file": str(task_dir / URL_FILENAME),
        "student_nickname": nickname,
        "result_files": [str(path) for path in result_files],
        "warnings": warnings,
    }


def read_form_url(task_dir: Path) -> str | None:
    path = task_dir / URL_FILENAME
    if not path.exists():
        return None

    for line in path.read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if value and not value.startswith("#"):
            return value

    return None


def write_form_url(task_dir: Path, url: str) -> None:
    value = url.strip()
    if not value:
        raise SystemExit("URL must not be empty")
    if not looks_like_https_url(value):
        raise SystemExit("URL must be an https URL")

    (task_dir / URL_FILENAME).write_text(value + "\n", encoding="utf-8")


def read_student_nickname(main_path: Path) -> str | None:
    if not main_path.exists():
        return None

    tree = ast.parse(main_path.read_text(encoding="utf-8"), filename=str(main_path))
    for statement in tree.body:
        if not isinstance(statement, ast.Assign):
            continue
        for target in statement.targets:
            if isinstance(target, ast.Name) and target.id == "STUDENT_NICKNAME":
                value = ast.literal_eval(statement.value)
                return value if isinstance(value, str) and value else None

    return None


def looks_like_https_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and bool(parsed.netloc)


def looks_like_microsoft_form_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    return parsed.scheme == "https" and (
        "forms.office.com" in host
        or "forms.microsoft.com" in host
        or "forms.cloud.microsoft" in host
    )


if __name__ == "__main__":
    main()
