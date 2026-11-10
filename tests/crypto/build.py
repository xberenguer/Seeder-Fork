#!/usr/bin/env python3
import pathlib, subprocess
ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[1]
LIB = REPO / 'lib/uBitcoin/src'
BUILD = ROOT / 'build'
BUILD.mkdir(exist_ok=True)
objs = []
sources = list(LIB.glob('*.cpp')) + list((LIB/'utility').glob('*.c')) + list((LIB/'utility/trezor').glob('*.c'))
sources += [REPO/'src/btc.cpp', ROOT/'harness.cpp']
for src in sources:
    obj = BUILD/(str(src.relative_to(REPO) if src.is_relative_to(REPO) else src.name).replace('/', '_')+'.o')
    cpp = src.suffix == '.cpp'
    flags = ['-std=c++11', '-DUSE_STDONLY'] if cpp else []
    subprocess.run(['c++' if cpp else 'cc', '-c', '-O2', *flags, '-I'+str(ROOT/'shim'), '-I'+str(REPO/'src'), '-I'+str(LIB), str(src), '-o', str(obj)], check=True)
    objs.append(str(obj))
subprocess.run(['c++', *objs, '-o', str(BUILD/'crypto-harness')], check=True)
print(BUILD/'crypto-harness')
