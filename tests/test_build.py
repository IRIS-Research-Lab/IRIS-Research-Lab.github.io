"""Check source consistency, failure handling, and the public artifact boundary."""
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

SPEC = importlib.util.spec_from_file_location("build", Path(__file__).resolve().parents[1] / "scripts/build.py")
build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build)


class SourceTests(unittest.TestCase):
    def test_private_fetch_uses_one_commit_for_every_file(self):
        sha = "a" * 40
        with tempfile.TemporaryDirectory() as tmp, patch.dict("os.environ", {"IRIS_UPDATES_TOKEN": "test-only"}):
            with patch.object(build, "download", side_effect=[json.dumps({"sha": sha}).encode()] + [b"[]\n"] * 4) as fetch:
                build.prepare_data(Path(tmp))
            urls = [call.args[0] for call in fetch.call_args_list]
            self.assertEqual(urls[0], f"{build.REPO}/commits/main")
            self.assertTrue(all(url.endswith(f"?ref={sha}") for url in urls[1:]))
            self.assertEqual({p.name for p in Path(tmp).iterdir()}, set(build.FILES))

    def test_missing_token_fails_without_public_fallback(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict("os.environ", {}, clear=True):
            with patch.object(build, "download") as fetch, self.assertRaisesRegex(RuntimeError, "IRIS_UPDATES_TOKEN is required"):
                build.prepare_data(Path(tmp))
            fetch.assert_not_called()

    def test_public_validation_never_sends_private_token(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict("os.environ", {"IRIS_UPDATES_TOKEN": "test-only"}):
            with patch.object(build, "urlopen", side_effect=lambda *a, **k: io.BytesIO(b"[]")) as fetch:
                build.prepare_data(Path(tmp), published=True)
            for call in fetch.call_args_list:
                self.assertIsNone(call.args[0].get_header("Authorization"))
                self.assertTrue(call.args[0].full_url.startswith(build.PUBLISHED))

    def test_unreachable_source_reports_actionable_error(self):
        for error in (URLError("offline"), HTTPError(build.REPO, 404, "Not Found", {}, None)):
            with self.subTest(error=error), patch.object(build, "urlopen", side_effect=error):
                with self.assertRaisesRegex(RuntimeError, "Cannot (reach|fetch)"):
                    build.download(build.REPO, "test-only")


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "lab"
        self.root.mkdir()
        for name in build.STATIC_DIRS:
            if name == "schemas":
                shutil.copytree(build.ROOT / name, self.root / name)
            else:
                (self.root / name).mkdir()
        shutil.copytree(build.ROOT / "scripts", self.root / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
        (self.root / "index.html").write_text("<h1>IRIS</h1>")
        (self.root / ".nojekyll").touch()
        (self.root / ".env").write_text("PRIVATE=not-for-publishing")
        (self.root / ".git").mkdir()
        self.source = Path(self.tmp.name) / "source"
        self.source.mkdir()
        for name in build.FILES:
            (self.source / name).write_bytes(b"[]\n")
        lab_media = self.root / "data"
        lab_media.mkdir()
        (lab_media / "lab_media.json").write_bytes(b"[]\n")
        self.root_patch = patch.object(build, "ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def test_build_preserves_bytes_and_publishes_only_site_files(self):
        build.build(self.source)
        output = self.root / "_site"
        for name in build.FILES:
            self.assertEqual((output / "data" / name).read_bytes(), b"[]\n")
        self.assertEqual((output / "data" / "lab_media.json").read_bytes(), b"[]\n")
        self.assertEqual((output / "index.html").read_text(), "<h1>IRIS</h1>")
        for name in (".git", ".env", "scripts", "tests", ".github"):
            self.assertFalse((output / name).exists())

    def test_failed_build_keeps_previous_output(self):
        build.build(self.source)
        output = self.root / "_site" / "index.html"
        before = output.read_bytes()
        for invalid in (b"not json", b'[{"id":"missing-required-fields"}]'):
            (self.source / "people.json").write_bytes(invalid)
            run_validator = subprocess.run
            # Expected validation failures should not create CI error annotations.
            with patch.object(build.subprocess, "run", side_effect=lambda *a, **k: run_validator(*a, **k, capture_output=True)):
                with self.assertRaises(subprocess.CalledProcessError):
                    build.build(self.source)
            self.assertEqual(output.read_bytes(), before)
        (self.source / "people.json").unlink()
        with self.assertRaises(FileNotFoundError):
            build.build(self.source)
        self.assertEqual(output.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
