# Native round-screen checks

Build `pio run -e waveshare175c`, install `requirements.txt` in this directory,
then run `python tests/round/build.py` and `python tests/round/verify.py` from the
repository root. A C/C++ compiler and Python are required.

The harness compiles the production composer, frozen BitMaker UI/QR encoder,
actual TFT_eSPI font/rasterizer, Arduino_GFX canvas, workflow, GPIO detector and
btc.cpp/uBitcoin. Host shims supply GPIO/time and Arduino String; SPI calls abort.
Only public deterministic data are used. Generated frames live in ignored
`tests/round/build/`.

## What is checked

- Frozen upstream source, font and renderer hashes; original JPG hashes and the
  five generated branding assets with their pixel hashes.
- 25 frames, exact scaled glyph reconstruction, overlap, circular bounds and
  rigid final orientation. The full-bleed menu background is the sole edge-bleed
  exception. Only the Exit pointer rotates independently.
- Explicit approved wording, positions and original-font masks for captions,
  rendered in a separate sprite that cannot overwrite the QR source.
- Counters 4/5, 5/5, 5/6 and 6/6, including real workflow navigation snapshots.
- Seven independently decoded QRs: address, seed 12, seed 24, watch-only 12/24,
  and additional valid version-7/version-9 seed exports. Sharp and controlled
  blur cases must recover the exact payload. Two-module white margins, unchanged
  export matrices and address Bech32/scriptPubKey equivalence are checked.
- Address cells remain 18x24, in 15/15/12-character rows, with intact five-character
  green/white groups and 8-pixel gaps. Every Bech32 glyph at every position must
  fit the safe circle. Address QR modules increase from 7 to 10 pixels.
- Fourteen approved, unaffected screens match stored pixel hashes in
  `approved_frames.json`. The version-bearing splash is tested through its
  original artwork/provenance instead of a fixed version-string hash.
- Exit idle/half/full line states; canceled 1.6-second holds, ignored MOVE while
  armed, restored idle state and a three-second clear. A short Exit press still
  wraps to the first page.
- Active-high OK / active-low MOVE, complete public 128-bit coin and 99-roll dice
  input, canceled/confirmed capture restart and page navigation/clearing.

Host rendering and flash readback do not prove physical camera scans, power
behavior or complete erasure of all memory copies. See `tests/crypto` for the
broader arithmetic vectors and `tests/qr` for the other targets' CompactSeedQR
checks. Remote CI is distinct from local results.
