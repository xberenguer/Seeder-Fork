#!/usr/bin/env python3
"""Verify original graphics, higher-resolution source assets and round layout."""
import argparse
import ctypes
import hashlib
import json
import math
import os
import re
import struct
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFilter
from embit import bech32
from embit.script import Script
import zxingcpp

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
p = argparse.ArgumentParser()
p.add_argument('--output', type=Path, default=HERE / 'build/preview')
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=True)
provenance = json.loads((ROOT / 'src/ui/bitmaker/SOURCE.json').read_text())
for name, item in provenance['files'].items():
    assert hashlib.sha256((ROOT / 'src/ui/bitmaker' / item['file']).read_bytes()).hexdigest() == item['sha256'], name + ' changed from upstream'
for name, digest in provenance['renderer_files'].items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name + ' renderer changed'


def rgb565(value):
    return (value >> 11) * 255 // 31, ((value >> 5) & 63) * 255 // 63, (value & 31) * 255 // 31


GREEN = rgb565(0x86f3)
TRACK = rgb565(0x2945)
ADDRESS_WHITE = rgb565(0xffff)
DIM = rgb565(0x4a49)
PUBLIC_ADDRESS = 'bc1qcr8te4kr609gcawutmrza0j4xv80jy8z306fyu'
MENU_FRAMES = {'03-menu-coin', '04-menu-dice', '05-words-12', '06-words-24'}
CAPTURE_FRAMES = {'07-coin-start', '08-coin-progress', '09-dice-progress', '10-hold'}
EXPORT_FRAMES = {'17-export-12', '18-export-24', '19-watch-only', '21-watch-only-24', '22-export-24-v7', '23-export-24-v9'}
EXIT_FRAMES = {'20-exit','24-exit-hold-half','25-exit-hold-full'}
WHITE = rgb565(0xd6ba)
QR_ROW_COLORS = {34: WHITE, 44: GREEN, 62: GREEN, 84: WHITE, 94: GREEN}
COUNTERS = {'17-export-12': '4/5', '18-export-24': '5/6', '19-watch-only': '5/5', '21-watch-only-24': '6/6', '22-export-24-v7': '5/6', '23-export-24-v9': '5/6'}

# High-resolution assets are checked against pinned original JPG source hashes,
# then against their actual generated uint16_t arrays. No invented art/font is
# accepted by a placement hook alone.
brand = json.loads((ROOT / 'src/ui/round_brand.json').read_text())
assert brand['source_revision'] == provenance['commit']
for name, item in brand['sources'].items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == item['sha256'], name + ' master artwork changed'
brand_header = (ROOT / 'src/ui/round_brand.h').read_text()
brand_assets = {}
for item in brand['assets']:
    match = re.search(r'\b' + re.escape(item['array']) + r'\s*\[[^\]]*\]\s*(?:PROGMEM\s*)?=\s*\{(.*?)\};', brand_header, re.S)
    assert match, item['array'] + ' missing generated pixels'
    body = re.sub(r'//[^\n]*|/\*.*?\*/', '', match[1], flags=re.S)
    values = [int(v, 16) for v in re.findall(r'0x[0-9a-fA-F]+', body)]
    assert len(values) == item['width'] * item['height']
    encoded = struct.pack('<' + 'H' * len(values), *values)
    assert hashlib.sha256(encoded).hexdigest() == item['pixel_sha256'], item['array'] + ' generated pixels changed'
    assert hashlib.sha256((ROOT / item['sourcepath']).read_bytes()).hexdigest() == item['source_sha256']
    image = Image.new('RGB', (item['width'], item['height']))
    image.putdata([rgb565(v) for v in values])
    brand_assets[item['id']] = (item, image)
assert set(brand_assets) == set(range(5))

