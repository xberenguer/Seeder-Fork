#!/usr/bin/env python3
"""Render production round UI with the same pinned graphics library as firmware.

Run `pio run -e waveshare175c` first to provision the pinned library. Only public
test data is used. Output is ignored under tests/round/build/.
"""
import hashlib
import configparser
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BUILD = HERE / 'build'
SHIM = HERE / 'shim'
GFX = ROOT / '.pio/libdeps/waveshare175c/GFX Library for Arduino/src'
if not GFX.is_dir(): raise SystemExit('First install dependencies: pio run -e waveshare175c')
BUILD.mkdir(exist_ok=True)
for name in ('ui/round_ui.cpp', 'gpio.cpp'):
    source = (ROOT / 'src' / name).read_text()
    source = source.replace('#include "../display.h"', '#include "display_host.h"')
    source = source.replace('#include "display.h"', '#include "display_host.h"')
    (BUILD / Path(name).name).write_text(source)
sources = [GFX / 'Arduino_G.cpp', GFX / 'Arduino_GFX.cpp', GFX / 'canvas/Arduino_Canvas.cpp',
           BUILD / 'round_ui.cpp', BUILD / 'gpio.cpp', ROOT / 'src/workflow.cpp',
           ROOT / 'src/btc.cpp', ROOT / 'src/qrcoded.c', ROOT / 'src/ui/bitmaker_reference.cpp', ROOT / 'lib/TFT_eSPI/TFT_eSPI.cpp', HERE / 'render.cpp']
UBTC = ROOT / 'lib/uBitcoin/src'
sources += sorted(UBTC.glob('*.cpp')) + sorted((UBTC / 'utility').glob('*.c')) + sorted((UBTC / 'utility/trezor').glob('*.c'))
config = configparser.ConfigParser(inline_comment_prefixes=(';', '#'))
config.read(ROOT / 'platformio.ini')
version = config.get('env:waveshare175c', 'custom_version')
common = ['-O1', '-ffunction-sections', '-fdata-sections', '-DSEEDER_BOARD_WAVESHARE175C', '-DUSE_STDONLY', '-DSEEDER_UI_VERIFY',
          f'-DSEEDER_VERSION="{version}"', '-DSEEDER_COMMIT="preview"',
          '-I' + str(SHIM), '-I' + str(ROOT / 'src'), '-I' + str(ROOT / 'src/ui'), '-I' + str(GFX), '-I' + str(UBTC), '-I' + str(ROOT / 'lib/TFT_eSPI')]
headers = b''.join(f.read_bytes() for d in (SHIM, ROOT / 'src', GFX, UBTC) for f in sorted(d.rglob('*.h')))
objects = []
for src in sources:
    cpp = src.suffix != '.c'
    flags = common + (['-std=c++17'] if cpp else ['-std=c99'])
    digest = hashlib.sha256(src.read_bytes() + headers + str(flags).encode()).hexdigest()[:16]
    obj = BUILD / (src.name + '-' + digest + '.o')
    if not obj.exists(): subprocess.run([os.environ.get('CXX', 'c++') if cpp else os.environ.get('CC', 'cc'), *flags, '-c', str(src), '-o', str(obj)], check=True)
    objects.append(str(obj))
gc_flag = '-Wl,-dead_strip' if sys.platform == 'darwin' else '-Wl,--gc-sections'
subprocess.run(['c++', *objects, gc_flag, '-o', str(BUILD / 'render')], check=True)
frames = BUILD / 'original-frames'
frames.mkdir(exist_ok=True)
subprocess.run([str(BUILD / 'render')], cwd=frames, check=True)
print(frames)
