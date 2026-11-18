# Browser release verification

The flasher imports published GitHub Releases through the
[release pipeline](publishing-releases.md). Device versions, source commits,
checksums and flash layouts are generated from the checked build artifacts.

The optional [browser flasher](https://xn--sg8hhb.ws/flasher/) verifies an **Ed25519-signed release catalog**, then checks each firmware download against the signed SHA-256, and verifies written flash bytes using device-side MD5. Installation is blocked if signature or hash checks fail.

The release public-key fingerprint is SHA-256 of its raw 32-byte Ed25519 encoding:

```text
34568ae48435426bb68028eb6f3bb338a2cba5115c906a33ca26c3592c31c5d4
```

The [public key, detached signature, commands and limitations](https://github.com/xberenguer/website/blob/main/flasher/SIGNING.md) are published separately from the local private signing key. Compare the key against an independently trusted copy: a fully compromised website could replace its JavaScript and public key together. Signed releases do not replace independent source review/builds or [mask-ROM verification](flashing.md).

This is release-manifest signing, **not hardware Secure Boot**. It leaves the StickS3 and Waveshare unlocked, does not program eFuses, and does not prevent using other projects. Secure Boot provisioning has been deferred. The Waveshare `.9` browser path passed a full backup/install/verification/restart flow; the StickS3 path and hardware restore writes remain pending. These checks do not establish physical camera scanning or reset-screen acceptance.