frames = HERE / 'build/original-frames'
paths = sorted(path for path in frames.glob('*.ppm') if not path.stem.endswith(('-panel', '-original')))
assert len(paths) == 25, f'Expected 25 representative frames, found {len(paths)}'
report = {'upstream_commit': provenance['commit'], 'original_asset_source_files': len(provenance['files']),
          'unchanged_renderer_files': len(provenance['renderer_files']), 'high_resolution_original_assets': len(brand_assets),
          'screens': [], 'qr': [], 'orientation': 'UI upright with enclosure held 270 degrees clockwise; buttons across top'}
qr_cases = {}


def scale_original(original, sx, sy, w, h, dw, dh):
    pixels = original.load()
    sampled = Image.new('RGB', (dw, dh))
    sampled.putdata([pixels[sx + x * w // dw, sy + y * h // dh] for y in range(dh) for x in range(dw)])
    return sampled


def foreground_mask(image):
    return image.convert('L').point(lambda v: 255 if v else 0)


def placed_tile(original, sx, sy, w, h, dw, dh, rotation, frame_name=None):
    if rotation == 3:
        image = scale_original(original, sx, sy, w, h, dh, dw).transpose(Image.Transpose.ROTATE_90)
    else:
        assert rotation == 0
        image = scale_original(original, sx, sy, w, h, dw, dh)
    return image


def original_qr_geometry(modules):
    scale = 1
    while (modules + 4) * (scale + 1) <= 135 and scale < 6:
        scale += 1
    quiet = min(4, (135 - modules * scale) // (2 * scale))
    return 240 - modules * scale - quiet * scale - 2, (135 - modules * scale) // 2, scale


class QRCode(ctypes.Structure):
    _fields_ = [('version', ctypes.c_uint8), ('size', ctypes.c_uint8), ('ecc', ctypes.c_uint8),
                ('mode', ctypes.c_uint8), ('mask', ctypes.c_uint8), ('modules', ctypes.POINTER(ctypes.c_uint8))]


qr_library = None
font_source = (ROOT / 'lib/TFT_eSPI/Fonts/glcdfont.c').read_text()
font_body = re.sub(r'//[^\n]*', '', font_source.split('{', 1)[1].split('}', 1)[0])
font_bytes = [int(value, 16) for value in re.findall(r'0x[0-9a-fA-F]+', font_body)]
assert len(font_bytes) == 1280


def native_text(text, color):
    image = Image.new('RGB', (len(text) * 6, 8))
    for index, character in enumerate(text):
        for x in range(5):
            column = font_bytes[ord(character) * 5 + x]
            for y in range(8):
                if column & (1 << y): image.putpixel((index * 6 + x, y), color)
    return image


def expected_address_matrix(payload, version):
    # The address page had no original QR; reconstruct the expected public
    # payload with the pinned upstream encoder, then independently decode the
    # actual rendered panel with ZXing and verify Bech32 semantics with embit.
    global qr_library
    if qr_library is None:
        source = ROOT / 'src/ui/bitmaker/src/qrcoded.c.inc'
        header = source.with_name('qrcoded.h')
        key = hashlib.sha256(source.read_bytes() + header.read_bytes()).hexdigest()[:16]
        library = HERE / 'build' / ('original-qr-' + key + ('.dylib' if sys.platform == 'darwin' else '.so'))
        if not library.exists():
            subprocess.run([os.environ.get('CC', 'cc'), '-x', 'c', '-std=c99', '-O2', '-shared', '-fPIC', str(source), '-o', str(library)], check=True)
        qr_library = ctypes.CDLL(str(library))
        qr_library.qrcode_getBufferSize.argtypes = [ctypes.c_uint8]
        qr_library.qrcode_getBufferSize.restype = ctypes.c_uint16
        qr_library.qrcode_initText.argtypes = [ctypes.POINTER(QRCode), ctypes.POINTER(ctypes.c_uint8), ctypes.c_uint8, ctypes.c_uint8, ctypes.c_char_p]
        qr_library.qrcode_initText.restype = ctypes.c_int8
        qr_library.qrcode_getModule.argtypes = [ctypes.POINTER(QRCode), ctypes.c_uint8, ctypes.c_uint8]
        qr_library.qrcode_getModule.restype = ctypes.c_uint8
    qr = QRCode()
    buffer = (ctypes.c_uint8 * qr_library.qrcode_getBufferSize(version))()
    assert qr_library.qrcode_initText(ctypes.byref(qr), buffer, version, 0, payload.encode()) >= 0
    assert qr.mode == 1 and qr.ecc == 0  # Uppercase Bech32 enables alphanumeric QR.
    return [[bool(qr_library.qrcode_getModule(ctypes.byref(qr), x, y)) for x in range(qr.size)] for y in range(qr.size)]


for path in paths:
    name = path.stem
    view = Image.open(path).convert('RGB')
    raw = Image.open(path.with_name(name + '-panel.ppm')).convert('RGB')
    original = Image.open(path.with_name(name + '-original.ppm')).convert('RGB')
    metadata = json.loads(path.with_suffix('.json').read_text())
    placements = [tuple(item) + ((0,) if len(item) == 8 else ()) for item in metadata['placements']]
    assert all(len(item) == 9 for item in placements)
    qr, qr_kind = metadata['qr'], metadata.get('qr_kind', 'seed')
    if name in COUNTERS:
        expected_counter = native_text(COUNTERS[name], DIM)
        assert ImageChops.difference(original.crop((10, 114, 28, 122)), expected_counter).getbbox() is None, name + ': page counter missing or incorrect in actual native raster'
        expected_counter = scale_original(expected_counter, 0, 0, 18, 8, 36, 16)
        assert ImageChops.difference(view.crop((307, 36, 343, 52)), expected_counter).getbbox() is None, name + ': visible page counter missing, obscured or incorrect'
        assert (10, 114, 18, 8, 307, 36, 36, 16, 0) in placements, name + ': counter not composed into round screen'
        footer = ['12 SEED WORDS' if name == '17-export-12' else '24 SEED WORDS', 'CAN SPEND', 'NEVER A PHONE', 'SCAN WITH AN', 'OFFLINE WALLET'] if 'export' in name else ['ACCOUNT ZPUB', 'SEES BALANCE', 'CANNOT SPEND', 'FINGERPRINT', '73c5da0a']
        native_colors = [WHITE, DIM, GREEN, DIM, WHITE]
        for source_y, text, color in zip(QR_ROW_COLORS, footer, native_colors):
            expected_text = native_text(text, color)
            assert ImageChops.difference(original.crop((10, source_y, 10 + expected_text.width, source_y + 8)), expected_text).getbbox() is None, name + ': original footer wording was altered'
    band, assets = metadata.get('header_band'), metadata.get('assets', [])
    address_glyphs = metadata.get('address_glyphs', [])
    captions = metadata.get('captions', [])
    exit_progress = metadata.get('exit_progress')
    projected = Image.new('RGB', (466, 466), 'black')
    covered = Image.new('1', (240, 135)); cover = ImageDraw.Draw(covered)
    allowed_colors = set(original.getdata()) | {(0, 0, 0)}
    if name in MENU_FRAMES:
        assert band == [94, 54, 0x86f3], 'Menu header must bleed fully to the physical circular edges'
        ImageDraw.Draw(projected).rectangle((0, band[0], 465, band[0] + band[1] - 1), fill=GREEN)
        cover.rectangle((0, 0, 239, 35), fill=1)
        # Remove only the old thin right-hand decorative line, not icons/text.
        assert all(original.getpixel((214, y)) in ((0, 0, 0), TRACK) for y in range(36, 135))
        cover.line((214, 36, 214, 134), fill=1)
        assert {item[0] for item in assets} == {3, 4}, 'Menu must use the original master wordmark and leaf'
    else:
        assert band is None, 'Full-bleed green band belongs only to menu and word choice'
    if name in CAPTURE_FRAMES:
        assert all(original.getpixel((183, y)) in ((0, 0, 0), TRACK) for y in range(135))
        cover.line((183, 0, 183, 134), fill=1)
    if name == '01-splash-brand':
        assert {item[0] for item in assets} == {0}
    elif name == '02-splash-credits':
        assert {item[0] for item in assets} == {1, 2}
    elif name not in MENU_FRAMES:
        assert not assets, 'Master artwork should not replace ordinary font glyphs'
    largest_scale, scaled_tiles = 1.0, 0
    for sx, sy, w, h, dx, dy, dw, dh, rotation in placements:
        assert 0 <= sx < sx + w <= 240 and 0 <= sy < sy + h <= 135
        assert 0 <= dx < dx + dw <= 466 and 0 <= dy < dy + dh <= 466
        tw, th = (dh, dw) if rotation == 3 else (dw, dh)
        assert rotation in (0, 3)
        if rotation:
            assert name in EXIT_FRAMES and (sx, sy, w, h) == (233, 100, 7, 30), 'Only the original Exit arrow may rotate; no glyphs'
        assert tw >= w and th >= h, name + ': original content reduced rather than enlarged'
        assert abs(tw * h - th * w) <= max(w, h), name + ': original aspect ratio distorted'
        tile = placed_tile(original, sx, sy, w, h, dw, dh, rotation, name)
        projected.paste(tile, (dx, dy), foreground_mask(tile))
        cover.rectangle((sx, sy, sx + w - 1, sy + h - 1), fill=1)
        largest_scale = max(largest_scale, tw / w, th / h)
        scaled_tiles += tw > w or th > h
    if name == '14-address':
        # The path and divider are intentionally removed for a single-row
        # header and larger QR. Both title/counter retain original glyphs.
        cover.rectangle((0,20,239,43),fill=1)
        assert (212,10,18,8,307,34,36,16,0) in placements, 'Address counter must align with title'
        assert len(address_glyphs) == len(PUBLIC_ADDRESS) == 42, 'Full address must retain all 42 characters'
        assert [glyph[0] for glyph in address_glyphs] == list(range(42)), 'Address characters reordered, omitted or duplicated'
        reconstructed = []
        for index, sx, sy, dx, dy, color in address_glyphs:
            row, column = divmod(index, 15)
            count = min(15, len(PUBLIC_ADDRESS) - row * 15)
            groups = (count + 4) // 5
            row_width = count * 18 + (groups - 1) * 8
            expected_x = 233 - row_width // 2 + column * 18 + (column // 5) * 8
            expected_color = 0x86f3 if (index // 5) % 2 == 0 else 0xffff
            assert (sx, sy) == (10 + (index % 18) * 12, 48 + (index // 18) * 20), 'Address glyph differs from original font cell'
            assert (dx, dy) == (expected_x, 350 + 28 * row), 'Address group spacing or line placement differs'
            assert color == expected_color, 'Address colors must alternate green/white every five characters'
            mask = foreground_mask(scale_original(original, sx, sy, 12, 16, 18, 24))
            projected.paste(Image.new('RGB', (18, 24), rgb565(color)), (dx, dy), mask)
            cover.rectangle((sx, sy, sx + 11, sy + 15), fill=1)
            reconstructed.append(PUBLIC_ADDRESS[index])
        assert ''.join(reconstructed) == PUBLIC_ADDRESS
        allowed_colors |= {GREEN, ADDRESS_WHITE}
    else:
        assert not address_glyphs, 'Address recoloring must not alter other screens'
    expected_captions = []
    if name in EXPORT_FRAMES:
        # Only the original footer wording is replaced; title/counter/QR remain.
        cover.rectangle((0, 34, 102, 101), fill=1)
        if 'export' in name:
            expected_captions = [
                ('12 SEED WORDS' if name == '17-export-12' else '24 SEED WORDS',370,WHITE),
                ('KEEP THIS QR PRIVATE.',384,GREEN),('SCAN ONLY WITH AN',402,WHITE),
                ('OFFLINE SIGNING DEVICE.',418,GREEN),('NEVER PHOTOGRAPH IT.',432,GREEN)]
        else:
            expected_captions = [('ACCOUNT PUBLIC KEY',370,WHITE),
                ('USE THIS KEY TO VIEW',384,GREEN),('WALLET ACTIVITY.',398,GREEN),
                ('IT CANNOT SPEND BITCOIN.',412,GREEN),('FINGERPRINT',428,WHITE),
                ('73c5da0a',442,GREEN)]
    elif name in EXIT_FRAMES:
        cover.rectangle((0,98,232,134),fill=1)
        filled,holding = {'20-exit':(0,0),'24-exit-hold-half':(108,1),'25-exit-hold-full':(216,1)}[name]
        assert exit_progress == [filled,holding], name + ': reset progress/state differs'
        expected_captions = [('RELEASE TO CANCEL' if holding else 'HOLD OK TO RESET',322,GREEN)]
        ImageDraw.Draw(projected).rectangle((125,350,340,353),fill=TRACK)
        if filled: ImageDraw.Draw(projected).rectangle((125,350,124+filled,353),fill=GREEN)
    else:
        assert exit_progress is None
    assert len(captions) == len(expected_captions), name + ': caption count differs'
    for actual,(text,y,color) in zip(captions,expected_captions):
        native = native_text(text,color)
        bbox = native.getbbox(); native = native.crop((bbox[0],0,bbox[2],8))
        dw = (native.width*3+1)//2; dx = 233-dw//2
        assert actual == [text,dx,y,dw,12,0x86f3 if color==GREEN else 0xd6ba], name + ': wording/style/placement differs'
        tile = scale_original(native,0,0,native.width,8,dw,12)
        projected.paste(tile,(dx,y),foreground_mask(tile))
        mask = foreground_mask(tile)
        difference = ImageChops.difference(view.crop((dx,y,dx+dw,y+12)),tile)
        assert Image.composite(difference,Image.new('RGB',tile.size),mask).getbbox() is None, name + ': caption obscured'
    for asset_id, x, y in assets:
        item, image = brand_assets[asset_id]
        assert x >= 0 and y >= 0 and x + image.width <= 466 and y + image.height <= 466
        projected.paste(image, (x, y))  # Black is real opaque logo ink, not transparency.
        sx, sy, w, h = item['original_rect']
        cover.rectangle((sx, sy, sx + w - 1, sy + h - 1), fill=1)
        allowed_colors |= set(image.getdata())
        background = rgb565(item['background_rgb565'])
        assert all(math.hypot(x + ax - 232.5, y + ay - 232.5) <= 228
                   for ay in range(image.height) for ax in range(image.width)
                   if image.getpixel((ax, ay)) != background), name + ': master asset lettering/leaf clips the circle'
    if qr is not None:
        version, modules, cell, x, y, quiet = qr
        assert modules == version * 4 + 17 and cell >= 4 and quiet == 2
        side = (modules + 2*quiet) * cell
        assert 0 <= x < x + side <= 466 and 0 <= y < y + side <= 466
        if qr_kind == 'address':
            assert name == '14-address' and (version, modules, cell,x,y) == (2,25,10,88,58)
            assert side >= 220
            matrix = expected_address_matrix('BC1QCR8TE4KR609GCAWUTMRZA0J4XV80JY8Z306FYU', version)
            allowed_colors |= {(255, 255, 255)}
        else:
            assert qr_kind == 'seed' and modules*cell >= 240
            ox, oy, old_cell = original_qr_geometry(modules)
            matrix = [[original.getpixel((ox + col * old_cell, oy + row * old_cell)) == (0, 0, 0)
                       for col in range(modules)] for row in range(modules)]
            cover.rectangle((103, 0, 239, 134), fill=1)
        draw = ImageDraw.Draw(projected)
        draw.rectangle((x, y, x + side - 1, y + side - 1), fill='white')
        for row in range(modules):
            for col in range(modules):
                if matrix[row][col]:
                    left, top = x + (col + quiet) * cell, y + (row + quiet) * cell
                    draw.rectangle((left, top, left + cell - 1, top + cell - 1), fill='black')
        qr_cases[name] = (qr_kind, version, modules, cell, x, y, quiet)
    assert ImageChops.difference(view, projected).getbbox() is None, name + ': artwork, scaled glyphs, band or QR matrix differ'
    # Black padding is transparent in the compositor, but original nonblack
    # glyphs/icons cannot be erased by an overlapping asset or panel.
    bright_label_samples = {}
    for sx, sy, w, h, dx, dy, dw, dh, rotation in placements:
        tile = placed_tile(original, sx, sy, w, h, dw, dh, rotation, name)
        difference = ImageChops.difference(view.crop((dx, dy, dx + dw, dy + dh)), tile)
        foreground_difference = Image.composite(difference, Image.new('RGB', tile.size), foreground_mask(tile))
        assert foreground_difference.getbbox() is None, name + ': overlapping regions obscure original content'
    for index, sx, sy, dx, dy, color in address_glyphs:
        mask = foreground_mask(scale_original(original, sx, sy, 12, 16, 18, 24))
        expected = Image.new('RGB', (18, 24), rgb565(color))
        difference = ImageChops.difference(view.crop((dx, dy, dx + 18, dy + 24)), expected)
        difference = Image.composite(difference, Image.new('RGB', (18, 24)), mask)
        assert difference.getbbox() is None, 'Address glyph mask was altered, obscured or recolored incorrectly'
    for asset_id, x, y in assets:
        _, image = brand_assets[asset_id]
        assert ImageChops.difference(view.crop((x, y, x + image.width, y + image.height)), image).getbbox() is None, name + ': master asset altered or obscured'
    omitted = [(x, y) for y in range(135) for x in range(240)
               if original.getpixel((x, y)) != (0, 0, 0) and not covered.getpixel((x, y))]
    assert not omitted, f'{name}: omitted upstream content {omitted[:4]}'
    outside = []
    bleed_pixels = 0
    for y in range(466):
        for x in range(466):
            color = view.getpixel((x, y))
            if color != (0, 0, 0) and math.hypot(x - 232.5, y - 232.5) > 228:
                if band is not None and band[0] <= y < band[0] + band[1] and color == GREEN:
                    bleed_pixels += 1  # Intentional background; round physical glass clips it.
                else:
                    outside.append((x, y))
    assert not outside, f'{name}: foreground content outside safe circle {outside[:4]}'
    assert ImageChops.difference(raw, view.transpose(Image.Transpose.ROTATE_270)).getbbox() is None
    assert set(view.getdata()) <= allowed_colors, name + ': substituted colors introduced outside original masters'
    nonblack = foreground_mask(view).getbbox()
    if name in ('12-mnemonic-wide', '13-mnemonic-24'):
        cells = [dw / w for sx, sy, w, h, dx, dy, dw, dh, rotation in placements if sy >= 30 and h == 17]
        assert cells and min(cells) >= 1.35, name + ': seed words remain at tiny native size'
        assert nonblack[2] - nonblack[0] >= 330, name + ': word grid does not use screen width'
    mask = Image.new('L', (466, 466)); ImageDraw.Draw(mask).ellipse((0, 0, 465, 465), fill=255)
    rounded = Image.new('RGB', (466, 466), '#161b19'); rounded.paste(view, (0, 0), mask)
    if band is not None:
        for y in range(band[0], band[0] + band[1]):
            inside = [x for x in range(466) if mask.getpixel((x, y))]
            assert view.getpixel((inside[0], y)) == GREEN and view.getpixel((inside[-1], y)) == GREEN, 'Header has a black sliver at round edge'

    rounded.save(a.output / (name + '.png'))
    approved = json.loads((HERE/'approved_frames.json').read_text())['frames']
    if name in approved:
        assert hashlib.sha256(rounded.tobytes()).hexdigest()==approved[name], name + ': an approved screen changed'

    report['screens'].append({'screen': name, 'original_graphics_mismatches': 0, 'omitted_original_pixels': 0,
                              'foreground_outside_safe_circle': 0, 'intentional_header_bleed_pixels': bleed_pixels,
                              'rotation_verified': True, 'largest_uniform_scale': largest_scale,
                              'scaled_tile_count': scaled_tiles, 'content_bounds': list(nonblack),
                              'master_asset_ids': [item[0] for item in assets],
                              'address_characters': len(address_glyphs),
                              'address_reconstructed': PUBLIC_ADDRESS if address_glyphs else None,
                              'address_group_size': 5 if address_glyphs else None,
                              'address_group_colors_rgb565': ['86F3', 'FFFF'] if address_glyphs else None,
                              'bright_export_label_source_rows': list(bright_label_samples),
                              'bright_export_label_samples': bright_label_samples,
                              'page_counter': COUNTERS.get(name)})

mn12 = ' '.join(['abandon'] * 11 + ['about'])
address = 'bc1qcr8te4kr609gcawutmrza0j4xv80jy8z306fyu'
checks = {'14-address': address.upper(), '17-export-12': mn12,
          '18-export-24': ' '.join(['abandon'] * 23 + ['art']),
          '22-export-24-v7': 'rule opera robot moon exhibit logic minute priority proof pigeon erase include voyage cable humor index club uncover ride furnace diagram age tape jeans',
          '23-export-24-v9': ' '.join(['abstract']*23+['banner']),
          '19-watch-only': 'zpub6rFR7y4Q2AijBEqTUquhVz398htDFrtymD1mfWTWvUqWxL2umYHFKQFm7ikXtRmhAbAxbyxDSdL36mhkBTjm7Exz6mnNw63zgRwRB3j4L5s',
          '21-watch-only-24': 'zpub6rFR7y4Q2AijBEqTUquhVz398htDFrtymD1mfWTWvUqWxL2umYHFKQFm7ikXtRmhAbAxbyxDSdL36mhkBTjm7Exz6mnNw63zgRwRB3j4L5s'}
assert set(qr_cases) == set(checks), 'Address and every export must have measurable QR geometry'
# Check every Bech32 glyph at every address position, retaining 18x24 cells.
address_metadata=json.loads((frames/'14-address.json').read_text())
for index,sx,sy,dx,dy,color in address_metadata['address_glyphs']:
    for character in 'bc1qpzry9x8gf2tvdw0s3jn54khce6mua7l':
        glyph=native_text(character,WHITE).resize((18,24),Image.Resampling.NEAREST)
        assert all(math.hypot(dx+x-232.5,dy+y-232.5)<=228
                   for y in range(24) for x in range(18)
                   if glyph.getpixel((x,y))!=(0,0,0)), 'Address characters can clip at round edge'
report['unchanged_approved_screen_count']=len(json.loads((HERE/'approved_frames.json').read_text())['frames'])
report['address_glyph_cell']=[18,24]
report['address_qr_pattern_increase_percent']=(10/7-1)*100

for name, payload in checks.items():
    view = Image.open(frames / (name + '.ppm')).convert('RGB')
    images = [view] if name == '14-address' else [Image.open(frames / (name + '-original.ppm')).convert('RGB'), view]
    for image in images + [view.filter(ImageFilter.GaussianBlur(.65)),view.filter(ImageFilter.GaussianBlur(1.0))]:
        result = zxingcpp.read_barcodes(image)
        assert len(result) == 1 and result[0].bytes == payload.encode(), name + ': QR payload differs'
    kind, version, modules, cell, x, y, quiet_modules = qr_cases[name]
    side, quiet = (modules + 2*quiet_modules) * cell, quiet_modules * cell
    bands = [(x, y, x + side, y + quiet), (x, y + side - quiet, x + side, y + side),
             (x, y, x + quiet, y + side), (x + side - quiet, y, x + side, y + side)]
    assert all(view.crop(band).getextrema() == ((255, 255),) * 3 for band in bands), name + ': incomplete two-module white margin'
    if kind == 'address':
        original_witness = bech32.decode('bc', address)
        assert original_witness[0] == 0 and len(original_witness[1]) == 20
        assert bech32.decode('bc', payload) == original_witness
        assert bech32.decode('bc', payload.lower()) == original_witness
        witness, program = original_witness
        assert Script.from_address(payload.lower()).data == bytes([witness, len(program)]) + bytes(program) == Script.from_address(address).data
    report['qr'].append({'screen': name, 'kind': kind, 'decoded_exactly': True,
                         'original_module_matrix_retained': kind == 'seed', 'version': version,
                         'modules': modules, 'module_pixels': cell, 'side_pixels': side,
                         'quiet_zone_pixels': quiet, 'address_scriptPubKey_preserved': kind == 'address'})

# These snapshots come from the real debounced-button workflow, after 12-word
# coin entry and 24-word dice entry, not just direct UI test calls.
workflow_counters = json.loads((frames / 'workflow-counters.json').read_text())
assert [case['expected'] for case in workflow_counters] == ['4/5', '5/5', '5/6', '6/6']
for case in workflow_counters:
    expected = native_text(case['expected'], DIM)
    actual_source = Image.new('RGB', (18, 8)); actual_source.putdata([rgb565(v) for v in case['source_pixels']])
    assert ImageChops.difference(actual_source, expected).getbbox() is None, 'Real workflow forwarded wrong QR step/total'
    actual_display = Image.new('RGB', (36, 16)); actual_display.putdata([rgb565(v) for v in case['display_pixels']])
    assert ImageChops.difference(actual_display, scale_original(expected, 0, 0, 18, 8, 36, 16)).getbbox() is None, 'Real workflow counter not visible on the round panel'
report['workflow_page_counters'] = [case['expected'] for case in workflow_counters]

# The byte-for-byte pinned native splash remains an independent source check.
asset = (ROOT / 'src/ui/bitmaker/src/Lib/images.h').read_text()
body = re.sub(r'//[^\n]*', '', asset.split('seeder_logo')[1].split('{', 1)[1].split('}', 1)[0])
pixels = [int(h, 16) for h in re.findall(r'0x[0-9a-fA-F]+', body)]
assert len(pixels) == 200 * 88
splash = Image.open(frames / '01-splash-brand-original.ppm').convert('RGB')
assert all(splash.getpixel((20 + i % 200, 15 + i // 200)) == rgb565(pixel) for i, pixel in enumerate(pixels)), 'Original splash source bitmap changed'

chosen = ['03-menu-coin', '05-words-12', '09-dice-progress', '12-mnemonic-wide', '14-address', '17-export-12']
sheet = Image.new('RGB', (3 * 486, 2 * 515), '#161b19'); draw = ImageDraw.Draw(sheet)
for i, name in enumerate(chosen):
    x, y = (i % 3) * 486 + 10, (i // 3) * 515 + 10
    sheet.paste(Image.open(a.output / (name + '.png')), (x, y))
    draw.text((x + 16, y + 477), name.split('-', 1)[1].replace('-', ' ').upper(), fill='#b8c9bf')
sheet.save(a.output / 'round-preview.png')
compare = Image.new('RGB', (766, 510), '#161b19'); draw = ImageDraw.Draw(compare)
compare.paste(Image.open(frames / '03-menu-coin-original.ppm'), (20, 170)); compare.paste(Image.open(a.output / '03-menu-coin.png'), (280, 22))
draw.text((20, 145), 'ORIGINAL 240 x 135', fill='white'); draw.text((280, 4), 'ROUND: ORIGINAL ART, ADAPTED', fill='white')
compare.save(a.output / 'original-vs-round.png')
(a.output / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(f'PASS: {len(paths)} frames: original masters/fonts, full-bleed round header, scaled glyphs and top-button orientation; {len(checks)} QR payloads/quiet zones verified.')
print(a.output / 'round-preview.png')
