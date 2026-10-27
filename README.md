# Smart CLI File Management System

A safe, standard-library Python application for organizing, analyzing, searching, and reviewing files in a user-selected directory. It is designed as a beginner-friendly but portfolio-ready second-year IT project.

## Project overview

The original organizer sorted files by extension. The upgraded system keeps that behavior and adds a terminal analytics dashboard, SHA-256 duplicate detection, flexible file search, activity history, and a review-first quarantine workflow.

The application never scans the whole computer by default, never executes files, never overwrites files, and never permanently deletes duplicates. Organization remains non-recursive; analytics, duplicate detection, and search can inspect the selected directory tree.

## Features

- Organize files directly inside a selected folder by extension.
- Preview every proposed move and require an explicit `yes` confirmation.
- Analytics dashboard with:
  - total files and storage used;
  - category counts and storage table;
  - largest 10 files;
  - files without extensions;
  - duplicate count and potential savings.
- Duplicate detection using file-size filtering followed by SHA-256 content hashes.
- Duplicate groups show paths, sizes, and last-modified timestamps.
- Optional duplicate quarantine after selecting groups and confirming.
- Rechecks file size and hash immediately before quarantine.
- Search by partial name, extension, category, minimum/maximum size, modified date, and duplicate status.
- JSON activity history with timestamps, source/destination paths, statuses, and errors.
- Safe undo of eligible organization moves without overwriting existing files.
- Standard library only; compatible with Python 3.10+ and tested with Python 3.14.7.

## Installation and execution on Windows

1. Install Python and enable the Python launcher.
2. Open this repository in VS Code.
3. Open the integrated terminal and run:

```powershell
py main.py
```

The menu is:

```text
1. Organize files
2. Preview organization
3. View file analytics
4. Find duplicate files
5. Search files
6. View activity history
7. Undo the last organization operation
8. Exit
```

Enter a directory explicitly when prompted. Organization scans only files immediately inside that directory. Duplicate detection and search can inspect subdirectories inside the selected directory, but never scan outside it.

## Example output

```text
==========================================================
FILE ANALYTICS DASHBOARD
==========================================================
Total files scanned:       42
Total storage used:        18.42 MB
Files without extensions:  3
Duplicate files detected:  6
Duplicate groups:          2
Potential duplicate savings: 2.10 MB

By category:
  Category             Files       Storage
  ------------------ ------- --------------
  Documents                8        4.30 MB
  Images                  19       10.02 MB
  Other                    3        1.00 KB
```

Duplicate detection first groups files with the same byte size, then hashes their contents with SHA-256. A group with three identical 5 MB files reports 10 MB of potential savings because one copy is retained. The tool does not assume that a same-named file is a duplicate.

To quarantine duplicates, select group numbers at the prompt. The application previews the selection, asks for `yes`, verifies that each file still exists with the same size and hash, and moves selected files into `.file_organizer_quarantine` rather than deleting them. Existing quarantine paths are never overwritten.

## Architecture

```text
main.py                 Interactive menu and terminal presentation
categories.py           Extension-to-category mapping
organizer.py            Non-recursive planning and safe organization
statistics.py           Analytics calculations and size formatting
duplicates.py           Size filtering, SHA-256 groups, quarantine
search.py               Selected-directory search filters
history.py              JSON activity records and undo
tests/                  Isolated unittest coverage
```

`.file_organizer_history.json` stores local history in the selected folder. It is ignored by Git. Quarantine contents are also ignored and are never included in normal scans.

## Testing

All tests use temporary directories and sample files. They do not access Downloads, Desktop, or system folders.

```powershell
py -m unittest discover -s tests
```

The tests cover classification, dry-run behavior, safe movement, duplicate names, invalid paths, analytics, duplicate groups, empty files, savings, search filters, quarantine rechecks, activity history, undo, and destination containment.

## Safety measures

- Explicit folder selection is required.
- Organization is non-recursive and confirmation-based.
- No automatic deletion or execution of user files.
- Existing destinations are never overwritten.
- Destination paths are checked to remain inside the selected directory.
- Duplicate quarantine is optional, reviewable, confirmation-based, and hash-rechecked.
- Undo verifies both the original and destination paths before moving.
- Inaccessible files are reported rather than silently treated as successful.

## Future improvements

- Configurable category files and user-defined search presets.
- A journaled quarantine restore command.
- Optional CSV/JSON export of analytics and search results.
- More platform-specific permission diagnostics.
- A fully non-interactive command mode for scripts.
