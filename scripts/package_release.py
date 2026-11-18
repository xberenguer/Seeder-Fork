#!/usr/bin/env python3
"""Package checked CI outputs for the two fork boards; never rebuild or flash.

Run after downloading the seeder-sticks3 and seeder-waveshare175c Actions
artifacts into separate directories. The manifest is consumed by the website's
release updater; device versions come from platformio.ini, not the bundle tag.
"""
import argparse
import configparser
import hashlib
import json
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[1]
STICK_PARTITIONS = [
    (1, 2, 0x9000, 0x5000, 'nvs', 0),
    (1, 0, 0xE000, 0x2000, 'otadata', 0),
    (0, 16, 0x10000, 0x330000, 'app0', 0),
]
WAVE_PARTITIONS = [
    (1, 2, 0x9000, 0x32000, 'nvsfactory', 0),
    (1, 2, 0x3B000, 0xD2000, 'nvs', 0),
    (1, 0, 0x10D000, 0x2000, 'otadata', 0),
    (1, 1, 0x10F000, 0x1000, 'phy_init', 0),
    (1, 130, 0x110000, 0xF0000, 'model', 0),
    (0, 0, 0x200000, 0x600000, 'factory', 0),
    (1, 130, 0x800000, 0x800000, 'storage', 0),
]


def image(data, flash_bytes, name):
    """Validate identity, flash geometry, segment checksum and appended digest."""
    if len(data) < 24 or data[0] != 0xE9 or not 1 <= data[1] <= 16:
        raise ValueError(f'{name}: invalid ESP image')
    if struct.unpack_from('<H', data, 12)[0] != 9:
        raise ValueError(f'{name}: expected ESP32-S3')
    flash_code = {8 * 1024**2: 3, 32 * 1024**2: 5}[flash_bytes]
    if data[2] != 2 or data[3] != (flash_code << 4 | 15):
        raise ValueError(f'{name}: expected DIO / 80MHz / board flash size')
    pos, checksum = 24, 0xEF
    for _ in range(data[1]):
        if pos + 8 > len(data):
            raise ValueError(f'{name}: truncated segment header')
        length = struct.unpack_from('<I', data, pos + 4)[0]
        pos += 8
        if pos + length > len(data):
            raise ValueError(f'{name}: truncated segment')
        for byte in data[pos:pos + length]:
            checksum ^= byte
        pos += length
    end = pos + (15 - pos % 16) + 1
    if end > len(data) or data[end - 1] != checksum or data[23] != 1:
        raise ValueError(f'{name}: invalid checksum or missing image digest')
    if len(data) != end + 32 or data[end:] != hashlib.sha256(data[:end]).digest():
        raise ValueError(f'{name}: invalid image SHA-256 or trailing bytes')


def check_table(data):
    if len(data) != 4096:
        raise ValueError('StickS3 partition table must be 4096 bytes')
    actual = []
    for offset in range(0, len(data), 32):
        row = data[offset:offset + 32]
        if row[:16] == b'\xeb\xeb' + b'\xff' * 14:
            if row[16:] != hashlib.md5(data[:offset]).digest():
                raise ValueError('invalid partition MD5')
            if data[offset + 32:] != b'\xff' * (len(data) - offset - 32):
                raise ValueError('partition trailing data')
            if actual != STICK_PARTITIONS:
                raise ValueError('unexpected StickS3 partition contract')
            return
        if row[:2] != b'\xaaP':
            raise ValueError('missing partition MD5 / invalid entry')
        _, kind, sub, start, size, label, flags = struct.unpack('<HBBII16sI', row)
        actual.append((kind, sub, start, size, label.rstrip(b'\0').decode('ascii'), flags))
    raise ValueError('missing partition MD5')


def partition_objects(rows):
    return [dict(zip(('type', 'subtype', 'offset', 'size', 'label', 'flags'), row)) for row in rows]


def check_source_map(root, device, expected):
    """Reject source partition changes until explicitly reviewed for the updater."""
    types = {'data': 1, 'app': 0}
    subtypes = {'nvs': 2, 'ota': 0, 'ota_0': 16, 'factory': 0, 'phy': 1, 'spiffs': 130}
    actual = []
    for line in (root / 'partitions' / f'{device}.csv').read_text().splitlines():
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        label, kind, sub, offset, size, flags = [p.strip() for p in line.split(',')]
        actual.append((types[kind], subtypes[sub], int(offset, 0), int(size, 0), label, int(flags or '0', 0)))
    if actual != expected:
        raise ValueError(f'{device}: source partition contract changed')


def stick_splash(root):
    source = (root / 'src/Lib/images.h').read_text()
    match = re.search(r'\bseeder_logo\s*\[[^]]+\][^=]*=\s*\{(.*?)\};', source, re.S)
    if match is None:
        raise ValueError('StickS3 source splash array missing')
    body = re.sub(r'//[^\n]*', '', match[1])
    words = [int(word, 16) for word in re.findall(r'0x[0-9a-fA-F]+', body)]
    if len(words) != 200 * 88:
        raise ValueError('StickS3 source splash dimensions changed')
    return struct.pack('<' + 'H' * len(words), *words)


