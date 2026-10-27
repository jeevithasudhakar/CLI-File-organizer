"""Interactive command-line interface for Smart CLI File Organizer."""

from pathlib import Path

from history import record_operation, undo_latest
from organizer import MovePlan, create_plan, execute_plan, scan_folder
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
    if result.moved:
        record_operation(folder, [(item.source, item.destination) for item in result.moved])
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
        stats = calculate_statistics(scan_folder(folder))
    except (OSError, ValueError) as error:
        print(f"Could not calculate statistics: {error}")
        return
    print(f"\nTotal files: {stats['total_files']}")
    print(f"Total storage: {format_size(stats['total_size'])}")
    print("\nBy category:")
    for category in sorted(stats["category_counts"]):
        print(f"  {category}: {stats['category_counts'][category]} files, "
              f"{format_size(stats['category_sizes'][category])}")
    print("\nLargest files:")
    for path, size in stats["largest_files"]:
        print(f"  {path.name}: {format_size(size)}")


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
            print("4. Undo the most recent organization")
            print("5. Exit")
            choice = input("Choose an option: ").strip()
            if choice == "1":
                organize()
            elif choice == "2":
                preview()
            elif choice == "3":
                show_statistics()
            elif choice == "4":
                undo()
            elif choice == "5":
                print("Goodbye!")
                break
            else:
                print("Please choose a number from 1 to 5.")
    except KeyboardInterrupt:
        print("\nOperation interrupted. No further files will be processed.")


if __name__ == "__main__":
    main()