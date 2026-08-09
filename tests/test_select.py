import unittest

from snapdiff.select import SelectError, select_text


class SelectTextTests(unittest.TestCase):
    """Exercise select_text / SelectError directly (pure, no I/O)."""

    def test_tag_selector(self):
        self.assertEqual(select_text("<span>9.99</span>", "span"), "9.99")

    def test_tag_selector_is_case_insensitive(self):
        # HTMLParser lowercases tag names; an uppercase selector must still match.
        self.assertEqual(select_text("<span>9.99</span>", "SPAN"), "9.99")

    def test_empty_selector_raises(self):
        with self.assertRaises(SelectError):
            select_text("<div>x</div>", "")

    def test_class_selector(self):
        self.assertEqual(select_text('<div class="price">$5</div>', ".price"), "$5")

    def test_class_selector_matches_multi_class(self):
        self.assertEqual(
            select_text('<div class="a price b">$5</div>', ".price"), "$5"
        )

    def test_id_selector(self):
        self.assertEqual(
            select_text('<span id="priceblock">$7</span>', "#priceblock"), "$7"
        )

    def test_compound_tag_class_matches_only_same_tag_and_class(self):
        html = (
            '<span class="price">A</span>'
            '<div class="price">B</div>'
            '<span class="other">C</span>'
        )
        self.assertEqual(select_text(html, "span.price"), "A")

    def test_compound_tag_id_matches_only_same_tag(self):
        html = '<div id="price">A</div><span id="price">B</span>'
        self.assertEqual(select_text(html, "div#price"), "A")

    def test_multi_class_requires_all_classes(self):
        html = '<p class="a b">both</p><p class="a">only-a</p>'
        self.assertEqual(select_text(html, ".a.b"), "both")

    def test_multiple_matches_joined_in_document_order(self):
        html = '<span class="price">1</span><span class="price">2</span>'
        self.assertEqual(select_text(html, ".price"), "1\n2")

    def test_nested_matches_capture_only_outermost(self):
        html = '<div class="box">outer<div class="box">inner</div></div>'
        result = select_text(html, ".box")
        # Only the outermost element is captured; inner text appears once.
        self.assertEqual(result.count("inner"), 1)
        self.assertEqual(result.count("outer"), 1)

    def test_entities_decoded(self):
        result = select_text('<span class="price">Tom &amp; $5</span>', ".price")
        self.assertIn("Tom & $5", result)

    def test_void_element_inside_selection(self):
        result = select_text('<div class="price">$5<br>each</div>', ".price")
        self.assertEqual(result, "$5\neach")

    def test_no_match_raises(self):
        with self.assertRaises(SelectError):
            select_text("<div>x</div>", ".price")

    def test_unsupported_selectors_raise(self):
        for selector in (
            "div span",
            "div>span",
            "[data-x]",
            ":first-child",
            "a,b",
            "*",
            "",
            "#a#b",
        ):
            with self.subTest(selector=selector):
                with self.assertRaises(SelectError):
                    select_text("<div>x</div>", selector)


if __name__ == "__main__":
    unittest.main()
