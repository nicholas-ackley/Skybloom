"""Skybloom "Wildlands" terrain and prop drawing code, used by generate_nature_assets.py.

Makes 16px terrain tiles (dirt, grass, golden meadow, river water with cliff
banks) laid out for Godot 4 terrain sets in "Match Corners" mode, plus props
(boulders, mushrooms, shrubs, wheat, tufts) in a day and a dusk palette.

Originally the standalone mockup generator; its main() still writes previews
next to this file if run directly. generate_nature_assets.py imports it.
"""
import os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.join(HERE, "..", "..", "skybloom-game")
TILE_DIR = os.path.join(GAME, "assets", "Tilesets", "Wildlands")
PROP_DIR = os.path.join(GAME, "assets", "Objects", "Wildlands")
T = 16

# ---------------------------------------------------------------- palette
def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

PAL = {
    "dirt": [hexc(c) for c in ("8a5232", "a8643a", "c27a42", "d6935a", "e6ad74")],
    "grass": [hexc(c) for c in ("2f5e44", "3f7a48", "5b9a4c", "7db85a", "a3d06c")],
    "gold": [hexc(c) for c in ("a8762f", "c99238", "deac4a", "ecc464", "f6dc8e")],
    "water": [hexc(c) for c in ("21474f", "2a5960", "33696c", "45807c", "6a9e94")],
    "rock": [hexc(c) for c in ("1f2830", "2e3a44", "414f58", "5c6a70", "7f8b8a")],
    "lip": hexc("f1e6c8"),
    "foam": hexc("c9e4da"),
    "outline": hexc("231d24"),
}

def grade_dusk(img):
    """Moody ground-world grade: darker, cooler, teal shadows."""
    a = np.asarray(img).astype(np.float32)
    rgb, alpha = a[..., :3] / 255.0, a[..., 3:]
    lum = (rgb @ np.array([0.3, 0.59, 0.11]))[..., None]
    rgb = rgb * 0.7 + lum * 0.3                        # desaturate a bit
    shadow = np.array([0.03, 0.08, 0.12])
    light = np.array([0.78, 0.86, 0.95])
    rgb = shadow + (light - shadow) * np.clip(rgb * 1.05, 0, 1) ** 1.35  # teal shadows, cool lights
    rgb = np.clip(rgb, 0, 1)
    return Image.fromarray(np.concatenate([rgb * 255, alpha], -1).round().astype(np.uint8), "RGBA")

# ---------------------------------------------------------------- noise
def periodic_noise(seed, lattice=4, size=T):
    """Value noise that tiles with period `size` (so tile edges stay continuous)."""
    rng = np.random.default_rng(seed)
    g = rng.random((lattice, lattice))
    out = np.zeros((size, size))
    for y in range(size):
        for x in range(size):
            fx, fy = (x + 0.5) / size * lattice, (y + 0.5) / size * lattice
            x0, y0 = int(fx) % lattice, int(fy) % lattice
            x1, y1 = (x0 + 1) % lattice, (y0 + 1) % lattice
            tx, ty = fx - int(fx), fy - int(fy)
            tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
            a = g[y0, x0] * (1 - tx) + g[y0, x1] * tx
            b = g[y1, x0] * (1 - tx) + g[y1, x1] * tx
            out[y, x] = a * (1 - ty) + b * ty
    return out

EDGE_N = periodic_noise(7, 4) * 0.45 + periodic_noise(11, 8) * 0.35 + periodic_noise(17, 16) * 0.2
SHADE_N = periodic_noise(3, 4) * 0.6 + periodic_noise(5, 8) * 0.4
FINE_N = periodic_noise(13, 16)

def hash01(x, y, s=0):
    h = (x * 374761393 + y * 668265263 + s * 2246822519) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0

# Corner weight with flat zones: the 4 px nearest an edge depend only on that
# edge's two corners, so neighbouring tiles always line up pixel-for-pixel.
MARGIN = 4
def w(p):
    t = np.clip((p + 0.5 - MARGIN) / (T - 2 * MARGIN), 0, 1)
    return t * t * (3 - 2 * t)

def field(corners):
    """corners: 2x2 array (TL,TR/BL,BR) of 0/1 -> 16x16 boolean 'is B' mask."""
    ys, xs = np.mgrid[0:T, 0:T]
    wx, wy = w(xs), w(ys)
    top = corners[0][0] * (1 - wx) + corners[0][1] * wx
    bot = corners[1][0] * (1 - wx) + corners[1][1] * wx
    f = top * (1 - wy) + bot * wy
    f = f + (EDGE_N - 0.5) * 0.85
    return f > 0.5

