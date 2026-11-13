"""Local publication media guards and the repository asset boundary."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator
import test_build
from test_build import build


class MediaTests(unittest.TestCase):
    def test_media_rejects_unsafe_paths(self):
        for path in ('../secret.png', 'assets/images/publications/../../secret.png',
                     'assets/images/people/face.png', 'assets/images/publications/code.svg',
                     'assets/images/publications/%2e%2e/figure.png',
                     'assets/images/publications//figure.png'):
            with self.subTest(path=path), self.assertRaisesRegex(RuntimeError, 'Unsafe'):
                build.media_path(path)

    def test_legacy_schema_still_accepts_rows_and_new_flag_is_boolean(self):
        schema = json.loads((build.ROOT / 'schemas/pubs.schema.json').read_text())
        validator = Draft202012Validator(schema)
        pub = dict(key='sample_2026', title='Title', authors='Author', venue='Venue',
                   year=2026, group='conference', lab=False)
        self.assertFalse(list(validator.iter_errors([pub])))
        pub['research_example'] = True
        pub['highlight'] = True
        pub['show_lab'] = True
        self.assertFalse(list(validator.iter_errors([pub])))
        pub['show_lab'] = False
        self.assertFalse(list(validator.iter_errors([pub])))
        pub['research_example'] = 'true'
        self.assertTrue(list(validator.iter_errors([pub])))
        pub['research_example'] = True
        pub['show_lab'] = 'false'
        self.assertTrue(list(validator.iter_errors([pub])))

    def test_legacy_show_is_a_boolean_alias_and_unknown_fields_stay_rejected(self):
        schema = json.loads((build.ROOT / 'schemas/pubs.schema.json').read_text())
        validator = Draft202012Validator(schema)
        self.assertIs(schema['items']['additionalProperties'], False)
        base = dict(key='sample_2026', title='Title', authors='Author', venue='Venue',
                    year=2026, group='conference', lab=False)

        only_show = dict(base, show=False)
        self.assertFalse(list(validator.iter_errors([only_show])))
        both = dict(base, show=True, show_lab=False)
        self.assertFalse(list(validator.iter_errors([both])))
        bad_show = dict(base, show='false')
        self.assertTrue(list(validator.iter_errors([bad_show])))
        unknown = dict(base, visible=True)
        self.assertTrue(any('Additional properties' in e.message for e in validator.iter_errors([unknown])))

        node = shutil.which('node')
        self.assertIsNotNone(node)
        script = """
import { shownOnResearch } from './assets/js/common.js';
const cases = [
  [{ group: 'conference', show: false, show_lab: true }, true],
  [{ group: 'conference', show: true, show_lab: false }, false],
  [{ group: 'conference', show: true }, true],
  [{ group: 'conference', show: false }, false],
  [{ group: 'thesis', show: true }, false],
  [{ group: 'submission', show: true }, true],
  [{ group: 'conference' }, true],
  [{ group: 'submission' }, false],
];
const bad = cases.filter(([pub, expected]) => shownOnResearch(pub) !== expected);
if (bad.length) {
  console.error(JSON.stringify(bad));
  process.exit(1);
}
"""
        run = subprocess.run([node, '--input-type=module', '-e', script],
                             cwd=build.ROOT, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)


class MediaArtifactTests(test_build.ArtifactTests):
    # Reuse the isolated build fixture, without rerunning its inherited test cases.
    test_build_preserves_bytes_and_publishes_only_site_files = None
    test_failed_build_keeps_previous_output = None

    def test_repo_image_is_staged_before_validation_and_private_files_excluded(self):
        media = self.root / build.MEDIA_PREFIX / 'hoak/figure.webp'
        media.parent.mkdir(parents=True)
        media.write_bytes(b'figure')
        (self.source.parent / 'PRIVATE.txt').write_text('never public')
        pub = dict(key='sample_2026', title='Title', authors='Author', venue='Venue', year=2026,
                   group='conference', lab=False, research_example=True,
                   image='https://iris-research-lab.github.io/' + build.MEDIA_PREFIX + 'hoak/figure.webp')
        (self.source / 'pubs.json').write_text(json.dumps([pub]))
        build.build(self.source)
        output = self.root / '_site'
        self.assertEqual((output / build.MEDIA_PREFIX / 'hoak/figure.webp').read_bytes(), b'figure')
        self.assertFalse((output / 'PRIVATE.txt').exists())
        media.unlink()
        import subprocess
        with self.assertRaises(subprocess.CalledProcessError):
            # Capture expected validator annotations, which should not mark CI failed.
            run = subprocess.run
            with patch.object(build.subprocess, 'run', side_effect=lambda *a, **k: run(*a, **k, capture_output=True)):
                build.build(self.source)
        self.assertEqual((output / build.MEDIA_PREFIX / 'hoak/figure.webp').read_bytes(), b'figure')

    def test_local_file_symlinks_fail(self):
        source = self.root / build.MEDIA_PREFIX
        source.mkdir(parents=True)
        (source / 'link.png').symlink_to(self.source / 'pubs.json')
        with self.assertRaisesRegex(RuntimeError, 'Symlink'):
            build.build(self.source)

    def test_local_directory_symlinks_fail(self):
        for relative in ('assets/images/publications', 'assets/images', 'assets'):
            with self.subTest(relative=relative):
                source = self.root / relative
                if source.exists():
                    shutil.rmtree(source)
                source.parent.mkdir(parents=True, exist_ok=True)
                source.symlink_to(self.source, target_is_directory=True)
                with self.assertRaisesRegex(RuntimeError, 'Symlink'):
                    build.build(self.source)
                source.unlink()

    def test_oversized_unsafe_and_nonregular_repo_media_fail(self):
        source = self.root / build.MEDIA_PREFIX
        source.mkdir(parents=True)
        for name, content, message in (
            ('big.png', b'x' * (build.MAX_MEDIA_BYTES + 1), '2 MiB'),
            ('code.svg', b'<svg/>', 'Unsafe'),
        ):
            path = source / name
            path.write_bytes(content)
            with self.assertRaisesRegex(RuntimeError, message):
                build.build(self.source)
            path.unlink()
        import os
        pipe = source / 'pipe.png'
        os.mkfifo(pipe)
        with self.assertRaisesRegex(RuntimeError, 'Unsupported'):
            build.build(self.source)
