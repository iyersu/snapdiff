import unittest

from snapdiff.fetch import FetchError, fetch


class FetchSchemeTests(unittest.TestCase):
    """Offline tests for input validation. Never makes a real request."""

    def test_rejects_non_http_scheme(self):
        with self.assertRaises(FetchError):
            fetch("ftp://example.com/file")

    def test_rejects_empty_string(self):
        with self.assertRaises(FetchError):
            fetch("")

    def test_rejects_bare_hostname(self):
        with self.assertRaises(FetchError):
            fetch("example.com")


if __name__ == "__main__":
    unittest.main()