def big_mask(cgrid):
    """cgrid: (h+1)x(w+1) corner grid of 0/1 -> boolean mask for the whole map."""
    h, wd = cgrid.shape[0] - 1, cgrid.shape[1] - 1
    m = np.zeros((h * T, wd * T), bool)
    for ty in range(h):
        for tx in range(wd):
            m[ty * T:(ty + 1) * T, tx * T:(tx + 1) * T] = field(cgrid[ty:ty + 2, tx:tx + 2])
    return m

# ---------------------------------------------------------------- terrain painting
def paint_fill(kind, H, W, ox=0, oy=0):
    """Base texture for a terrain over an HxW area (pixel origin ox,oy for hashes)."""
    pal = PAL[kind]
    ys, xs = np.mgrid[0:H, 0:W]
    n = SHADE_N[(ys + oy) % T, (xs + ox) % T]
    fn = FINE_N[(ys + oy) % T, (xs + ox) % T]
    out = np.zeros((H, W, 3), np.uint8)
    for y in range(H):
        for x in range(W):
            v = n[y, x] * 0.7 + fn[y, x] * 0.3
            r = hash01(x + ox, y + oy, 1)
            if kind == "water":
                idx = 2 if v < 0.55 else 3
                if v < 0.32: idx = 1
                if r > 0.985: idx = 4
            elif kind == "grass":
                idx = 2 if v < 0.5 else 3
                if v < 0.3: idx = 1
                # little blade glints
                if r > 0.93: idx = 4
                elif r < 0.05: idx = 1
            else:
                idx = 2 if v < 0.58 else 3
                if v < 0.3: idx = 1
                if r > 0.96: idx = 4
                elif r < 0.03: idx = 0
            out[y, x] = pal[idx]
    return out

def render_pair(mask, kind_a, kind_b, style, ox=0, oy=0):
    """Paint an area where mask=False is kind_a and mask=True is kind_b."""
    H, W = mask.shape
    A = paint_fill(kind_a, H, W, ox, oy)
    B = paint_fill(kind_b, H, W, ox, oy)
    out = np.where(mask[..., None], B, A).copy()

    def m(y, x):
        return mask[min(max(y, 0), H - 1), min(max(x, 0), W - 1)]

    if style == "soft":
        pa, pb = PAL[kind_a], PAL[kind_b]
        for y in range(H):
            for x in range(W):
                nb = [m(y - 1, x), m(y + 1, x), m(y, x - 1), m(y, x + 1)]
                if mask[y, x] and not all(nb):
                    out[y, x] = pb[1]                      # darker rim on the top terrain
                elif mask[y, x] and not m(y + 2, x):
                    out[y, x] = pb[2] if hash01(x + ox, y + oy, 4) < .6 else pb[1]
                elif not mask[y, x] and (m(y - 1, x) or m(y - 2, x) and hash01(x + ox, y + oy, 5) < .5):
                    out[y, x] = pa[1]                      # soft shadow under the edge
    else:  # cliff: kind_b is water, kind_a is high ground
        rock, wat = PAL["rock"], PAL["water"]
        ground = ~mask
        face = np.zeros_like(mask)
        depth = np.zeros(mask.shape, int)
        for y in range(H):
            for x in range(W):
                if mask[y, x]:
                    for d in range(1, 4):
                        if not m(y - d, x):
                            face[y, x] = True
                            depth[y, x] = d
                            break
        for y in range(H):
            for x in range(W):
                gx, gy = x + ox, y + oy
                if ground[y, x]:
                    if m(y + 1, x) or m(y, x - 1) or m(y, x + 1) or m(y - 1, x):
                        out[y, x] = PAL["lip"] if m(y + 1, x) else PAL[kind_a][1]
                    elif m(y + 2, x) or m(y + 1, x - 1) or m(y + 1, x + 1):
                        out[y, x] = PAL[kind_a][3]
                elif face[y, x]:
                    d = depth[y, x]
                    stripe = hash01(gx, 0, 9)
                    idx = {1: 2, 2: 1, 3: 0}[d]
                    if stripe < 0.25: idx = max(idx - 1, 0)
                    if d == 1 and stripe > 0.7: idx = 3
                    out[y, x] = rock[idx]
                else:
                    near_ground = any(not m(y + dy, x + dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1))
                    below_face = y > 0 and face[y - 1, x] if y > 0 else False
                    side = (not m(y, x - 1) or not m(y, x + 1) or not m(y, x - 2) or not m(y, x + 2))
                    if near_ground or side:
                        # rocky bank on the sides, wet rock at the waterline
                        out[y, x] = rock[2] if side and (not m(y, x - 1) or not m(y, x + 1)) else rock[1]
                    elif below_face or (m(y - 1, x) and face[max(y - 1, 0), x]):
                        out[y, x] = PAL["foam"] if hash01(gx, gy, 6) < 0.7 else wat[4]
                    elif any(face[min(max(y - k, 0), H - 1), x] for k in (2, 3)):
                        out[y, x] = wat[1]                # shadow cast by the cliff
    return out

