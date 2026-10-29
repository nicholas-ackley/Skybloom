"""Build reference_tileset.png + reference_tileset.tres from the repacked sheet."""
import json, sys, os
from PIL import Image
import numpy as np
S, OUTDIR = sys.argv[1], sys.argv[2]
RES = 'res://assets/Tilesets/Reference/reference_tileset.png'
T = 16
sheet = np.asarray(Image.open(S + '/packed.png')).copy()
meta = {m['src']: m for m in json.load(open(S + '/packed.json'))}

def is_dirt(p):
    r, g, b = p[..., 0].astype(int), p[..., 1].astype(int), p[..., 2].astype(int)
    return (p[..., 3] > 0) & (r > g) & (g > b) & (r > 150)

# --- fill tiles: grass (from blob centre), dirt (best all-dirt window), water (generated)
g33 = meta[33]
grass = sheet[(g33['cy'] + 1) * T:(g33['cy'] + 2) * T, (g33['cx'] + 1) * T:(g33['cx'] + 2) * T].copy()
g32 = meta[32]
blk = sheet[g32['cy'] * T:(g32['cy'] + g32['ch']) * T, g32['cx'] * T:(g32['cx'] + g32['cw']) * T]
ref_dirt = np.median(blk[is_dirt(blk)][:, :3], axis=0)
d = is_dirt(sheet).astype(int)
ii = d.cumsum(0).cumsum(1)
best = None
for y in range(0, sheet.shape[0] - T):
    for x in range(0, sheet.shape[1] - T):
        s = ii[y + T - 1, x + T - 1] - (ii[y - 1, x + T - 1] if y else 0) - (ii[y + T - 1, x - 1] if x else 0) + (ii[y - 1, x - 1] if x and y else 0)
        if s == T * T:
            v = np.abs(sheet[y:y + T, x:x + T, :3].reshape(-1, 3).mean(0) - ref_dirt).sum() + 0.3 * sheet[y:y + T, x:x + T, :3].astype(int).std()
            if best is None or v < best[0]: best = (v, x, y)
_, dx, dy = best
dirt = sheet[dy:dy + T, dx:dx + T].copy()
rng = np.random.default_rng(7)
water = np.zeros((T, T, 4), np.uint8); water[...] = (85, 114, 191, 255)
for _ in range(5):  # a few short ripple glints
    y, x = rng.integers(1, T - 1), rng.integers(0, T - 4)
    water[y, x:x + rng.integers(2, 5), :3] = (95, 128, 198)
water2 = np.zeros_like(water); water2[...] = (85, 114, 191, 255)
water2[7, 5:9, :3] = (95, 128, 198); water2[12, 10:12, :3] = (95, 128, 198); water2[3, 11:14, :3] = (95, 128, 198)
fills = [grass, dirt, water, water2, grass.copy()]
FY = sheet.shape[0] // T + 1
full = np.zeros(((FY + 1) * T, sheet.shape[1], 4), np.uint8)
full[:sheet.shape[0]] = sheet
for i, f in enumerate(fills):
    full[FY * T:(FY + 1) * T, i * T:(i + 1) * T] = f
os.makedirs(OUTDIR, exist_ok=True)
Image.fromarray(full, 'RGBA').save(OUTDIR + '/reference_tileset.png')

# --- terrain classification (match-corners mode)
def cls(px):
    a = px[..., 3] > 0
    if a.mean() < 0.85: return '.'
    rgb = px[a][:, :3].astype(int)
    r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    if ((g > r) & (g > b)).mean() >= 0.5: return 'G'
    if ((r > g) & (g > b) & (r > 150)).mean() >= 0.5: return 'D'
    return '?'
C = 5
def corners(cx, cy):
    t = full[cy * T:(cy + 1) * T, cx * T:(cx + 1) * T]
    return [cls(t[:C, :C]), cls(t[:C, -C:]), cls(t[-C:, :C]), cls(t[-C:, -C:])], cls(t[4:12, 4:12])

