"""Inventory and organize static/images without changing article URLs or image bytes."""

import argparse
import csv
import hashlib
import json
import re
import subprocess
import shutil
from collections import Counter
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / "static/images"
TEXT_EXTENSIONS = {".md", ".markdown", ".html", ".css", ".js", ".json", ".toml", ".yaml", ".yml", ".xml", ".svg", ".txt"}


def inventory(pages_csv):
    pages = {row["path"].casefold(): row for row in csv.DictReader(Path(pages_csv).read_text(encoding="utf-8-sig").splitlines())}
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    texts = {}
    for name in tracked:
        if not name or not (name.startswith(("content/", "layouts/", "assets/", "config/", "static/")) or name == "hugo.toml"):
            continue
        path = ROOT / name
        if path.suffix.lower() in TEXT_EXTENSIONS:
            try:
                texts[name] = path.read_bytes().decode("utf-8-sig")
            except (UnicodeDecodeError, FileNotFoundError):
                continue
    result = []
    for path in sorted(IMAGES.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(IMAGES).as_posix()
        variants = {"images/" + relative, "images/" + quote(relative), "images/" + quote(relative, safe="/")}
        refs = [name for name, text in texts.items() if any(v in text for v in variants) or "images/" + relative in re.sub(r"(?<=images/)/+", "", unquote(text))]
        owners = set()
        site = False
        unknown = []
        for name in refs:
            page = pages.get(name.casefold())
            if page and page["section"] in {"posts", "legacy", "private"}:
                # Translations share the same final permalink component.
                owners.add(unquote(urlsplit(page["permalink"]).path.rstrip("/").split("/")[-1]))
            elif name.startswith("content/posts/"):
                # Hugo omits pages with build.list=never from `hugo list`.
                slug = re.search(r'^slug:\s*[\"\']?([^\"\'\r\n]+)', texts[name], re.MULTILINE)
                owners.add(slug.group(1).strip() if slug else re.sub(r'\.(en|ja)$', '', Path(name).stem).lower())
            elif name.startswith(("layouts/", "assets/", "config/")) or name == "hugo.toml" or page:
                site = True
            else:
                unknown.append(name)
        if site:
            folder = "site"
        elif len(owners) == 1:
            folder = next(iter(owners))
        elif len(owners) > 1:
            folder = "shared"
        else:
            folder = ""
        target = "/".join(filter(None, (folder, path.name)))
        result.append({"old": relative, "new": target, "owners": sorted(owners), "site": site, "refs": refs, "unknown": unknown, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return result


def apply(rows):
    targets = [r["new"].casefold() for r in rows]
    if len(targets) != len(set(targets)):
        raise ValueError("Destination collision; inspect the report before moving files")
    mapping = {}
    for row in rows:
        if row["old"] == row["new"]:
            continue
        for old, new in ((row["old"], row["new"]), (quote(row["old"]), quote(row["new"]))):
            mapping["images/" + old] = "images/" + new
            mapping["images//" + old] = "images/" + new
    pattern = re.compile("|".join(re.escape(k) for k in sorted(mapping, key=len, reverse=True)) + r'''(?=$|[\s"'<>?#)\]}])''')
    refs = sorted({ref for r in rows for ref in r["refs"]})
    changes = []
    for ref in refs:
        path = ROOT / ref
        original = path.read_bytes()
        updated = pattern.sub(lambda m: mapping[m.group()], original.decode("utf-8"))
        if updated.encode("utf-8") != original:
            changes.append((path, updated.encode("utf-8")))
    staging = ROOT / ".image-migration-staging"
    staging.mkdir(exist_ok=False)
    for index, row in enumerate(rows):
        old = IMAGES / row["old"]
        new = IMAGES / row["new"]
        if not old.resolve().is_relative_to(IMAGES.resolve()) or not new.resolve().is_relative_to(IMAGES.resolve()):
            raise ValueError("Path outside static/images")
        if hashlib.sha256(old.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError(f"Image changed since inventory: {old}")
        if old != new:
            shutil.move(str(old), str(staging / str(index)))
    for index, row in enumerate(rows):
        if row["old"] != row["new"]:
            new = IMAGES / row["new"]
            new.parent.mkdir(parents=True, exist_ok=True)
            if new.exists():
                raise ValueError(f"Destination already exists: {new}")
            shutil.move(str(staging / str(index)), str(new))
    for path, data in changes:
        path.write_bytes(data)
    staging.rmdir()
    for directory in sorted((p for p in IMAGES.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
        if not any(directory.iterdir()):
            directory.rmdir()
    verify(rows)
    print(f"Updated {len(changes)} source files; verified all {len(rows)} image hashes.")


def verify(rows):
    actual = {p.relative_to(IMAGES).as_posix() for p in IMAGES.rglob("*") if p.is_file()}
    expected = {r["new"] for r in rows}
    if actual != expected:
        raise ValueError(f"Image inventory differs: {actual ^ expected}")
    for row in rows:
        if hashlib.sha256((IMAGES / row["new"]).read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError(f"Image bytes changed: {row['new']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pages_csv")
    parser.add_argument("report")
    parser.add_argument("--apply", action="store_true", help="Apply the generated plan after checking collisions")
    parser.add_argument("--verify", action="store_true", help="Verify image locations and hashes against an existing report")
    args = parser.parse_args()
    if args.verify:
        rows = json.loads(Path(args.report).read_text(encoding="utf-8"))
        verify(rows)
        print(f"Verified {len(rows)} files: paths and SHA-256 hashes match.")
        return
    rows = inventory(args.pages_csv)
    Path(args.report).write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"images": len(rows), "move": sum(r["old"] != r["new"] for r in rows), "groups": dict(Counter("site" if r["site"] else "article" if len(r["owners"]) == 1 else "shared" if r["owners"] else "unassigned" for r in rows)), "unknown": [r for r in rows if r["unknown"]]}, ensure_ascii=False, indent=2))
    if args.apply:
        apply(rows)


if __name__ == "__main__":
    main()
