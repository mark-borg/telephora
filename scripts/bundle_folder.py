#!/usr/bin/env python3
"""Bundle a folder's contents for delivery.

Usage: uv run python scripts/bundle_folder.py <path> [--ignore <file>]
"""

import argparse
import os
import zipfile
import zlib
from collections import Counter, defaultdict
from pathlib import Path

import pathspec
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

IGNORE_FILE = ".bundleignore"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INCOMING_DIR = PROJECT_ROOT / "incoming"


def build_ignore_spec(ignore_path: Path, extra_patterns: list[str]) -> pathspec.PathSpec | None:
    lines: list[str] = []
    if ignore_path.is_file():
        lines.extend(ignore_path.read_text().splitlines())
    lines.extend(extra_patterns)
    if not lines:
        return None
    return pathspec.PathSpec.from_lines("gitwildmatch", lines)


def collect_files(root: Path, spec: pathspec.PathSpec | None) -> list[Path]:
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        if spec:
            dirnames[:] = [
                d for d in dirnames
                if not spec.match_file(str(Path(dirpath, d).relative_to(root)) + "/")
            ]
        for name in filenames:
            filepath = Path(dirpath) / name
            relpath = filepath.relative_to(root)
            if spec and spec.match_file(str(relpath)):
                continue
            files.append(filepath)
    return files


def scan_files(
    files: list[Path], progress: Progress,
) -> list[tuple[Path, int, int]]:
    results = []
    task = progress.add_task("Scanning files...", total=len(files))
    for filepath in files:
        if filepath.is_symlink() or not filepath.is_file():
            progress.advance(task)
            continue
        data = filepath.read_bytes()
        results.append((filepath, len(data), len(zlib.compress(data))))
        progress.advance(task)
    return results


def scan_and_display(root: Path, spec: pathspec.PathSpec | None, console: Console) -> None:
    files = collect_files(root, spec)
    if not files:
        console.print("[red]No files found after applying ignore patterns.[/red]")
        return

    with Progress() as progress:
        scan_results = scan_files(files, progress)

    ext_counts: Counter[str] = Counter()
    ext_sizes: dict[str, int] = defaultdict(int)
    ext_compressed: dict[str, int] = defaultdict(int)
    folder_counts: Counter[str] = Counter()
    folder_sizes: dict[str, int] = defaultdict(int)
    folder_compressed: dict[str, int] = defaultdict(int)
    folder_largest: dict[str, tuple[str, int]] = {}

    for filepath, size, comp_size in scan_results:
        ext = filepath.suffix.lower()
        ext_key = ext if ext else "(no extension)"
        ext_counts[ext_key] += 1
        ext_sizes[ext_key] += size
        ext_compressed[ext_key] += comp_size

        folder = str(filepath.parent.relative_to(root))
        folder_key = folder if folder != "." else "(root)"
        folder_counts[folder_key] += 1
        folder_sizes[folder_key] += size
        folder_compressed[folder_key] += comp_size
        prev_largest = folder_largest.get(folder_key)
        if prev_largest is None or size > prev_largest[1]:
            folder_largest[folder_key] = (ext_key, size)

    table = Table(title="File counts by extension")
    table.add_column("Ext", style="cyan")
    table.add_column("Count", style="green", justify="right")
    table.add_column("Size MB", style="magenta", justify="right")
    table.add_column("Zipped MB", style="yellow", justify="right")

    for ext in sorted(ext_counts, key=lambda e: ext_sizes[e], reverse=True):
        size_mb = ext_sizes[ext] / (1024 * 1024)
        comp_mb = ext_compressed[ext] / (1024 * 1024)
        table.add_row(ext, str(ext_counts[ext]), f"{size_mb:.2f}", f"{comp_mb:.2f}")

    table.add_section()
    total_size_mb = sum(ext_sizes.values()) / (1024 * 1024)
    total_comp_mb = sum(ext_compressed.values()) / (1024 * 1024)
    table.add_row("Total", str(sum(ext_counts.values())), f"{total_size_mb:.2f}", f"{total_comp_mb:.2f}", style="bold")

    folder_table = Table(title="File counts by folder")
    folder_table.add_column("Folder", style="cyan")
    folder_table.add_column("Count", style="green", justify="right")
    folder_table.add_column("Size MB", style="magenta", justify="right")
    folder_table.add_column("Zipped MB", style="yellow", justify="right")
    folder_table.add_column("Largest Ext", style="cyan")

    for folder in sorted(folder_counts):
        size_mb = folder_sizes[folder] / (1024 * 1024)
        comp_mb = folder_compressed[folder] / (1024 * 1024)
        largest_ext = folder_largest[folder][0]
        folder_table.add_row(folder, str(folder_counts[folder]), f"{size_mb:.2f}", f"{comp_mb:.2f}", largest_ext)

    folder_table.add_section()
    total_folder_mb = sum(folder_sizes.values()) / (1024 * 1024)
    total_folder_comp_mb = sum(folder_compressed.values()) / (1024 * 1024)
    folder_table.add_row("Total", str(sum(folder_counts.values())), f"{total_folder_mb:.2f}", f"{total_folder_comp_mb:.2f}", "", style="bold")

    console.print(table)
    console.print()
    console.print(folder_table)


def bundle_files(root: Path, spec: pathspec.PathSpec | None, console: Console) -> None:
    files = collect_files(root, spec)
    if not files:
        console.print("[red]No files to bundle.[/red]")
        return

    folder_name = root.name or "root"
    zip_path = INCOMING_DIR / f"{folder_name}.zip"

    with Progress() as progress:
        task = progress.add_task("Bundling files...", total=len(files))
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for filepath in files:
                arcname = str(filepath.relative_to(root))
                zf.write(filepath, arcname)
                progress.advance(task)

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    console.print(f"[green]Bundle saved:[/green] {zip_path} ({size_mb:.2f} MB, {len(files)} files)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Count files by extension in a directory tree.")
    parser.add_argument("path", type=Path, help="Root directory to scan")
    parser.add_argument("--ignore", type=Path, help=f"Ignore file (default: <path>/{IGNORE_FILE})")
    args = parser.parse_args()

    root: Path = args.path.resolve()
    if not root.is_dir():
        raise SystemExit(f"Error: {root} is not a directory")

    ignore_path = args.ignore or PROJECT_ROOT / IGNORE_FILE
    extra_patterns: list[str] = []
    console = Console()

    while True:
        spec = build_ignore_spec(ignore_path, extra_patterns)
        scan_and_display(root, spec, console)
        console.print()
        console.print("[bold]q[/bold] quit  [bold]a[/bold] add pattern to ignore  [bold]b[/bold] bundle to zip")
        choice = input("> ").strip().lower()
        if choice == "q":
            break
        elif choice == "a":
            pattern = input("Enter pattern to ignore (e.g. *.log, docs/): ").strip()
            if pattern:
                extra_patterns.append(pattern)
                console.print(f"Added pattern: [cyan]{pattern}[/cyan]")
            console.print()
        elif choice == "b":
            bundle_files(root, spec, console)
            break


if __name__ == "__main__":
    main()
