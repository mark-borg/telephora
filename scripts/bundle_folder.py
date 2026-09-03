#!/usr/bin/env python3
"""Bundle a folder's contents for delivery.

Usage: uv run python scripts/bundle_folder.py <path>
"""

import argparse
import os
import zlib
from collections import Counter, defaultdict
from pathlib import Path

from rich.console import Console
from rich.progress import Progress
from rich.table import Table


def collect_files(root: Path) -> list[Path]:
    files = []
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            files.append(Path(dirpath) / name)
    return files


def count_extensions(
    files: list[Path], progress: Progress,
) -> tuple[Counter[str], dict[str, int], dict[str, int]]:
    counts: Counter[str] = Counter()
    sizes: dict[str, int] = defaultdict(int)
    compressed: dict[str, int] = defaultdict(int)
    task = progress.add_task("Scanning files...", total=len(files))
    for filepath in files:
        ext = filepath.suffix.lower()
        key = ext if ext else "(no extension)"
        counts[key] += 1
        data = filepath.read_bytes()
        sizes[key] += len(data)
        compressed[key] += len(zlib.compress(data))
        progress.advance(task)
    return counts, sizes, compressed


def main() -> None:
    parser = argparse.ArgumentParser(description="Count files by extension in a directory tree.")
    parser.add_argument("path", type=Path, help="Root directory to scan")
    args = parser.parse_args()

    root: Path = args.path.resolve()
    if not root.is_dir():
        raise SystemExit(f"Error: {root} is not a directory")

    files = collect_files(root)
    if not files:
        raise SystemExit(f"No files found in {root}")

    with Progress() as progress:
        counts, sizes, compressed = count_extensions(files, progress)

    table = Table(title="File counts and sizes aggregated by extension")
    table.add_column("Ext", style="cyan")
    table.add_column("Count", style="green", justify="right")
    table.add_column("Size MB", style="magenta", justify="right")
    table.add_column("Zipped MB", style="yellow", justify="right")

    for ext in sorted(counts, key=lambda e: sizes[e], reverse=True):
        size_mb = sizes[ext] / (1024 * 1024)
        comp_mb = compressed[ext] / (1024 * 1024)
        table.add_row(ext, str(counts[ext]), f"{size_mb:.2f}", f"{comp_mb:.2f}")

    table.add_section()
    total_size_mb = sum(sizes.values()) / (1024 * 1024)
    total_comp_mb = sum(compressed.values()) / (1024 * 1024)
    table.add_row("Total", str(sum(counts.values())), f"{total_size_mb:.2f}", f"{total_comp_mb:.2f}", style="bold")

    Console().print(table)


if __name__ == "__main__":
    main()
