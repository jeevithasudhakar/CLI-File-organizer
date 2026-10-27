"""Search files within a user-selected directory."""

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from categories import classify_file
from duplicates import DuplicateGroup
from organizer import HISTORY_FILENAME


@dataclass(frozen=True)
class SearchCriteria:
    name: str = ""
    extension: str = ""
    category: str = ""
    minimum_size: int | None = None
    maximum_size: int | None = None
    modified_after: date | None = None
    duplicates_only: bool = False


def _duplicate_paths(groups: list[DuplicateGroup]) -> set[Path]:
    return {item.path.resolve() for group in groups for item in group.files}


def search_files(
    folder: Path,
    criteria: SearchCriteria,
    duplicate_groups: list[DuplicateGroup] | None = None,
) -> tuple[list[Path], list[str]]:
    """Return matching files recursively, plus access errors."""
    root = folder.resolve()
    if not root.is_dir():
        raise ValueError("The selected path is not an accessible folder.")
    duplicate_paths = _duplicate_paths(duplicate_groups or [])
    matches: list[Path] = []
    errors: list[str] = []
    for path in root.rglob("*"):
        try:
            if not path.is_file() or path.name == HISTORY_FILENAME:
                continue
            if ".file_organizer_quarantine" in path.relative_to(root).parts:
                continue
            if criteria.name and criteria.name.lower() not in path.name.lower():
                continue
            if criteria.extension and path.suffix.lower() != criteria.extension.lower():
                continue
            if criteria.category and classify_file(path).lower() != criteria.category.lower():
                continue
            stat = path.stat()
            if criteria.minimum_size is not None and stat.st_size < criteria.minimum_size:
                continue
            if criteria.maximum_size is not None and stat.st_size > criteria.maximum_size:
                continue
            if criteria.modified_after and date.fromtimestamp(stat.st_mtime) < criteria.modified_after:
                continue
            if criteria.duplicates_only and path.resolve() not in duplicate_paths:
                continue
            matches.append(path.resolve())
        except OSError as error:
            errors.append(f"{path}: {error}")
    return sorted(matches, key=lambda item: str(item).lower()), errors
