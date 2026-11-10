#!/usr/bin/env python3
"""Compare production btc.cpp + vendored uBitcoin against embit 0.8.0.

All inputs here are public, deterministic test data, never real seed material.
Run after build.py with embit installed from requirements.txt.
"""
import argparse
import hashlib
import json
import pathlib
import subprocess
from embit import bip32, bip39, networks, script

ROOT = pathlib.Path(__file__).resolve().parent
BIN = ROOT / 'build/crypto-harness'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--report', type=pathlib.Path, help='Optional JSON report destination')
args = parser.parse_args()

def reference(entropy):
    mnemonic = bip39.mnemonic_from_bytes(entropy)
    master = bip32.HDKey.from_seed(bip39.mnemonic_to_seed(mnemonic))
    account = master.derive('m/84h/0h/0h')
    return [entropy.hex().upper(), mnemonic, master.my_fingerprint.hex(),
        account.to_public().to_base58(version=networks.NETWORKS['main']['zpub']),
        script.p2wpkh(account.derive('0/0').key).address()]

cases = []
for words, nbytes, nrolls in ((12, 16, 50), (24, 32, 99)):
    patterns = [bytes(nbytes), bytes([255])*nbytes,
        bytes([0xaa])*nbytes, bytes([0x55])*nbytes, bytes(range(nbytes))]
    patterns += [hashlib.sha256(f'Seeder public test vector {i}'.encode()).digest()[:nbytes] for i in range(20)]
    for i, entropy in enumerate(patterns):
        bits = ''.join(f'{b:08b}' for b in entropy)
        cases.append((f'coin-{words}-{i}', words, 'coin', bits, entropy))
    rolls = ['1'*nrolls, '6'*nrolls, ('123456'*17)[:nrolls], ('654321'*17)[:nrolls]]
    for i in range(10):
        public = hashlib.shake_256(f'Seeder public dice test {i}'.encode()).digest(nrolls)
        rolls.append(''.join(str(x % 6 + 1) for x in public))
    for i, roll in enumerate(rolls):
        entropy = hashlib.sha256(roll.encode('ascii')).digest()[:nbytes]
        cases.append((f'dice-{words}-{i}', words, 'dice', roll, entropy))

fields = ('entropy', 'mnemonic', 'fingerprint', 'account_zpub', 'first_receive_address')
results = []
for label, words, kind, data, entropy in cases:
    got = subprocess.check_output([str(BIN), str(words), kind, data], text=True).splitlines()
    expected = reference(entropy)
    assert len(got) == len(expected), (label, got)
    for field, value, expect in zip(fields, got, expected):
        assert value == expect, (label, field, value, expect)
    results.append({'case': label, 'passed': True})

# Sanity check against the published BIP84 first receiving address (zero entropy,
# 'abandon' x11 + 'about', empty BIP39 passphrase).
assert reference(bytes(16))[4] == 'bc1qcr8te4kr609gcawutmrza0j4xv80jy8z306fyu'
summary = {
    'production_source': 'Seeder/src/btc.cpp (unmodified)',
    'library': 'Seeder/lib/uBitcoin (vendored sources, USE_STDONLY)',
    'independent_reference': 'embit 0.8.0',
    'cases': len(results),
    'fields_per_case': list(fields),
    'passed': len(results),
    'limitations': [
        'Host test uses std::string via a minimal Arduino String compatibility shim.',
        'Coin bit assembly mirrors doCoinSeed; this harness does not execute the physical button workflow.',
        'Does not validate display rendering, device RAM clearing, entropy quality, or physical hardware.',
    ],
    'results': results,
}
if args.report:
    args.report.write_text(json.dumps(summary, indent=2)+'\n')
print(f'PASS: {len(results)} public coin/dice vectors; all 5 fields match embit 0.8.0.')
