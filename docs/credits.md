# Credits and project history

[Back to Seeder Fork](../readme.md) · [All fork differences](fork-differences.md)

## Original Seeder

**Seeder is BitMaker's project.** The original hardware/software project,
interface, artwork and seed-generation workflow are maintained at
[BitMaker-hub/Seeder](https://github.com/BitMaker-hub/Seeder).
The original documentation credits **Lunaticoin** for the idea. Both authors
remain named in the [original MIT license](../LICENSE).

This fork uses the **v2.2.0 source**, pinned to
[`ba6e9ebe226222cbb04415a635a934eeae372dab`](https://github.com/BitMaker-hub/Seeder/tree/ba6e9ebe226222cbb04415a635a934eeae372dab).
The original coin/dice calculations, BIP39 word list, BIP84 derivation and
mnemonic/account-key export data are retained. Frozen original UI/source and
font hashes are recorded in [SOURCE.json](../src/ui/bitmaker/SOURCE.json).

## This fork

[berenguer / xberenguer](https://github.com/xberenguer) maintains the StickS3 and
Waveshare 1.75C adaptations in
[Seeder-Fork](https://github.com/xberenguer/Seeder-Fork).
The additions cover board support, device-specific display layouts, controls,
address QRs, readability and export changes, verification tools and this manual.
The [complete differences guide](fork-differences.md) records intentional changes;
this fork is an adaptation rather than a claim of pixel-identical upstream UI.

Hardware manufacturers are **M5Stack** and **Waveshare**. Their product names
identify compatible hardware; the fork is an independent community project.
The two device photographs show the project hardware. The README header removes
their original backgrounds and places them on a shared background; exact screen
captures and original photos remain available in the manuals/gallery.

## Software dependencies

| Component | Credit / role |
|---|---|
| uBitcoin | Stepan Snigirev; original Bitcoin/BIP39/BIP84 calculations |
| TFT_eSPI | Bodmer; original fonts, rasterizer and LilyGO display support |
| M5Unified and M5GFX | M5Stack; StickS3 display, board and power integration |
| Arduino_GFX | moononournation and contributors; Waveshare CO5300 QSPI display/canvas |
| Arduino-ESP32 / ESP-IDF | Espressif and contributors; ESP32 runtime and toolchain |
| SeedSigner CompactSeedQR | [SeedSigner specification](https://github.com/SeedSigner/seedsigner/blob/dev/docs/seed_qr/README.md); earlier StickS3 compact export and retained encoder compatibility tests |
| embit / zxing-cpp / Pillow | Independent test calculations, QR decoding and render verification |

The original [LICENSE](../LICENSE) and
[THIRD-PARTY-NOTICES.txt](../THIRD-PARTY-NOTICES.txt) retain dependency notices.
Manufacturer hardware documentation is linked in each device manual. The
[screenshot provenance](screenshot-provenance.json) identifies reference and
current render hashes; the [image notes](artwork.md) distinguish photographs
from software captures.