def package(root, artifacts, output, tag, commit):
    if not re.fullmatch(r'v\d+\.\d+\.\d+-ports\.[1-9]\d*', tag):
        raise ValueError('release tag must be vX.Y.Z-ports.N')
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('commit must be a full lowercase Git SHA')
    config = configparser.ConfigParser(inline_comment_prefixes=(';', '#'))
    config.read(root / 'platformio.ini')
    manifest = dict(schemaVersion=1, project='seeder', repository='xberenguer/Seeder-Fork',
                    tag=tag, commit=commit, releases=[])
    files_to_write = {}
    for device, rows, flash_bytes in [('sticks3', STICK_PARTITIONS, 8 * 1024**2),
                                       ('waveshare175c', WAVE_PARTITIONS, 32 * 1024**2)]:
        check_source_map(root, device, rows)
        version = config[f'env:{device}']['custom_version']
        suffix = 'sticks3' if device == 'sticks3' else 'ws175c'
        if not re.fullmatch(r'\d+\.\d+\.\d+-' + suffix + r'\.\d+', version):
            raise ValueError(f'{device}: invalid committed device version')
        if version.split('-')[0] != tag[1:].split('-')[0]:
            raise ValueError('bundle and device base versions differ')
        directory = artifacts / f'seeder-{device}'
        app = (directory / f'seeder-{device}-firmware.bin').read_bytes()
        image(app, flash_bytes, device)
        footer = f'V{version}  {commit[:7]}'.encode() + b'\0'
        if footer not in app:
            raise ValueError(f'{device}: expected version/source footer absent from application')
        if device == 'sticks3' and stick_splash(root) not in app:
            raise ValueError('StickS3 compiled splash differs from the corrected source bitmap')
        if len(app) > (0x330000 if device == 'sticks3' else 0x600000):
            raise ValueError(f'{device}: application exceeds partition')
        if device == 'sticks3':
            name = f'seeder-sticks3-{version}-merged.bin'
            data = (directory / 'seeder-sticks3-merged.bin').read_bytes()
            boot = (directory / 'seeder-sticks3-bootloader.bin').read_bytes()
            table = (directory / 'seeder-sticks3-partitions.bin').read_bytes()
            ota = (directory / 'seeder-sticks3-boot_app0.bin').read_bytes()
            image(boot, flash_bytes, 'StickS3 bootloader')
            check_table(table)
            if len(ota) != 8192:
                raise ValueError('StickS3 OTA image must be 8192 bytes')
            segments = [(0, boot, 'bootloader'), (0x8000, table, 'partitions'),
                        (0xE000, ota, 'ota'), (0x10000, app, 'application')]
            if len(boot) > 0x8000 or len(data) != 0x10000 + len(app):
                raise ValueError('invalid merged image length')
            previous_end = 0
            for offset, chunk, _ in segments:
                if not chunk or data[offset:offset + len(chunk)] != chunk:
                    raise ValueError('merged image differs from checked build inputs')
                if data[previous_end:offset] != b'\xff' * (offset - previous_end):
                    raise ValueError('merged image contains non-erased gaps')
                previous_end = offset + len(chunk)
        else:
            name = f'seeder-waveshare175c-{version}.bin'
            data = app
            segments = [(0x200000, app, 'application')]
        files_to_write[name] = data
        manifest['releases'].append(dict(
            device=device, version=version, chip='esp32s3', flashBytes=flash_bytes,
            status='CI validated release',
            qualification='Published release: automated calculation, UI, workflow and image checks passed. '
                          'This exact CI artifact has not been physically qualified; hardware checks are separate.',
            files=[dict(id=name, url=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())],
            parts=[dict(file=name, sourceOffset=offset if device == 'sticks3' else 0,
                        length=0x8000 if kind == 'bootloader' else len(chunk),
                        address=offset, kind=kind) for offset, chunk, kind in segments],
            partitions=partition_objects(rows)))
    manifest_data = (json.dumps(manifest, indent=2) + '\n').encode()
    files_to_write['flasher-release.json'] = manifest_data
    sums = ''.join(f'{hashlib.sha256(data).hexdigest()}  {name}\n' for name, data in sorted(files_to_write.items()))
    if output.exists() and any(output.iterdir()):
        raise ValueError('release output directory must be empty')
    output.mkdir(parents=True, exist_ok=True)
    for name, data in files_to_write.items():
        (output / name).write_bytes(data)
    (output / 'SHA256SUMS').write_text(sums)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--commit', required=True)
    args = parser.parse_args()
    package(ROOT, args.artifacts, args.output, args.tag, args.commit)
