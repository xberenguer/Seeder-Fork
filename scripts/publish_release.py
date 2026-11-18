#!/usr/bin/env python3
"""Publish one complete draft only after both checked board artifacts exist.

Uses the GitHub Actions GITHUB_TOKEN through gh. Existing releases are never
edited/reused: a failed draft remains for inspection and requires a new tag or
explicit operator cleanup. A failure before the final edit cannot expose a
partially uploaded public release.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


def gh(*args):
    return subprocess.check_output(['gh', *args], text=True).strip()


def validate_assets(directory, tag, commit):
    if not re.fullmatch(r'v\d+\.\d+\.\d+-ports\.[1-9]\d*', tag) or not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('invalid release tag or commit')
    manifest = json.loads((directory / 'flasher-release.json').read_text())
    if manifest['tag'] != tag or manifest['commit'] != commit:
        raise ValueError('manifest tag/source mismatch')
    if {r['device'] for r in manifest['releases']} != {'sticks3', 'waveshare175c'} or len(manifest['releases']) != 2:
        raise ValueError('complete two-board release required')
    names = {'flasher-release.json', 'SHA256SUMS'}
    for release in manifest['releases']:
        for entry in release['files']:
            name = entry['url']
            if name != Path(name).name or name in names:
                raise ValueError('invalid or duplicate asset name')
            data = (directory / name).read_bytes()
            if len(data) != entry['bytes'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
                raise ValueError('asset hash/size mismatch')
            names.add(name)
    if {p.name for p in directory.iterdir()} != names:
        raise ValueError('unexpected or missing release assets')
    sums = {}
    for line in (directory / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ')
        if name in sums or name not in names - {'SHA256SUMS'}:
            raise ValueError('unexpected checksum entry')
        sums[name] = digest
    if set(sums) != names - {'SHA256SUMS'}:
        raise ValueError('incomplete checksums')
    for name, digest in sums.items():
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != digest:
            raise ValueError('checksum mismatch')
    return {name: (directory / name).stat().st_size for name in sorted(names)}


def check_existing_tag(tag, commit):
    """An existing tag must already resolve to the exact checked source."""
    repo = os.environ.get('GH_REPO', os.environ.get('GITHUB_REPOSITORY', ''))
    if repo != 'xberenguer/Seeder-Fork':
        raise ValueError('release publication is restricted to xberenguer/Seeder-Fork')
    # The commits endpoint responds 422 for an unknown name. The Git refs
    # endpoint has an unambiguous 404 for an absent tag; only that means we may
    # create a new tag. Resolve existing refs separately to support annotated
    # tags without confusing their tag-object SHA with the source commit SHA.
    result = subprocess.run(['gh', 'api', '--include', f'repos/{repo}/git/ref/tags/{tag}'],
                            text=True, capture_output=True)
    headers, _, _ = result.stdout.replace('\r\n', '\n').partition('\n\n')
    if result.returncode:
        if re.search(r'^HTTP/\S+ 404\b', headers):
            return  # Creating a new release tag at --target is permitted.
        raise ValueError('could not verify release tag; refusing publication')
    resolved = json.loads(gh('api', f'repos/{repo}/commits/{tag}'))
    if resolved['sha'] != commit:
        raise ValueError('existing release tag points to different source')


def publish(directory, tag, commit):
    expected = validate_assets(directory, tag, commit)
    check_existing_tag(tag, commit)
    notes = ('Seeder fork release for M5Stack StickS3 and Waveshare AMOLED 1.75C.\n\n'
             f'Source commit: `{commit}`. The asset `flasher-release.json` records each board version, '
             'SHA-256 and flash contract. Automated checks passed; these exact CI binaries do not '
             'inherit physical qualification from previous local builds.\n\n'
             'StickS3 uses a merged image at 0x0. Waveshare uses application-only at 0x200000, '
             'preserving its factory bootloader and partition table.\n\n'
             'Original Seeder by BitMaker, from an idea by Lunaticoin. MIT license and credits retained.\n')
    gh('release', 'create', tag, '--draft', '--target', commit, '--title', f'Seeder {tag}',
       '--notes', notes, *[str(directory / name) for name in expected])
    remote = json.loads(gh('release', 'view', tag, '--json', 'assets,isDraft,targetCommitish'))
    actual = {asset['name']: asset['size'] for asset in remote['assets']}
    if not remote['isDraft'] or remote['targetCommitish'] != commit or actual != expected:
        raise ValueError('draft assets/source differ; draft left unpublished')
    # Download each uploaded asset before publication: size checks alone cannot
    # detect an upload corruption. Use the authenticated asset URL through gh.
    import tempfile
    with tempfile.TemporaryDirectory(prefix='seeder-release-verify-') as temporary:
        gh('release', 'download', tag, '--dir', temporary)
        for name in expected:
            if (Path(temporary) / name).read_bytes() != (directory / name).read_bytes():
                raise ValueError('uploaded asset bytes differ; draft left unpublished')
    gh('release', 'edit', tag, '--draft=false', '--latest')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', required=True, type=Path)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--commit', required=True)
    args = parser.parse_args()
    publish(args.directory, args.tag, args.commit)
