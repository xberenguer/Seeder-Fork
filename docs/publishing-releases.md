# Publishing fork firmware

GitHub Releases are the firmware source for the [browser flasher](https://xn--sg8hhb.ws/flasher/).
An ordinary commit or pull request runs checks but does not publish firmware.
The flasher follows published stable releases, not moving source branches or
temporary Actions artifacts. Previous releases remain available for rollback.

## Publish a complete release

1. Commit the intended firmware and documentation. Board versions live in
   `platformio.ini`: StickS3 and Waveshare have independent version numbers.
2. In GitHub Actions, open **build → Run workflow**, select the intended branch,
   and enter an unused bundle tag such as `v2.2.0-ports.1` in `release_tag`.
   Leaving it empty runs checks only. Alternatively, pushing a matching tag runs
   the same pipeline. The base version must match both device versions.
3. The workflow runs calculation, QR, UI, button-workflow and packaging checks,
   then builds all four supported environments. Any failed job prevents release
   publication. The release job packages only the two supported fork boards.
4. One final job creates a draft containing both versioned firmware assets,
   `flasher-release.json` and `SHA256SUMS`. It checks the uploaded asset names,
   sizes and downloaded bytes before publishing the draft as the latest release.
5. The website updater imports that published release, verifies its source,
   checksums and fixed board contracts, signs its catalog and deploys the update.
   Website synchronization status is separate from the firmware build status.

Publication uses the repository's GitHub Actions token with `contents: write`
only in the final release job. Seeder does not contain the website catalog's
private signing key. The website's separate workflow owns catalog signing.

## Release contract

`flasher-release.json` records the full source commit and bundle tag, followed
by independent device versions, SHA-256 hashes, sizes, image parts and partition
maps. Firmware filenames contain the device version. `SHA256SUMS` uses plain
filenames, so users can verify the downloaded assets together in one directory.

| Device | Firmware contract |
| --- | --- |
| M5Stack StickS3 | Checked merged ESP32-S3 image; 8MB flash; bootloader at `0x0`, partitions at `0x8000`, OTA data at `0xe000`, application at `0x10000` |
| Waveshare AMOLED 1.75C | ESP32-S3 application only at `0x200000`; 32MB chip, 6MB application slot; existing factory bootloader and partition map preserved |

Packaging rejects a different chip, invalid image checksum/digest, wrong flash
size, changed partition contract, missing version/source footer or inconsistent
merged bytes. The corrected native StickS3 splash is pinned by a regression test,
and packaging requires those exact source bitmap bytes inside the application.
A newly compiled artifact does not inherit physical qualification
from an older locally flashed file. Release metadata states that distinction.
The pipeline does not flash hardware or program eFuses.

## Failed publication and recovery

A failed upload or byte verification leaves the release as a draft. It is not
offered as a new stable release. Inspect the failure before explicitly deleting
the failed draft and retrying, or publish a new bundle tag. The workflow never
silently replaces assets on an existing release. An existing Git tag must point
to the same source commit that passed the current workflow.

If website synchronization fails, the previously verified catalog remains live.
Check the website workflow, fix the rejection and re-run synchronization; do not
manually relabel an old firmware file as the new version.

Local packaging tests:

```sh
python -m unittest discover -s tests/release -v
```
