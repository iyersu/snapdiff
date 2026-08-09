import tempfile
import unittest
from unittest import mock

from snapdiff import cli


class CliExitCodeTests(unittest.TestCase):
    """Exercise cli.main() offline by patching the fetch transport."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def _run(self, content, *extra):
        with mock.patch.object(cli, "fetch", return_value=content):
            return cli.main(["https://site.test", "--dir", self.dir, *extra])

    def test_first_run_exits_ok(self):
        self.assertEqual(self._run("a\nb"), cli.EXIT_OK)

    def test_no_change_exits_ok(self):
        self._run("a\nb")
        self.assertEqual(self._run("a\nb"), cli.EXIT_OK)

    def test_change_exits_ok_without_flag(self):
        self._run("a\nb")
        self.assertEqual(self._run("a\nb\nc"), cli.EXIT_OK)

    def test_fail_on_change_returns_changed_code(self):
        self._run("a\nb")
        self.assertEqual(self._run("a\nb\nc", "--fail-on-change"), cli.EXIT_CHANGED)

    def test_fail_on_change_ignores_first_run(self):
        self.assertEqual(self._run("a\nb", "--fail-on-change"), cli.EXIT_OK)

    def test_fail_on_change_ok_when_unchanged(self):
        self._run("a\nb")
        self.assertEqual(self._run("a\nb", "--fail-on-change"), cli.EXIT_OK)

    def test_fetch_error_returns_error_code(self):
        with mock.patch.object(cli, "fetch", side_effect=cli.FetchError("boom")):
            code = cli.main(["https://site.test", "--dir", self.dir])
        self.assertEqual(code, cli.EXIT_FETCH_ERROR)

    def test_no_save_does_not_persist_baseline(self):
        self._run("a\nb", "--no-save")
        # Still a first run on the next call, since nothing was saved.
        self.assertEqual(self._run("a\nb\nc", "--fail-on-change"), cli.EXIT_OK)


if __name__ == "__main__":
    unittest.main()
