# Host crypto checks

This compiles the application's actual `src/btc.cpp` and the vendored uBitcoin
sources, then compares their output with the independent Python implementation
embit 0.8.0. It requires a C/C++ compiler and Python 3.9 or newer.

From the repository root:

```sh
python3 -m venv tests/crypto/.venv
tests/crypto/.venv/bin/python -m pip install -r tests/crypto/requirements.txt
python3 tests/crypto/build.py
tests/crypto/.venv/bin/python tests/crypto/verify.py
```

The 78 public deterministic vectors cover both 12 and 24 words: coin inputs
with zeroes, ones, alternating patterns, increasing bytes and varied data;
and dice inputs with repeated, sequential and varied 50/99-roll sequences.
Each checks entropy hex, BIP39 words, the master fingerprint, the account zpub
at `m/84'/0'/0'`, and the first receiving address at `m/84'/0'/0'/0/0`.
The four cases in `TESTVECTORS.md` are included. The zero-entropy address is also
checked against the published [BIP84 vector](https://github.com/bitcoin/bips/blob/master/bip-0084.mediawiki).

These public inputs must never be used for funds. No production seed material
is required or read. An optional `--report /path/to/report.json` writes a JSON
report; otherwise only the pass/fail result is printed.

The host shim replaces Arduino String with a small std::string wrapper and
makes delay a no-op. uBitcoin uses its existing `USE_STDONLY` mode. Coin bit
assembly mirrors `doCoinSeed()`; this does not drive physical button events.
The checks validate arithmetic, not display rendering, ESP32 runtime behavior,
entropy quality, or complete RAM erasure.
