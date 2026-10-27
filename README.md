# Smart CLI File Organizer

A beginner-friendly Python command-line tool that organizes files directly inside a selected folder into category subfolders based on file extensions. It previews every proposed change, asks for confirmation, never overwrites files, and supports safe undo.

## Problem and solution

Manually sorting downloads is repetitive and error-prone. This project scans one user-selected folder (without recursive scanning), classifies files by extension, and safely moves them into folders such as `Images`, `Documents`, and `Code`.

## Features

- Preview mode with original and proposed destination paths.
- Explicit `yes` confirmation before any move.
- Case-insensitive extension classification, including files without extensions.
- Collision-safe names such as `photo (1).jpg`.
- Clear scanned, moved, skipped, and error summaries.
- File statistics, category totals, storage totals, and largest files.
- JSON activity history and safe undo of the latest completed operation.
- Standard-library only and cross-platform `pathlib` file handling.

## Technology stack

Python 3.10+ (tested with Python 3.14.7), `pathlib`, `shutil`, `json`, and `unittest`.

## Project structure

```text
main.py                 Interactive menu
categories.py           Extension-to-category mapping
organizer.py            Scanning, planning, and moving
statistics.py           File statistics and size formatting
history.py              JSON history and undo
tests/test_organizer.py Automated tests
```

## Installation and Windows usage

1. Install Python from [python.org](https://www.python.org/downloads/) and enable the Python launcher.
2. Open this folder in VS Code.
3. In the VS Code terminal, run:

```powershell
py main.py
```

Select an option and enter a folder path, for example `C:\Users\YourName\Downloads`.

The organizer only scans files immediately inside the selected folder. It does not recursively scan subfolders or execute files.

## Example

```text
Smart CLI File Organizer
1. Organize a folder
2. Preview organization without moving files
3. View file statistics
4. Undo the most recent organization
5. Exit
Choose an option: 2
Enter the folder path: C:\Users\YourName\Downloads

Proposed changes:
  C:\...\photo.jpg  ->  C:\...\Images\photo.jpg
```

Preview never changes files. Organize displays the same preview and moves files only when `yes` is entered. Successful moves are written to `.file_organizer_history.json` in the selected folder. Undo checks that the original filename is available and refuses to overwrite anything.

## Testing

Tests use isolated temporary directories and never touch personal folders:

```powershell
py -m unittest discover -s tests
```

## Limitations and future improvements

- Only files directly inside the selected folder are organized.
- Symbolic links and unusual filesystem permissions depend on the operating system.
- Future versions could offer configurable categories, recursive mode with stronger safeguards, logging, and a non-interactive command-line argument mode.