# Seeder for Waveshare AMOLED 1.75C

An offline, two-button Seeder port for the **ESP32-S3-Touch-AMOLED-1.75C**:
466x466 CO5300 AMOLED, 32MB flash and 8MB PSRAM. The non-C model uses different
wiring and is not supported by this target.

**Firmware:** `2.2.0-ws175c.8` · **Reference:** BitMaker Seeder v2.2.0,
[`ba6e9eb`](https://github.com/BitMaker-hub/Seeder/tree/ba6e9ebe226222cbb04415a635a934eeae372dab).
Original MIT license and credits retained.

![Round Seeder screens](Images/Waveshare-overview.png)

*Production-code renders using public test data. These are not camera photos.*

[Full gallery: all 25 screens and 21 comparisons with the original](docs/screenshots.md).

## Interface

Original green palette, fonts and design language, enlarged/repositioned for the
round display. Higher-resolution splash/menu derivatives use BitMaker's original
JPG masters. The green menu band reaches the curved edges.
The splash corrects `SOVEREING` to `SOVEREIGN` using the existing letter shapes.

The First Address page combines a larger QR and complete lowercase address:
18x24 character cells, green/white five-character groups and no reduced text size.
The QR pattern is 250x250 pixels inside a 290x290 white panel. All QRs have a
thinner two-module white margin. Export and Watch Only use clearer sentences,
retain their page counters and preserve their original payloads.

**The interface is adapted, not pixel-identical to upstream.** The complete
[comparison with BitMaker's original](docs/fork-differences.md) separates UI,
behavior, export-format and hardware changes.

## Controls

Hold the enclosure with both buttons across the top.

| Screen | Small right BOOT: MOVE | Big left PWR: OK |
|---|---|---|
| Coin/dice and word-count menus | Change selection | Select |
| Coin entry | Heads / bit 1 | Tails / bit 0 |
| Dice entry | Cycle 1-6 | Record selected roll |
| Generated seed pages | Previous page | Next page |
| Write It Down / Exit | Previous page | Tap: first page; hold: reset countdown |

During input, hold OK for three seconds to discard the entry. The warning
appears after about 1.2 seconds; releasing during its countdown cancels without
recording an extra flip/roll.

On Write It Down, hold OK until the line fills. RELEASE TO CANCEL appears after
about 1.2 seconds; releasing then preserves the seed. A continuous three-second
hold clears application seed fields and returns to the main menu. Touch is off.
The PWR button also retains the board's hardware power behavior.

Page order: mnemonic 1-12, mnemonic 13-24 when applicable, First Address, Entropy,
Export, Watch Only, Exit. This target does not add CompactSeedQR.

## Build

```sh
python3 -m venv .venv
.venv/bin/python -m pip install platformio==6.2.0 esptool==4.9.0
.venv/bin/pio run -e waveshare175c
```

Pinned dependencies: Espressif32 6.12.0 / Arduino-ESP32 2.0.17, Arduino_GFX 1.5.9
and the original vendored TFT_eSPI 2.5.43. Output:
`.pio/build/waveshare175c/firmware.bin` (application only, maximum 6MB).

## Flash with the guarded installer

The factory application starts at **0x200000**. Preserve the board's factory
bootloader and partition table; do not use a generic merged image or chip erase.

```sh
.venv/bin/python scripts/flash_waveshare175c.py \
  --port PORT --expect-mac DEVICE_MAC \
  --application .pio/build/waveshare175c/firmware.bin \
  --backup-dir dist/flash-backups
```

The installer checks device identity/32MB flash and the complete factory map,
verifies a backup, writes only the application, verifies it and resets. A failed
write attempts verified rollback. USB port names can change: identify the board
by its MAC/USB serial rather than the port name alone. Keep device backups private.
Recovery: hold BOOT while powering/resetting, release BOOT, then reinstall.

## Validation

- All four firmware targets compile.
- 25 native-rendered frames: source/font provenance, approved-screen regression,
  circular bounds, original glyph masks, captions and progress indicators.
- Seven QR cases, including all four seed-export size variants, decode in sharp
  and controlled-blur tests. White margins and module matrices are checked.
- Every Bech32 character is checked in every address position; 18x24 cells and
  five-character grouping remain intact.
- Real debounced GPIO simulation covers coin/dice generation, page counters,
  forward/back navigation, canceled resets and three-second Exit clearing.
- Original calculation code is unchanged; 78 public vectors were independently
  checked against embit.

Run the UI checks after building:

```sh
.venv/bin/python -m pip install -r tests/round/requirements.txt
.venv/bin/python tests/round/build.py
.venv/bin/python tests/round/verify.py
```

Version .7 was flashed, readback-verified and approved on the device. Version .8
retains that layout and corrects the splash spelling and version label; it was
also flashed and readback-verified. Its build and rendered UI checks pass. Physical camera scanning, battery operation, complete RAM
scrubbing and security auditing are separate from host tests. Read
[SECURITY.md](SECURITY.md) and [third-party notices](THIRD-PARTY-NOTICES.txt).
