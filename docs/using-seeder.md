# Using Seeder

Seeder turns **your physical coin flips or die rolls** into BIP39 seed words and the corresponding Bitcoin account information. It does not supply its own random entropy. This fork retains [BitMaker and Lunaticoin's Seeder](https://github.com/BitMaker-hub/Seeder) calculations and adds the board/interface adaptations described in [fork differences](fork-differences.md).

[Project hub](../readme.md) · [StickS3 manual](../README-STICKS3.md) · [Waveshare manual](../README-WAVESHARE175C.md) · [Flashing](flashing.md) · [Security](../SECURITY.md)

## Before entering private entropy

Learn the controls with a public test seed first. Gallery screenshots and published test vectors are for testing and must never receive funds. If you create a private seed, keep its words, entropy and seed-export QRs out of online cameras, notes, chat and cloud storage. A compatible offline signing device is the intended destination for a seed QR.

The firmware does not initialize Wi-Fi/Bluetooth, does not intentionally persist seed material, and offers no BIP39 passphrase-entry screen. Its derivation uses an **empty passphrase**, Bitcoin mainnet, and native SegWit BIP84. It is a seed generator/exporter; it does not load an existing seed, track a balance, build a transaction or sign a transaction.

Check the [security model](../SECURITY.md) and [device-specific validation](#what-has-and-has-not-been-validated) before relying on it. In particular, Exit clearing is not proof that every RAM copy is erased.

## Button reference

| Action | M5Stack StickS3 | Waveshare 1.75C, buttons at top |
| --- | --- | --- |
| Change menu selection | Side B | Small right BOOT |
| Accept menu selection | Front A | Big left PWR |
| Coin Heads / 1 | Side B | Small BOOT |
| Coin Tails / 0 | Front A | Big PWR |
| Change displayed die face | Side B | Small BOOT |
| Record displayed die face | Front A | Big PWR |
| Next generated page | Front A | Big PWR |
| Previous generated page | Side B | Small BOOT |
| Discard unfinished input | Hold A three seconds | Hold PWR three seconds |
| Clear at Exit | Hold A three seconds, cancellable warning | Hold PWR three seconds, cancellable warning |

Normal taps are registered on release. The separate StickS3 power key is not the front A button. Waveshare touch is disabled.

## Choose an input and word count

Select **Coin** or **Dice**, then **12** or **24** words. A new selection initially offers 12 words. Press the select button to begin capture.

| Input mode | 12 words | 24 words |
| --- | --- | --- |
| Coin | 128 physical flips | 256 physical flips |
| Six-sided die | 50 physical rolls | 99 physical rolls |

There is no individual undo or input editor. If a result is wrong, hold the select button for three seconds to discard the whole unfinished entry. The hold warning appears after about 1.2 seconds; releasing during that warning cancels the discard without also entering a result. A brief press released before the warning remains a normal input tap.

### Coin workflow

1. Flip the physical coin.
2. Record Heads with the move button or Tails with the select button.
3. Repeat until the displayed required count is complete.

Each Heads contributes bit **1** and each Tails contributes bit **0**, in the order entered. The final required input automatically triggers generation; do not add an extra flip to confirm.

### Dice workflow

1. Roll a physical six-sided die.
2. Tap the move button until the displayed face matches the roll, cycling 1 through 6.
3. Tap select to record that value.
4. Repeat. Each recorded roll resets the selected face to **1**; the recent history shows the three latest recorded values.

Cycling the face is selection, not entropy input until you record it. The last required roll automatically triggers generation. Seeder checks neither the fairness of your die/coin nor whether your entry matches what happened physically.

## How the input becomes a seed

The process is reproducible independently of the display:

- **Coin:** pack the entered bits into bytes, first bit at the most significant position. For 12 words, use 16 bytes; for 24, use 32. Coin bits are used directly, without hashing.
- **Dice:** concatenate the recorded digits `1`–`6` in order, without spaces or newline. Hash their ASCII bytes with SHA-256. For 12 words, use the first 16 bytes of the digest; for 24, use all 32 bytes.
- **BIP39:** derive the mnemonic from those entropy bytes, adding the normal BIP39 checksum bits. The Entropy page shows the original bytes, not the checksum-extended bit string.
- **Account:** derive mainnet BIP84 account `m/84'/0'/0'` with an empty BIP39 passphrase. First Address is external-chain index zero, `m/84'/0'/0'/0/0`. The fingerprint is the **master** fingerprint, not the account key's fingerprint.

Verify your result with a trusted **offline** independent BIP39/derivation tool. Compare entropy, complete word order, account path and first address. Do not type a private seed into an online verifier. Public [test vectors](../TESTVECTORS.md) and the [independent crypto checks](../tests/crypto/README.md) explain the test method; passing known test cases does not establish the trustworthiness of all possible inputs or hardware.

## Pages and QR payloads

After generation, the first mnemonic page opens automatically. The sequence is:

| Position | StickS3 | Waveshare 1.75C |
| --- | --- | --- |
| 1 | Mnemonic words 1–12 | Mnemonic words 1–12 |
| 2, for 24 words only | Mnemonic words 13–24 | Mnemonic words 13–24 |
| Next | First Address | First Address |
| Next | Entropy (hex) | Entropy (hex) |
| Next | Export | Export |
| Next | Watch Only | Watch Only |
| Last | Exit / Write It Down | Exit / Write It Down |

Skipping the second word page for a 12-word seed is intentional. Normal next/back navigation wraps between the beginning and Exit; a tap alone does not clear the seed. Display counters identify review pages, not an extra entry/confirmation step.

### Mnemonic words

Copy the numbered words in numerical order, including words 13–24 on the second page when applicable. All 12/24 words are needed to reproduce the seed. Do not copy a sample gallery seed for real use.

### First Address

This page shows the first mainnet native SegWit receiving address at **`m/84'/0'/0'/0/0`**. The QR contains the same address in uppercase Bech32 form so the encoder can use larger modules. The lowercase text and uppercase QR represent the same receiving address; compare them with a Bech32-aware tool rather than a case-sensitive raw-text test.

The QR is just an address. It is not the seed, a private key, an extended account key, a `bitcoin:` URI or a complete wallet descriptor. This fork adds the address QR while keeping the full address visible. Its grouping colors are reading aids, not extra address characters.

### Entropy (hex)

The page contains **16 bytes / 32 hexadecimal characters** for 12 words, or **32 bytes / 64 hexadecimal characters** for 24 words. These bytes recreate the seed words and are private seed material. Line breaks, colors and spacing are visual grouping only.

### Export: mnemonic text

Both targets encode the full mnemonic as **space-separated word text**. This is neither numeric SeedQR nor CompactSeedQR. The QR permits seed recovery and spending; the label does not make it safe to scan with an online phone.

Use a compatible offline signing device that accepts this exact text format. If the intended importer expects a different SeedQR representation, use the supported format or copy the words manually.

### Compact QR in earlier builds

Earlier StickS3 builds included CompactSeedQR. It is removed from the current `.2` review sequence to match Waveshare `.9`. Neither current port offers numeric SeedQR or CompactSeedQR; **Export remains space-separated mnemonic text**. Retained binary-encoder utilities/tests do not add a reachable Compact QR screen.

### Watch Only

The QR contains the **bare BIP84 account zpub** for **`m/84'/0'/0'`**. It lets compatible wallet software derive that account's addresses and observe activity; it cannot itself sign a spend. It is still privacy-sensitive account information.

The **master fingerprint** is shown beside/below the QR as text. It is not embedded in the zpub QR. The export is not a complete origin-tagged descriptor, multisig setup, PSBT or seed. Your wallet may need you to specify native SegWit/BIP84 and enter the shown fingerprint and account origin separately. Check its imported first address against Seeder before using the account.

### Exit / Write It Down

This page reminds you to secure a backup because Seeder does not intentionally store the seed. It stays accessible until you deliberately clear or power/reset the device.

- **StickS3:** tap B to return to Watch Only, A to wrap to words; hold A **three seconds** to clear and leave.
- **Waveshare:** tap BOOT to return to Watch Only, PWR to wrap to words; hold PWR **three seconds** to clear.

Both ports show the original outlined **HOLD OK** control while idle. After about 1.2 seconds of holding OK, **START OVER**, the filling bar and **RELEASE TO CANCEL** replace the page. Release during the warning to cancel.

The clear operation overwrites application-owned mnemonic, entropy, account key/fingerprint/address and captured inputs. Complete removal of every library/stack/display-buffer copy is unverified. Hardware power-off behavior and cold-start behavior are separate validation subjects; a normal application reset is not a permanent seed backup.

## Troubleshooting a comparison or export

| Problem | What to check |
| --- | --- |
| Word count or words differ | Same 12/24 selection, physical entry sequence, Heads=1/Tails=0, no extra die digits/spaces/newline, correct dice digest truncation |
| Address differs | Complete words in order; empty BIP39 passphrase; Bitcoin mainnet; BIP84 account0; receive chain0/address0 |
| QR importer rejects Export | Export is mnemonic text, not numeric or binary SeedQR; use an importer that supports it |
| Compact QR is missing | Intentional in StickS3 `.2` and Waveshare `.9`; both use the same page set |
| Watch-only wallet cannot sign | Expected: it has a public account key. Signing requires the seed/private keys in a suitable offline signing device. |
| Imported fingerprint is blank or zero | The bare zpub QR does not carry origin metadata; compare/enter the master fingerprint shown on the device where the wallet supports it |
| Reboot lost the displayed seed | Expected application behavior; it is not intentionally stored. Restore from your own verified backup, not device memory. |

If an independent calculation still disagrees after these checks, do not use the result with funds. Keep test evidence separate from private seed material.

## What has and has not been validated

Current source versions are StickS3 `.2` and Waveshare `.9`. Waveshare `.9` was flashed with a verified backup and independently ROM-verified; its revised reset visuals still need physical acceptance. StickS3 `.2` has not been flashed. Host checks exercise the production calculation code against 78 independent public vectors, QR decoding/module matrices, rendered text/layout and the real button detector/workflows for both board pin mappings. Both ports have matching seed-page order, counters, controls and reset behavior. See [device parity](device-parity.md). StickS3's tested clean image was flashed and ROM-verified. Waveshare .7 was physically accepted and .8 was flashed/readback-verified with its limited splash/version change.

These observations do not establish every physical button sequence, camera model, battery condition or security property. Physical camera QR scanning, complete battery/power qualification, exhaustive RAM scrubbing and independent security auditing remain incomplete. See the individual manuals and [Security](../SECURITY.md) for each device's exact scope.


## Repeatable demonstration

The Waveshare photograph uses **12 words / Dice / 50 rolls of 1**. This fixed
input produces the following public demonstration words:

```text
diet glad hat rural panther lawsuit act drop gallery urge where fit
```

The entropy is the first 16 bytes of SHA-256 over the ASCII string of fifty
`1` characters (no newline): `3dac51a65ec9fcfc409a1b5f1defe92b`.
This is a repeatable test example, not private randomness. Do not use it for funds.
