"""Check a Hugo build's local links, resources, anchors and JSON-LD (stdlib only)."""

import argparse
import json
import sys
from html.parser import HTMLParser
from functools import lru_cache
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
        self.ids = set()
        self.canonicals = []
        self.schemas = []
        self.schema = False
        self.buffer = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "a" and attrs.get("name"):
            self.ids.add(attrs["name"])
        if tag == "a" and attrs.get("href"):
            self.refs.append(("link", attrs["href"]))
        if tag in ("img", "script", "source", "video", "audio", "iframe"):
            if attrs.get("src"):
                self.refs.append(("asset", attrs["src"]))
        if tag == "video" and attrs.get("poster"):
            self.refs.append(("asset", attrs["poster"]))
        if tag in ("img", "source") and attrs.get("srcset"):
            # Data URLs may contain commas and do not represent local files.
            if not attrs["srcset"].lstrip().startswith("data:"):
                for candidate in attrs["srcset"].split(","):
                    if candidate.strip():
                        self.refs.append(("asset", candidate.split()[0]))
        if tag == "link":
            rels = attrs.get("rel", "").split()
            if "canonical" in rels:
                self.canonicals.append(attrs.get("href", ""))
            if set(rels) & {"stylesheet", "icon", "mask-icon", "apple-touch-icon", "manifest", "preload"}:
                if attrs.get("href"):
                    self.refs.append(("asset", attrs["href"]))
        if tag == "script" and attrs.get("type") == "application/ld+json":
            self.schema = True
            self.buffer = ""

    def handle_data(self, data):
        if self.schema:
            self.buffer += data

    def handle_endtag(self, tag):
        if tag == "script" and self.schema:
            self.schema = False
            self.schemas.append(self.buffer)


def check(root):
    pages = {}
    for file in root.rglob("*.html"):
        page = Page()
        page.feed(file.read_text(encoding="utf-8"))
        pages[file] = page
    if not pages:
        return ["No HTML files found; build the site before running this check."]
    home = pages.get(root / "index.html")
    if not home or len(home.canonicals) != 1:
        return ["Home page must have exactly one canonical URL."]
    origin = urlsplit(home.canonicals[0])
    errors = set()

    @lru_cache(maxsize=None)
    def resolve_target(path):
        target = (root / unquote(path).lstrip("/")).resolve()
        if not target.is_relative_to(root):
            return target, False, False
        if target.is_dir():
            target /= "index.html"
        return target, True, target.is_file()

    for file, page in pages.items():
        relative = file.relative_to(root).as_posix()
        base = urljoin(home.canonicals[0], relative.removesuffix("index.html"))
        for schema in page.schemas:
            try:
                json.loads(schema)
            except ValueError as error:
                errors.add(f"{relative}: invalid JSON-LD: {error}")
        for kind, reference in page.refs:
            url = urlsplit(urljoin(base, reference))
            if url.scheme not in ("http", "https") or url.netloc != origin.netloc:
                continue
            target, inside, exists = resolve_target(url.path)
            if not inside:
                errors.add(f"{relative}: path escapes output directory: {reference}")
                continue
            if not exists:
                errors.add(f"{relative}: missing {kind}: {reference}")
            elif kind == "link" and url.fragment and target in pages:
                if unquote(url.fragment) not in pages[target].ids:
                    errors.add(f"{relative}: missing anchor: {reference}")
    print(f"Checked {len(pages)} HTML files: local links, assets, anchors and JSON-LD.")
    return sorted(errors)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    errors = check(args.output.resolve())
    for error in errors:
        print(error, file=sys.stderr)
    sys.exit(bool(errors))
