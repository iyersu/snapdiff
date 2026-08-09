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


class CliTextFlagTests(unittest.TestCase):
    """Exercise the --text reduction path offline by patching fetch."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def _run(self, content, *extra):
        with mock.patch.object(cli, "fetch", return_value=content):
            return cli.main(["https://site.test", "--dir", self.dir, *extra])

    def test_markup_only_change_is_no_change_with_text(self):
        # Baseline saved from the text reduction of the first HTML.
        self._run('<p class="v1">Hello world</p>', "--text")
        # Second fetch differs only in markup: same visible text -> no change.
        code = self._run(
            '<p class="v2">  Hello   world  </p>', "--text", "--fail-on-change"
        )
        self.assertEqual(code, cli.EXIT_OK)

    def test_markup_only_change_is_a_change_without_text(self):
        # Without --text, the raw HTML markup difference is a real change.
        self._run('<p class="v1">Hello world</p>')
        code = self._run('<p class="v2">Hello world</p>', "--fail-on-change")
        self.assertEqual(code, cli.EXIT_CHANGED)

    def test_visible_text_change_is_a_change_with_text(self):
        self._run("<p>Hello world</p>", "--text")
        code = self._run("<p>Goodbye world</p>", "--text", "--fail-on-change")
        self.assertEqual(code, cli.EXIT_CHANGED)

    def test_text_flag_reduces_summary_and_baseline(self):
        # First run reports the first-snapshot summary and saves reduced text.
        out = _capture(lambda: self._run("<div>Alpha</div>", "--text"))
        self.assertIn("First snapshot", out)
        # Re-running identical HTML yields "No change" against the reduced baseline.
        out2 = _capture(lambda: self._run("<div>Alpha</div>", "--text"))
        self.assertIn("No change", out2)

    def test_no_save_with_text_does_not_persist(self):
        self._run("<p>Alpha</p>", "--text", "--no-save")
        # Nothing saved: next run is still a first run, so no failing change.
        code = self._run("<p>Beta</p>", "--text", "--fail-on-change")
        self.assertEqual(code, cli.EXIT_OK)


class CliRenderFlagTests(unittest.TestCase):
    """Exercise the --render fallback decision offline.

    Patches both cli.fetch and cli.render so no browser or network is used.
    """

    # Substantial real HTML whose visible text is well past MIN_VISIBLE_CHARS.
    GOOD_HTML = (
        "<html><body><p>This is a real page with plenty of visible text "
        "past the threshold.</p></body></html>"
    )
    RENDERED_HTML = (
        "<html><body><p>Fully rendered content produced by the headless "
        "browser fallback.</p></body></html>"
    )

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def test_fallback_triggers_on_empty_fetch(self):
        render_mock = mock.Mock(return_value=self.RENDERED_HTML)
        with mock.patch.object(cli, "fetch", return_value=""), \
                mock.patch.object(cli, "render", render_mock):
            code = cli.main(["https://site.test", "--dir", self.dir, "--render"])
        self.assertEqual(code, cli.EXIT_OK)
        render_mock.assert_called_once_with("https://site.test")

        # The rendered HTML became the baseline: an identical rendered re-run
        # is "No change".
        with mock.patch.object(cli, "fetch", return_value=""), \
                mock.patch.object(cli, "render", return_value=self.RENDERED_HTML):
            out = _capture(
                lambda: cli.main(
                    ["https://site.test", "--dir", self.dir, "--render",
                     "--fail-on-change"]
                )
            )
        self.assertIn("No change", out)

    def test_fallback_not_triggered_on_good_content(self):
        render_mock = mock.Mock(side_effect=AssertionError("render must not run"))
        with mock.patch.object(cli, "fetch", return_value=self.GOOD_HTML), \
                mock.patch.object(cli, "render", render_mock):
            code = cli.main(["https://site.test", "--dir", self.dir, "--render"])
        self.assertEqual(code, cli.EXIT_OK)
        render_mock.assert_not_called()

    def test_flag_off_never_renders(self):
        render_mock = mock.Mock(side_effect=AssertionError("render must not run"))
        with mock.patch.object(cli, "fetch", return_value=""), \
                mock.patch.object(cli, "render", render_mock):
            code = cli.main(["https://site.test", "--dir", self.dir])
        self.assertEqual(code, cli.EXIT_OK)
        render_mock.assert_not_called()

    def test_render_error_surfaces_as_fetch_error_code(self):
        render_mock = mock.Mock(side_effect=cli.RenderError("nope"))
        with mock.patch.object(cli, "fetch", return_value=""), \
                mock.patch.object(cli, "render", render_mock):
            code = cli.main(["https://site.test", "--dir", self.dir, "--render"])
        self.assertEqual(code, cli.EXIT_FETCH_ERROR)
        render_mock.assert_called_once_with("https://site.test")


def _capture(fn):
    import contextlib
    import io

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fn()
    return buf.getvalue()


if __name__ == "__main__":
    unittest.main()