def render_tile(corners, kind_a, kind_b, style):
    """Render one 16px tile seamlessly by painting it inside its 3x3 neighbourhood."""
    c = np.array(corners)
    cg = np.zeros((4, 4), int)
    cg[1:3, 1:3] = c
    cg[0, 1:3], cg[3, 1:3] = c[0], c[1]
    cg[:, 0], cg[:, 3] = cg[:, 1], cg[:, 2]
    mask = big_mask(cg)
    img = render_pair(mask, kind_a, kind_b, style, ox=-T, oy=-T)
    return img[T:2 * T, T:2 * T]

PAIRS = [  # (A = base, B = painted over, style, label)
    ("dirt", "grass", "soft", "Dirt / Grass"),
    ("dirt", "gold", "soft", "Dirt / Golden meadow"),
    ("dirt", "water", "cliff", "Dirt cliff / River"),
    ("gold", "water", "cliff", "Meadow cliff / River"),
    ("grass", "water", "cliff", "Grass cliff / River"),
]
TERRAINS = ["dirt", "grass", "gold", "water"]
TERRAIN_NAMES = {"dirt": "Dirt", "grass": "Grass", "gold": "Golden Meadow", "water": "River"}
TERRAIN_COLORS = {"dirt": "Color(0.76, 0.48, 0.26, 1)", "grass": "Color(0.36, 0.6, 0.3, 1)",
                  "gold": "Color(0.87, 0.67, 0.29, 1)", "water": "Color(0.2, 0.41, 0.42, 1)"}

def corner_bits(i):
    # index = TL*8 + TR*4 + BL*2 + BR ; 1 means terrain B
    return [[(i >> 3) & 1, (i >> 2) & 1], [(i >> 1) & 1, i & 1]]

def build_terrain_sheet():
    W = len(PAIRS) * 4 * T
    sheet = np.zeros((5 * T, W, 4), np.uint8)
    tiles = []  # (col,row, corner terrains TL,TR,BL,BR, probability)
    for p, (a, b, style, _) in enumerate(PAIRS):
        for i in range(16):
            cb = corner_bits(i)
            col, row = p * 4 + i % 4, i // 4
            # skip duplicated pure tiles after the first pair that owns them
            sheet[row * T:(row + 1) * T, col * T:(col + 1) * T, :3] = render_tile(cb, a, b, style)
            sheet[row * T:(row + 1) * T, col * T:(col + 1) * T, 3] = 255
            names = [b if v else a for v in (cb[0][0], cb[0][1], cb[1][0], cb[1][1])]
            pure = len(set(names)) == 1
            tiles.append((col, row, names, 1.0 if not pure else 0.0))
    # bottom row: decorated full-tile variants
    row = 4
    deco = []
    for k, kind in enumerate(TERRAINS):
        for v in range(4):
            col = k * 4 + v
            t = paint_fill(kind, T, T, ox=v * 37 + 5, oy=v * 11 + 3)
            decorate(t, kind, v)
            sheet[row * T:(row + 1) * T, col * T:(col + 1) * T, :3] = t
            sheet[row * T:(row + 1) * T, col * T:(col + 1) * T, 3] = 255
            deco.append((col, row, [kind] * 4, 1.0 if v == 0 else 0.25))
    return sheet, tiles + deco

def decorate(t, kind, v):
    pal = PAL[kind]
    rng = np.random.default_rng(100 + v * 7 + TERRAINS.index(kind))
    if kind == "water":
        if v in (1, 2):  # small ripple lines
            y, x = rng.integers(3, 12), rng.integers(2, 9)
            t[y, x:x + 4] = pal[4]
            t[y + 1, x + 1:x + 3] = pal[3]
        if v == 3:
            for _ in range(3):
                y, x = rng.integers(2, 14), rng.integers(2, 14)
                t[y, x] = PAL["foam"]
        return
    if v == 0:
        return
    for _ in range(1 + v):  # grass tufts / pebbles / blades
        cx, cy = rng.integers(3, 13), rng.integers(4, 13)
        if kind in ("dirt",) and v == 3:
            t[cy, cx:cx + 2] = PAL["dirt"][4]; t[cy + 1, cx:cx + 2] = PAL["dirt"][1]
            t[cy + 1, cx + 2] = PAL["dirt"][0]; t[cy + 2, cx:cx + 2] = PAL["dirt"][0]
            continue
        hi = pal[4]; lo = pal[1]
        if kind == "dirt":
            hi, lo = PAL["gold"][3], PAL["gold"][1]
        for dx, h in ((-1, 2), (0, 3), (1, 2)):
            for k in range(h):
                if 0 <= cy - k < T and 0 <= cx + dx < T:
                    t[cy - k, cx + dx] = hi if k == h - 1 else lo

