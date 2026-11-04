#!/usr/bin/env python3
"""Build a privacy-safe Lab gallery image.

Reads an original (it is not modified) and writes OUTPUT.webp plus OUTPUT.jpg.
The results are at most 1600px wide, and EXIF, GPS, and XMP are left behind.
Prints a data/lab_media.json object to paste.

    python3 scripts/optimize_lab_media.py original.jpg assets/media/lab/2026-12-01/lunch

Pillow is required (`pip install pillow`). Videos are not handled here; see
CONTRIBUTING.md for the ffmpeg command.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://iris-research-lab.github.io/"
DEFAULT_MAX_WIDTH = 1600
JPEG_QUALITY = 88
WEBP_QUALITY = 82


def public_url(path):
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(ROOT)
    except ValueError:
        relative = path
    return SITE + relative.as_posix()


def assert_clean(path, size):
    """Fail if a saved gallery image kept metadata or the wrong dimensions."""
    raw = path.read_bytes()
    if b"Exif\x00\x00" in raw or b"http://ns.adobe.com/xap/1.0/" in raw:
        raise RuntimeError(f"Metadata remained in {path}")
    if path.suffix.lower() == ".webp" and (b"EXIF" in raw[12:64] or b"XMP " in raw[12:64]):
        raise RuntimeError(f"WebP metadata chunk remained in {path}")
    from PIL import Image

    with Image.open(path) as saved:
        saved.load()
        if saved.size != size:
            raise RuntimeError(f"{path} is {saved.size}, expected {size}")
        if saved.getexif():
            raise RuntimeError(f"EXIF remained in {path}")
        if saved.info.get("exif") or saved.info.get("xmp") or saved.info.get("icc_profile"):
            raise RuntimeError(f"Embedded metadata remained in {path}")


def optimize(source, stem, max_width=DEFAULT_MAX_WIDTH, jpeg_quality=JPEG_QUALITY, webp_quality=WEBP_QUALITY):
    """Write stem.webp and stem.jpg. Returns their paths and pixel size."""
    from PIL import Image, ImageOps

    source = Path(source)
    stem = Path(stem)
    if source.resolve() in {stem.with_suffix(".webp").resolve(), stem.with_suffix(".jpg").resolve()}:
        raise RuntimeError(f"Refusing to overwrite the original: {source}")
    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened)
        image = image.convert("RGB")
        if image.width > max_width:
            height = round(image.height * max_width / image.width)
            image = image.resize((max_width, height), Image.Resampling.LANCZOS)
        stem.parent.mkdir(parents=True, exist_ok=True)
        webp = stem.with_suffix(".webp")
        jpeg = stem.with_suffix(".jpg")
        image.save(webp, format="WEBP", quality=webp_quality, method=6, exif=b"")
        image.save(
            jpeg, format="JPEG", quality=jpeg_quality, optimize=True, progressive=True, exif=b""
        )
        size = image.size
    assert_clean(webp, size)
    assert_clean(jpeg, size)
    return {"webp": webp, "jpeg": jpeg, "width": size[0], "height": size[1]}


def catalog_object(stem, size):
    parent = stem.parent.name
    item_id = f"{parent}-{stem.name}" if len(parent) == 10 and parent[4] == "-" and parent[7] == "-" else stem.name
    webp = stem.with_suffix(".webp")
    jpeg = stem.with_suffix(".jpg")
    return {
        "id": item_id,
        "type": "image",
        "date": parent if item_id.startswith(parent) else None,
        "src": public_url(webp),
        "fallback": public_url(jpeg),
        "width": size[0],
        "height": size[1],
        "alt": "Describe this photo.",
        "caption": "",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Original image. This file is only read.")
    parser.add_argument("stem", type=Path, help="Output path without an extension")
    parser.add_argument("--max-width", type=int, default=DEFAULT_MAX_WIDTH)
    args = parser.parse_args(argv)
    if args.max_width < 1:
        parser.error("--max-width must be positive")
    try:
        result = optimize(args.source, args.stem, max_width=args.max_width)
    except ImportError:
        print("Pillow is required: pip install pillow", file=sys.stderr)
        return 1
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Could not optimize {args.source}: {exc}", file=sys.stderr)
        return 1
    webp, jpeg = result["webp"], result["jpeg"]
    print(f"Wrote {webp} ({webp.stat().st_size} bytes) and {jpeg} ({jpeg.stat().st_size} bytes)")
    print(f"Size: {result['width']}x{result['height']}. Metadata stripped. Original unchanged.")
    item = catalog_object(args.stem, (result["width"], result["height"]))
    if not item["date"]:
        item.pop("date")
    if not item.get("caption"):
        item.pop("caption", None)
    print("Paste into data/lab_media.json and replace alt (caption is optional):")
    print(json.dumps(item, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
