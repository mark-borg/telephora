#!/usr/bin/env python3
"""Bundle a folder's contents for delivery.

Usage: uv run python scripts/bundle_folder.py <path>
"""

import argparse
import os
from collections import Counter, defaultdict
from pathlib import Path

from rich.console import Console
from rich.table import Table


def count_extensions(root: Path) -> tuple[Counter[str], dict[str, int]]:
    counts: Counter[str] = Counter()
    sizes: dict[str, int] = defaultdict(int)
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            ext = Path(name).suffix.lower()
            key = ext if ext else "(no extension)"
            counts[key] += 1
            sizes[key] += (Path(dirpath) / name).stat().st_size
    return counts, sizes


def main() -> None:
    parser = argparse.ArgumentParser(description="Count files by extension in a directory tree.")
    parser.add_argument("path", type=Path, help="Root directory to scan")
    args = parser.parse_args()

    root: Path = args.path.resolve()
    if not root.is_dir():
        raise SystemExit(f"Error: {root} is not a directory")

    counts, sizes = count_extensions(root)
    if not counts:
        raise SystemExit(f"No files found in {root}")

    table = Table(title=f"File extensions in {root}")
    table.add_column("Extension", style="cyan")
    table.add_column("Count", style="green", justify="right")
    table.add_column("Total Size (MB)", style="magenta", justify="right")

    for ext in sorted(counts, key=lambda e: sizes[e], reverse=True):
        size_mb = sizes[ext] / (1024 * 1024)
        table.add_row(ext, str(counts[ext]), f"{size_mb:.2f}")

    table.add_section()
    total_size_mb = sum(sizes.values()) / (1024 * 1024)
    table.add_row("Total", str(sum(counts.values())), f"{total_size_mb:.2f}", style="bold")

    Console().print(table)


if __name__ == "__main__":
    main()
