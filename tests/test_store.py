import tempfile
import unittest
from pathlib import Path

from snapdiff.store import SnapshotStore


class SnapshotStoreTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.store = SnapshotStore(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_load_missing_returns_none(self):
        self.assertIsNone(self.store.load("http://example.com"))

    def test_save_then_load_roundtrip(self):
        self.store.save("http://example.com", "hello")
        self.assertEqual(self.store.load("http://example.com"), "hello")

    def test_save_overwrites_baseline(self):
        self.store.save("http://example.com", "v1")
        self.store.save("http://example.com", "v2")
        self.assertEqual(self.store.load("http://example.com"), "v2")

    def test_distinct_urls_do_not_collide(self):
        self.store.save("http://a.com", "a-content")
        self.store.save("http://b.com", "b-content")
        self.assertEqual(self.store.load("http://a.com"), "a-content")
        self.assertEqual(self.store.load("http://b.com"), "b-content")

    def test_writes_metadata_file(self):
        self.store.save("http://example.com", "hello")
        metas = list(Path(self._tmp.name).glob("*.meta.json"))
        self.assertEqual(len(metas), 1)

    def test_unicode_content_roundtrips(self):
        self.store.save("http://example.com", "héllo — wörld ✓")
        self.assertEqual(self.store.load("http://example.com"), "héllo — wörld ✓")


if __name__ == "__main__":
    unittest.main()
