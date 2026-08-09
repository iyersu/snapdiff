import unittest

from snapdiff.htmltext import html_to_text


class HtmlToTextTests(unittest.TestCase):
    """Focused tests for the pure html_to_text() reducer."""

    def test_tags_are_stripped(self):
        out = html_to_text('<p class="lead">Hello <b>brave</b> world</p>')
        self.assertNotIn("<", out)
        self.assertNotIn(">", out)
        for word in ("Hello", "brave", "world"):
            self.assertIn(word, out)

    def test_script_body_dropped(self):
        out = html_to_text("<div>Visible</div><script>var secret = 42;</script>")
        self.assertIn("Visible", out)
        self.assertNotIn("secret", out)
        self.assertNotIn("42", out)

    def test_style_body_dropped(self):
        out = html_to_text("<style>.hidden{color:red}</style><div>Shown</div>")
        self.assertIn("Shown", out)
        self.assertNotIn("color", out)
        self.assertNotIn("red", out)

    def test_entities_decode(self):
        out = html_to_text("<p>Tom &amp; Jerry &lt;3</p>")
        self.assertIn("Tom & Jerry <3", out)
        # The decoded characters are literal, not entity escapes.
        self.assertNotIn("&amp;", out)
        self.assertNotIn("&lt;", out)

    def test_markup_only_change_is_identical(self):
        # Same visible text; only class attribute and insignificant whitespace differ.
        a = html_to_text('<p class="v1">The quick brown fox</p>')
        b = html_to_text('<p class="v2">  The   quick    brown fox  </p>')
        self.assertEqual(a, b)

    def test_visible_text_change_differs(self):
        a = html_to_text("<p>The quick brown fox</p>")
        b = html_to_text("<p>The quick red fox</p>")
        self.assertNotEqual(a, b)

    def test_idempotent(self):
        html = (
            "<html><head><title>Report</title></head>"
            "<body><h1>Heading</h1><p>Para &amp; text</p>"
            "<script>ignore()</script><ul><li>One</li><li>Two</li></ul></body></html>"
        )
        once = html_to_text(html)
        twice = html_to_text(once)
        self.assertEqual(once, twice)

    def test_title_preserved(self):
        out = html_to_text(
            "<html><head><title>Page Title</title></head><body><p>Body copy</p></body></html>"
        )
        self.assertIn("Page Title", out)
        self.assertIn("Body copy", out)

    def test_block_tags_produce_line_breaks(self):
        out = html_to_text("<div>First</div><div>Second</div>")
        self.assertEqual(out.splitlines(), ["First", "Second"])

    def test_empty_and_whitespace_only(self):
        self.assertEqual(html_to_text(""), "")
        self.assertEqual(html_to_text("   \n\t  "), "")
        self.assertEqual(html_to_text("<div></div><p>  </p>"), "")


if __name__ == "__main__":
    unittest.main()
