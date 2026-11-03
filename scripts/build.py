#!/usr/bin/env python3
"""Build _site with validated content from the private IRIS-Updates repository."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
REPO = "https://api.github.com/repos/IRIS-Research-Lab/IRIS-Updates"
PUBLISHED = "https://iris-research-lab.github.io/data"
FILES = ("news.json", "people.json", "pubs.json", "research.json")
STATIC_DIRS = ("assets", "partials", "people", "publications", "research", "join", "schemas")


def download(url, token=None, raw=False):
    headers = {"Accept": "application/vnd.github.raw+json" if raw else "application/vnd.github+json",
               "User-Agent": "iris-lab-site-build"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urlopen(Request(url, headers=headers), timeout=30) as response:
            return response.read()
    except HTTPError as e:
        raise RuntimeError(f"Cannot fetch {url} (HTTP {e.code}). Check source access and IRIS_UPDATES_TOKEN.") from None
    except (URLError, TimeoutError) as e:
        raise RuntimeError(f"Cannot reach data source {url}: {e}") from None


def prepare_data(destination, local=None, published=False):
    if local:
        for name in FILES:
            shutil.copyfile(local / name, destination / name)
        print(f"Content source: {local.resolve()}", flush=True)
        return
    if published:
        # PR validation only: no private-repository credential is exposed to PR code.
        base, token = PUBLISHED, None
        print("Content source: public deployed snapshot (PR validation only)", flush=True)
    else:
        token = os.environ.get("IRIS_UPDATES_TOKEN")
        if not token:
            raise RuntimeError("IRIS_UPDATES_TOKEN is required to read private IRIS-Updates. "
                               "Set a read-only Contents token, or use --data-dir ../IRIS-Updates/data locally.")
        # Resolve main once so all four files come from the same commit.
        sha = json.loads(download(f"{REPO}/commits/main", token))["sha"]
        if not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise RuntimeError("IRIS-Updates returned an invalid commit SHA")
        print(f"Content source: IRIS-Updates@{sha}", flush=True)
        base = f"{REPO}/contents/data"
    for name in FILES:
        url = f"{base}/{name}" if published else f"{base}/{name}?ref={sha}"
        (destination / name).write_bytes(download(url, token, raw=not published))


def build(local=None, published=False):
    # Stage and validate everything before replacing any prior local build.
    with tempfile.TemporaryDirectory(prefix="iris-site-") as temporary:
        staging = Path(temporary) / "site"
        data = staging / "data"
        data.mkdir(parents=True)
        prepare_data(data, local, published)
        subprocess.run([sys.executable, str(ROOT / "scripts/validate.py"), "--data-dir", str(data)], check=True)
        for name in STATIC_DIRS:
            shutil.copytree(ROOT / name, staging / name)
        for page in ROOT.glob("*.html"):
            shutil.copyfile(page, staging / page.name)
        shutil.copyfile(ROOT / ".nojekyll", staging / ".nojekyll")
        output = ROOT / "_site"
        if output.exists():
            shutil.rmtree(output)
        shutil.copytree(staging, output)
    print("Built _site/ (existing /data/*.json URLs preserved).")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--data-dir", type=Path, help="Use an IRIS-Updates data checkout for local preview")
    source.add_argument("--published", action="store_true", help="Validate the public snapshot without secrets (PRs only)")
    args = parser.parse_args()
    try:
        build(args.data_dir, args.published)
    except (RuntimeError, OSError, ValueError, KeyError, subprocess.CalledProcessError) as e:
        print(f"Build failed: {e}\nNo new site was published. Fix the source/access and retry.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
