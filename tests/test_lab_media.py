"""Lab gallery catalog, privacy of published images, and the local optimizer."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("optimize_lab_media", ROOT / "scripts" / "optimize_lab_media.py")
optimize_lab_media = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(optimize_lab_media)

import test_build


def jpeg_size(data):
    if data[:2] != b"\xff\xd8":
        raise AssertionError("not a JPEG")
    i = 2
    while i + 4 < len(data):
        if data[i] != 0xFF:
            raise AssertionError(f"JPEG marker desync at {i}")
        while data[i] == 0xFF:
            i += 1
        marker = data[i]
        i += 1
        if marker in (0xD8, 0xD9):
            continue
        if marker == 0xDA:
            break
        if i + 2 > len(data):
            break
        length = int.from_bytes(data[i:i + 2], "big")
        if marker in (0xE1, 0xE2, 0xED, 0xFE) or 0xE1 <= marker <= 0xEF:
            raise AssertionError(f"JPEG metadata marker {marker:#x}")
        if marker in range(0xC0, 0xD0) and marker not in (0xC4, 0xC8, 0xCC):
            height = int.from_bytes(data[i + 3:i + 5], "big")
            width = int.from_bytes(data[i + 5:i + 7], "big")
            return width, height
        i += length
    raise AssertionError("JPEG has no frame header")


def webp_size(data):
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise AssertionError("not a WebP")
    i = 12
    size = None
    while i + 8 <= len(data):
        name = data[i:i + 4]
        chunk = int.from_bytes(data[i + 4:i + 8], "little")
        if name in (b"EXIF", b"XMP "):
            raise AssertionError(f"WebP metadata chunk {name!r}")
        payload = data[i + 8:i + 8 + chunk]
        if name == b"VP8 " and payload[3:6] == b"\x9d\x01\x2a":
            size = (int.from_bytes(payload[6:8], "little") & 0x3FFF,
                    int.from_bytes(payload[8:10], "little") & 0x3FFF)
        elif name == b"VP8X" and len(payload) >= 10:
            size = (1 + int.from_bytes(payload[4:7], "little"),
                    1 + int.from_bytes(payload[7:10], "little"))
        i += 8 + chunk + (chunk & 1)
    if size is None:
        raise AssertionError("WebP has no dimension chunk")
    return size


class LabMediaTests(unittest.TestCase):
    def test_catalog_validates_and_published_images_are_small_and_clean(self):
        catalog = json.loads((ROOT / "data" / "lab_media.json").read_text())
        schema = json.loads((ROOT / "schemas" / "lab_media.schema.json").read_text())
        validator = Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
        self.assertFalse(list(validator.iter_errors(catalog)))
        self.assertTrue(catalog)
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            for name in ("news.json", "people.json", "pubs.json", "research.json"):
                (data / name).write_text("[]\n")
            (data / "lab_media.json").write_text(json.dumps(catalog))
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "validate.py"), "--data-dir", str(data)],
                capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        for item in catalog:
            for field in ("src", "fallback", "poster"):
                url = item.get(field)
                if not url:
                    continue
                relative = url.split("https://iris-research-lab.github.io/", 1)[1]
                path = ROOT / relative
                raw = path.read_bytes()
                self.assertLessEqual(path.stat().st_size, 2 * 1024 * 1024, path)
                self.assertNotIn(b"Exif\x00\x00", raw)
                self.assertNotIn(b"http://ns.adobe.com/xap/1.0/", raw)
                self.assertNotIn(b"iPhone", raw)
                if path.suffix.lower() == ".webp":
                    width, height = webp_size(raw)
                else:
                    width, height = jpeg_size(raw)
                self.assertLessEqual(width, 1600, path)
                self.assertEqual((width, height), (item["width"], item["height"]))

    def test_schema_requires_image_fallback_and_video_poster(self):
        schema = json.loads((ROOT / "schemas" / "lab_media.schema.json").read_text())
        validator = Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
        image = {
            "id": "2026-12-01-lunch",
            "type": "image",
            "src": "https://iris-research-lab.github.io/assets/media/lab/2026-12-01/lunch.webp",
            "alt": "Lunch",
        }
        self.assertTrue(list(validator.iter_errors([image])))
        image["fallback"] = "https://iris-research-lab.github.io/assets/media/lab/2026-12-01/lunch.jpg"
        self.assertFalse(list(validator.iter_errors([image])))
        video = {
            "id": "2026-12-01-clip",
            "type": "video",
            "src": "https://iris-research-lab.github.io/assets/media/lab/2026-12-01/clip.mp4",
            "alt": "A clip",
        }
        self.assertTrue(list(validator.iter_errors([video])))
        video["poster"] = "https://iris-research-lab.github.io/assets/media/lab/2026-12-01/clip-poster.jpg"
        self.assertFalse(list(validator.iter_errors([video])))

    def test_duplicate_media_id_fails_validation(self):
        item = json.loads((ROOT / "data" / "lab_media.json").read_text())[0]
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            for name in ("news.json", "people.json", "pubs.json", "research.json"):
                (data / name).write_text("[]\n")
            (data / "lab_media.json").write_text(json.dumps([item, dict(item, caption="again")]))
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "validate.py"), "--data-dir", str(data)],
                capture_output=True, text=True, check=False)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("duplicate", proc.stdout)

    def test_missing_lab_media_catalog_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "site"
            root.mkdir()
            dest = Path(tmp) / "out"
            dest.mkdir()
            with patch.object(test_build.build, "ROOT", root):
                with self.assertRaisesRegex(RuntimeError, "lab_media.json"):
                    test_build.build.publish_lab_media(dest)

    def test_optimizer_strips_metadata_and_respects_orientation(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow is not installed")
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            source = tmp / "original.jpg"
            wide = Image.new("RGB", (4000, 1000), (20, 90, 40))
            exif = Image.Exif()
            exif[270] = "PRIVACY-SENTINEL-do-not-publish"
            exif[305] = "iPhone 17 Pro"
            wide.save(source, format="JPEG", quality=85, exif=exif.tobytes())
            before = source.read_bytes()
            stem = tmp / "out" / "frame"
            result = optimize_lab_media.optimize(source, stem, max_width=1600)
            self.assertEqual(source.read_bytes(), before)
            self.assertEqual((result["width"], result["height"]), (1600, 400))
            for path in (result["webp"], result["jpeg"]):
                raw = path.read_bytes()
                self.assertNotIn(b"PRIVACY-SENTINEL-do-not-publish", raw)
                self.assertNotIn(b"iPhone", raw)
                self.assertNotIn(b"Exif\x00\x00", raw)
            turned = Image.new("RGB", (80, 40), (200, 10, 10))
            turned_exif = Image.Exif()
            turned_exif[274] = 6
            portrait = tmp / "portrait.jpg"
            turned.save(portrait, format="JPEG", quality=85, exif=turned_exif.tobytes())
            rotated = optimize_lab_media.optimize(portrait, tmp / "rotated", max_width=1600)
            self.assertEqual((rotated["width"], rotated["height"]), (40, 80))


if __name__ == "__main__":
    unittest.main()
