import tempfile
import unittest
from datetime import date
from pathlib import Path

from duplicates import duplicate_savings, find_duplicate_groups, quarantine_files
from history import recent_activity, record_activity
from search import SearchCriteria, search_files
from statistics import calculate_statistics


class SmartFeatureTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def write(self, name, content=b"data"):
        path = self.folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def test_duplicate_names_and_extensions_are_detected(self):
        self.write("first.txt", b"same")
        self.write("second.bin", b"same")
        self.write("different.txt", b"other")
        groups, errors = find_duplicate_groups(self.folder)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(groups), 1)
        self.assertEqual({item.path.name for item in groups[0].files}, {"first.txt", "second.bin"})

    def test_empty_files_and_group_of_more_than_two(self):
        for name in ("a", "b", "c"):
            self.write(name, b"")
        groups, _ = find_duplicate_groups(self.folder)
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0].files), 3)
        self.assertEqual(duplicate_savings(groups), 0)

    def test_potential_savings_keep_one_copy(self):
        for name in ("a.bin", "b.bin", "c.bin"):
            self.write(name, b"12345")
        groups, _ = find_duplicate_groups(self.folder)
        self.assertEqual(duplicate_savings(groups), 10)

    def test_search_filters(self):
        target = self.write("Reports/annual.PDF", b"12345")
        self.write("Reports/notes.txt", b"1")
        results, errors = search_files(
            self.folder,
            SearchCriteria(
                name="annual",
                extension=".pdf",
                category="Documents",
                minimum_size=5,
                maximum_size=5,
                modified_after=date.today(),
            ),
        )
        self.assertEqual(errors, [])
        self.assertEqual(results, [target.resolve()])

    def test_duplicate_only_search(self):
        first = self.write("one.txt", b"same")
        self.write("two.txt", b"same")
        self.write("unique.txt", b"unique")
        groups, _ = find_duplicate_groups(self.folder)
        results, _ = search_files(
            self.folder, SearchCriteria(duplicates_only=True), groups
        )
        self.assertEqual({path.name for path in results}, {"one.txt", "two.txt"})
        self.assertIn(first.resolve(), results)

    def test_analytics_includes_largest_ten_and_duplicate_fields(self):
        for index in range(12):
            self.write(f"file{index}.txt", bytes([index]) * (index + 1))
        groups, _ = find_duplicate_groups(self.folder)
        stats = calculate_statistics(
            [path for path in self.folder.iterdir() if path.is_file()],
            duplicate_groups=groups,
        )
        self.assertEqual(stats["total_files"], 12)
        self.assertEqual(len(stats["largest_files"]), 10)
        self.assertEqual(stats["files_without_extensions"], 0)
        self.assertEqual(stats["duplicate_files"], 0)

    def test_quarantine_rechecks_file_before_move(self):
        source = self.write("original.txt", b"same")
        self.write("copy.txt", b"same")
        groups, _ = find_duplicate_groups(self.folder)
        selected = [groups[0].files[1]]
        source.write_bytes(b"changed")
        moved, errors = quarantine_files(self.folder, selected)
        self.assertEqual(moved, [])
        self.assertTrue(any("changed" in error for error in errors))
        self.assertTrue(source.exists())

    def test_activity_history_records_status(self):
        record_activity(
            self.folder,
            "search",
            [{"source": "a", "destination": "", "status": "completed", "error": None}],
        )
        records = recent_activity(self.folder)
        self.assertEqual(records[0]["operation"], "search")
        self.assertEqual(records[0]["moves"][0]["status"], "completed")


if __name__ == "__main__":
    unittest.main()
