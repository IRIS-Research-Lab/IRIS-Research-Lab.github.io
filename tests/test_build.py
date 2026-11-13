"""Offline source ownership, staged failure handling, and the public boundary."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("build", Path(__file__).resolve().parents[1] / "scripts/build.py")
build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build)
ROOT = build.ROOT


class SourceTests(unittest.TestCase):
    def test_default_copies_exact_repository_json_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            build.prepare_data(Path(tmp))
            self.assertEqual({p.name for p in Path(tmp).iterdir()}, set(build.FILES))
            for name in build.FILES:
                self.assertEqual((Path(tmp) / name).read_bytes(), (ROOT / 'data' / name).read_bytes())


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "lab"
        self.root.mkdir()
        for name in build.STATIC_DIRS:
            if name == "schemas":
                shutil.copytree(ROOT / name, self.root / name)
            else:
                (self.root / name).mkdir()
        shutil.copytree(ROOT / "scripts", self.root / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
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
            with patch.object(build.subprocess, "run", side_effect=lambda *a, **k: run_validator(*a, **k, capture_output=True)):
                with self.assertRaises(subprocess.CalledProcessError):
                    build.build(self.source)
            self.assertEqual(output.read_bytes(), before)
        (self.source / "people.json").unlink()
        with self.assertRaises(FileNotFoundError):
            build.build(self.source)
        self.assertEqual(output.read_bytes(), before)


class OfflineProcessTests(unittest.TestCase):
    """Run the real CLI and validator child with network denied in both processes."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'website'
        self.root.mkdir()
        for name in (*build.STATIC_DIRS, 'data', 'scripts'):
            shutil.copytree(ROOT / name, self.root / name, ignore=shutil.ignore_patterns('__pycache__'))
        for path in (*ROOT.glob('*.html'), ROOT / '.nojekyll'):
            shutil.copyfile(path, self.root / path.name)
        for name in ('.env', 'PRIVATE.txt', 'private.key'):
            (self.root / name).write_text('OFFLINE-TEST-PRIVATE-SENTINEL')
        for name in ('.git', '.github', 'tests', 'docs'):
            (self.root / name).mkdir(exist_ok=True)
            (self.root / name / 'private.txt').write_text('OFFLINE-TEST-PRIVATE-SENTINEL')
        self.guard = self.base / 'guard'
        self.guard.mkdir()
        self.log = self.base / 'network-guard.log'
        (self.guard / 'sitecustomize.py').write_text('''import os, sys
from pathlib import Path
log = Path(os.environ['OFFLINE_GUARD_LOG'])
with log.open('a') as f:
    f.write('guard pid=' + str(os.getpid()) + ' token_absent=' + str('IRIS_UPDATES_TOKEN' not in os.environ) + '\\n')
def audit(event, args):
    if event.startswith('socket.') or event == 'urllib.Request':
        with log.open('a') as f:
            f.write('DENIED ' + event + '\\n')
        raise RuntimeError('Network is forbidden in an offline build')
sys.addaudithook(audit)
''')
        self.env = dict(os.environ, PYTHONPATH=str(self.guard), OFFLINE_GUARD_LOG=str(self.log))
        self.env.pop('IRIS_UPDATES_TOKEN', None)

    def run_build(self, *args):
        return subprocess.run([sys.executable, str(self.root / 'scripts/build.py'), *args],
                              cwd=self.root, env=self.env, capture_output=True, text=True)

    def hashes(self):
        return {str(p.relative_to(self.root / '_site')): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (self.root / '_site').rglob('*') if p.is_file()}

    def test_real_default_build_and_validator_are_offline_and_emit_all_references(self):
        result = self.run_build()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('All data files are valid', result.stdout)
        log = self.log.read_text().splitlines()
        self.assertEqual(len(log), 2, log)  # script and its real validator child
        self.assertTrue(all('token_absent=True' in line for line in log), log)
        self.assertEqual(len({line.split()[1] for line in log}), 2)
        output = self.root / '_site'
        self.assertEqual({p.name for p in (output / 'data').iterdir()}, {*build.FILES, build.LAB_MEDIA})
        for name in (*build.FILES, build.LAB_MEDIA):
            self.assertEqual((output / 'data' / name).read_bytes(), (self.root / 'data' / name).read_bytes())
            for item in json.loads((output / 'data' / name).read_text()):
                for field in ('image', 'photo', 'src', 'fallback', 'poster'):
                    url = item.get(field, '')
                    if url.startswith('https://iris-research-lab.github.io/'):
                        relative = url.removeprefix('https://iris-research-lab.github.io/')
                        self.assertEqual((output / relative).read_bytes(), (self.root / relative).read_bytes())
        for name in ('.git', '.github', '.env', 'private.key', 'PRIVATE.txt', 'tests', 'docs', 'scripts'):
            self.assertFalse((output / name).exists(), name)
        self.assertFalse(any(b'OFFLINE-TEST-PRIVATE-SENTINEL' in p.read_bytes()
                             for p in output.rglob('*') if p.is_file()))

    def test_json_override_cannot_import_assets_or_replace_gallery(self):
        source = self.base / 'external' / 'data'
        source.mkdir(parents=True)
        for name in build.FILES:
            shutil.copyfile(self.root / 'data' / name, source / name)
        (source / 'lab_media.json').write_text('invalid external gallery')
        relative = 'assets/images/publications/hoak/2021_domain_constraints.webp'
        impostor = source.parent / relative
        impostor.parent.mkdir(parents=True)
        impostor.write_bytes(b'external assets must not be imported')
        result = self.run_build('--data-dir', str(source))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.root / '_site' / relative).read_bytes(), (self.root / relative).read_bytes())
        self.assertEqual((self.root / '_site/data/lab_media.json').read_bytes(),
                         (self.root / 'data/lab_media.json').read_bytes())

    def test_invalid_or_missing_local_input_keeps_entire_previous_artifact(self):
        first = self.run_build()
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        before = self.hashes()
        people = self.root / 'data/people.json'
        original = people.read_bytes()
        for invalid in (b'not json', b'[{"id":"missing-fields"}]'):
            people.write_bytes(invalid)
            result = self.run_build()
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('No new site was published', result.stderr)
            self.assertEqual(before, self.hashes())
        people.unlink()
        self.assertNotEqual(self.run_build().returncode, 0)
        self.assertEqual(before, self.hashes())
        people.write_bytes(original)
        image = self.root / 'assets/images/publications/hoak/2021_domain_constraints.webp'
        image.unlink()
        result = self.run_build()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('which does not exist', result.stdout)
        self.assertEqual(before, self.hashes())

    def test_validator_defaults_to_repository_even_with_stale_output(self):
        self.assertEqual(self.run_build().returncode, 0)
        (self.root / 'data/people.json').write_text('invalid repository content')
        result = subprocess.run([sys.executable, str(self.root / 'scripts/validate.py')],
                                env=self.env, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('invalid JSON', result.stdout)


if __name__ == '__main__':
    unittest.main()