# ---------------------------------------------------------------- Godot TileSet
PEER = ["top_left_corner", "top_right_corner", "bottom_left_corner", "bottom_right_corner"]
QUAD = {  # collision quadrant per corner, tile-centred coords
    0: "-8, -8, 0, -8, 0, 0, -8, 0", 1: "0, -8, 8, -8, 8, 0, 0, 0",
    2: "-8, 0, 0, 0, 0, 8, -8, 8", 3: "0, 0, 8, 0, 8, 8, 0, 8"}

def write_tres(path, png_res_path, tiles):
    lines = ['[gd_resource type="TileSet" load_steps=3 format=3]', "",
             f'[ext_resource type="Texture2D" path="{png_res_path}" id="1_tex"]', "",
             '[sub_resource type="TileSetAtlasSource" id="TileSetAtlasSource_wild"]',
             'texture = ExtResource("1_tex")']
    seen_pure = set()
    for col, row, names, prob in tiles:
        pure = len(set(names)) == 1
        if pure and prob == 0.0:
            # plain full tiles inside each 16-block: keep as low-weight extras
            prob = 0.5 if names[0] not in seen_pure else 0.15
            seen_pure.add(names[0])
        # Godot's corner mode also matches the tile's centre terrain, so every
        # mixed tile gets one alternative per terrain it contains.
        centers = sorted(set(names), key=lambda n: (-names.count(n), TERRAINS.index(n)))
        for alt, center in enumerate(centers):
            k = f"{col}:{row}/{alt}"
            lines.append(f"{k} = {alt}")
            if prob != 1.0:
                lines.append(f"{k}/probability = {prob}")
            lines.append(f"{k}/terrain_set = 0")
            lines.append(f"{k}/terrain = {TERRAINS.index(center)}")
            polys = []
            for ci, n in enumerate(names):
                lines.append(f"{k}/terrains_peering_bit/{PEER[ci]} = {TERRAINS.index(n)}")
                if n == "water":
                    polys.append(QUAD[ci])
            if len(polys) == 4:
                polys = ["-8, -8, 8, -8, 8, 8, -8, 8"]
            for pi, pts in enumerate(polys):
                lines.append(f"{k}/physics_layer_0/polygon_{pi}/points = PackedVector2Array({pts})")
    lines += ["", "[resource]", "physics_layer_0/collision_layer = 1",
              "terrain_set_0/mode = 1"]
    for i, t in enumerate(TERRAINS):
        lines.append(f'terrain_set_0/terrain_{i}/name = "{TERRAIN_NAMES[t]}"')
        lines.append(f"terrain_set_0/terrain_{i}/color = {TERRAIN_COLORS[t]}")
    lines.append('sources/0 = SubResource("TileSetAtlasSource_wild")')
    open(path, "w").write("\n".join(lines) + "\n")

# ---------------------------------------------------------------- props
def blob(w_, h_, seed, rough=0.12):
    rng = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:h_, 0:w_]
    nx, ny = (xs + 0.5 - w_ / 2) / (w_ / 2), (ys + 0.5 - h_ / 2) / (h_ / 2)
    ang = np.arctan2(ny, nx)
    k = rng.random(3) * 2 * np.pi
    r = 1 - rough * (np.sin(3 * ang + k[0]) * .5 + np.sin(5 * ang + k[1]) * .3 + np.sin(2 * ang + k[2]) * .4)
    return nx * nx + ny * ny < r * r * 0.92, nx, ny

def shade_blob(img, ox, oy, mask, nx, ny, pal, outline=True, light=(-0.6, -0.8)):
    h_, w_ = mask.shape
    nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
    lum = (-nx * light[0] * -1 * -1 + 0) if False else None
    lx, ly, lz = -0.55, -0.7, 0.55
    L = np.clip(nx * lx + ny * ly + nz * lz, 0, 1)
    for y in range(h_):
        for x in range(w_):
            if not mask[y, x]:
                continue
            v = L[y, x] + (hash01(x, y, 21) - 0.5) * 0.12
            idx = 0 if v < 0.15 else 1 if v < 0.38 else 2 if v < 0.62 else 3 if v < 0.85 else 4
            img[oy + y, ox + x] = (*pal[idx], 255)
    if outline:
        H, W = img.shape[:2]
        for y in range(h_):
            for x in range(w_):
                if mask[y, x]:
                    continue
                if any(0 <= y + dy < h_ and 0 <= x + dx < w_ and mask[y + dy, x + dx]
                       for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0))):
                    img[oy + y, ox + x] = (*PAL["outline"], 255)

