#!/usr/bin/env python3
"""Exercise the real button detector, workflow and crypto for both port mappings."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BUILD=HERE/'build';BUILD.mkdir(exist_ok=True)
SHIM=ROOT/'tests/round/shim'
UBTC=ROOT/'lib/uBitcoin/src'
# Exclude display/power initialization only; preserve all production button code.
gpio=(ROOT/'src/gpio.cpp').read_text()
buttons='#include "GlobalVARS.h"\n#include "gpio.h"\n'+gpio[gpio.index('sButton::sButton'):]
(BUILD/'buttons.cpp').write_text(buttons)
sources=[HERE/'controls.cpp',BUILD/'buttons.cpp',ROOT/'src/workflow.cpp',ROOT/'src/btc.cpp']
sources+=sorted(UBTC.glob('*.cpp'))+sorted((UBTC/'utility').glob('*.c'))+sorted((UBTC/'utility/trezor').glob('*.c'))
for port,flag in [('sticks3','SEEDER_BOARD_STICKS3'),('waveshare175c','SEEDER_BOARD_WAVESHARE175C')]:
 flags=['-O1','-ffunction-sections','-fdata-sections','-DUSE_STDONLY','-D'+flag,'-I'+str(SHIM),'-I'+str(ROOT/'src'),'-I'+str(UBTC)]
 headers=b''.join(f.read_bytes() for base in [SHIM,ROOT/'src',UBTC] for f in sorted(base.rglob('*.h')))
 objects=[]
 for src in sources:
  digest=hashlib.sha256(src.read_bytes()+headers+str(flags).encode()).hexdigest()[:16];obj=BUILD/(src.name+'-'+digest+'.o')
  if not obj.exists():subprocess.run([os.environ.get('CXX','c++') if src.suffix=='.cpp' else os.environ.get('CC','cc'),*flags,'-std=c++17' if src.suffix=='.cpp' else '-std=c99','-c',str(src),'-o',str(obj)],check=True)
  objects.append(str(obj))
 target=BUILD/port
 subprocess.run(['c++',*objects,'-Wl,-dead_strip' if sys.platform=='darwin' else '-Wl,--gc-sections','-o',str(target)],check=True)
 subprocess.run([str(target)],check=True)
