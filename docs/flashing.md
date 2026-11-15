# Build, flash and verify Seeder

Use the procedure for the **exact board**. StickS3 and Waveshare both contain ESP32-S3 chips, but their images, flash sizes and installation maps are different.

[Project hub](../readme.md) · [StickS3 manual](../README-STICKS3.md) · [Waveshare manual](../README-WAVESHARE175C.md) · [Using Seeder](using-seeder.md) · [Security](../SECURITY.md)

## Choose the correct image

| Target | Complete install / build output | Address | Hardware requirement |
| --- | --- | --- | --- |
| M5Stack StickS3 / K150 | `dist/seeder-sticks3-merged.bin` | **`0x0`** | 8MB flash + 8MB PSRAM |
| Waveshare ESP32-S3-Touch-AMOLED-1.75C | `.pio/build/waveshare175c/firmware.bin`, app only | **`0x200000`** | 32MB flash + 8MB PSRAM and existing C factory map |

The StickS3 app-only build `.pio/build/sticks3/firmware.bin` belongs at `0x10000`, but a first install needs the complete StickS3 image. Waveshare must retain its factory bootloader and partition table; use its guarded app-only script. Neither procedure needs a separate filesystem/asset image for Seeder.

Flashing replaces existing firmware. Install before entering private entropy. Keep any device backup private; do not upload flash dumps or installation logs containing device identifiers with a public source contribution.

## Optional browser path

