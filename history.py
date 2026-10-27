"""JSON activity history and safe undo support."""

from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

HISTORY_FILENAME = ".file_organizer_history.json"


def history_path(folder: Path) -> Path:
    return folder / HISTORY_FILENAME


def _read(folder: Path) -> list[dict]:
    path = history_path(folder)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _write(folder: Path, records: list[dict]) -> None:
    history_path(folder).write_text(
        json.dumps(records, indent=2), encoding="utf-8"
    )


def record_operation(
    folder: Path,
    moves: list[tuple[Path, Path]],
    failures: list[tuple[Path, str]] | None = None,
) -> None:
    """Append successful moves from one operation to the local history file."""
    records = _read(folder)
    entries = [
        {
            "source": str(source),
            "destination": str(destination),
            "status": "completed",
            "error": None,
        }
        for source, destination in moves
    ]
    entries.extend(
        {
            "source": str(source),
            "destination": "",
            "status": "skipped",
            "error": error,
        }
        for source, error in failures or []
    )
    records.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": "organize",
            "status": "completed" if not failures else "partial",
            "undone": False,
            "moves": entries,
        }
    )
    _write(folder, records)


def record_activity(
    folder: Path,
    operation: str,
    entries: list[dict],
    status: str = "completed",
) -> None:
    """Record a non-undoable operation with per-entry status and errors."""
    records = _read(folder)
    records.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "status": status,
            "undone": True,
            "moves": entries,
        }
    )
    _write(folder, records)


def recent_activity(folder: Path, limit: int = 10) -> list[dict]:
    """Return the newest activity records first."""
    return list(reversed(_read(folder)[-limit:]))


def undo_latest(folder: Path) -> tuple[int, list[str]]:
    """Restore the latest operation without overwriting existing files."""
    records = _read(folder)
    latest_index = next(
        (index for index in range(len(records) - 1, -1, -1)
         if not records[index].get("undone")),
        None,
    )
    if latest_index is None:
        return 0, ["No completed organization operation is available to undo."]

    latest = records[latest_index]
    remaining = list(latest.get("moves", []))
    restored = 0
    errors: list[str] = []
    root = folder.resolve()
    for move in list(remaining):
        source = Path(move["source"])
        destination = Path(move["destination"])
        try:
            if source.resolve().parent != root:
                errors.append(f"Unsafe original location: {source}")
                continue
            if not destination.resolve().is_relative_to(root):
                errors.append(f"Unsafe destination location: {destination}")
                continue
            if not destination.exists():
                errors.append(f"Moved file is missing: {destination}")
                continue
            if source.exists():
                errors.append(f"Original filename already exists: {source}")
                continue
            shutil.move(str(destination), str(source))
            remaining.remove(move)
            restored += 1
        except (OSError, shutil.Error) as error:
            errors.append(f"Could not restore {destination}: {error}")

    latest["moves"] = remaining
    latest["undone"] = not remaining
    latest["status"] = "undone" if not remaining else "partial"
    for move in latest["moves"]:
        move["status"] = "not_restored"
        move["error"] = "Could not safely restore this file."
    _write(folder, records)
    return restored, errors
