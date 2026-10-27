"""Interactive command-line interface for Smart CLI File Organizer."""

from pathlib import Path
from datetime import date, datetime

from duplicates import duplicate_savings, find_duplicate_groups, quarantine_files
from history import recent_activity, record_activity, record_operation, undo_latest
from organizer import MovePlan, create_plan, execute_plan, scan_folder
from search import SearchCriteria, search_files
from statistics import calculate_statistics, format_size


def prompt_folder() -> Path | None:
    raw_path = input("Enter the folder path: ").strip().strip('"')
    if not raw_path:
        print("Please enter a folder path.")
        return None
    folder = Path(raw_path).expanduser()
    if not folder.exists() or not folder.is_dir():
        print("That path is not an accessible folder.")
        return None
    return folder.resolve()


def display_plan(plans: list[MovePlan]) -> None:
    if not plans:
        print("No files were found directly inside this folder.")
        return
    print("\nProposed changes:")
    for plan in plans:
        print(f"  {plan.source}  ->  {plan.destination}")


def organize() -> None:
    folder = prompt_folder()
    if folder is None:
        return
    try:
        plans = create_plan(folder)
    except (OSError, ValueError) as error:
        print(f"Could not prepare organization: {error}")
        return
    display_plan(plans)
    if not plans:
        return
    if input("\nMove these files? Type 'yes' to confirm: ").strip().lower() != "yes":
        print("No files were moved.")
        return
    result = execute_plan(plans)
    if result.moved or result.skipped or result.errors:
        record_operation(
            folder,
            [(item.source, item.destination) for item in result.moved],
            [(item.source, reason) for item, reason in result.skipped + result.errors],
        )
    print(f"Scanned: {len(plans)} | Moved: {len(result.moved)} | "
          f"Skipped: {len(result.skipped)} | Errors: {len(result.errors)}")
    for plan, reason in result.skipped + result.errors:
        print(f"  {plan.source.name}: {reason}")


def preview() -> None:
    folder = prompt_folder()
    if folder is None:
        return
    try:
        display_plan(create_plan(folder))
    except (OSError, ValueError) as error:
        print(f"Could not create preview: {error}")


def show_statistics() -> None:
    folder = prompt_folder()
    if folder is None:
        return
    try:
        groups, duplicate_errors = find_duplicate_groups(folder)
        stats = calculate_statistics(
            scan_folder(folder, recursive=True), duplicate_groups=groups
        )
    except (OSError, ValueError) as error:
        print(f"Could not calculate statistics: {error}")
        return
    print("\n" + "=" * 58)
    print("FILE ANALYTICS DASHBOARD")
    print("=" * 58)
    print(f"Total files scanned:       {stats['total_files']}")
    print(f"Total storage used:        {format_size(stats['total_size'])}")
    print(f"Files without extensions:  {stats['files_without_extensions']}")
    print(f"Duplicate files detected:  {stats['duplicate_files']}")
    print(f"Duplicate groups:          {stats['duplicate_groups']}")
    print(f"Potential duplicate savings: {format_size(stats['duplicate_savings'])}")
    print("\nBy category:")
    print(f"  {'Category':<18} {'Files':>7} {'Storage':>14}")
    print(f"  {'-' * 18} {'-' * 7} {'-' * 14}")
    for category in sorted(stats["category_counts"]):
        print(f"  {category:<18} {stats['category_counts'][category]:>7} "
              f"{format_size(stats['category_sizes'][category]):>14}")
    print("\nLargest files:")
    for path, size in stats["largest_files"]:
        print(f"  {path.name}: {format_size(size)}")
    for error in duplicate_errors:
        print(f"  Duplicate scan warning: {error}")


