"""Publication import contracts and the source-media artifact boundary."""
import base64
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator
import test_build
from test_build import build


class MediaTests(unittest.TestCase):
    def test_private_json_and_media_share_resolved_revision(self):
        sha = 'b' * 40
        path = build.MEDIA_PREFIX + 'hoak/figure.webp'
        tree = {'tree': [{'path': path, 'type': 'blob', 'mode': '100644', 'size': 6, 'sha': 'c' * 40}]}
        responses = [json.dumps({'sha': sha}).encode()] + [b'[]'] * 4 + [json.dumps(tree).encode(), json.dumps({'encoding': 'base64', 'content': base64.b64encode(b'figure').decode()}).encode()]
        with tempfile.TemporaryDirectory() as tmp, patch.dict('os.environ', {'IRIS_UPDATES_TOKEN': 'test-only'}):
            stage = Path(tmp)
            data = stage / 'data'
            data.mkdir()
            with patch.object(build, 'download', side_effect=responses) as fetch:
                revision = build.prepare_data(data)
                build.prepare_media(stage, revision=revision)
            self.assertEqual((stage / path).read_bytes(), b'figure')
            urls = [c.args[0] for c in fetch.call_args_list]
            self.assertIn(f'/git/trees/{sha}?recursive=1', urls[-2])
            self.assertTrue(all(f'?ref={sha}' in u for u in urls[1:5]))
            self.assertEqual(urls[-1], f"{build.REPO}/git/blobs/{'c' * 40}")

    def test_media_rejects_unsafe_paths_collisions_and_oversized_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp)
            for path in ('../secret.png', 'assets/images/publications/../../secret.png',
                         'assets/images/people/face.png', 'assets/images/publications/code.svg',
                         'assets/images/publications/%2e%2e/figure.png'):
                with self.subTest(path=path), self.assertRaisesRegex(RuntimeError, 'Unsafe'):
                    build.write_media(stage, path, b'figure')
            path = build.MEDIA_PREFIX + 'figure.webp'
            build.write_media(stage, path, b'figure')
            with self.assertRaisesRegex(RuntimeError, 'collides'):
                build.write_media(stage, path, b'new')
            with self.assertRaisesRegex(RuntimeError, '2 MiB'):
                build.write_media(stage, build.MEDIA_PREFIX + 'big.png', b'x' * (build.MAX_MEDIA_BYTES + 1))
            with patch.object(build, 'urlopen', return_value=io.BytesIO(b'x' * 11)):
                with self.assertRaisesRegex(RuntimeError, 'exceeds'):
                    build.download('https://example.com/figure.png', max_bytes=10)

    def test_remote_symlinks_and_truncated_tree_fail(self):
        path = build.MEDIA_PREFIX + 'link.png'
        for tree in ({'tree': [], 'truncated': True},
                     {'tree': [{'path': path, 'type': 'blob', 'mode': '120000', 'size': 6}]}):
            with tempfile.TemporaryDirectory() as tmp, patch.object(build, 'download', return_value=json.dumps(tree).encode()):
                with self.assertRaises(RuntimeError):
                    build.prepare_media(Path(tmp), revision=('b' * 40, 'test-only'))

    def test_published_media_fetches_only_missing_own_origin_images_without_token(self):
        path = build.MEDIA_PREFIX + 'hoak/figure.webp'
        pubs = [{'image': 'https://iris-research-lab.github.io/' + path},
                {'image': 'https://hoak.me/external.png'}]
        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp)
            (stage / 'data').mkdir()
            (stage / 'data/pubs.json').write_text(json.dumps(pubs))
            with patch.object(build, 'download', return_value=b'figure') as fetch:
                build.prepare_media(stage, published=True)
            self.assertEqual(fetch.call_count, 1)
            self.assertEqual(fetch.call_args.args, ('https://iris-research-lab.github.io/' + path,))
            self.assertNotIn('token', fetch.call_args.kwargs)
            with patch.object(build, 'download') as fetch:
                build.prepare_media(stage, published=True)
            fetch.assert_not_called()

    def test_legacy_schema_still_accepts_rows_and_new_flag_is_boolean(self):
        schema = json.loads((build.ROOT / 'schemas/pubs.schema.json').read_text())
        validator = Draft202012Validator(schema)
        pub = dict(key='sample_2026', title='Title', authors='Author', venue='Venue',
                   year=2026, group='conference', lab=False)
        self.assertFalse(list(validator.iter_errors([pub])))
        pub['research_example'] = True
        pub['highlight'] = True
        pub['show'] = True
        self.assertFalse(list(validator.iter_errors([pub])))
        pub['show'] = False
        self.assertFalse(list(validator.iter_errors([pub])))
        pub['research_example'] = 'true'
        self.assertTrue(list(validator.iter_errors([pub])))
        pub['research_example'] = True
        pub['show'] = 'false'
        self.assertTrue(list(validator.iter_errors([pub])))


class MediaArtifactTests(test_build.ArtifactTests):
    # Reuse the isolated build fixture, without rerunning its inherited test cases.
    test_build_preserves_bytes_and_publishes_only_site_files = None
    test_failed_build_keeps_previous_output = None

    def test_source_only_image_is_staged_before_validation_and_private_files_excluded(self):
        media = self.source.parent / build.MEDIA_PREFIX / 'hoak/figure.webp'
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

    def test_local_symlinks_fail(self):
        source = self.source.parent / build.MEDIA_PREFIX
        source.mkdir(parents=True)
        (source / 'link.png').symlink_to(self.source / 'pubs.json')
        with self.assertRaisesRegex(RuntimeError, 'Symlink'):
            build.build(self.source)
