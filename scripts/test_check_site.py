"""Regression checks for the deployment link checker."""

import tempfile
import unittest
from pathlib import Path

from check_site import check


class SiteCheckTests(unittest.TestCase):
    def scan(self, body, files=None):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as directory:
            root = Path(directory).resolve()
            (root / "index.html").write_text(
                '<link rel="canonical" href="https://zisai.com/">' + body,
                encoding="utf-8",
            )
            for name, content in (files or {}).items():
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            return check(root)

    def test_valid_encoded_link_anchor_and_external_resource(self):
        self.assertEqual(self.scan(
            '<a href="/%E6%89%BF%E5%BE%B7/#hello">Read</a>'
            '<img src="https://example.org/external.png">',
            {"承德/index.html": '<h1 id="hello">Hello</h1>'},
        ), [])

    def test_missing_resource_and_srcset_candidate(self):
        errors = self.scan('<img src="ok.png" srcset="ok.png 1x, missing.png 2x">', {"ok.png": "image"})
        self.assertEqual(len(errors), 1)
        self.assertIn("missing.png", errors[0])

    def test_invalid_schema_and_missing_anchor_fail(self):
        errors = self.scan('<a href="#absent">Read</a><script type="application/ld+json">{</script>')
        self.assertTrue(any("invalid JSON-LD" in error for error in errors))
        self.assertTrue(any("missing anchor" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
