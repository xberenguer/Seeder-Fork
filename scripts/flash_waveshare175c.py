#!/usr/bin/env python3
"""Verified app-only installation for the 32 MB Waveshare 1.75C factory map.

Backs up every sector this operation can overwrite. Never writes the bootloader,
partition table, NVS, model or storage. A failed install attempts verified rollback.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import time

EXPECTED_PARTITIONS = [
    (1, 2, 0x9000, 0x32000, 'nvsfactory', 0),
    (1, 2, 0x3b000, 0xd2000, 'nvs', 0),
    (1, 0, 0x10d000, 0x2000, 'otadata', 0),
    (1, 1, 0x10f000, 0x1000, 'phy_init', 0),
    (1, 130, 0x110000, 0xf0000, 'model', 0),
    (0, 0, 0x200000, 0x600000, 'factory', 0),
    (1, 130, 0x800000, 0x800000, 'storage', 0),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def partitions(data):
    if len(data) != 4096:
        raise RuntimeError('Incomplete partition-table read; nothing written')
    rows = []
    for i in range(0, len(data), 32):
        raw = data[i:i + 32]
        if raw == b'\xff' * 32:
            if data[i:] != b'\xff' * (len(data) - i):
                raise RuntimeError('Unexpected data after partition table; nothing written')
            break
        if raw[:16] == b'\xeb\xeb' + b'\xff' * 14:
            if hashlib.md5(data[:i]).digest() != raw[16:] or data[i + 32:] != b'\xff' * (len(data) - i - 32):
                raise RuntimeError('Invalid partition-table MD5 or padding; nothing written')
            break
        if raw[:2] != b'\xaaP':
            raise RuntimeError('Unrecognized partition-table entry; nothing written')
        _, kind, sub, offset, size, label, flags = struct.unpack('<HBBII16sI', raw)
        rows.append(dict(kind=kind, subtype=sub, offset=offset, size=size,
                         label=label.rstrip(b'\0').decode('ascii'), flags=flags))
    actual = [(r['kind'], r['subtype'], r['offset'], r['size'], r['label'], r['flags']) for r in rows]
    if actual != EXPECTED_PARTITIONS:
        raise RuntimeError('Expected complete seven-entry factory application map is absent; nothing written')
    ranges = sorted((r['offset'], r['offset'] + r['size']) for r in rows)
    if any(start < 0x9000 or end > 0x2000000 or start >= end for start, end in ranges) or any(a[1] > b[0] for a, b in zip(ranges, ranges[1:])):
        raise RuntimeError('Overlapping or out-of-bounds partitions; nothing written')
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port', required=True)
    p.add_argument('--expect-mac', required=True)
    p.add_argument('--application', required=True, type=Path)
    p.add_argument('--backup-dir', required=True, type=Path)
    p.add_argument('--esptool-python', default=sys.executable)
    p.add_argument('--platformio-upload', action='store_true', help=argparse.SUPPRESS)
    if '--platformio-upload' in sys.argv:
        p.error('Use an explicit app-only installation: python3 scripts/flash_waveshare175c.py --port PORT --expect-mac MAC --application .pio/build/waveshare175c/firmware.bin --backup-dir dist/flash-backups')
    a = p.parse_args()
    app = a.application.resolve()
    if not app.is_file() or not 256 < app.stat().st_size <= 0x600000 or app.read_bytes()[0] != 0xE9:
        p.error('Expected an ESP32-S3 application image, not a merged image or archive')
    # ESP image chip id is 9 for ESP32-S3. This also rejects ESP32/C3 images.
    if struct.unpack_from('<H', app.read_bytes(), 12)[0] != 9:
        p.error('Application header is not ESP32-S3')
    a.backup_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(a.backup_dir, 0o700)
    run = a.backup_dir / time.strftime('install-%Y%m%d-%H%M%S')
    run.mkdir(mode=0o700)
    manifest = {'status': 'preflight', 'expected_mac': a.expect_mac.lower(),
                'application_sha256': sha(app), 'application_bytes': app.stat().st_size,
                'offset': 0x200000}
    def save():
        (run / 'transaction.json').write_text(json.dumps(manifest, indent=2) + '\n')
    def tool(name, *args, after='no_reset'):
        cmd = [a.esptool_python, '-m', 'esptool', '--chip', 'esp32s3', '--port', a.port,
               '--baud', '921600', '--before', 'default_reset', '--after', after, *args]
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=180)
        (run / (name + '.log')).write_text(r.stdout)
        if r.returncode:
            raise RuntimeError(f'{name} failed; see {run / (name + ".log")}')
        return r.stdout
    def check_identity(name):
        identity = tool(name, 'flash_id')
        found = re.search(r'MAC:\s*([0-9a-f:]{17})', identity, re.I)
        if not found or found[1].lower() != a.expect_mac.lower() or 'Detected flash size: 32MB' not in identity:
            raise RuntimeError('Device MAC or 32 MB flash does not match; no write authorized for this identity')
    save()
    written = False
    try:
        check_identity('identity')
        pt = run / 'partitions.bin'
        tool('read-partitions', 'read_flash', '0x8000', '0x1000', str(pt))
        table = partitions(pt.read_bytes())
        factory = [x for x in table if x['kind'] == 0 and x['subtype'] == 0 and x['label'] == 'factory']
        if len(factory) != 1 or factory[0]['offset'] != 0x200000 or factory[0]['size'] != 0x600000:
            raise RuntimeError('Expected factory application map is absent; nothing written')
        manifest['partition_sha256'] = sha(pt)
        backup = run / 'overwritten-sectors.bin'
        n = (app.stat().st_size + 4095) // 4096 * 4096
        tool('read-backup', 'read_flash', '0x200000', str(n), str(backup))
        os.chmod(backup, 0o600)
        if backup.stat().st_size != n:
            raise RuntimeError('Incomplete backup; nothing written')
        tool('verify-backup', 'verify_flash', '0x200000', str(backup))
        manifest.update(status='backup-verified', backup_sha256=sha(backup), backup_bytes=n)
        save()
        check_identity('identity-before-write')
        written = True
        tool('write-application', 'write_flash', '0x200000', str(app))
        tool('verify-application', 'verify_flash', '0x200000', str(app), after='hard_reset')
        manifest['status'] = 'application-verified-and-reset'
        save()
        print(json.dumps({'pass': True, 'transaction': str(run), **manifest}))
    except BaseException as error:
        manifest.update(status='failed', error=str(error))
        if written:
            try:
                check_identity('identity-before-rollback')
                tool('rollback-write', 'write_flash', '0x200000', str(backup))
                tool('rollback-verify', 'verify_flash', '0x200000', str(backup), after='hard_reset')
                manifest['rollback'] = 'verified-and-reset'
            except BaseException as rollback_error:
                manifest['rollback'] = 'UNVERIFIED: ' + str(rollback_error)
        save()
        raise


if __name__ == '__main__':
    main()
