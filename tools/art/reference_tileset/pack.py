import sys, json
from PIL import Image
import numpy as np
B, OUT = sys.argv[1], sys.argv[2]
idx = json.load(open(B + '/index.json'))
T = 16

def phase(alpha, axis):
    a = alpha.astype(int)
    tr = np.abs(np.diff(a, axis=axis)).sum(axis=1 - axis)  # transitions between i and i+1
    n = alpha.shape[axis]
    strength = np.zeros(n + 1)
    strength[1:n] = tr
    # outer edges: count opaque pixels on the first/last line
    strength[0] = a.take(0, axis=axis).sum(); strength[n] = a.take(n - 1, axis=axis).sum()
    best = max(range(T), key=lambda o: (strength[o::T].sum(), -o))
    return best, strength[best::T].sum() / max(1, strength.sum())

groups = []
for i, b in enumerate(idx):
    im = np.asarray(Image.open(f'{B}/b{i:03d}.png')).copy()
    # drop bg-blended halo pixels (light, grey) that touch transparency
    bgc = np.array([188, 200, 194])
    for _ in range(2):
        a = im[..., 3] > 0
        pad = np.pad(a, 1)
        touch = ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
        rgb = im[..., :3].astype(int)
        grey = (rgb.max(2) - rgb.min(2) < 45) & (np.abs(rgb - bgc).sum(2) < 110)
        im[a & touch & grey, 3] = 0
    al = im[..., 3] > 0
    if al.sum() < 12: continue
    h, w = al.shape
    ox, sx = phase(al, 1); oy, sy = phase(al, 0)
    # grid line at offset o inside the crop -> cells start at o - k*T; pad so origin is on a line
    padl = (T - ox) % T; padt = (T - oy) % T
    W = -(-(w + padl) // T) * T; H = -(-(h + padt) // T) * T
    # drop near-empty border cells (overhang slivers of a couple of pixels)
    canvas = np.zeros((H, W, 4), np.uint8); canvas[padt:padt + h, padl:padl + w] = im
    def cell_count(r0, r1, c0, c1): return (canvas[r0:r1, c0:c1, 3] > 0).sum()
    while W > T and cell_count(0, H, W - T, W) <= 3: canvas = canvas[:, :W - T]; W -= T
    while W > T and cell_count(0, H, 0, T) <= 3: canvas = canvas[:, T:]; W -= T
    while H > T and cell_count(H - T, H, 0, W) <= 3: canvas = canvas[:H - T]; H -= T
    while H > T and cell_count(0, T, 0, W) <= 3: canvas = canvas[T:]; H -= T
    groups.append(dict(src=i, ox=b['x'], oy=b['y'], img=canvas, edge=(round(sx, 2), round(sy, 2))))

# pack in original reading order, rows by original y band
groups.sort(key=lambda g: (round(g['oy'] / 40), g['ox']))
SHEET_W = 40 * T
x = y = 0; rowh = 0; placed = []
for g in groups:
    h, w = g['img'].shape[:2]
    if x + w > SHEET_W: x = 0; y += rowh + T; rowh = 0
    placed.append((g, x, y)); x += w + T; rowh = max(rowh, h)
H = y + rowh
sheet = np.zeros((H, SHEET_W, 4), np.uint8)
meta = []
for g, x, y in placed:
    h, w = g['img'].shape[:2]
    sheet[y:y + h, x:x + w] = g['img']
    meta.append(dict(src=g['src'], cx=x // T, cy=y // T, cw=w // T, ch=h // T, edge=g['edge']))
# snap noisy upscaled colours back to a small palette
rgb = Image.fromarray(sheet[..., :3], 'RGB').quantize(colors=56, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert('RGB')
sheet[..., :3] = np.asarray(rgb)
sheet[sheet[..., 3] == 0] = 0
Image.fromarray(sheet, 'RGBA').save(OUT + '.png')
json.dump(meta, open(OUT + '.json', 'w'), indent=0)
print(sheet.shape, len(meta))
