#!/usr/bin/env python3
"""Correct SOVEREING using the original native bitmap's final N/G glyphs.
The pinned reference remains unchanged; only these two glyph regions move.
"""
from pathlib import Path
import re
import subprocess
ROOT=Path(__file__).resolve().parents[1]
REV='ba6e9ebe226222cbb04415a635a934eeae372dab'
original=subprocess.check_output(['git','show',REV+':src/Lib/images.h'],cwd=ROOT,text=True)
pattern=re.compile(r'(\bseeder_logo\s*\[[^]]+\][^=]*=\s*\{)(.*?)(\};)',re.S)
m=pattern.search(original)
pixels=[int(x,16) for x in re.findall(r'0x[0-9a-fA-F]+',re.sub(r'//[^\n]*','',m[2]))]
assert len(pixels)==200*88
fixed=pixels.copy()
for y in range(43,57):
 for x in range(10):
  fixed[y*200+167+x]=pixels[y*200+178+x]
  fixed[y*200+178+x]=pixels[y*200+167+x]
assert all(a==b or (43<=i//200<57 and (167<=i%200<177 or 178<=i%200<188)) for i,(a,b) in enumerate(zip(pixels,fixed)))
# Preserve upstream formatting so the diff contains only the exchanged pixels.
cursor=0
def replace_pixel(match):
 global cursor
 if match[0].startswith('//'): return match[0]
 value=fixed[cursor];cursor+=1
 return match[0] if int(match[0],16)==value else f'0x{value:04X}'
body=re.sub(r'//[^\n]*|0x[0-9a-fA-F]+',replace_pixel,m[2])
assert cursor==len(fixed)
output=original[:m.start(2)]+body+original[m.end(2):]
(ROOT/'src/Lib/images.h').write_text('// Splash spelling corrected by scripts/gen_sticks3_splash.py; original glyph pixels retained.\n'+output)
print('Corrected native SOVEREIGN splash; only final N/G glyphs exchanged.')
