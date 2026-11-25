"""Release assembly tests use synthetic ESP images, never private seed data."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('package_release', REPO / 'scripts/package_release.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)
COMMIT = '1234567890abcdef1234567890abcdef12345678'


def image(payload, flash_code):
    header = bytearray(24)
    header[0:4] = bytes([0xE9, 1, 2, flash_code << 4 | 15])
    struct.pack_into('<H', header, 12, 9)
    header[23] = 1
    data = header + struct.pack('<II', 0x3F000000, len(payload)) + payload
    checksum = 0xEF
    for byte in payload:
        checksum ^= byte
    data.extend(b'\0' * (15 - len(data) % 16))
    data.append(checksum)
    return bytes(data) + hashlib.sha256(data).digest()


def table(rows, length=3072):
    data = b''.join(struct.pack('<HBBII16sI', 0x50AA, kind, sub, offset, size,
                                label.encode(), flags) for kind, sub, offset, size, label, flags in rows)
    data += b'\xeb\xeb' + b'\xff' * 14 + hashlib.md5(data).digest()
    return data + b'\xff' * (length - len(data))


class PackageTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.artifacts = self.root / 'artifacts'
        self.output = self.root / 'release'
        shutil.copy(REPO / 'platformio.ini', self.root)
        shutil.copytree(REPO / 'partitions', self.root / 'partitions')
        (self.root / 'src/Lib').mkdir(parents=True)
        shutil.copy(REPO / 'src/Lib/images.h', self.root / 'src/Lib/images.h')
        self.stick = self.artifacts / 'seeder-sticks3'
        self.wave = self.artifacts / 'seeder-waveshare175c'
        self.stick.mkdir(parents=True)
        self.wave.mkdir(parents=True)
        boot = image(b'boot', 3)
        app = image(f'V2.2.0-sticks3.4  {COMMIT[:7]}'.encode() + b'\0' + release.stick_splash(self.root), 3)
        partitions = table(release.STICK_PARTITIONS)
        ota = b'\xff' * 8192
        merged = bytearray(b'\xff' * (65536 + len(app)))
        for offset, chunk in ((0, boot), (0x8000, partitions), (0xE000, ota), (0x10000, app)):
            merged[offset:offset + len(chunk)] = chunk
        for name, data in [('bootloader', boot), ('firmware', app), ('partitions', partitions),
                           ('boot_app0', ota), ('merged', merged)]:
            (self.stick / f'seeder-sticks3-{name}.bin').write_bytes(data)
        (self.wave / 'seeder-waveshare175c-firmware.bin').write_bytes(
            image(f'V2.2.0-ws175c.11  {COMMIT[:7]}'.encode() + b'\0', 5))

    def package(self, **kwargs):
        return release.package(self.root, self.artifacts, self.output,
                               kwargs.get('tag', 'v2.2.0-ports.1'), kwargs.get('commit', COMMIT))

    def test_complete_deterministic_contract(self):
        self.assertEqual((self.stick / 'seeder-sticks3-partitions.bin').stat().st_size, 3072)
        manifest = self.package()
        a, b = manifest['releases']
        self.assertEqual(a['version'], '2.2.0-sticks3.4')
        self.assertEqual([p['address'] for p in a['parts']], [0, 32768, 57344, 65536])
        self.assertEqual([p['length'] for p in a['parts'][:3]], [32768, 4096, 8192])
        self.assertEqual(b['parts'][0]['address'], 0x200000)
        self.assertEqual(len(b['parts']), 1)
        self.assertEqual(b['parts'][0]['sourceOffset'], 0)
        self.assertEqual(manifest['commit'], COMMIT)
        for r in manifest['releases']:
            f = r['files'][0]
            self.assertEqual(f['url'], Path(f['url']).name)
            self.assertEqual(hashlib.sha256((self.output / f['url']).read_bytes()).hexdigest(), f['sha256'])
            self.assertIn('not been physically qualified', r['qualification'])
        for line in (self.output / 'SHA256SUMS').read_text().splitlines():
            digest, name = line.split('  ')
            self.assertEqual(hashlib.sha256((self.output / name).read_bytes()).hexdigest(), digest)
        first = {p.name: p.read_bytes() for p in self.output.iterdir()}
        shutil.rmtree(self.output)
        self.package()
        self.assertEqual(first, {p.name: p.read_bytes() for p in self.output.iterdir()})

    def test_accepts_full_padded_partition_sector(self):
        path = self.stick / 'seeder-sticks3-partitions.bin'
        path.write_bytes(table(release.STICK_PARTITIONS, 4096))
        manifest = self.package()
        self.assertEqual(manifest['releases'][0]['parts'][1]['length'], 4096)

    def test_rejects_unexpected_partition_length(self):
        path = self.stick / 'seeder-sticks3-partitions.bin'
        path.write_bytes(path.read_bytes()[:-32])
        with self.assertRaisesRegex(ValueError, '3072 or 4096'):
            self.package()

    def test_rejects_non_erased_partition_sector_padding(self):
        path = self.stick / 'seeder-sticks3-merged.bin'
        data = bytearray(path.read_bytes())
        data[0x8C00] = 0
        path.write_bytes(data)
        with self.assertRaisesRegex(ValueError, 'gaps'):
            self.package()

    def test_reject_bad_image_digest(self):
        path = self.wave / 'seeder-waveshare175c-firmware.bin'
        path.write_bytes(path.read_bytes()[:-1] + b'X')
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            self.package()
        self.assertFalse(self.output.exists())

    def test_reject_missing_or_wrong_source_commit(self):
        with self.assertRaisesRegex(ValueError, 'footer'):
            self.package(commit='a' * 40)

    def test_reject_wrong_compiled_splash(self):
        path = self.stick / 'seeder-sticks3-firmware.bin'
        path.write_bytes(image(f'V2.2.0-sticks3.4  {COMMIT[:7]}'.encode() + b'\0', 3))
        with self.assertRaisesRegex(ValueError, 'compiled splash'):
            self.package()

    def test_native_splash_keeps_corrected_sovereign_pixels(self):
        # Native master produced by gen_sticks3_splash.py after exchanging the
        # original final N/G glyphs. Updating artwork requires explicit review.
        self.assertEqual(hashlib.sha256(release.stick_splash(REPO)).hexdigest(),
                         'f4e4c88ac1a9c0efbc034dde17404235c4fe6372fac6afb1e77544d4f6d8cba2')

    def test_reject_merged_gap_change(self):
        path = self.stick / 'seeder-sticks3-merged.bin'
        data = bytearray(path.read_bytes())
        data[400] = 0
        path.write_bytes(data)
        with self.assertRaisesRegex(ValueError, 'gaps'):
            self.package()

    def test_reject_wrong_board(self):
        path = self.wave / 'seeder-waveshare175c-firmware.bin'
        path.write_bytes(image(f'V2.2.0-ws175c.11  {COMMIT[:7]}'.encode() + b'\0', 3))
        with self.assertRaisesRegex(ValueError, 'flash size'):
            self.package()

    def test_reject_changed_partition_source(self):
        path = self.root / 'partitions/waveshare175c.csv'
        path.write_text(path.read_text().replace('0x600000', '0x700000'))
        with self.assertRaisesRegex(ValueError, 'partition contract'):
            self.package()

    def test_reject_dirty_or_disconnected_footer_values(self):
        path = self.wave / 'seeder-waveshare175c-firmware.bin'
        for payload in [f'V2.2.0-ws175c.11  {COMMIT[:7]}*'.encode() + b'\0',
                        b'2.2.0-ws175c.11\0' + COMMIT[:7].encode() + b'\0']:
            with self.subTest(payload=payload):
                path.write_bytes(image(payload, 5))
                with self.assertRaisesRegex(ValueError, 'footer'):
                    self.package()

    def test_reject_table_mutation(self):
        path = self.stick / 'seeder-sticks3-partitions.bin'
        data = bytearray(path.read_bytes())
        data[8] ^= 1
        path.write_bytes(data)
        with self.assertRaisesRegex(ValueError, 'MD5'):
            self.package()

    def test_reject_ambiguous_tag(self):
        for tag in ['latest', 'v2.2.0', '../../tag', 'v2.2.0-ports.0', 'v2.3.0-ports.1']:
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                self.package(tag=tag)

    def test_never_overwrite_existing_release(self):
        self.package()
        with self.assertRaisesRegex(ValueError, 'empty'):
            self.package()


if __name__ == '__main__':
    unittest.main()
