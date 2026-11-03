#!/usr/bin/env python3
"""Validate the lab's data files. Run locally with:

    pip install jsonschema
    python scripts/validate.py

The same check runs on every pull request (.github/workflows/validate.yml).
"""
import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://iris-research-lab.github.io/"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--data-dir", type=Path, default=ROOT / "_site" / "data",
                    help="Directory containing the four content files (default: _site/data)")
DATA = parser.parse_args().data_dir

# data file -> (schema file, field that must be unique)
FILES = {
    "pubs.json": ("pubs.schema.json", "key"),
    "people.json": ("people.schema.json", "id"),
    "news.json": ("news.schema.json", None),
    "research.json": ("research.schema.json", "id"),
}

errors = []


def err(file, msg):
    errors.append(f"data/{file}: {msg}")


def where(path):
    return "".join(f"[{p}]" if isinstance(p, int) else f".{p}" for p in path) or "(top level)"


def check_local_image(file, i, field, url):
    """Images hosted on this site must exist in the repo."""
    if url and url.startswith(SITE):
        local = ROOT / url[len(SITE):]
        if not local.is_file():
            err(file, f"[{i}].{field}: {url} points to {local.relative_to(ROOT)}, which does not exist")


for name, (schema_name, unique) in FILES.items():
    try:
        data = json.loads((DATA / name).read_text(encoding="utf-8"))
    except OSError as e:
        err(name, f"cannot read {DATA / name}: {e}. Run scripts/build.py first.")
        continue
    except json.JSONDecodeError as e:
        err(name, f"invalid JSON at line {e.lineno}, column {e.colno}: {e.msg}")
        continue
    schema = json.loads((ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
    for e in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        err(name, f"{where(e.path)}: {e.message}")

    if not isinstance(data, list):
        continue
    if unique:
        seen = {}
        for i, item in enumerate(data):
            v = item.get(unique) if isinstance(item, dict) else None
            if v is None:
                continue
            if v in seen:
                err(name, f"[{i}].{unique}: duplicate '{v}' (also at [{seen[v]}])")
            seen[v] = i
    for i, item in enumerate(data):
        if isinstance(item, dict):
            for field in ("image", "photo"):
                check_local_image(name, i, field, item.get(field))

if errors:
    print(f"Found {len(errors)} problem(s):\n")
    for e in errors:
        print(f"  ✗ {e}")
        # GitHub Actions annotation so errors show on the PR's Files tab
        print(f"::error::{e}")
    sys.exit(1)

print("✓ All data files are valid.")
