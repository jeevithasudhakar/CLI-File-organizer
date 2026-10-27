import tempfile
import unittest
from pathlib import Path

from categories import classify_file
from history import record_operation, undo_latest
from organizer import MovePlan, create_plan, execute_plan, scan_folder
from statistics import calculate_statistics


class OrganizerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def write(self, name, content="data"):
        path = self.folder / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_categories_and_case_insensitivity(self):
        self.assertEqual(classify_file(Path("photo.PNG")), "Images")
        self.assertEqual(classify_file(Path("notes")), "Other")

    def test_dry_run_plan_does_not_move_files(self):
        source = self.write("photo.jpg")
        plan = create_plan(self.folder)
        self.assertEqual(plan[0].source, source.resolve())
        self.assertTrue(source.exists())
        self.assertFalse((self.folder / "Images" / "photo.jpg").exists())

    def test_successful_move(self):
        self.write("report.pdf")
        result = execute_plan(create_plan(self.folder))
        self.assertEqual(len(result.moved), 1)
        self.assertTrue((self.folder / "Documents" / "report.pdf").exists())

    def test_duplicate_filename_never_overwrites(self):
        self.write("photo.jpg", "new")
        (self.folder / "Images").mkdir()
        (self.folder / "Images" / "photo.jpg").write_text("old", encoding="utf-8")
        result = execute_plan(create_plan(self.folder))
        self.assertEqual(len(result.moved), 1)
        self.assertEqual((self.folder / "Images" / "photo.jpg").read_text(), "old")
        self.assertEqual((self.folder / "Images" / "photo (1).jpg").read_text(), "new")

    def test_invalid_folder(self):
        with self.assertRaises(ValueError):
            scan_folder(self.folder / "missing")

    def test_statistics(self):
        self.write("a.txt", "123")
        self.write("b.png", "12345")
        stats = calculate_statistics(scan_folder(self.folder))
        self.assertEqual(stats["total_files"], 2)
        self.assertEqual(stats["total_size"], 8)
        self.assertEqual(stats["category_counts"]["Documents"], 1)
        self.assertEqual(stats["category_counts"]["Images"], 1)

    def test_undo_restores_moved_file(self):
        source = self.write("song.mp3")
        result = execute_plan(create_plan(self.folder))
        destination = result.moved[0].destination
        record_operation(self.folder, [(source, destination)])
        restored, errors = undo_latest(self.folder)
        self.assertEqual((restored, errors), (1, []))
        self.assertTrue(source.exists())
        self.assertFalse(destination.exists())

    def test_plan_destinations_stay_inside_selected_folder(self):
        self.write("script.py")
        for plan in create_plan(self.folder):
            self.assertTrue(plan.destination.resolve().is_relative_to(self.folder.resolve()))

    def test_execute_rejects_destination_outside_selected_folder(self):
        source = self.write("safe.txt")
        outside = self.folder.parent / "not-allowed.txt"
        result = execute_plan([MovePlan(source, outside, "Other")])
        self.assertEqual(len(result.errors), 1)
        self.assertTrue(source.exists())
        self.assertFalse(outside.exists())


if __name__ == "__main__":
    unittest.main()
