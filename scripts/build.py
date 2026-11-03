#!/usr/bin/env python3
"""Build _site with validated content from the private IRIS-Updates repository."""
import argparse
import base64
import binascii
import json
import os
from pathlib import Path, PurePosixPath
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
MEDIA_PREFIX = "assets/images/publications/"
MAX_MEDIA_BYTES = 2 * 1024 * 1024
STATIC_DIRS = ("assets", "partials", "people", "publications", "research", "join", "schemas")


def download(url, token=None, raw=False, max_bytes=None):
    headers = {"Accept": "application/vnd.github.raw+json" if raw else "application/vnd.github+json",
               "User-Agent": "iris-lab-site-build"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urlopen(Request(url, headers=headers), timeout=30) as response:
            content = response.read(max_bytes + 1) if max_bytes else response.read()
            if max_bytes and len(content) > max_bytes:
                raise RuntimeError(f"Download exceeds {max_bytes} bytes: {url}")
            return content
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
        # Resolve main once so all JSON and media come from the same commit.
        sha = json.loads(download(f"{REPO}/commits/main", token))["sha"]
        if not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise RuntimeError("IRIS-Updates returned an invalid commit SHA")
        print(f"Content source: IRIS-Updates@{sha}", flush=True)
        base = f"{REPO}/contents/data"
    for name in FILES:
        url = f"{base}/{name}" if published else f"{base}/{name}?ref={sha}"
        (destination / name).write_bytes(download(url, token, raw=not published))
    return None if published else (sha, token)


def media_path(path):
    """Only publish regular raster publication figures from the source repo."""
    pure = PurePosixPath(path)
    if (pure.is_absolute() or '..' in pure.parts or str(pure) != path
            or not re.fullmatch(r'[a-zA-Z0-9_./-]+', path)
            or not path.startswith(MEDIA_PREFIX)
            or pure.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.webp', '.gif'}):
        raise RuntimeError(f"Unsafe publication media path: {path}")
    return pure


def write_media(staging, path, content):
    media_path(path)
    if len(content) > MAX_MEDIA_BYTES:
        raise RuntimeError(f"Publication media exceeds 2 MiB: {path}")
    target = staging / path
    if target.exists():
        raise RuntimeError(f"Source media collides with website asset: {path}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)


def prepare_media(staging, local=None, published=False, revision=None):
    if local:
        source = local.resolve().parent / MEDIA_PREFIX
        for directory in (source, source.parent, source.parent.parent):
            if directory.is_symlink():
                raise RuntimeError(f"Symlink media directory: {directory}")
        if source.exists():
            for path in sorted(source.rglob('*')):
                if path.is_symlink():
                    raise RuntimeError(f"Symlink publication media: {path}")
                if path.is_file():
                    write_media(staging, MEDIA_PREFIX + path.relative_to(source).as_posix(), path.read_bytes())
        return
    if published:
        # PRs fetch only referenced public figures on our own origin, never hoak.me.
        pubs = json.loads((staging / 'data/pubs.json').read_text())
        origin = PUBLISHED.removesuffix('/data') + '/'
        paths = {p['image'][len(origin):] for p in pubs
                 if p.get('image', '').startswith(origin)}
        for path in sorted(paths):
            media_path(path)
            if not (staging / path).is_file():
                write_media(staging, path, download(origin + path, max_bytes=MAX_MEDIA_BYTES))
        return
    sha, token = revision
    tree = json.loads(download(f"{REPO}/git/trees/{sha}?recursive=1", token))
    if tree.get('truncated'):
        raise RuntimeError('IRIS-Updates media tree was truncated')
    for entry in tree['tree']:
        path = entry['path']
        if not path.startswith(MEDIA_PREFIX) or entry['type'] == 'tree':
            continue
        media_path(path)
        if entry.get('mode') != '100644' or entry['type'] != 'blob':
            raise RuntimeError(f"Unsupported publication media entry: {path}")
        if entry.get('size', MAX_MEDIA_BYTES + 1) > MAX_MEDIA_BYTES:
            raise RuntimeError(f"Publication media exceeds 2 MiB: {path}")
        blob_sha = entry['sha']
        if not re.fullmatch(r'[0-9a-f]{40}', blob_sha):
            raise RuntimeError(f"Invalid publication blob SHA: {path}")
        blob = json.loads(download(f"{REPO}/git/blobs/{blob_sha}", token, max_bytes=MAX_MEDIA_BYTES * 2))
        if blob.get('encoding') != 'base64':
            raise RuntimeError(f"Unsupported publication blob encoding: {path}")
        try:
            content = base64.b64decode(''.join(blob['content'].split()), validate=True)
        except binascii.Error:
            raise RuntimeError(f"Invalid publication blob content: {path}") from None
        write_media(staging, path, content)


def build(local=None, published=False):
    # Stage and validate everything before replacing any prior local build.
    with tempfile.TemporaryDirectory(prefix="iris-site-") as temporary:
        staging = Path(temporary) / "site"
        data = staging / "data"
        data.mkdir(parents=True)
        revision = prepare_data(data, local, published)
        for name in STATIC_DIRS:
            shutil.copytree(ROOT / name, staging / name)
        prepare_media(staging, local, published, revision)
        subprocess.run([sys.executable, str(ROOT / "scripts/validate.py"), "--data-dir", str(data),
                        "--asset-root", str(staging)], check=True)
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
