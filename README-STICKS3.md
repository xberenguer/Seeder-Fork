# Seeder for M5StickS3

Experimental M5Stack **StickS3 (K150)** port of
[BitMaker-hub/Seeder](https://github.com/BitMaker-hub/Seeder), based on upstream
commit `ba6e9ebe226222cbb04415a635a934eeae372dab` (v2.2.0 source).
The original MIT license and author credits are retained.

This targets the ESP32-S3 StickS3 with 8MB flash and 8MB PSRAM. It does not
target the ESP32 StickC, StickC Plus, or StickC Plus2.

## What the port changes

- Adds the `sticks3` PlatformIO environment and M5Unified/M5GFX display and power
  initialization, with pinned dependencies.
- Uses the original 240×135 landscape layout, with A/B button labels and the
  font handling needed by M5GFX.
- Uses a blue accent matched to the StickS3 button's hue, including the menu
  artwork and startup logo. Address text keeps its white/grey checkerboard.
- Maps **B / side button / GPIO12** to MOVE and **A / front button / GPIO11** to OK.
- Keeps the original BIP39 coin/dice calculation, BIP84 derivation, seed QR and
  watch-only zpub QR. The First Address page also shows its receiving-address
  QR beside the complete address text. The address keeps its original full-size
  lettering and continuous line wrapping. White/grey colour sections of up to
  five characters reverse on each row; the QR contains the original address.
  It does not generate random entropy for you.
- Disables application/library logging, sensors, audio, and external accessories.
  The application does not initialize Wi-Fi or Bluetooth or save seed data.
- Uses a custom partition table without a crash-dump partition or filesystem.
  This matters because the precompiled Arduino SDK enables flash crash dumps.
- Retains the original LilyGO build environments.

## Build

Install Python 3 and PlatformIO, then run from this directory:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install platformio==6.2.0
.venv/bin/pio run -e sticks3
```

The build produces `.pio/build/sticks3/firmware.bin` (application only) and
`dist/seeder-sticks3-merged.bin` (complete image for address **0x0**).
The application alone belongs at **0x10000**; do not flash it at 0x0.

The StickS3 environment pins Espressif32 6.12.0 (Arduino-ESP32 2.0.17), M5GFX
0.3.0, and M5Unified commit `96576a14247ddc935149145aa6b51943464120f1`.
Upstream uBitcoin and TFT_eSPI remain vendored; TFT_eSPI is excluded from the
StickS3 build. M5Unified includes its own M5PM1 support. On first startup,
Arduino initializes NVS and M5GFX stores the board-identification hint
`M5GFX / AUTODETECT = 26` (StickS3). This behavior was confirmed by ROM readback;
the port does not store seed material there.

## Flash and verify

Flashing replaces the firmware currently on the StickS3. For the supplied
complete image, use [Espressif's browser flasher](https://espressif.github.io/esptool-js/)
with address **0x0**, or use esptool from a terminal:

```sh
python -m pip install esptool==4.9.0
python -m esptool --chip esp32s3 --port PORT --after no_reset write_flash 0x0 seeder-sticks3-merged.bin
python -m esptool --chip esp32s3 --port PORT --before no_reset --after hard_reset --no-stub verify_flash 0x0 seeder-sticks3-merged.bin
```

Run these commands in order. The first leaves the chip in its ROM download
mode, so firmware cannot change flash before verification. The second verifies
the complete image through the ROM loader, then resets to start the application.

After normal startup, the NVS initialization and board hint change bytes that
were erased (`0xff`) in the merged image. A subsequent whole-image comparison
can therefore fail even though the firmware is unchanged. This also applies
after a browser flasher starts the application. For an already booted device,
verify the original build's immutable segments instead:

```sh
python -m esptool --chip esp32s3 --port PORT --no-stub verify_flash \
  0x0 .pio/build/sticks3/bootloader.bin \
  0x8000 .pio/build/sticks3/partitions.bin \
  0x10000 .pio/build/sticks3/firmware.bin
```

Alternatively, compare a ROM flash readback with the merged image at those
same bootloader, partition-table, and application ranges. NVS is mutable data;
any difference in those immutable segments is a verification failure. The
first observed post-boot readback matched all three segments and differed only
in the expected NVS board hint.

Replace `PORT` with the device's serial port. On macOS it is usually
`/dev/cu.usbmodem...`; on Windows it is a `COM` port.
If normal flashing cannot connect, connect USB-C with a data cable, hold the
separate **power button** until the green LED blinks, then release it to enter
the manufacturer's documented download mode.

For a downloaded package, check `SHA256SUMS` with `shasum -a 256 -c SHA256SUMS`
(macOS) or `sha256sum -c SHA256SUMS` (Linux). Checksums detect file changes;
they do not constitute a security audit or prove who built a file.

## Controls

| Screen | B: side / MOVE | A: front / OK |
|---|---|---|
| Menus | Change selection | Accept |
| Coin entry | Heads / bit 1 | Tails / bit 0 |
| Dice entry | Cycle 1–6 | Accept selected roll |
| Seed pages | Next page | Previous page |
| Exit page | Return to first page | Hold to clear application seed state and leave |

During coin/dice entry, hold A for three seconds to discard the current entry.
Releasing after the hold prompt appears cancels the discard without recording
an extra coin flip or roll.

The separate power key retains the manufacturer's hardware behavior: one press
resets, two presses power off. Battery operation, power-key behavior, and USB
power interactions still need testing on a physical StickS3. This port adds no
automatic sleep, wake, or inactivity timeout.

## Validation and limits

The port compiles for all three board targets. The StickS3 image has been flashed
and verified against the build through its ROM bootloader. Device photos confirm
the receiving-address screen. The host crypto checks run production
`src/btc.cpp` and vendored uBitcoin against independent embit reference results
for 78 public deterministic 12/24-word coin/dice cases. These compare entropy,
mnemonic, fingerprint, account zpub, and first address. They do not exercise
physical buttons or verify the ESP32's runtime behavior.

Run the geometry audit with `python scripts/audit_ui.py`; see
`tests/crypto/README.md` for repeatable arithmetic checks. GitHub Actions builds
all three targets and prepares complete flash images.

**Hardware validation is partial.** Full input-flow coverage, physical-camera QR
scanning, and battery/power behavior still need testing. Use public test seeds
while checking these paths.
Then independently verify any newly entered entropy offline as described in
upstream [SECURITY.md](SECURITY.md).

The upstream exit action clears application-owned seed fields, but is not a
verified complete RAM scrub: uBitcoin also uses a static mnemonic buffer and
temporary derivation buffers. This port does not change those routines. The
upstream RAM-erasure claims should be read with that limitation. Hardware
power-off behavior is a separate boundary that still needs physical validation.

Hardware validation should cover both 12/24-word coin/dice paths, 8-letter words
at both screen edges, hold/release cancellation, seed and watch-only QR scanning,
battery startup, reset, and off/on with a generated public test seed displayed.

The menu and address screens have also been rendered with the production M5GFX
backend. Address text reconstruction and white/grey colouring pass four host
checks; address, seed, and zpub QR payloads pass 24 independent decoding checks.
These checks are separate from physical camera scanning and device testing.

The original license is in [LICENSE](LICENSE). Additional M5Stack dependency
notices are in [THIRD-PARTY-NOTICES.txt](THIRD-PARTY-NOTICES.txt).

## Hardware references

- [Official StickS3 hardware, pinout and PlatformIO settings](https://docs.m5stack.com/en/core/StickS3)
- [Official StickS3 button examples](https://docs.m5stack.com/en/arduino/m5sticks3/button)
- [M5PM1 power management](https://docs.m5stack.com/en/arduino/m5sticks3/m5pm1)