The **[browser flasher](https://xn--sg8hhb.ws/flasher/)** offers both supported Seeder devices. Use desktop Chrome/Edge or another Web Serial browser, select the exact model and Seeder, follow its flashing-mode instructions, connect, prepare and save a local recovery file, then install. The installer checks download SHA-256, backs up affected sectors, verifies written bytes and resets only after verification. Waveshare requires the complete factory map and remains app-only. StickS3 splits the merged image into explicit ranges and skips NVS.

An Ed25519 signature authenticates the release catalog before its firmware hashes are used. See [release signatures](release-signatures.md) for the pinned public-key fingerprint and independent verification. This does not provision Secure Boot. The terminal route below remains available for independently built firmware and mask-ROM verification. The Waveshare `.9` browser path passed a full Chrome install, including signed download, verified saved backup, app-only write, device digest verification and restart. The StickS3 browser path and real restore writes remain unqualified. See the flasher validation record.

The terminal methods below are independent of that website. A generic browser flasher that defaults to chip erase or `0x10000` is not a substitute for the Waveshare guarded procedure.

## Get binaries or build locally

**This fork currently has no tagged Seeder binary release.** The [upstream BitMaker releases](https://github.com/BitMaker-hub/Seeder/releases) are the original project's releases; do not assume they contain either fork-specific board image.

For a current automated build, open this fork's [build workflow](https://github.com/xberenguer/Seeder-Fork/actions/workflows/build.yml), choose a **successful** run for the intended commit, and download the matching artifact:

| Actions artifact | Relevant files inside |
| --- | --- |
| `seeder-sticks3` | `seeder-sticks3-merged.bin`, app/bootloader/table verification files, `SHA256SUMS-sticks3` |
| `seeder-waveshare175c` | `seeder-waveshare175c-firmware.bin`, `flash_waveshare175c.py`, device guide, `SHA256SUMS-waveshare175c` |

GitHub may require sign-in to download Actions artifacts, and artifacts can expire. Record the run and source commit. A passing CI build is software evidence for its exact source; it does not make its binary byte-identical to an earlier physically tested build. The exact installed/frozen browser downloads listed below are planned for the separate installer, not currently tagged release assets.

**CI checksum paths include `dist/`.** Actions downloads can flatten that directory inside the ZIP. Extract/place the complete artifact contents inside a directory named `dist`, then run verification **from its parent**, for example:

```sh
shasum -a 256 -c dist/SHA256SUMS-sticks3
```

For the Waveshare artifact, use `dist/SHA256SUMS-waveshare175c`. Running the checksum file from a flattened directory without restoring its recorded paths will fail to find the files. Keep the files together rather than editing their checksum values.

Alternatively, build directly from public source using the steps below. This path remains available without Actions download access or the browser installer.

## Prepare source and tools

You need the correct board, a USB-C **data** cable, Python 3, Git, and a computer. Tool/dependency installation and the initial build need internet access; Seeder itself runs offline. Close serial monitors, device dashboards and other flashers that could hold the USB port.

Clone the public fork and create an isolated tool environment:

```sh
git clone https://github.com/xberenguer/Seeder-Fork.git
cd Seeder-Fork
python3 -m venv .venv
.venv/bin/python -m pip install platformio==6.2.0 esptool==4.9.0
```

Commands below use macOS/Linux virtual-environment paths. On Windows, use `py -3` in place of the initial `python3`, and replace `.venv/bin/python` with `.venv\Scripts\python.exe` and `.venv/bin/pio` with `.venv\Scripts\pio.exe`.

Replace the literal **`PORT`** with the board's current serial port, such as `/dev/cu.usbmodem...` on macOS, `/dev/ttyACM...` on Linux or `COM3` on Windows. Do not assume a previously used port still identifies the same device. USB serial names may change after entering download mode.

## StickS3 complete image

### 1. Identify the board

Confirm **M5Stack StickS3 / SKU K150**, not a StickC-family product. The [official guide](https://docs.m5stack.com/en/core/StickS3) documents the hardware and download mode.

Connect USB. If automatic connection fails, hold the separate **power key** until the green LED blinks, then release it. This is the manufacturer's download-mode sequence, not a hold of front A or side B.

### 2. Build or choose a matching prebuilt image

Build from the repository root:

```sh
.venv/bin/pio run -e sticks3
```

The build generates:

- `dist/seeder-sticks3-merged.bin`: complete image for `0x0`.
- `.pio/build/sticks3/firmware.bin`: application for `0x10000`.
- `.pio/build/sticks3/bootloader.bin` and `partitions.bin`: immutable verification inputs for this build.

The merge script validates the ESP32-S3 image headers/digests, exact 8MB partition map, bootloader/app sizes, and segment/gap contents. It includes the framework's matching `boot_app0.bin`. Do not manually replace those components with files from a different build.

If using the tested prebuilt `seeder-sticks3-2.2.0-sticks3.1-merged.bin`, verify its checksum and substitute that filename for `dist/seeder-sticks3-merged.bin` in both commands below. A locally rebuilt app/image has its own hash and is not automatically the exact previously tested artifact.

### 3. Write, verify before boot, then reset

Run the commands **in order**:

```sh
.venv/bin/python -m esptool --chip esp32s3 --port PORT --after no_reset write_flash 0x0 dist/seeder-sticks3-merged.bin
.venv/bin/python -m esptool --chip esp32s3 --port PORT --before no_reset --after hard_reset --no-stub verify_flash 0x0 dist/seeder-sticks3-merged.bin
```

The first command writes and leaves the chip in download mode. The second verifies the complete image through the ROM loader **before the application runs**, then resets into Seeder. Keep global flags such as `--before`, `--after` and `--no-stub` before the `write_flash` / `verify_flash` subcommand as shown.

A successful write is not the same as completing the second verification command. If verification fails, keep the original files, record which range failed and resolve it before treating installation as verified.

### 4. Verification after a normal boot

On first startup, Arduino initializes NVS and M5GFX records the non-secret board hint `M5GFX / AUTODETECT = 26`. Those mutable bytes no longer match the `0xff` gap in the original merged image. A whole-image comparison **after boot** may therefore fail even while firmware is unchanged.

For your own source build, verify its original immutable files instead:

```sh
.venv/bin/python -m esptool --chip esp32s3 --port PORT --no-stub verify_flash \
  0x0 .pio/build/sticks3/bootloader.bin \
  0x8000 .pio/build/sticks3/partitions.bin \
  0x10000 .pio/build/sticks3/firmware.bin
```

Use only files corresponding to the installed image. If you installed a prebuilt image, use its matching verification components or compare those exact ranges against the original merged file in a ROM readback. Do not substitute current local build components just because their filenames match. An immutable bootloader/table/app mismatch is a real verification failure.

## Waveshare 1.75C guarded application install

### 1. Identify the C model and existing factory map

Confirm **ESP32-S3-Touch-AMOLED-1.75C** with **32MB flash**. The [official C hardware guide](https://docs.waveshare.com/ESP32-S3-Touch-AMOLED-1.75C) and [C product page](https://www.waveshare.com/esp32-s3-touch-amoled-1.75c.htm) identify the intended board. The non-C 1.75 is different hardware.

The installer expects this existing factory layout:

| Partition | Start | Size |
| --- | --- | --- |
| nvsfactory | `0x9000` | `0x32000` |
| nvs | `0x3b000` | `0xd2000` |
| otadata | `0x10d000` | `0x2000` |
| phy_init | `0x10f000` | `0x1000` |
| model | `0x110000` | `0xf0000` |
| factory app | **`0x200000`** | **`0x600000`** |
| storage | `0x800000` | `0x800000` |

These addresses describe the required existing map; they are **not instructions to recreate it by hand**. The script reads and checks the complete table, checksum/padding, identity and flash size before writing.

### 2. Build or choose the matching app

```sh
.venv/bin/pio run -e waveshare175c
```

Output is `.pio/build/waveshare175c/firmware.bin`, application-only, maximum 6MB. It is not a bootloader, partition table or merged image. For the tested prebuilt .8 app, use `seeder-waveshare175c-2.2.0-ws175c.8.bin` after checking its checksum, and substitute that path for `--application` below.

The environment intentionally refuses generic `pio run -t upload` use. Run the explicit guarded script with the actual port and expected MAC.

### 3. Find the board identity

Read its identity without writing firmware:

```sh
.venv/bin/python -m esptool --chip esp32s3 --port PORT flash_id
```

Record the **MAC** shown and confirm **Detected flash size: 32MB**. Replace `DEVICE_MAC` below with that board's MAC, not an example or someone else's identifier. Only an ESP32-S3 chip ID is insufficient to distinguish this board from StickS3.

If connection fails, hold **BOOT** while powering/resetting the board, then release BOOT and retry. Recheck the port after mode changes.

### 4. Install with backup and readback

```sh
.venv/bin/python scripts/flash_waveshare175c.py \
  --port PORT \
  --expect-mac DEVICE_MAC \
  --application .pio/build/waveshare175c/firmware.bin \
  --backup-dir ../seeder-private-backups
```

The script checks identity/32MB flash, reads and validates the full factory partition table, backs up the application sectors it could overwrite, verifies that backup, rechecks identity, writes at **`0x200000`**, verifies the app and resets. It writes neither factory bootloader/table nor NVS/model/storage. No chip erase is part of this procedure.

Success records **`application-verified-and-reset`** in the private transaction directory. Keep the logs and backup locally. If a failure occurs after writing starts, the installer attempts to write back the saved sectors and verify the rollback. Read its actual status: **`UNVERIFIED` rollback is not successful recovery**.

If the map guard rejects the board, confirm the model and its current factory firmware/map before doing anything else. Do not bypass the checks or write a generic table to make the error disappear.

## Checksums and tested artifacts

For a downloaded package, verify its matching checksum file before flashing. Preserve the paths written in that file. For a package whose checksum entries are plain filenames in the current directory:

```sh
shasum -a 256 -c SHA256SUMS
```

For the current Actions packages, restore `dist/` and use the artifact-specific command in [Get binaries](#get-binaries-or-build-locally) instead. On Linux, `sha256sum -c CHECKSUM_FILE` is equivalent. To calculate one local file's digest, use `shasum -a 256 FILENAME`; on Windows use `Get-FileHash FILENAME -Algorithm SHA256` in PowerShell. Compare the complete hexadecimal digest.

| Exact tested artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `seeder-sticks3-2.2.0-sticks3.1-merged.bin` | 812448 | `4aacbe515abb924d2c88eb1f33845e32453d431a9ed7571f592467a9055f68c2` |
| `seeder-waveshare175c-2.2.0-ws175c.8.bin` | 706400 | `6c2e071401b6bca2b39d6dacb3a3f0bd2d5e8befd1e7ae37cf0f108422c2d622` |
| `seeder-waveshare175c-2.2.0-ws175c.9.bin` | 706272 | `a6f43313ecd21f7b09432205a0405ba0f5b0dec655ba74335c3d78bb4731a0b7` |

These identify the exact locally tested artifacts. A source rebuild, other commit, different version/footer or dependency change can produce a different file. Its digest must be tied to its own source/build and verification; do not alter the binary to force a known checksum or claim its tests apply to a different file.

Checksums detect file changes. They are not an independent security audit or proof of a builder's identity. Retain [MIT and dependency notices](../THIRD-PARTY-NOTICES.txt) with redistributed builds.

## First boot and functional check

1. Confirm the expected Seeder splash and menu on the correct display.
2. Use **public test inputs** to check both input modes and the intended 12/24-word option; the menu defaults to 12 when newly selected.
3. Review the words, first address, entropy, Export and Watch Only. Current source versions StickS3 `.3` and Waveshare `.9` have no Compact QR. Earlier tested StickS3 `.1` still includes it.
4. Check generated-page direction and Exit using the correct [StickS3](../README-STICKS3.md#buttons) or [Waveshare](../README-WAVESHARE175C.md#orientation-and-buttons) manual.
5. Independently verify the public test output and test the intended offline scanner before any private use.

The recorded flash verification establishes written bytes, not every physical button sequence, QR camera, battery condition or security property. Do not substitute a screenshot or successful build for a device test.

## Connection and recovery

| Symptom | Next step |
| --- | --- |
| Port absent | Check data cable, physical USB connection and operating-system port list; close other device tools |
| Port busy | Quit serial monitors/browser flashers and reconnect |
| StickS3 will not connect | Use the official power-key hold-to-green-blink download sequence, then release |
| Waveshare will not connect | Hold BOOT while powering/resetting; release and reselect its port |
| Screen stays black | Confirm exact model, image type, matching map and write offset. Use the board's download mode to reinstall the correct image. |
| Verification fails | Keep the exact input files and inspect the failing range. StickS3 mutable NVS after boot needs the segment procedure above; immutable mismatches must be resolved. |
| Waveshare factory map missing/different | Stop this install path and investigate the board's existing firmware/map using the official resources; preserve backups rather than blindly erasing |

For both boards, do not import private seed material until recovery, display, controls and intended exports have been checked with public data.

## Current source and previous device-tested builds

The current source is **StickS3 `2.2.0-sticks3.3` / Waveshare `2.2.0-ws175c.9`**. These feature-alignment updates are build/host-tested. Waveshare `.9` was flashed app-only with a verified sector backup and independently ROM-verified; its revised reset visuals await physical acceptance. StickS3 `.3` has not yet been flashed. The `.1`/`.8` hashes above describe the previous physically checked files, not current rebuilds. Check the version offered by the browser catalog before installation; it may still offer that previous validated baseline. [Current controls and feature changes](device-parity.md).