def show_duplicates() -> None:
    folder = prompt_folder()
    if folder is None:
        return
    try:
        groups, errors = find_duplicate_groups(folder)
    except (OSError, ValueError) as error:
        print(f"Could not find duplicates: {error}")
        return
    if not groups:
        print("No identical duplicate files were found.")
    selected = []
    for index, group in enumerate(groups, start=1):
        print(f"\nGroup {index} | {format_size(group.size)} each | "
              f"Potential savings: {format_size(group.savings)}")
        for item in group.files:
            print(f"  {item.path} | {item.modified:%Y-%m-%d %H:%M:%S}")
    if groups:
        choice = input(
            "\nEnter group/file paths to quarantine, or press Enter to keep all: "
        ).strip()
        if choice:
            try:
                indexes = {int(value.strip()) for value in choice.split(",")}
                for index in indexes:
                    if 1 <= index <= len(groups):
                        selected.extend(groups[index - 1].files[1:])
            except ValueError:
                print("Invalid selection. No files were changed.")
                return
        if selected and input(
            f"Quarantine {len(selected)} duplicate files? Type 'yes' to confirm: "
        ).strip().lower() == "yes":
            moved, move_errors = quarantine_files(folder, selected)
            record_activity(
                folder,
                "duplicate_quarantine",
                [
                    {
                        "source": str(item.path),
                        "destination": str(destination),
                        "status": "completed",
                        "error": None,
                    }
                    for item, destination in moved
                ],
                "completed" if not move_errors else "partial",
            )
            print(f"Quarantined: {len(moved)}")
            for error in move_errors:
                print(f"  {error}")
        elif selected:
            print("No duplicates were changed.")
    for error in errors:
        print(f"  Duplicate scan warning: {error}")


def _prompt_size(label: str) -> int | None:
    value = input(f"{label} size in bytes (Enter to skip): ").strip()
    if not value:
        return None
    try:
        size = int(value)
        if size < 0:
            raise ValueError
        return size
    except ValueError:
        print("Please enter a non-negative whole number.")
        return None


def search_menu() -> None:
    folder = prompt_folder()
    if folder is None:
        return
    name = input("Filename contains (Enter to skip): ").strip()
    extension = input("Extension, e.g. .pdf (Enter to skip): ").strip()
    category = input("Category, e.g. Images (Enter to skip): ").strip()
    minimum = _prompt_size("Minimum")
    maximum = _prompt_size("Maximum")
    modified = input("Modified on/after YYYY-MM-DD (Enter to skip): ").strip()
    modified_date = None
    if modified:
        try:
            modified_date = date.fromisoformat(modified)
        except ValueError:
            print("Invalid date. The date filter was skipped.")
    duplicate_only = input("Duplicates only? (y/N): ").strip().lower() == "y"
    try:
        groups = find_duplicate_groups(folder)[0] if duplicate_only else []
        results, errors = search_files(
            folder,
            SearchCriteria(
                name=name,
                extension=extension,
                category=category,
                minimum_size=minimum,
                maximum_size=maximum,
                modified_after=modified_date,
                duplicates_only=duplicate_only,
            ),
            groups,
        )
    except (OSError, ValueError) as error:
        print(f"Could not search files: {error}")
        return
    print(f"\nFound {len(results)} file(s):")
    for path in results:
        try:
            stat = path.stat()
            print(f"  {path} | {format_size(stat.st_size)} | "
                  f"{datetime.fromtimestamp(stat.st_mtime):%Y-%m-%d}")
        except OSError as error:
            print(f"  {path} | unavailable: {error}")
    for error in errors:
        print(f"  Search warning: {error}")


def show_history() -> None:
    folder = prompt_folder()
    if folder is None:
        return
    records = recent_activity(folder)
    if not records:
        print("No activity has been recorded for this folder.")
        return
    print("\nRecent activity:")
    for record in records:
        print(f"  {record.get('timestamp', 'unknown')} | "
              f"{record.get('operation', 'unknown')} | {record.get('status', 'unknown')}")
        for entry in record.get("moves", []):
            print(f"    {entry.get('source', '')} -> {entry.get('destination', '')} "
                  f"[{entry.get('status', 'unknown')}]")


def undo() -> None:
    folder = prompt_folder()
    if folder is None:
        return
    restored, errors = undo_latest(folder)
    print(f"Restored: {restored}")
    for error in errors:
        print(f"  {error}")


def main() -> None:
    try:
        while True:
            print("\nSmart CLI File Organizer")
            print("1. Organize a folder")
            print("2. Preview organization without moving files")
            print("3. View file statistics")
            print("4. Find duplicate files")
            print("5. Search files")
            print("6. View activity history")
            print("7. Undo the last organization operation")
            print("8. Exit")
            choice = input("Choose an option: ").strip()
            if choice == "1":
                organize()
            elif choice == "2":
                preview()
            elif choice == "3":
                show_statistics()
            elif choice == "4":
                show_duplicates()
            elif choice == "5":
                search_menu()
            elif choice == "6":
                show_history()
            elif choice == "7":
                undo()
            elif choice == "8":
                print("Goodbye!")
                break
            else:
                print("Please choose a number from 1 to 8.")
    except KeyboardInterrupt:
        print("\nOperation interrupted. No further files will be processed.")


if __name__ == "__main__":
    main()