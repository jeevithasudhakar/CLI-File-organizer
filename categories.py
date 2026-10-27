"""File extension categories used by the organizer."""

from pathlib import Path

CATEGORY_EXTENSIONS = {
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"},
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt"},
    "Spreadsheets": {".xls", ".xlsx", ".csv", ".ods"},
    "Presentations": {".ppt", ".pptx", ".odp"},
    "Videos": {".mp4", ".mkv", ".avi", ".mov", ".webm"},
    "Audio": {".mp3", ".wav", ".aac", ".flac", ".ogg"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz"},
    "Code": {".py", ".c", ".cpp", ".java", ".js", ".ts", ".html", ".css", ".sql"},
    "Executables": {".exe", ".msi", ".bat", ".sh"},
}


def classify_file(path: Path) -> str:
    """Return the category for a file, using a case-insensitive suffix."""
    suffix = path.suffix.lower()
    for category, extensions in CATEGORY_EXTENSIONS.items():
        if suffix in extensions:
            return category
    return "Other"
