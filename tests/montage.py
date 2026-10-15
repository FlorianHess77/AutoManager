"""Fasst Screenshots zu Übersichtsbildern zusammen (zum schnellen Ansehen).

python3 tests/montage.py <ordner> [pro_bild=6] [max_höhe=1700] [skala=0.5]
"""
import os, sys
from PIL import Image, ImageDraw

d = sys.argv[1]
per = int(sys.argv[2]) if len(sys.argv) > 2 else 6
maxh = int(sys.argv[3]) if len(sys.argv) > 3 else 1700
sc = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
files = sorted(f for f in os.listdir(d) if f.endswith('.png') and not f.startswith('M_'))
for k in range(0, len(files), per):
    group = files[k:k + per]
    ims = []
    for f in group:
        im = Image.open(os.path.join(d, f)).convert('RGB')
        im = im.crop((0, 0, im.width, min(im.height, maxh)))
        im = im.resize((int(im.width * sc), int(im.height * sc)))
        ims.append((f, im))
    W = sum(i.width for _, i in ims) + 10 * (len(ims) + 1)
    Hh = max(i.height for _, i in ims) + 34
    out = Image.new('RGB', (W, Hh), (90, 90, 90))
    dr = ImageDraw.Draw(out)
    x = 10
    for f, im in ims:
        out.paste(im, (x, 28))
        dr.text((x, 8), f[:-4][:40], fill=(255, 255, 255))
        x += im.width + 10
    out.save(os.path.join(d, f'M_{k // per:02d}.png'))
print('ok')