def ground_shadow(img, cx, cy, rx, ry):
    H, W = img.shape[:2]
    for y in range(H):
        for x in range(W):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 < 1 and img[y, x, 3] == 0:
                img[y, x] = (20, 30, 36, 90)

def boulder(w_, h_, seed):
    img = np.zeros((h_ + 3, w_ + 2, 4), np.uint8)
    ground_shadow(img, (w_ + 2) / 2 + 1, h_ - 1, w_ / 2 + 0.5, 3.2)
    mask, nx, ny = blob(w_, h_, seed)
    shade_blob(img, 1, 0, np.pad(mask, 0), nx, ny, PAL["rock"][1:] + [hexc("9aa29c")])
    # a crack/seam for character
    rng = np.random.default_rng(seed)
    x = int(w_ * (0.45 + rng.random() * 0.2)); y = int(h_ * 0.35)
    for k in range(int(h_ * 0.35)):
        if mask[min(y + k, h_ - 1), min(x, w_ - 1)]:
            img[y + k, 1 + x] = (*PAL["rock"][1], 255)
        x += rng.integers(-1, 2) if k % 2 else 0
    return img

def mushroom_cluster(seed, glow=False):
    img = np.zeros((16, 16, 4), np.uint8)
    rng = np.random.default_rng(seed)
    cap = [hexc(c) for c in ("4a2420", "6e3424", "934632", "b0603e", "cf8a5e")]
    if glow:
        cap = [hexc(c) for c in ("1d3c4a", "1f6a74", "3fa3a0", "7fd6c4", "d2fff0")]
    stem = [hexc("cdb8a0"), hexc("efe0c8")]
    ground_shadow(img, 8, 13.5, 6.5, 2)
    spots = [(4, 9, 5, 4), (9, 11, 6, 5), (11, 7, 4, 3)] if seed % 2 else [(5, 8, 6, 5), (10, 10, 5, 4)]
    for (cx, by, cw, ch) in spots:
        # stem
        for y in range(by - 1, by + 3):
            if 0 <= y < 16:
                img[y, cx] = (*stem[1], 255); img[y, cx + 1] = (*stem[0], 255)
        m, nx, ny = blob(cw, ch, seed + cx, rough=0.04)
        m[ch // 2 + 1:, :] &= np.abs(nx[ch // 2 + 1:, :]) < 0.7
        sub = np.zeros((ch + 2, cw + 2, 4), np.uint8)
        shade_blob(sub, 1, 1, np.pad(m, ((0, 1), (0, 1)))[:ch, :cw], nx, ny, cap)
        ox, oy = cx - cw // 2, by - ch - 1
        for y in range(sub.shape[0]):
            for x in range(sub.shape[1]):
                if sub[y, x, 3] and 0 <= oy + y < 16 and 0 <= ox + x < 16:
                    img[oy + y, ox + x] = sub[y, x]
        if cw >= 5:
            img[oy + 2, ox + cw // 2] = (*cap[4], 255)
    return img

def shrub(seed, w_=24, h_=20, pal=None):
    pal = pal or PAL["grass"]
    img = np.zeros((h_, w_, 4), np.uint8)
    ground_shadow(img, w_ / 2, h_ - 2.5, w_ / 2 - 1, 2.5)
    rng = np.random.default_rng(seed)
    full = np.zeros((h_, w_), bool)
    lights = np.zeros((h_, w_))
    for _ in range(7):
        r = rng.uniform(3.5, 5.5)
        cx, cy = rng.uniform(r + 1, w_ - r - 1), rng.uniform(r + 1, h_ - r - 3)
        ys, xs = np.mgrid[0:h_, 0:w_]
        d = np.sqrt((xs + .5 - cx) ** 2 + (ys + .5 - cy) ** 2) / r
        inside = d < 1
        L = np.clip(1 - np.sqrt(((xs + .5 - (cx - r * .35)) / r) ** 2 + ((ys + .5 - (cy - r * .4)) / r) ** 2), 0, 1)
        lights = np.where(inside, np.maximum(lights * (~inside) + L * inside, L * inside), lights)
        full |= inside
    yy = np.mgrid[0:h_, 0:w_][0]
    for y in range(h_):
        for x in range(w_):
            if full[y, x]:
                v = lights[y, x] * 1.1 - (y / h_) * 0.25 + (hash01(x, y, seed) - .5) * .2
                idx = 0 if v < .05 else 1 if v < .25 else 2 if v < .45 else 3 if v < .65 else 4
                img[y, x] = (*pal[idx], 255)
            elif any(0 <= y + dy < h_ and 0 <= x + dx < w_ and full[y + dy, x + dx]
                     for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0))):
                img[y, x] = (*PAL["outline"], 255)
    return img

