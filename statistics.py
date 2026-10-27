"""Statistics for files directly inside a selected folder."""

from collections import defaultdict
from pathlib import Path

from categories import classify_file


def format_size(size: int) -> str:
    """Format a byte count using readable binary units."""
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{size} B"


def calculate_statistics(
    files: list[Path],
    largest_count: int = 10,
    duplicate_groups: list | None = None,
) -> dict:
    """Calculate totals and category breakdowns for a list of files."""
    category_counts = defaultdict(int)
    category_sizes = defaultdict(int)
    file_sizes: list[tuple[Path, int]] = []
    for path in files:
        try:
            size = path.stat().st_size
        except OSError:
            continue
        category = classify_file(path)
        category_counts[category] += 1
        category_sizes[category] += size
        file_sizes.append((path, size))
    file_sizes.sort(key=lambda item: item[1], reverse=True)
    duplicate_count = sum(len(group.files) for group in duplicate_groups or [])
    duplicate_savings = sum(group.savings for group in duplicate_groups or [])
    return {
        "total_files": len(file_sizes),
        "total_size": sum(size for _, size in file_sizes),
        "category_counts": dict(category_counts),
        "category_sizes": dict(category_sizes),
        "largest_files": file_sizes[:largest_count],
        "files_without_extensions": sum(1 for path, _ in file_sizes if not path.suffix),
        "duplicate_files": duplicate_count,
        "duplicate_groups": len(duplicate_groups or []),
        "duplicate_savings": duplicate_savings,
    }
