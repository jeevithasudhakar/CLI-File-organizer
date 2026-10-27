"""Scanning, planning, and safe file movement operations."""

from dataclasses import dataclass
from pathlib import Path
import shutil

from categories import classify_file

HISTORY_FILENAME = ".file_organizer_history.json"


@dataclass(frozen=True)
class MovePlan:
    source: Path
    destination: Path
    category: str


@dataclass
class MoveResult:
    moved: list[MovePlan]
    skipped: list[tuple[MovePlan, str]]
    errors: list[tuple[MovePlan, str]]


def validate_folder(folder: Path) -> tuple[bool, str]:
    """Check that a path exists, is a directory, and can be read."""
    try:
        if not folder.exists():
            return False, "The selected path does not exist."
        if not folder.is_dir():
            return False, "The selected path is not a folder."
        next(folder.iterdir(), None)
        return True, ""
    except OSError as error:
        return False, f"The folder cannot be accessed: {error}"


def scan_folder(folder: Path, recursive: bool = False) -> list[Path]:
    """Return regular files, directly inside folder unless recursive is enabled."""
    valid, message = validate_folder(folder)
    if not valid:
        raise ValueError(message)
    try:
        entries = folder.rglob("*") if recursive else folder.iterdir()
        return sorted(
            (
                entry.resolve()
                for entry in entries
                if entry.is_file()
                and entry.name != HISTORY_FILENAME
                and ".file_organizer_quarantine" not in entry.relative_to(folder).parts
            ),
            key=lambda path: path.name.lower(),
        )
    except OSError as error:
        raise OSError(f"Could not scan the folder: {error}") from error


def _is_within(path: Path, folder: Path) -> bool:
    try:
        path.resolve().relative_to(folder.resolve())
        return True
    except ValueError:
        return False


def _unique_destination(destination: Path, reserved: set[Path]) -> Path:
    candidate = destination
    counter = 1
    while candidate.exists() or candidate in reserved:
        candidate = destination.with_name(
            f"{destination.stem} ({counter}){destination.suffix}"
        )
        counter += 1
    return candidate


def create_plan(folder: Path) -> list[MovePlan]:
    """Build a safe, non-recursive movement plan for files in folder."""
    folder = folder.resolve()
    plans: list[MovePlan] = []
    reserved: set[Path] = set()
    for source in scan_folder(folder):
        category = classify_file(source)
        destination_folder = folder / category
        destination = _unique_destination(destination_folder / source.name, reserved)
        if not _is_within(destination, folder):
            raise ValueError("A proposed destination would leave the selected folder.")
        reserved.add(destination)
        plans.append(MovePlan(source, destination, category))
    return plans


def execute_plan(plans: list[MovePlan]) -> MoveResult:
    """Move planned files without overwriting and report every outcome."""
    result = MoveResult([], [], [])
    for plan in plans:
        try:
            if not _is_within(plan.destination, plan.source.parent):
                result.errors.append((plan, "Destination is outside the selected folder."))
                continue
            if not plan.source.exists():
                result.skipped.append((plan, "Source file no longer exists."))
                continue
            if plan.destination.exists():
                result.skipped.append((plan, "Destination already exists."))
                continue
            plan.destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(plan.source), str(plan.destination))
            result.moved.append(plan)
        except (OSError, shutil.Error) as error:
            result.errors.append((plan, str(error)))
        except KeyboardInterrupt:
            result.errors.append((plan, "Operation interrupted by the user."))
            break
    return result
