import unittest

from snapdiff.diff import describe_delta, diff_snapshots


class DiffSnapshotsTests(unittest.TestCase):
    def test_first_run_has_no_baseline(self):
        delta = diff_snapshots(None, "hello\nworld")
        self.assertTrue(delta.is_first_run)
        self.assertTrue(delta.changed)
        self.assertEqual(delta.added_lines, 0)
        self.assertEqual(delta.removed_lines, 0)

    def test_no_change(self):
        content = "a\nb\nc"
        delta = diff_snapshots(content, content)
        self.assertFalse(delta.is_first_run)
        self.assertFalse(delta.changed)
        self.assertEqual(delta.added_lines, 0)
        self.assertEqual(delta.removed_lines, 0)

    def test_added_lines(self):
        delta = diff_snapshots("a\nb", "a\nb\nc\nd")
        self.assertTrue(delta.changed)
        self.assertEqual(delta.added_lines, 2)
        self.assertEqual(delta.removed_lines, 0)
        self.assertIn("c", delta.added_samples)

    def test_removed_lines(self):
        delta = diff_snapshots("a\nb\nc", "a")
        self.assertTrue(delta.changed)
        self.assertEqual(delta.removed_lines, 2)
        self.assertEqual(delta.added_lines, 0)

    def test_changed_line_counts_as_add_and_remove(self):
        delta = diff_snapshots("hello world", "hello there")
        self.assertTrue(delta.changed)
        self.assertEqual(delta.added_lines, 1)
        self.assertEqual(delta.removed_lines, 1)
        self.assertTrue(delta.unified_diff)

    def test_empty_to_content(self):
        delta = diff_snapshots("", "new line")
        self.assertTrue(delta.changed)
        self.assertEqual(delta.added_lines, 1)


class DescribeDeltaTests(unittest.TestCase):
    def test_describes_first_run(self):
        text = describe_delta("http://x", diff_snapshots(None, "a"))
        self.assertIn("First snapshot", text)

    def test_describes_no_change(self):
        text = describe_delta("http://x", diff_snapshots("a", "a"))
        self.assertIn("No change", text)

    def test_describes_change_with_counts(self):
        text = describe_delta("http://x", diff_snapshots("a\nb", "a\nb\nc"))
        self.assertIn("Change detected", text)
        self.assertIn("added", text)


if __name__ == "__main__":
    unittest.main()