def wheat(stage):
    img = np.zeros((32, 16, 4), np.uint8)
    stalk = [hexc("6f8a3a"), hexc("93a848")] if stage < 3 else [hexc("a37a2c"), hexc("c99a3a")]
    head = PAL["gold"]
    heights = [6, 12, 18, 22][stage]
    xs = [3, 6, 8, 10, 13] if stage > 0 else [5, 8, 11]
    ground_shadow(img, 8, 30, 6.5, 1.8)
    for i, x in enumerate(xs):
        h = heights - (i % 2) * 2
        lean = (i - len(xs) // 2) * 0.12
        for k in range(h):
            yy, xx = 30 - k, int(round(x + lean * k))
            if 0 <= xx < 16:
                img[yy, xx] = (*stalk[k % 3 == 0], 255)
        if stage >= 2:
            tx, ty = int(round(x + lean * h)), 30 - h
            for k in range(5 if stage == 3 else 3):
                for dx in (-1, 0):
                    xx = tx + dx
                    if 0 <= xx < 16 and 0 <= ty + k < 32:
                        img[ty + k, xx] = (*head[4 - (k + (dx == 0)) % 3 - (stage < 3)], 255)
            if 0 <= tx + 1 < 16 and 0 <= ty - 1:
                img[ty - 1, tx] = (*head[4], 255)
        elif stage == 1:
            img[30 - h, min(max(int(round(x + lean * h)), 0), 15)] = (*stalk[1], 255)
    return img

def tuft(kind, seed):
    img = np.zeros((16, 16, 4), np.uint8)
    rng = np.random.default_rng(seed)
    pal = PAL[kind]
    for _ in range(4):
        cx, base = rng.integers(3, 13), rng.integers(11, 15)
        h = rng.integers(3, 7)
        for dx in (-1, 0, 1):
            hh = h - abs(dx) * 2
            for k in range(max(hh, 1)):
                img[base - k, cx + dx] = (*(pal[4] if k == hh - 1 else pal[2] if k > 1 else pal[1]), 255)
    return img

def pebbles(seed):
    img = np.zeros((16, 16, 4), np.uint8)
    rng = np.random.default_rng(seed)
    for _ in range(3):
        cx, cy = rng.integers(3, 12), rng.integers(5, 13)
        w_, h_ = rng.integers(3, 5), rng.integers(2, 4)
        m, nx, ny = blob(w_, h_, seed + cx, 0.05)
        sub = np.zeros((h_, w_, 4), np.uint8)
        shade_blob(sub, 0, 0, m, nx, ny, PAL["rock"][1:] + [hexc("9aa29c")], outline=False)
        for y in range(h_):
            for x in range(w_):
                if sub[y, x, 3]:
                    img[cy + y, cx + x] = sub[y, x]
    return img

def paste(sheet, sprite, x, y):
    h_, w_ = sprite.shape[:2]
    region = sheet[y:y + h_, x:x + w_].astype(np.float32)
    src = sprite.astype(np.float32)
    a = src[..., 3:] / 255.0
    rgb = src[..., :3] * a + region[..., :3] * (1 - a)
    alpha = np.maximum(region[..., 3:], src[..., 3:])
    sheet[y:y + h_, x:x + w_] = np.concatenate([rgb, alpha], -1).round().astype(np.uint8)

def build_props():
    """Returns {name: RGBA array}. Each sheet uses a fixed cell size noted in the README."""
    out = {}
    # rocks: 32x32 cells (large, medium x2, cluster) + 16x16 small
    rocks = np.zeros((32, 128, 4), np.uint8)
    paste(rocks, boulder(26, 22, 1), 2, 6)
    paste(rocks, boulder(22, 18, 4), 36, 10)
    paste(rocks, boulder(18, 16, 9), 70, 12)
    pair = np.zeros((32, 32, 4), np.uint8)
    paste(pair, boulder(18, 17, 12), 1, 10)
    paste(pair, boulder(14, 13, 15), 16, 15)
    paste(rocks, pair, 96, 0)
    out["rocks_32"] = rocks
    small = np.zeros((16, 64, 4), np.uint8)
    paste(small, boulder(12, 10, 21), 1, 3)
    paste(small, boulder(10, 9, 23), 18, 4)
    paste(small, pebbles(5), 32, 0)
    paste(small, pebbles(8), 48, 0)
    out["rocks_16"] = small
    mush = np.zeros((16, 64, 4), np.uint8)
    for i, (s, g) in enumerate([(1, False), (2, False), (3, True), (4, True)]):
        paste(mush, mushroom_cluster(s, g), i * 16, 0)
    out["mushrooms_16"] = mush
    shr = np.zeros((24, 96, 4), np.uint8)
    paste(shr, shrub(3), 0, 2 - 2)
    paste(shr, shrub(8), 24, 0)
    paste(shr, shrub(5, pal=PAL["gold"]), 48, 0)
    teal = [hexc(c) for c in ("1d3438", "28504f", "39706a", "52948a", "86c4b4")]
    paste(shr, shrub(11, pal=teal), 72, 0)
    out["shrubs_24"] = shr
    wh = np.zeros((32, 64, 4), np.uint8)
    for s in range(4):
        paste(wh, wheat(s), s * 16, 0)
    out["wheat_stages_16x32"] = wh
    tf = np.zeros((16, 64, 4), np.uint8)
    paste(tf, tuft("grass", 1), 0, 0)
    paste(tf, tuft("grass", 2), 16, 0)
    paste(tf, tuft("gold", 3), 32, 0)
    paste(tf, tuft("gold", 4), 48, 0)
    out["tufts_16"] = tf
    return out

# ---------------------------------------------------------------- preview scene
def scene_corners(W, H):
    """Corner grid of terrain ids for a demo map: dirt base, grass NE, meadow W, river N->S.
    3-terrain tiles are resolved the way you would paint them in Godot (no such tiles exist)."""
    D, G, M, R = (TERRAINS.index(k) for k in ("dirt", "grass", "gold", "water"))
    ys, xs = np.mgrid[0:H + 1, 0:W + 1]
    river_x = 9 + np.round(2.2 * np.sin(ys / 3.2) + 0.8 * np.sin(ys / 1.7)).astype(int)
    c = np.full(xs.shape, D)
    c[(xs > river_x + 6 + np.round(np.sin(ys / 2.5) * 1.5)) & (ys < H * 0.55 + np.sin(xs) * 1.5)] = G
    c[(xs < river_x - 3 + np.round(np.cos(ys / 2.0))) & (ys > 3)] = M
    c[(xs >= river_x) & (xs <= river_x + 2)] = R
    for _ in range(10):
        changed = False
        for ty in range(H):
            for tx in range(W):
                q = c[ty:ty + 2, tx:tx + 2]
                kinds = set(q.flatten())
                if len(kinds) > 2:
                    land = [k for k in kinds if k not in (D, R)][0]
                    q[q == D] = land
                    changed = True
        if not changed:
            break
    return c

def tile_lookup(tiles):
    lut = {}
    for col, row, names, prob in tiles:
        key = tuple(names)
        if key not in lut or (len(set(names)) == 1 and row == 4 and prob == 1.0):
            lut.setdefault(key, [])
        lut.setdefault(key, []).append((col, row, prob))
    return lut

def render_scene(sheet_img, tiles, W=22, H=16):
    c = scene_corners(W, H)
    lut = tile_lookup(tiles)
    sheet = np.asarray(sheet_img)
    out = np.zeros((H * T, W * T, 4), np.uint8)
    wm = np.zeros((H * T, W * T), bool)
    for ty in range(H):
        for tx in range(W):
            key = tuple(TERRAINS[v] for v in (c[ty, tx], c[ty, tx + 1], c[ty + 1, tx], c[ty + 1, tx + 1]))
            opts = lut[key]
            if len(set(key)) == 1:
                deco = [o for o in opts if o[1] == 4]
                r = hash01(tx, ty, 77)
                col, row, _ = deco[0] if r < 0.6 or len(deco) == 1 else deco[1 + int(hash01(tx, ty, 78) * (len(deco) - 1))]
            else:
                col, row, _ = opts[0]
            out[ty * T:(ty + 1) * T, tx * T:(tx + 1) * T] = sheet[row * T:(row + 1) * T, col * T:(col + 1) * T]
            if "water" in key:
                wm[ty * T:(ty + 1) * T, tx * T:(tx + 1) * T] |= field(
                    [[key[0] == "water", key[1] == "water"], [key[2] == "water", key[3] == "water"]])
    return out, wm

def dilate(m, n):
    m = m.copy()
    for _ in range(n):
        p = np.pad(m, 1)
        m = p[1:-1, 1:-1] | p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    return m

def place_props(img, wm, props):
    rng = np.random.default_rng(3)
    H, W = img.shape[:2]
    blocked = dilate(wm, 6)
    spr = []
    r = props["rocks_32"]; s = props["rocks_16"]; mu = props["mushrooms_16"]; sh = props["shrubs_24"]
    wh = props["wheat_stages_16x32"]; tf = props["tufts_16"]
    cells = [(r[:, i * 32:(i + 1) * 32], 32) for i in range(4)]
    smalls = [s[:, i * 16:(i + 1) * 16] for i in range(4)] + [mu[:, i * 16:(i + 1) * 16] for i in range(2)] \
        + [tf[:, i * 16:(i + 1) * 16] for i in range(4)] * 2
    shrubs = [sh[:, i * 24:(i + 1) * 24] for i in range(3)]
    placed = []
    def ok(x, y, w_, h_):
        if x < 0 or y < 0 or x + w_ > W or y + h_ > H: return False
        if blocked[y:y + h_, x:x + w_].any(): return False
        return all(abs(x + w_ / 2 - px) > (w_ + pw) / 2 or abs(y + h_ / 2 - py) > (h_ + ph) / 2 for px, py, pw, ph in placed)
    def drop(sprite, tries=200):
        h_, w_ = sprite.shape[:2]
        for _ in range(tries):
            x, y = int(rng.integers(0, W - w_)), int(rng.integers(0, H - h_))
            if ok(x, y, w_, h_):
                placed.append((x + w_ / 2, y + h_ / 2, w_, h_)); spr.append((y + h_, x, y, sprite)); return
    for c, _ in cells * 2: drop(c)
    for c in shrubs * 2: drop(c)
    for k in range(3): drop(wh[:, 48:64])
    for c in smalls * 2: drop(c)
    for _, x, y, sprite in sorted(spr, key=lambda t: t[0]):
        paste(img, sprite, x, y)
    return img

# ---------------------------------------------------------------- main
def save(arr, path, mode="RGBA"):
    Image.fromarray(arr, mode).save(path)

def upscale(img, k):
    return img.resize((img.width * k, img.height * k), Image.NEAREST)

def main():
    os.makedirs(TILE_DIR, exist_ok=True)
    os.makedirs(PROP_DIR, exist_ok=True)
    sheet, tiles = build_terrain_sheet()
    day = Image.fromarray(sheet, "RGBA")
    day.save(os.path.join(TILE_DIR, "wildlands_terrain.png"))
    grade_dusk(day).save(os.path.join(TILE_DIR, "wildlands_terrain_dusk.png"))
    write_tres(os.path.join(TILE_DIR, "wildlands_terrain.tres"),
               "res://assets/Tilesets/Wildlands/wildlands_terrain.png", tiles)
    write_tres(os.path.join(TILE_DIR, "wildlands_terrain_dusk.tres"),
               "res://assets/Tilesets/Wildlands/wildlands_terrain_dusk.png", tiles)

    props = build_props()
    for name, arr in props.items():
        im = Image.fromarray(arr, "RGBA")
        im.save(os.path.join(PROP_DIR, f"{name}.png"))
        grade_dusk(im).save(os.path.join(PROP_DIR, f"{name}_dusk.png"))

    # previews
    scene, wm = render_scene(day, tiles)
    scene = place_props(scene, wm, props)
    sc = Image.fromarray(scene, "RGBA")
    upscale(sc, 4).save(os.path.join(HERE, "PREVIEW_do_not_import_wildlands_scene.png"))
    upscale(grade_dusk(sc), 4).save(os.path.join(HERE, "PREVIEW_do_not_import_wildlands_scene_dusk.png"))
    # labelled sheet preview on a dark backdrop
    pw = max(day.width, 128)
    canvas = Image.new("RGBA", (pw, day.height + 4 + 32 + 4 + 24 + 4 + 32), (30, 30, 38, 255))
    canvas.paste(day, (0, 0))
    y = day.height + 4
    x = 0
    for name in ("rocks_32", "wheat_stages_16x32"):
        im = Image.fromarray(props[name], "RGBA"); canvas.alpha_composite(im, (x, y)); x += im.width + 4
    y += 36; x = 0
    for name in ("shrubs_24", "mushrooms_16", "tufts_16"):
        im = Image.fromarray(props[name], "RGBA"); canvas.alpha_composite(im, (x, y)); x += im.width + 4
    y += 28; x = 0
    im = Image.fromarray(props["rocks_16"], "RGBA"); canvas.alpha_composite(im, (x, y))
    upscale(canvas, 4).save(os.path.join(HERE, "PREVIEW_do_not_import_wildlands_sheets.png"))
    print("ok", len(tiles), "tiles")

if __name__ == "__main__":
    main()
