# Screen gallery and original comparison

**Waveshare firmware: `2.2.0-ws175c.9`.** Current source is build/host-tested and has not yet been flashed. The previous .7 layout was physically approved and .8 was readback-verified. In .9, the HOLD OK control returns and holding reuses the input reset warning; button directions are unchanged.

These are **software renders of production UI code**, not photographs. All seed words, keys and addresses are public deterministic test fixtures. Never use them for funds. The reference is [BitMaker v2.2.0 at ba6e9eb](https://github.com/BitMaker-hub/Seeder/tree/ba6e9ebe226222cbb04415a635a934eeae372dab).

Comparison images show the original 240x135 frame at 2x nearest-neighbor scale on the left and the current native 466x466 frame on the right. This makes the pixel structure visible; it does not imply equal physical display size, calibrated colors or camera-scan performance. Original QR pages have no added counter. The original splash intentionally retains its spelling error in the left panel.

[All differences](fork-differences.md) · [Controls and installation](../README-WAVESHARE175C.md)

## Overview

![Current round-screen overview](../Images/Waveshare-overview.png)

## Every rendered screen

### 1. Startup

SOVEREIGN spelling corrected using the original letter shapes; sharper source artwork.

![Startup](../Images/waveshare/01-splash-brand-comparison.png)

[Native 466×466 render](../Images/waveshare/01-splash-brand.png)

### 2. Credits

Original credits retained, downsampled from their high-resolution masters.

![Credits](../Images/waveshare/02-splash-credits-comparison.png)

[Native 466×466 render](../Images/waveshare/02-splash-credits.png)

### 3. Coin menu

Full-width green band, larger original artwork and top-button indicators.

![Coin menu](../Images/waveshare/03-menu-coin-comparison.png)

[Native 466×466 render](../Images/waveshare/03-menu-coin.png)

### 4. Dice menu

Same capture choices and values; larger layout for the round panel.

![Dice menu](../Images/waveshare/04-menu-dice-comparison.png)

[Native 466×466 render](../Images/waveshare/04-menu-dice.png)

### 5. 12 words

Original word-count options retained.

![12 words](../Images/waveshare/05-words-12-comparison.png)

[Native 466×466 render](../Images/waveshare/05-words-12.png)

### 6. 24 words

Original word-count options retained.

![24 words](../Images/waveshare/06-words-24-comparison.png)

[Native 466×466 render](../Images/waveshare/06-words-24.png)

### 7. Coin entry

Original capture values, legends and progress; repositioned for the circle.

![Coin entry](../Images/waveshare/07-coin-start-comparison.png)

[Native 466×466 render](../Images/waveshare/07-coin-start.png)

### 8. Coin progress

Original capture values, legends and progress; repositioned for the circle.

![Coin progress](../Images/waveshare/08-coin-progress-comparison.png)

[Native 466×466 render](../Images/waveshare/08-coin-progress.png)

### 9. Dice entry

Original die/history/counter and input behavior retained.

![Dice entry](../Images/waveshare/09-dice-progress-comparison.png)

[Native 466×466 render](../Images/waveshare/09-dice-progress.png)

### 10. Cancel input

Original capture reset warning and timing retained.

![Cancel input](../Images/waveshare/10-hold-comparison.png)

[Native 466×466 render](../Images/waveshare/10-hold.png)

### 11. Generating

Original generating message, enlarged.

![Generating](../Images/waveshare/11-generating-comparison.png)

[Native 466×466 render](../Images/waveshare/11-generating.png)

### 12. Mnemonic (12 words)

Original numbered two-column words, enlarged.

![Mnemonic (12 words)](../Images/waveshare/12-mnemonic-wide-comparison.png)

[Native 466×466 render](../Images/waveshare/12-mnemonic-wide.png)

### 13. Mnemonic (24 words)

Original numbered two-column words, enlarged.

![Mnemonic (24 words)](../Images/waveshare/13-mnemonic-24-comparison.png)

[Native 466×466 render](../Images/waveshare/13-mnemonic-24.png)

### 14. First Address

Adds QR, complete address in five-character colors; hides path and puts counter inline.

![First Address](../Images/waveshare/14-address-comparison.png)

[Native 466×466 render](../Images/waveshare/14-address.png)

### 15. 128-bit entropy

Original entropy bytes and colors, enlarged.

![128-bit entropy](../Images/waveshare/15-entropy-16-comparison.png)

[Native 466×466 render](../Images/waveshare/15-entropy-16.png)

### 16. 256-bit entropy

Original entropy bytes and colors, enlarged.

![256-bit entropy](../Images/waveshare/16-entropy-32-comparison.png)

[Native 466×466 render](../Images/waveshare/16-entropy-32.png)

### 17. Export (12 words)

New complete-sentence captions, counter and thinner QR margins; same seed words.

![Export (12 words)](../Images/waveshare/17-export-12-comparison.png)

[Native 466×466 render](../Images/waveshare/17-export-12.png)

### 18. Export (24 words)

New complete-sentence captions, counter and thinner QR margins; same seed words.

![Export (24 words)](../Images/waveshare/18-export-24-comparison.png)

[Native 466×466 render](../Images/waveshare/18-export-24.png)

### 19. Watch Only

New public-key explanation and counter; same account zpub and fingerprint.

![Watch Only](../Images/waveshare/19-watch-only-comparison.png)

[Native 466×466 render](../Images/waveshare/19-watch-only.png)

### 20. Write It Down

Original-style outlined HOLD OK control restored; holding opens the shared reset warning.

![Write It Down](../Images/waveshare/20-exit-comparison.png)

[Native 466×466 render](../Images/waveshare/20-exit.png)

### 21. Watch Only (24 words)

Same account zpub and fingerprint; new explanation and counter.

![Watch Only (24 words)](../Images/waveshare/21-watch-only-24-comparison.png)

[Native 466×466 render](../Images/waveshare/21-watch-only-24.png)

### 22. Export: version 7 QR

Additional public 24-word fixture tests a version-7 export.

![Export: version 7 QR](../Images/waveshare/22-export-24-v7.png)

[Native 466×466 render](../Images/waveshare/22-export-24-v7.png)

### 23. Export: version 9 QR

Additional public 24-word fixture tests a version-9 export.

![Export: version 9 QR](../Images/waveshare/23-export-24-v9.png)

[Native 466×466 render](../Images/waveshare/23-export-24-v9.png)

### 24. Reset: halfway

Release during countdown cancels and preserves the seed.

![Reset: halfway](../Images/waveshare/24-exit-hold-half.png)

[Native 466×466 render](../Images/waveshare/24-exit-hold-half.png)

### 25. Reset: complete

Continuous three-second hold clears the application fields and returns to menu.

![Reset: complete](../Images/waveshare/25-exit-hold-full.png)

[Native 466×466 render](../Images/waveshare/25-exit-hold-full.png)
