import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest.mock import patch

import test_package as fixtures

COMMIT, REPO = fixtures.COMMIT, fixtures.REPO

spec = importlib.util.spec_from_file_location('publish_release', REPO / 'scripts/publish_release.py')
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


class PublishTest(unittest.TestCase):
    setUp = fixtures.PackageTest.setUp
    package = fixtures.PackageTest.package
    def test_no_publication_when_asset_missing(self):
        self.package()
        next(self.output.glob('*.bin')).unlink()
        with patch.object(publisher, 'gh') as call:
            with self.assertRaises(FileNotFoundError):
                publisher.publish(self.output, 'v2.2.0-ports.1', COMMIT)
            call.assert_not_called()

    def test_failed_or_incomplete_upload_stays_draft(self):
        self.package()
        def gh(*args):
            if args[:2] == ('release', 'view'):
                return json.dumps(dict(assets=[], isDraft=True, targetCommitish=COMMIT))
            return ''
        with patch.object(publisher, 'gh', side_effect=gh) as call, patch.object(publisher, 'check_existing_tag'):
            with self.assertRaisesRegex(ValueError, 'draft assets'):
                publisher.publish(self.output, 'v2.2.0-ports.1', COMMIT)
            self.assertFalse(any(c.args[:2] == ('release', 'edit') for c in call.call_args_list))

    def test_publishes_only_after_remote_byte_verification(self):
        self.package()
        def gh(*args):
            if args[:2] == ('release', 'view'):
                return json.dumps(dict(assets=[dict(name=p.name, size=p.stat().st_size) for p in self.output.iterdir()],
                                       isDraft=True, targetCommitish=COMMIT))
            if args[:2] == ('release', 'download'):
                destination = Path(args[args.index('--dir') + 1])
                for p in self.output.iterdir():
                    shutil.copy(p, destination)
            return ''
        with patch.object(publisher, 'gh', side_effect=gh) as call, patch.object(publisher, 'check_existing_tag'):
            publisher.publish(self.output, 'v2.2.0-ports.1', COMMIT)
            self.assertEqual(call.call_args_list[-1].args[:2], ('release', 'edit'))

    def test_rejects_remote_bytes_even_with_correct_size(self):
        self.package()
        def gh(*args):
            if args[:2] == ('release', 'view'):
                return json.dumps(dict(assets=[dict(name=p.name, size=p.stat().st_size) for p in self.output.iterdir()],
                                       isDraft=True, targetCommitish=COMMIT))
            if args[:2] == ('release', 'download'):
                destination = Path(args[args.index('--dir') + 1])
                for p in self.output.iterdir():
                    shutil.copy(p, destination)
                p = next(destination.glob('*.bin'))
                data = bytearray(p.read_bytes())
                data[20] ^= 1
                p.write_bytes(data)
            return ''
        with patch.object(publisher, 'gh', side_effect=gh) as call, patch.object(publisher, 'check_existing_tag'):
            with self.assertRaisesRegex(ValueError, 'uploaded asset bytes'):
                publisher.publish(self.output, 'v2.2.0-ports.1', COMMIT)
            self.assertFalse(any(c.args[:2] == ('release', 'edit') for c in call.call_args_list))

    def test_existing_tag_must_match_source(self):
        result = subprocess.CompletedProcess([], 0, 'HTTP/2.0 200 OK\n\n' + json.dumps(dict(object=dict(type='tag', sha='b' * 40))), '')
        with patch.dict('os.environ', GH_REPO='xberenguer/Seeder-Fork'), patch.object(publisher.subprocess, 'run', return_value=result) as lookup, patch.object(publisher, 'gh', return_value=json.dumps(dict(sha='a' * 40))) as resolve:
            with self.assertRaisesRegex(ValueError, 'different source'):
                publisher.check_existing_tag('v2.2.0-ports.1', COMMIT)
            self.assertEqual(lookup.call_args.args[0][-1], 'repos/xberenguer/Seeder-Fork/git/ref/tags/v2.2.0-ports.1')
            resolve.assert_called_once_with('api', 'repos/xberenguer/Seeder-Fork/commits/v2.2.0-ports.1')

    def test_annotated_tag_uses_resolved_commit(self):
        result = subprocess.CompletedProcess([], 0, 'HTTP/2.0 200 OK\n\n' + json.dumps(dict(object=dict(type='tag', sha='b' * 40))), '')
        with patch.dict('os.environ', GH_REPO='xberenguer/Seeder-Fork'), patch.object(publisher.subprocess, 'run', return_value=result), patch.object(publisher, 'gh', return_value=json.dumps(dict(sha=COMMIT))):
            publisher.check_existing_tag('v2.2.0-ports.1', COMMIT)

    def test_only_404_allows_new_tag(self):
        for status, allowed in [(404, True), (401, False), (403, False), (422, False), (500, False)]:
            result = subprocess.CompletedProcess([], 1, f'HTTP/2.0 {status} Error\n\n{{}}', '')
            with self.subTest(status=status), patch.dict('os.environ', GH_REPO='xberenguer/Seeder-Fork'), patch.object(publisher.subprocess, 'run', return_value=result) as lookup, patch.object(publisher, 'gh') as resolve:
                if allowed:
                    publisher.check_existing_tag('v2.2.0-ports.1', COMMIT)
                else:
                    with self.assertRaisesRegex(ValueError, 'could not verify'):
                        publisher.check_existing_tag('v2.2.0-ports.1', COMMIT)
                self.assertEqual(lookup.call_args.args[0][-1], 'repos/xberenguer/Seeder-Fork/git/ref/tags/v2.2.0-ports.1')
                resolve.assert_not_called()
