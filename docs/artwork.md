# Photos and screenshots

The header `Images/Seeder-devices.png` places the StickS3 photo on the left and
Waveshare photo on the right. Backgrounds were removed and replaced with the
same neutral background using the built-in image editing tool. Device shape and
photographed screen content were preserved; this is an edited photo layout.

Original photographs are available as `Images/StickS3-device.jpg` and
`Images/Waveshare-device.jpg`, converted to JPEG with metadata removed. The
StickS3 photograph shows an earlier green interface; the current rectangular
firmware now uses the original green theme shown in its exact screen captures. The Waveshare
photo shows the public 50-dice-rolls-of-1 test seed documented in
[Using Seeder](using-seeder.md#repeatable-demonstration).

Every other interface image is a production-code capture using public test data.
The [screen gallery](screenshots.md) and [pixel/source hashes](screenshot-provenance.json)
separate those captures from hardware photography. Original comparison panels
use pinned BitMaker v2.2.0 code.

## Header editing prompt

Remove only the fabric and tabletop backgrounds; place the exact StickS3 photo
on the left and the exact Waveshare photo on the right against a shared neutral
dark-slate background. Keep both devices fully visible, with no overlap, balanced
visual scale and subtle shadows. Preserve the photographed device silhouettes,
screen text, colors, textures, blue button and all words; add no text, logos or
new device parts.

Current StickS3 screenshots show Export rather than the removed CompactSeedQR page. All fixture seeds are public test data. QR appearance is not an entropy test. The native StickS3 splash now corrects SOVEREIGN using only the original N/G letter pixels; `scripts/gen_sticks3_splash.py` reproduces that change from the pinned upstream image.
