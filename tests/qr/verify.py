#!/usr/bin/env python3
"""Build production qrcoded.c and independently decode public seed/address QRs."""
import json
import pathlib
import subprocess
import tempfile

from embit import bech32, bip39
from embit.script import Script
import zxingcpp

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[1]
BUILD = ROOT / 'build'
BUILD.mkdir(exist_ok=True)
HARNESS = BUILD / 'qr-harness'
subprocess.run([
    'cc', '-std=c99', '-O2', '-I' + str(REPO/'src'),
    str(REPO/'src/qrcoded.c'), str(ROOT/'harness.c'), '-o', str(HARNESS),
], check=True)
subprocess.run([str(HARNESS), '--contract'], check=True)

fixtures = json.loads((ROOT/'official_vectors.json').read_text())
cases = [(v['name'], bytes.fromhex(v['entropy_hex']), v['mnemonic']) for v in fixtures['vectors']]
for length in (16, 32):
    for label, data in [
        ('zero', bytes(length)),
        ('ff', b'\xff' * length),
        ('numeric-ascii', (b'1234567890123456' * 2)[:length]),
        ('uppercase-ascii', (b'ABCDEFGHIJKLMNOP' * 2)[:length]),
        ('controls', bytes(range(length))),
    ]:
        cases.append((f'{label}-{length}', data, None))

def decode_image(path, name):
    magic, dimensions, maximum, pixels = path.read_bytes().split(b'\n', 3)
    width, height = map(int, dimensions.split())
    assert magic == b'P5' and maximum == b'255'
    assert len(pixels) == width * height
    image = memoryview(pixels).cast('B', shape=(height, width))
    barcode = zxingcpp.read_barcode(
        image, formats=zxingcpp.BarcodeFormat.QRCode,
        try_invert=False, is_pure=True,
    )
    assert barcode is not None and barcode.valid, (name, 'independent decode failed')
    return barcode.bytes

# Public zero-entropy BIP39 vectors, first receive path m/84'/0'/0'/0/0.
# The 12-word case is also the published BIP84 example.
addresses = [
    ('address-12-word-zero', 'bc1qcr8te4kr609gcawutmrza0j4xv80jy8z306fyu'),
    ('address-24-word-zero', 'bc1qzmtrqsfuaf6l6kkcsseumq26ukaphfj9skkug6'),
]

with tempfile.TemporaryDirectory(prefix='qr-check-', dir=BUILD) as temporary:
    for name, entropy, mnemonic in cases:
        path = pathlib.Path(temporary) / f'{name}.pgm'
        metadata = subprocess.check_output([str(HARNESS), entropy.hex(), str(path)], text=True)
        version, size, ecc, mode = map(int, metadata.split())
        expected_version = 1 if len(entropy) == 16 else 2
        assert version == expected_version, (name, 'QR version', version)
        assert size == (21 if len(entropy) == 16 else 25), (name, 'QR size', size)
        assert ecc == 0, (name, 'expected ECC_LOW', ecc)
        # Auto-selecting numeric/alphanumeric is a regression even if the
        # decoded printable bytes happen to match. CompactSeedQR uses BYTE.
        assert mode == 2, (name, 'expected forced MODE_BYTE', mode)

        # .text may normalize/escape NUL, line breaks or non-UTF8 data.
        decoded = decode_image(path, name)
        assert len(decoded) == len(entropy), (name, 'decoded byte count', len(decoded))
        assert decoded == entropy, (name, 'decoded byte mismatch', decoded.hex())
        if mnemonic is not None:
            assert bip39.mnemonic_from_bytes(decoded) == mnemonic, (name, 'mnemonic mismatch')

    for name, address in addresses:
        path = pathlib.Path(temporary) / f'{name}.pgm'
        metadata = subprocess.check_output([str(HARNESS), '--address', address, str(path)], text=True)
        assert tuple(map(int, metadata.split())) == (2, 25, 0, 1), (name, 'expected version2/25px/ECC_LOW/MODE_ALPHANUMERIC')
        decoded = decode_image(path, name).decode('ascii')
        assert decoded == address.upper(), (name, 'address QR must be all uppercase')
        # SeedSigner normalizes Bech32 scanner data to lowercase before
        # passing it onward. embit Script.from_address itself requires that
        # normalization, whereas its underlying Bech32 decoder handles both.
        normalized = decoded.lower()
        assert normalized == address
        original_witness = bech32.decode('bc', address)
        assert original_witness[0] == 0 and len(original_witness[1]) == 20
        assert bech32.decode('bc', decoded) == original_witness, (name, 'uppercase witness changed')
        assert bech32.decode('bc', normalized) == original_witness, (name, 'normalized witness changed')
        witness_version, program = original_witness
        expected_script = bytes([witness_version, len(program)]) + bytes(program)
        assert Script.from_address(normalized).data == expected_script == Script.from_address(address).data

print(f'PASS: {len(cases)} CompactSeedQR vectors and {len(addresses)} uppercase address QRs; modes, sizes/ECC, bytes, mnemonics, scriptPubKeys and API guards verified.')
