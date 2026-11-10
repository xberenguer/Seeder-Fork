# QR regression checks

Requires Python 3.12 or newer and a C compiler. From the repository root:

```sh
python3 -m venv tests/qr/.venv
tests/qr/.venv/bin/python -m pip install -r tests/qr/requirements.txt
tests/qr/.venv/bin/python tests/qr/verify.py
```

The test compiles the actual `src/qrcoded.c`, encodes public entropy through
`qrcode_initBinary()`, renders QR modules to PGM, and independently decodes
them with ZXing-C++. It checks forced BYTE mode, version 1/2, 21/25 modules,
low error correction, and exact decoded byte length/content.
It also checks rejection of oversized/invalid binary requests and preserves
automatic numeric/alphanumeric encoding through the existing APIs.

All nine public [SeedSigner vectors](https://github.com/SeedSigner/seedsigner/blob/995ce5c65df4bd333f61cd3dd992b39a49138a1d/docs/seed_qr/README.md)
also recover their expected BIP39 mnemonics with embit. Additional 16/32-byte
inputs cover all NUL, all `0xff`, control characters, and ASCII-only numeric or
uppercase data that would otherwise trigger mode auto-selection. The official
vectors include embedded NUL, leading/trailing LF, CR and CRLF bytes.

Two public first-receive addresses from the zero-entropy 12/24-word BIP39
vectors test the address page's uppercasing step. The production encoder must
use version 2-L, 25 modules and alphanumeric mode; independent decoding must
yield exactly the uppercase address. Lowercase normalization and embit's
Bech32 decoder must preserve the witness version/program and scriptPubKey.
This follows [BIP173's QR guidance](https://github.com/bitcoin/bips/blob/master/bip-0173.mediawiki#uppercaselowercase)
and [SeedSigner's decoder normalization](https://github.com/SeedSigner/seedsigner/blob/0.8.7/src/seedsigner/models/decode_qr.py#L1016-L1066).

These are public test seeds and must never be used for funds. Temporary images
are removed after the check; the host binary lives in ignored `build/`.
This validates the QR encoder and payload preservation. It does not validate
the physical LCD, camera scan quality, or the firmware screen navigation.
