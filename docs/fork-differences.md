# Differences from BitMaker Seeder

This fork is based on [BitMaker Seeder v2.2.0](https://github.com/BitMaker-hub/Seeder/tree/ba6e9ebe226222cbb04415a635a934eeae372dab), commit `ba6e9ebe226222cbb04415a635a934eeae372dab`.
It adapts that project and intentionally changes parts of its interface. It is
not a pixel-identical reproduction. BitMaker's original credits and MIT license
are retained.

## Seed calculations and export data

The original `src/btc.cpp` and vendored uBitcoin implementation are unchanged.

| Feature | Behavior retained from v2.2.0 |
|---|---|
| Coin input | 128 flips for 12 words; 256 flips for 24 words |
| Dice input | 50 or 99 ASCII roll digits, hashed with SHA-256 |
| Mnemonic | Original BIP39 word list, checksum and 12/24-word generation |
| Derivation | BIP84; first receive address at `m/84'/0'/0'/0/0` |
| Account export | Same bare account zpub and master fingerprint |
| Original seed export | Same space-separated mnemonic words |
| Networking | Wi-Fi/Bluetooth are not initialized; no OTA |
| Persistence | Seed material is not intentionally saved to flash |
| Restart during input | Three-second OK hold; releasing after the prompt cancels |

There is no new device-generated entropy, sensor entropy, passphrase editor,
transaction signing or balance-query feature. Existing application-field clearing
is retained; complete erasure of every library, heap, stack or display-buffer copy
has not been established.

## Waveshare 1.75C: visible and behavioral changes

Current source version: **2.2.0-ws175c.9**. It has not yet been flashed; `.8` is the previous readback-verified build. See [the full device comparison](device-parity.md) for both ports and every remaining difference.

| Area | Difference from the original |
|---|---|
| Screen composition | Uses the 466x466 circle rather than a centered landscape rectangle. Original regions are enlarged and repositioned. Ordinary glyphs use the original TFT_eSPI rasterizer/font data, generally at 1.5-2x scale; the generating message is 2.5x. Integer rounding affects pixel spacing. |
| Startup artwork | Five images are regenerated from the original high-resolution JPG masters, with cropping, downsampling, near-black cleanup and menu silhouette processing. These are different pixel images from the native firmware bitmaps. Source hashes/crops are recorded in `src/ui/round_brand.json`. |
| Splash spelling | Corrects upstream's `SOVEREING` to `SOVEREIGN` by exchanging its existing final N/G letter pixels before downsampling. Original JPG and frozen reference pixels remain unchanged. |
| Artwork sizes | Splash 200x88 -> 320x141; credit logo 102x57 -> 163x91; Powered image 119x17 -> 190x27; menu wordmark 134x26 -> 201x39; leaf 27x33 -> 41x50. |
| Menus | Enlarged option rows, numerals, icons and selection bars. The green band reaches the curved edges. The old right-side grey divider is removed. Indicators are placed beneath the top buttons. |
| Coin and dice entry | Counters, legends, history, die, entropy preview and progress bars are enlarged/repositioned. Their values and capture behavior remain original. |
| Input restart warning | Original warning and progress are enlarged/repositioned. |
| Mnemonic pages | Original numbered two-column/six-row structure, enlarged and repositioned. |
| First Address | Adds a receiving-address QR using equivalent uppercase Bech32. The visible lowercase address is complete, in five-character groups, with green/bright-white alternation and 8-pixel group gaps. Lines contain 15/15/12 characters. |
| Address size in .7 | Address characters retain their 18x24 cells. The QR pattern increases from 175x175 to 250x250 pixels, about 43% larger. Its white panel is 290x290. The displayed derivation path and divider are removed; the underlying BIP84 derivation is unchanged. Title and counter share a single baseline; address lines move six pixels downward. |
| Entropy page | Same eight-byte rows and original colors, enlarged/repositioned. |
| Seed and watch-only QRs | Larger integer-sized modules. The code is above the caption rather than beside it. New page counters show 4/5 and 5/5 for 12 words, or 5/6 and 6/6 for 24 words. Upstream did not number these QR pages. |
| White QR margins | Uses two white modules on each side, reduced from the port's previous four. Address margin: 20 pixels; export margins depend on module pitch. Original seed/zpub module pitch is retained, and all panels fit inside the circle. Physical camera scanning remains a separate check. |
| Export wording | Replaces the original fragments with the sentences reproduced below. The original font and green/white palette are used. |
| Watch-only wording | Uses an explicit public-key description and complete sentences, with the fingerprint label/value retained. |
| Exit / Write It Down | Restores the original outlined HOLD OK control and wipe legend while idle. After about 1.2 seconds of holding, it reuses the input START OVER / RELEASE TO CANCEL warning and bar. A continuous three-second hold clears application fields; release cancels. Upstream exited at about 1.2 seconds without this confirmation screen. |
| Exit pointer | Rotated/repositioned toward the big top-left OK button. |
| Orientation | Both buttons are held at the top; the framebuffer compensates with a rigid 90-degree rotation. |
| Navigation | Big left PWR = OK/select; small right BOOT = MOVE. On generated pages, big advances and small goes back, reversing upstream's logical page-navigation directions. Short OK on Exit still wraps to the first page. |
| Version label | Device-specific version and this fork's build commit/dirty marker. |
| Brightness | Fixed AMOLED brightness register value 128/255; its physical brightness and color response are not calibrated to the original LCD. |

### Export caption

```text
12 SEED WORDS  (or 24 SEED WORDS)
KEEP THIS QR PRIVATE.
SCAN ONLY WITH AN
OFFLINE SIGNING DEVICE.
NEVER PHOTOGRAPH IT.
```

### Watch-only caption

```text
ACCOUNT PUBLIC KEY
USE THIS KEY TO VIEW
WALLET ACTIVITY.
IT CANNOT SPEND BITCOIN.
FINGERPRINT
<master fingerprint>
```

Payload/fingerprint labels use original white `0xD6BA`; warnings, explanatory
sentences and the fingerprint value use original green `0x86F3`. Address groups
use green and bright white `0xFFFF`. Other ordinary grey text is unchanged except
for intentionally removed/replaced elements. Regenerated artwork adds edge shades.
The original credits remain; the splash spelling is corrected as documented above.
CompactSeedQR is **not** part of the Waveshare page sequence.

## StickS3: current fork changes

Current source version: **2.2.0-sticks3.2**, build/host-tested and not yet flashed.
The previous `.1` restored the original green palette and was physically checked.

- Original native artwork and green `0x86F3` palette; `.2` corrects the splash
  spelling using only the original N/G letter pixels. Earlier blue fork builds
  are historical, not the current design.
- Adds the receiving-address QR beside complete lowercase address text, with
  alternating green/white five-character groups. Removes the displayed path;
  the BIP84 derivation is unchanged. The new panel is 116×116 at 240×135.
- Full-height integer-module seed/zpub QR panels with reduced white margins.
- Uses the same revised Export and Watch Only wording, counters and page order
  as Waveshare. Removes the earlier extra CompactSeedQR page.
- Big front A goes forward through generated pages; small side B goes backward,
  matching Waveshare. Menus and input keep their existing button roles.
- Exit retains the outlined HOLD OK control but now reuses the input START OVER /
  RELEASE TO CANCEL screen, bar and three-second timing. Releasing cancels.
- M5GFX-compatible font selection and A/B screen hints differ from the original
  TFT_eSPI backend and generic MOVE/OK hints.

The binary QR encoder utility and tests are retained, but neither supported
port exposes a Compact QR page. The Waveshare renderer uses the frozen upstream
encoder. Legacy LilyGO targets retain the earlier rectangular fork's page set,
wrapping/captions and navigation; the current StickS3/Waveshare feature alignment
does not claim to change those legacy targets.

[Every shared feature and remaining difference between the two supported devices](device-parity.md).

## Hardware adaptations, separately

| Target | Hardware-specific implementation |
|---|---|
| StickS3 | M5Unified/M5GFX, GPIO11/12 buttons, M5 power initialization, 8MB flash/PSRAM profile, disabled unused peripherals/logging and a custom partition map without flash crash dumps or a filesystem. Startup NVS stores the board-identification hint, not seed material. |
| Waveshare 1.75C | CO5300 QSPI panel, Arduino_GFX canvas, original TFT_eSPI used for software sprites only, active-high PWR normalization, 32MB flash/8MB PSRAM profile and additional display buffers. Touch is held in reset; amplifier is disabled; unused microphones/IMU are stopped. |
| Waveshare installation | Guarded application-only write at `0x200000` in the 6MB factory app slot. It checks chip/MAC/flash size, the factory partition table, backup and readback, preserving bootloader, NVS and other storage. |

The rendering backend, full-frame transfers, board initialization and power-key
hardware differ from the original devices. Identical physical brightness,
latency, battery behavior and power-button timing are not claimed.

## Development and validation additions

The fork adds pinned build profiles, CI jobs, independent cryptographic vectors,
binary QR tests, native UI rendering, circular-layout checks, original-source and
font hashes, approved-screen regression hashes, button-workflow tests and guarded
installers. Tests use public deterministic data; screenshots contain no private
user seed. Host checks and flash readback are distinct from camera scans,
battery testing and a security audit. See the device guides and `SECURITY.md`.