TERR = {'G': 0, 'D': 1, '.': -1}
# terrain set 0 = Ground (dark-outline edges), set 1 = Shore (edges with the blue water shadow)
# (the pack's dirt-on-water blobs are only 2x2 with no straight edges, so dirt is a
# terrain inside grass only; paint dirt shores by hand)
GROUPS = {0: [(33, 'G.'), (32, 'GD'), (34, 'D.')],
          1: [(58, 'G.')]}
terrain = {}
for tset, gl in GROUPS.items():
    for src, allowed in gl:
        m = meta[src]
        for y in range(m['ch']):
            for x in range(m['cw']):
                cx, cy = m['cx'] + x, m['cy'] + y
                c, ctr = corners(cx, cy)
                if '.' in allowed:  # water shadow / unclear corners count as the open side
                    c = [k if k in allowed else '.' for k in c]
                if any(k not in allowed for k in c) or all(k == '.' for k in c): continue
                tile = full[cy * T:(cy + 1) * T, cx * T:(cx + 1) * T]
                # a "fill" tile must really be solid, not a hole/inner piece whose corners happen to match
                if len(set(c)) == 1 and ((tile[..., 3] > 0).mean() < 0.98 or ctr != c[0]): continue
                real = [k for k in c if k != '.']
                centre = ctr if ctr in real else max(set(real), key=real.count)
                terrain[(cx, cy)] = (tset, TERR[centre], [TERR[k] for k in c])
terrain[(0, FY)] = (0, 0, [0] * 4); terrain[(1, FY)] = (0, 1, [1] * 4)
terrain[(4, FY)] = (1, 0, [0] * 4)

lines = ['[gd_resource type="TileSet" load_steps=3 format=3]', '',
         f'[ext_resource type="Texture2D" path="{RES}" id="1_ref"]', '',
         '[sub_resource type="TileSetAtlasSource" id="TileSetAtlasSource_ref"]',
         'texture = ExtResource("1_ref")']
names = ['top_left_corner', 'top_right_corner', 'bottom_left_corner', 'bottom_right_corner']
count = 0
for cy in range(full.shape[0] // T):
    for cx in range(full.shape[1] // T):
        if (full[cy * T:(cy + 1) * T, cx * T:(cx + 1) * T, 3] > 0).sum() == 0: continue
        count += 1
        lines.append(f'{cx}:{cy}/0 = 0')
        if (cx, cy) in terrain:
            tset, ter, bits = terrain[(cx, cy)]
            # Godot only places a tile in a cell painted with the tile's own (centre) terrain, so a
            # grass/dirt transition gets one alternative per terrain on its corners.
            centres = [ter] + sorted({b for b in bits if b >= 0 and b != ter})
            for alt, c in enumerate(centres):
                if alt: lines.append(f'{cx}:{cy}/{alt} = {alt}')
                lines += [f'{cx}:{cy}/{alt}/terrain_set = {tset}', f'{cx}:{cy}/{alt}/terrain = {c}']
                lines += [f'{cx}:{cy}/{alt}/terrains_peering_bit/{n} = {b}' for n, b in zip(names, bits) if b >= 0]
lines += ['', '[resource]', 'terrain_set_0/mode = 1',
          'terrain_set_0/terrain_0/name = "Grass"', 'terrain_set_0/terrain_0/color = Color(0.45, 0.7, 0.3, 1)',
          'terrain_set_0/terrain_1/name = "Dirt"', 'terrain_set_0/terrain_1/color = Color(0.75, 0.5, 0.25, 1)',
          'terrain_set_1/mode = 1',
          'terrain_set_1/terrain_0/name = "Shore Grass"', 'terrain_set_1/terrain_0/color = Color(0.3, 0.7, 0.6, 1)',
          'sources/0 = SubResource("TileSetAtlasSource_ref")', '']
open(OUTDIR + '/reference_tileset.tres', 'w').write('\n'.join(lines))
print('tiles', count, 'terrain tiles', len(terrain), 'sheet', full.shape, 'fills row', FY, 'dirt from', dx, dy)
