"""Safe duplicate detection and optional quarantine operations."""

from dataclasses import dataclass
from datetime import datetime
import hashlib
from pathlib import Path
import shutil

from organizer import HISTORY_FILENAME

QUARANTINE_FOLDER = ".file_organizer_quarantine"


@dataclass(frozen=True)
class DuplicateFile:
    path: Path
    size: int
    modified: datetime
    digest: str


@dataclass(frozen=True)
class DuplicateGroup:
    files: tuple[DuplicateFile, ...]

    @property
    def size(self) -> int:
        return self.files[0].size

    @property
    def savings(self) -> int:
        return self.size * (len(self.files) - 1)


def _file_hash(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        while chunk := file.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _is_scan_candidate(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    return (
        path.is_file()
        and path.name != HISTORY_FILENAME
        and QUARANTINE_FOLDER not in relative.parts
    )


def find_duplicate_groups(folder: Path, recursive: bool = True) -> tuple[list[DuplicateGroup], list[str]]:
    """Find identical files, reporting files that could not be read."""
    root = folder.resolve()
    if not root.is_dir():
        raise ValueError("The selected path is not an accessible folder.")
    candidates = root.rglob("*") if recursive else root.iterdir()
    by_size: dict[int, list[Path]] = {}
    errors: list[str] = []
    for path in candidates:
        try:
            if not _is_scan_candidate(path, root):
                continue
            by_size.setdefault(path.stat().st_size, []).append(path)
        except OSError as error:
            errors.append(f"{path}: {error}")

    by_digest: dict[tuple[int, str], list[DuplicateFile]] = {}
    for size, paths in by_size.items():
        if len(paths) < 2:
            continue
        for path in paths:
            try:
                stat = path.stat()
                item = DuplicateFile(
                    path=path,
                    size=size,
                    modified=datetime.fromtimestamp(stat.st_mtime),
                    digest=_file_hash(path),
                )
                by_digest.setdefault((size, item.digest), []).append(item)
            except OSError as error:
                errors.append(f"{path}: {error}")

    groups = [
        DuplicateGroup(tuple(sorted(files, key=lambda item: str(item.path).lower())))
        for files in by_digest.values()
        if len(files) > 1
    ]
    groups.sort(key=lambda group: str(group.files[0].path).lower())
    return groups, errors


def duplicate_savings(groups: list[DuplicateGroup]) -> int:
    """Return removable storage while retaining one copy per group."""
    return sum(group.savings for group in groups)


def quarantine_files(
    folder: Path,
    selected: list[DuplicateFile],
) -> tuple[list[tuple[DuplicateFile, Path]], list[str]]:
    """Move explicitly selected duplicates into a collision-safe quarantine."""
    root = folder.resolve()
    quarantine = root / QUARANTINE_FOLDER
    moved: list[tuple[DuplicateFile, Path]] = []
    errors: list[str] = []
    for item in selected:
        try:
            source = item.path.resolve()
            if not source.is_file() or not source.is_relative_to(root):
                errors.append(f"Unsafe or missing duplicate: {item.path}")
                continue
            current_stat = source.stat()
            if current_stat.st_size != item.size or _file_hash(source) != item.digest:
                errors.append(f"File changed since detection: {source}")
                continue
            destination = quarantine / source.relative_to(root)
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                errors.append(f"Quarantine destination already exists: {destination}")
                continue
            shutil.move(str(source), str(destination))
            moved.append((item, destination))
        except (OSError, shutil.Error) as error:
            errors.append(f"Could not quarantine {item.path}: {error}")
    return moved, errors
