#!/usr/bin/env python3
"""Downsample original high-resolution Seeder artwork for the round AMOLED.

python3 scripts/gen_round_brand.py
python3 scripts/gen_round_brand.py --check
python3 scripts/gen_round_brand.py --preview-dir /path/to/native-previews

Requires Pillow. No font, logo or icon is redrawn: menu silhouettes are recovered
from the original high-resolution JPG, then composited on the exact menu green.
The first splash corrects SOVEREING to SOVEREIGN by exchanging the original
final N/G glyphs at source resolution; no replacement font is introduced.
Generated RGB565
arrays use native uint16 values; their hashes serialize those values little-endian.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
REVISION = 'ba6e9ebe226222cbb04415a635a934eeae372dab'
SOURCE_HASHES = {
    'Logo/BLACK_small.jpg': '29ffac3ce69c8b297d4a936230567d69353183668b2e004d5a0b50f7895c7a9e',
    'Logo/LOGO SEEDER.jpg': '4e833d4aaf321fd0035a56bf4561f0cfb5a753bfb854a1c3d7f4512994660144',
    'Logo/uBitcoinLogo.jpg': '98ba342dcae2ac99f329921ffecbc8c03a2ffa594f976b103d2c9d70a92250f0',
    'Logo/powered.jpg': '6fbb0dfbc52a00a4827f275801842da11954422bd39a4ef4aa802f9494d0009f',
}
GREEN_565 = 0x86F3


def source(path):
    raw = (ROOT / path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SOURCE_HASHES[path]:
        raise ValueError('Original artwork differs from pinned upstream: ' + path)
    return Image.open(ROOT / path).convert('RGB')


def clean_black(image, threshold):
    """Remove only near-black JPEG background noise; retain real grey artwork."""
    raw = bytearray(image.tobytes())
    for index in range(0, len(raw), 3):
        if max(raw[index:index+3]) <= threshold:
            raw[index:index+3] = b'\0\0\0'
    return Image.frombytes('RGB', image.size, bytes(raw))


def photo_asset(path, crop, size):
    # Source pixels around 0..12 are JPEG noise in the OLED-black background.
    im = clean_black(source(path).crop(crop), 12)
    if path == 'Logo/BLACK_small.jpg':
        im = correct_sovereign(im)
    im = im.resize(size, Image.Resampling.LANCZOS)
    return clean_black(im, 7)


def correct_sovereign(image):
    """Swap the final N/G using the original high-resolution letter pixels.

    Boxes include JPEG edge padding. The original 14px inter-letter gap and
    total word width are retained. The immutable upstream JPG stays untouched.
    """
    corrected = image.copy()
    n = image.crop((1220, 316, 1291, 406))
    g = image.crop((1299, 316, 1372, 406))
    corrected.paste((0, 0, 0), (1220, 316, 1372, 406))
    corrected.paste(g, (1220, 316))
    corrected.paste(n, (1301, 316))
    return corrected


def menu_asset(crop, size):
    # The master has solid dark artwork on a much lighter gradient. Its dark
    # portions all belong to the original silhouette. Thresholding at source
    # resolution removes that gradient, including the leaves' dark shading,
    # matching the original flat-black menu roles. Downsampling supplies the
    # native target-resolution antialiasing instead of magnifying 27px pixels.
    master = source('Logo/LOGO SEEDER.jpg').crop(crop)
    mask = master.getchannel('G').point(lambda value: 255 if value < 100 else 0)
    mask = mask.resize(size, Image.Resampling.LANCZOS)
    background = ((GREEN_565 >> 11) * 255 // 31,
                  ((GREEN_565 >> 5) & 63) * 255 // 63,
                  (GREEN_565 & 31) * 255 // 31)
    return Image.composite(Image.new('RGB', size, 'black'),
                           Image.new('RGB', size, background), mask)


def rgb565(image):
    raw = image.tobytes()
    return [((raw[i] & 0xf8) << 8) | ((raw[i+1] & 0xfc) << 3) | (raw[i+2] >> 3)
            for i in range(0, len(raw), 3)]


def decoded(values, size):
    image = Image.new('RGB', size)
    image.putdata([((v >> 11) * 255 // 31, ((v >> 5) & 63) * 255 // 63,
                    (v & 31) * 255 // 31) for v in values])
    return image


def render():
    # original_rect is sx,sy,width,height in the immutable 240x135 reference.
    specs = [
        ('Splash', 'Logo/BLACK_small.jpg', (0, 0, 1460, 640), (320, 141),
         (20, 15, 200, 88), 'Original green-on-black splash; final N/G glyphs exchanged at source resolution to correct SOVEREING to SOVEREIGN, then downsampled from 1460x640.'),
        ('CreditsLogo', 'Logo/uBitcoinLogo.jpg', (0, 0, 842, 468), (163, 91),
         (69, 13, 102, 57), 'Original BitMaker/uBitcoin credit image, downsampled from 842x468.'),
        ('CreditsPowered', 'Logo/powered.jpg', (0, 0, 686, 98), (190, 27),
         (60, 76, 119, 17), 'Original Powered by uBitcoin lettering, downsampled from 686x98.'),
        ('MenuWordmark', 'Logo/LOGO SEEDER.jpg', (585, 289, 1559, 478), (201, 39),
         (10, 5, 134, 26), 'Original SEEDER letter shapes; source ink bbox586,290..1557,474 with crop padding matching the original menu aspect ratio.'),
        ('MenuLeaf', 'Logo/LOGO SEEDER.jpg', (224, 230, 434, 487), (41, 50),
         (203, 1, 27, 33), 'Original top three leaves and stem only; excludes seedpod/roots. Crop aligned to the 27x33 original menu silhouette.'),
    ]
    assets = []
    records = []
    for ident, (name, path, crop, size, original, note) in enumerate(specs):
        image = menu_asset(crop, size) if name.startswith('Menu') else photo_asset(path, crop, size)
        values = rgb565(image)
        payload = struct.pack('<' + 'H' * len(values), *values)
        assets.append((name, size, values))
        records.append({
            'id': ident, 'name': name, 'array': name + 'Pixels',
            'width': size[0], 'height': size[1],
            'pixel_sha256': hashlib.sha256(payload).hexdigest(),
            'pixel_hash_encoding': 'little-endian uint16 RGB565',
            'sourcepath': path, 'source_sha256': SOURCE_HASHES[path],
            'crop': list(crop), 'original_rect': list(original),
            'resampling': 'Lanczos downsampling from original high-resolution source',
            'background_rgb565': GREEN_565 if name.startswith('Menu') else 0,
            'preview_name': name + '.png', 'provenance': note,
        })
    sources = {}
    for path, digest in SOURCE_HASHES.items():
        image = source(path)
        sources[path] = {'sha256': digest, 'width': image.width, 'height': image.height,
                         'upstream_git_blob': hashlib.sha1(('blob ' + str((ROOT / path).stat().st_size) + '\0').encode() + (ROOT / path).read_bytes()).hexdigest()}
    manifest = {'format_version': 1, 'repository': 'https://github.com/BitMaker-hub/Seeder',
                'source_revision': REVISION, 'generator': 'scripts/gen_round_brand.py',
                'menu_palette_rgb565': GREEN_565,
                'description': 'Higher-resolution derivatives of original authored artwork; no AI, new typography or redesigned logo.',
                'sources': sources, 'assets': records}
    return assets, manifest


def header(assets):
    out = ['#pragma once', '#include <stdint.h>', '#include <pgmspace.h>', '',
           '// Generated by scripts/gen_round_brand.py from pinned original JPG artwork.',
           '// Do not edit these RGB565 values by hand. See round_brand.json.',
           'namespace roundBrand {',
           'enum AssetId { Splash=0, CreditsLogo=1, CreditsPowered=2, MenuWordmark=3, MenuLeaf=4 };',
           'struct Asset { const uint16_t *pixels; int w, h; };', '']
    for name, size, values in assets:
        out.append('static const uint16_t ' + name + 'Pixels[' + str(len(values)) + '] PROGMEM = {')
        for start in range(0, len(values), 16):
            out.append('  ' + ', '.join('0x%04X' % v for v in values[start:start+16]) + ',')
        out += ['};', '']
    out.append('static const Asset assets[5] = {')
    for name, size, values in assets:
        out.append('  {' + name + 'Pixels, ' + str(size[0]) + ', ' + str(size[1]) + '},')
    out += ['};', '} // namespace roundBrand', '']
    return '\n'.join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--preview-dir', type=Path)
    args = parser.parse_args()
    assets, manifest = render()
    outputs = {ROOT / 'src/ui/round_brand.h': header(assets),
               ROOT / 'src/ui/round_brand.json': json.dumps(manifest, indent=2) + '\n'}
    stale = []
    for path, text in outputs.items():
        if not path.exists() or path.read_text() != text:
            stale.append(str(path.relative_to(ROOT)))
            if not args.check:
                path.write_text(text)
    if args.check and stale:
        raise SystemExit('Stale generated assets: ' + ', '.join(stale))
    if args.preview_dir:
        args.preview_dir.mkdir(parents=True, exist_ok=True)
        for name, size, values in assets:
            decoded(values, size).save(args.preview_dir / (name + '.png'))
    print(('Checked' if args.check else 'Generated') + ' five original-artwork RGB565 assets.')


if __name__ == '__main__':
    main()
