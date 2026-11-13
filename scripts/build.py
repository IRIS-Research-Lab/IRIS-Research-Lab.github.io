#!/usr/bin/env python3
"""Build _site offline from validated repository-owned content and assets."""
import argparse
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
FILES = ("news.json", "people.json", "pubs.json", "research.json")
# The gallery catalog always belongs to this checkout, including with --data-dir.
LAB_MEDIA = "lab_media.json"
MEDIA_PREFIX = "assets/images/publications/"
MAX_MEDIA_BYTES = 2 * 1024 * 1024
STATIC_DIRS = ("assets", "partials", "people", "photos", "publications", "research", "join", "schemas")


def prepare_data(destination, local=None):
    """Copy only the four public JSON files; an override never supplies assets."""
    source = local if local is not None else ROOT / "data"
    for name in FILES:
        shutil.copyfile(source / name, destination / name)
    print(f"Content source: {source.resolve()}", flush=True)


def media_path(path):
    """Only publish regular raster publication figures at safe repository paths."""
    pure = PurePosixPath(path)
    if (pure.is_absolute() or '..' in pure.parts or str(pure) != path
            or not re.fullmatch(r'[a-zA-Z0-9_./-]+', path)
            or not path.startswith(MEDIA_PREFIX)
            or pure.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.webp', '.gif'}):
        raise RuntimeError(f"Unsafe publication media path: {path}")
    return pure


def validate_publication_media():
    """Check repo-owned publication figures before copytree can follow symlinks."""
    source = ROOT / MEDIA_PREFIX
    for directory in (source, source.parent, source.parent.parent):
        if directory.is_symlink():
            raise RuntimeError(f"Symlink media directory: {directory}")
    if not source.exists():
        return
    for path in sorted(source.rglob('*')):
        if path.is_symlink():
            raise RuntimeError(f"Symlink publication media: {path}")
        if path.is_dir():
            continue
        relative = path.relative_to(ROOT).as_posix()
        media_path(relative)
        if not stat.S_ISREG(path.stat().st_mode):
            raise RuntimeError(f"Unsupported publication media entry: {relative}")
        if path.stat().st_size > MAX_MEDIA_BYTES:
            raise RuntimeError(f"Publication media exceeds 2 MiB: {relative}")


def publish_lab_media(destination):
    """Copy this repo's gallery catalog into the staged /data directory."""
    source = ROOT / "data" / LAB_MEDIA
    if not source.is_file():
        raise RuntimeError(
            f"Missing {source}. List lab photos and videos in data/{LAB_MEDIA} in this repository."
        )
    target = destination / LAB_MEDIA
    if target.exists():
        raise RuntimeError(f"Refusing to overwrite staged {LAB_MEDIA}")
    shutil.copyfile(source, target)


def build(local=None):
    # Stage and validate everything before replacing any prior local build.
    with tempfile.TemporaryDirectory(prefix=".iris-site-", dir=ROOT) as temporary:
        staging = Path(temporary) / "site"
        data = staging / "data"
        data.mkdir(parents=True)
        prepare_data(data, local)
        publish_lab_media(data)
        validate_publication_media()
        for name in STATIC_DIRS:
            shutil.copytree(ROOT / name, staging / name)
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
    parser.add_argument("--data-dir", type=Path,
                        help="Override the four content JSON files only (default: data/); assets and lab_media stay local")
    args = parser.parse_args()
    try:
        build(args.data_dir)
    except (RuntimeError, OSError, ValueError, KeyError, subprocess.CalledProcessError) as e:
        print(f"Build failed: {e}\nNo new site was published. Fix the local content and retry.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
