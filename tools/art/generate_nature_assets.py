"""Skybloom nature retexture (original pixel art, Pillow + numpy).

Repaints the ground and nature sheets used by tilesets/game_tilesets.tres in the
Skyfall Village / Wildlands style, keeping every sheet's size and tile layout
the same as the sheet it replaces, so terrain bits, collisions and scene tiles
keep working:

  Grass.png                   -> assets/Tilesets/Nature/grass_terrain.png
  Tilled_Dirt_Wide.png        -> assets/Tilesets/Nature/tilled_dirt.png
  Water.png                   -> assets/Tilesets/Nature/water.png (4 frames)
  Basic Grass Biom things 1   -> assets/Objects/Nature/nature_props.png

It also rebuilds the Wildlands corner terrain (dirt, grass, golden meadow,
river) with the same grass colours into assets/Tilesets/Wildlands/, and adds
it to game_tilesets.tres as extra source 6 / terrain set 1 for later use.

Run from the repo root:  python3 tools/art/generate_nature_assets.py
"""
import math
import os
import re
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wildlands as wl  # noqa: E402

GAME = os.path.normpath(os.path.join(HERE, "..", "..", "skybloom-game"))
ASSETS = os.path.join(GAME, "assets")
T = 16
hexc = wl.hexc

# ---------------------------------------------------------------- palette
# Grass matches the Skyfall Village mockup; it replaces the Wildlands grass so
# every grass tile in the game is the same green.
GRASS = [hexc(c) for c in ("356640", "4e8c46", "62a94c", "84c25a", "b2dc76")]
wl.PAL["grass"] = GRASS
GRASS_MID = tuple((a + b) // 2 for a, b in zip(GRASS[2], GRASS[3]))
GRASS_LOW = tuple((a + b) // 2 for a, b in zip(GRASS[1], GRASS[2]))
WATER = wl.PAL["water"]
SOIL = [hexc(c) for c in ("4a2e24", "6a442e", "84583a", "9c6c46", "b8875a")]
BARK = [hexc(c) for c in ("36221e", "503426", "704a32", "946642")]
LEAF = [hexc(c) for c in ("1a3822", "2a5e32", "40843c", "64a84a", "a0d064")]
PINE_LEAF = [hexc(c) for c in ("10302a", "1a4c34", "28703e", "46924a", "82be62")]
ROCK = wl.PAL["rock"][1:] + [hexc("9aa29c")]
OUT = wl.PAL["outline"]
WHITE = hexc("f4f0e0")
RED = [hexc(c) for c in ("5a1a22", "9a2a30", "cc4a3e", "f08a6a")]
BERRY = [hexc(c) for c in ("2a1438", "4a2a6a", "6e4aa0", "a488d0")]


def rgba(c, a=255):
    return (*c, a)


def blank(w, h):
    return np.zeros((h, w, 4), np.uint8)


def outline(img, col=OUT, diag=False):
    """1px rim around the solid pixels (ground shadows don't count as solid)."""
    a = img[..., 3] == 255
    n = np.zeros_like(a)
    n[1:, :] |= a[:-1, :]
    n[:-1, :] |= a[1:, :]
    n[:, 1:] |= a[:, :-1]
    n[:, :-1] |= a[:, 1:]
    if diag:
        n[1:, 1:] |= a[:-1, :-1]
        n[:-1, :-1] |= a[1:, 1:]
    img[n & ~a] = rgba(col)
    return img


def over(dst, src, x, y):
    """Alpha-composite src onto dst at (x, y), clipped to dst."""
    h, w = src.shape[:2]
    H, W = dst.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x0 >= x1 or y0 >= y1:
        return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x].astype(np.float32)
    d = dst[y0:y1, x0:x1].astype(np.float32)
    a = s[..., 3:] / 255.0
    rgb = s[..., :3] * a + d[..., :3] * (1 - a)
    al = np.maximum(d[..., 3:], s[..., 3:])
    dst[y0:y1, x0:x1] = np.concatenate([rgb, al], -1).round().astype(np.uint8)


def shadow(img, cx, cy, rx, ry, a=80):
    H, W = img.shape[:2]
    ys, xs = np.mgrid[0:H, 0:W]
    m = ((xs + .5 - cx) / rx) ** 2 + ((ys + .5 - cy) / ry) ** 2 < 1
    img[m & (img[..., 3] == 0)] = (20, 30, 36, a)


def hash01(x, y, s=0):
    return wl.hash01(int(x), int(y), s)


# ---------------------------------------------------------------- terrain sheets
def grass_fill(H, W, ox=0, oy=0):
    """Calm village-style grass: two soft tones, sparse speckles and small tufts.
    Tufts stay inside each 16px cell so tile edges always line up."""
    ys, xs = np.mgrid[0:H, 0:W]
    n = wl.SHADE_N[(ys + oy) % T, (xs + ox) % T]
    out = np.zeros((H, W, 3), np.uint8)
    out[:] = GRASS[2]
    out[n > .55] = GRASS_MID
    for y in range(H):
        for x in range(W):
            gx, gy = x + ox, y + oy
            r = hash01(gx, gy, 1)
            if r > .975:
                out[y, x] = GRASS[3]
            elif r < .025:
                out[y, x] = GRASS_LOW
            tx, ty = gx % T, gy % T
            if 2 <= tx <= 13 and 3 <= ty <= 14 and hash01(gx, gy, 7) < .018:
                out[y, x] = GRASS[1]
                if y > 0:
                    out[y - 1, x - 1] = GRASS[3]
                    out[y - 1, x + 1 if x + 1 < W else x] = GRASS[4]
    return out


_paint_fill = wl.paint_fill
wl.paint_fill = lambda kind, H, W, ox=0, oy=0: grass_fill(H, W, ox, oy) if kind == "grass" else _paint_fill(kind, H, W, ox, oy)


def recolor(src_path, rules, fill):
    """Repaint a sheet pixel by pixel. rules maps old RGB -> new RGB (or None for
    'use fill'); fill(x, y) gives the textured base colour. Alpha is kept."""
    im = np.asarray(Image.open(src_path).convert("RGBA"))
    out = np.zeros_like(im)
    H, W = im.shape[:2]
    for y in range(H):
        for x in range(W):
            r, g, b, a = im[y, x]
            if a == 0:
                continue
            new = rules.get((int(r), int(g), int(b)), None)
            out[y, x] = rgba(fill(x, y) if new is None else new, a)
    return out


def grass_sheet():
    tex = wl.paint_fill("grass", 112, 176)
    rules = {
        (120, 161, 88): GRASS[0],   # outer rim
        (164, 194, 99): GRASS[1],   # inner rim
        (192, 212, 112): None,      # fill
        (210, 224, 119): GRASS[3],  # light patches
        (232, 238, 170): GRASS[4],  # blades
        (234, 225, 120): hexc("f2cf5a"),  # flower heads
    }
    sheet = recolor(os.path.join(ASSETS, "Tilesets", "Grass.png"), rules, lambda x, y: tex[y, x])
    # rows 5-6 are decoration tiles: soften their dark patches
    deco = sheet[5 * T:, :]
    deco[(deco[..., 3] > 0) & np.all(deco[..., :3] == GRASS[1], -1)] = rgba(GRASS_LOW)
    # a highlight row just inside the top rim so edges read as a raised lip
    a = sheet[..., 3] > 0
    for y in range(1, sheet.shape[0] - 1):
        for x in range(sheet.shape[1]):
            if a[y, x] and tuple(sheet[y - 1, x, :3]) == GRASS[1] and tuple(sheet[y, x, :3]) not in (GRASS[0], GRASS[1]):
                if a[y + 1, x] and hash01(x, y, 3) < .7:
                    sheet[y, x] = rgba(GRASS[3])
    return sheet


def soil_fill(x, y):
    k = y % 4
    v = hash01(x, y, 8)
    idx = 3 if k == 0 else 1 if k == 3 else 2
    if v > .9:
        idx = min(idx + 1, 4)
    elif v < .08:
        idx = max(idx - 1, 1)
    return SOIL[idx]


def dirt_sheet():
    rules = {
        (232, 207, 166): None,
        (220, 185, 138): SOIL[0],
        (225, 195, 151): SOIL[1],
        (237, 218, 181): SOIL[4],
        (164, 194, 99): GRASS[1],
        (192, 212, 112): GRASS[2],
    }
    return recolor(os.path.join(ASSETS, "Tilesets", "Tilled_Dirt_Wide.png"), rules, soil_fill)


def water_sheet():
    base = wl.paint_fill("water", T, T)
    sheet = blank(4 * T, T)
    rng = np.random.default_rng(4)
    ripples = [(int(rng.integers(0, 16)), int(rng.integers(0, 16)), int(rng.integers(2, 5))) for _ in range(3)]
    for f in range(4):
        tile = np.roll(base, f * 4, axis=1)
        tile = np.concatenate([tile, np.full((T, T, 1), 255, np.uint8)], -1)
        for i, (rx, ry, ln) in enumerate(ripples):
            x0 = (rx + f * 2 + i) % T
            phase = (f + i) % 4
            col = WATER[4] if phase in (0, 1) else WATER[3]
            for k in range(ln - (phase == 3)):
                tile[ry, (x0 + k) % T] = rgba(col)
        sheet[:, f * T:(f + 1) * T] = tile
    return sheet


# ---------------------------------------------------------------- canopy / props
def leafy(w, h, blobs, pal, seed, edge_dark=True):
    """Clumpy round canopy from overlapping circles, lit from the top left."""
    rnd = np.random.default_rng(seed)
    img = blank(w, h)
    lx, ly = -0.55, -0.83
    for cx, cy, r in sorted(blobs, key=lambda b: b[1]):
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                if not (0 <= x < w and 0 <= y < h):
                    continue
                dx, dy = x + .5 - cx, y + .5 - cy
                d = math.hypot(dx, dy)
                ang = math.atan2(dy, dx)
                rr = r + 0.8 * math.sin(ang * 6 + cx * 1.7)
                if d > rr:
                    continue
                v = (dx * lx + dy * ly) / max(r, 1) + rnd.uniform(-.1, .1)
                if edge_dark and d > rr - 1.2 and dy > -r * .2:
                    k = 1
                elif v > .5:
                    k = 4
                elif v > .1:
                    k = 3
                elif v > -.4:
                    k = 2
                else:
                    k = 1
                img[y, x] = rgba(pal[k])
    # leaf-clump texture: a few darker ticks inside the canopy
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if img[y, x, 3] and hash01(x, y, seed) < .05 and tuple(img[y, x, :3]) == pal[3]:
                img[y, x] = rgba(pal[2])
    return outline(img, pal[0])


def trunk(w, h, cx, top, bot, half):
    img = blank(w, h)
    for y in range(top, bot + 1):
        flare = 1 if y >= bot - 1 else 0
        for x in range(cx - half - flare, cx + half + flare + 1):
            rel = (x - (cx - half - flare)) / max(2 * (half + flare), 1)
            k = 3 if rel < .3 else 2 if rel < .65 else 1
            if (x * 3 + y) % 5 == 0:
                k = max(1, k - 1)
            img[y, x] = rgba(BARK[k])
    return outline(img, BARK[0])


def tree(w, h, blobs, trunk_args, seed, pal=LEAF, fruit=None, shadow_r=(9, 2.5)):
    img = blank(w, h)
    tx, ttop, tbot, half = trunk_args
    shadow(img, tx + .5, tbot + .5, *shadow_r)
    over(img, trunk(w, h, *trunk_args), 0, 0)
    over(img, leafy(w, h, blobs, pal, seed), 0, 0)
    for fx, fy in fruit or []:
        img[fy, fx] = rgba(RED[2])
        img[fy, fx + 1] = rgba(RED[1])
        img[fy + 1, fx] = rgba(RED[1])
        img[fy + 1, fx + 1] = rgba(RED[0])
        img[fy, fx] = rgba(RED[3]) if hash01(fx, fy, 1) < .5 else rgba(RED[2])
    return img


def small_tree():  # 16x32, the choppable tree scene uses this cell
    return tree(16, 32, [(8, 15, 6), (5, 12, 4), (11, 12, 4), (8, 8, 5), (8, 4, 3.5)],
                (8, 18, 29, 1), 11, shadow_r=(6, 2))


def oak():  # 32x32
    return tree(32, 32, [(16, 17, 9), (8, 15, 6), (24, 15, 6), (16, 10, 8), (10, 8, 5), (22, 8, 5), (16, 4, 4)],
                (16, 21, 29, 2), 5, shadow_r=(11, 2.5))


def fruit_tree():  # 32x32
    return tree(32, 32, [(16, 17, 9), (8, 15, 6), (24, 15, 6), (16, 10, 8), (10, 8, 5), (22, 8, 5), (16, 4, 4)],
                (16, 21, 29, 2), 9, fruit=[(10, 12), (20, 8), (15, 17), (24, 15), (8, 18)], shadow_r=(11, 2.5))


def bush(w, h, seed, pal=LEAF, berries=None, berry=RED):
    img = blank(w, h)
    shadow(img, w / 2, h - 2, w / 2 - 1, 2)
    rng = np.random.default_rng(seed)
    blobs = []
    n = max(3, w // 4)
    for i in range(n):
        r = rng.uniform(3.6, 4.8) if h <= 16 else rng.uniform(4.5, 6)
        cx = r + .5 + (w - 2 * r - 1) * (i + .5) / n + rng.uniform(-1, 1)
        cy = h - r - 3 + rng.uniform(-1.5, 0)
        blobs.append((cx, cy, r))
    blobs.append((w / 2, h - 2 - min(w, h) * .55, min(w, h) * .38))
    over(img, leafy(w, h, blobs, pal, seed), 0, 0)
    for bx, by in berries or []:
        img[by, bx] = rgba(berry[2])
        img[by, bx + 1] = rgba(berry[1])
        img[by + 1, bx] = rgba(berry[1])
        img[by + 1, bx + 1] = rgba(berry[0])
        img[by, bx] = rgba(berry[3])
    return img


def item_outline(img):
    """Pickup icons get a white rim like the original sheet's items."""
    img = outline(img, OUT)
    return outline(img, WHITE)


def mushroom(cap_pal, cells, size=16, glow=False):
    img = blank(size, size)
    shadow(img, size / 2, size - 3, size / 2 - 2, 1.6)
    stem = [hexc("bfa88e"), hexc("efe0c8")]
    for cx, by, cw, ch in cells:
        for y in range(by - 1, by + 3):
            img[y, cx] = rgba(stem[1])
            img[y, cx + 1] = rgba(stem[0])
        ox, oy = cx + 1 - cw // 2, by - ch
        for y in range(ch):
            for x in range(cw):
                nx = (x + .5 - cw / 2) / (cw / 2)
                ny = (y + .5) / ch
                if nx * nx * (0.4 + ny) > 1.0 - 0.2 * (y == 0):
                    continue
                v = -nx * .5 - (ny - .5) * 1.2 + (hash01(x, y, cx) - .5) * .2
                k = 4 if v > .7 else 3 if v > .25 else 2 if v > -.3 else 1
                img[oy + y, ox + x] = rgba(cap_pal[k])
        if cw >= 5:
            img[oy + 1, ox + 1] = rgba(cap_pal[4] if not glow else WHITE)
            img[oy + 2, ox + cw - 2] = rgba(cap_pal[4] if not glow else WHITE)
    outline(img, cap_pal[0])
    if glow:  # soft halo so they read as glowing in the dusk ground world
        halo = img[..., 3] == 0
        ys, xs = np.mgrid[0:size, 0:size]
        near = np.zeros_like(halo)
        for cx, by, cw, ch in cells:
            near |= (xs + .5 - cx - 1) ** 2 + (ys + .5 - by + ch / 2) ** 2 < (cw * .9) ** 2
        img[halo & near & (hash01(1, 1) >= 0)] = rgba(cap_pal[3], 60)
    return img


BROWN_CAP = [hexc(c) for c in ("3a1c1a", "6e3424", "934632", "b0603e", "d79868")]
RED_CAP = [hexc(c) for c in ("3a1418", "7a2228", "a83432", "d05a48", "f6c8b0")]
GLOW_CAP = [hexc(c) for c in ("163038", "1f6a74", "3fa3a0", "7fd6c4", "d2fff0")]


def sprout(cells):
    img = blank(16, 16)
    for cx, cy in cells:
        stem = GRASS[1]
        img[cy, cx] = rgba(stem)
        img[cy + 1, cx] = rgba(stem)
        for dx, dy, k in ((-1, -1, 3), (-2, -2, 4), (-2, -1, 2), (-3, -2, 3), (1, -1, 3), (2, -2, 4), (2, -1, 2), (3, -2, 3)):
            img[cy + dy, cx + dx] = rgba(GRASS[k])
    return outline(img, GRASS[0])


def rock(w, h, seed, ox, oy, size=16, rim=False):
    img = blank(size, size)
    shadow(img, ox + w / 2, oy + h - .5, w / 2 + .5, 1.8)
    mask, nx, ny = wl.blob(w, h, seed)
    sub = np.zeros((h, w, 4), np.uint8)
    wl.shade_blob(sub, 0, 0, mask, nx, ny, ROCK, outline=False)
    over(img, sub, ox, oy)
    if w >= 8:
        x = ox + w // 2
        for k in range(h // 3):
            if img[oy + h // 3 + k, x, 3] == 255:
                img[oy + h // 3 + k, x] = rgba(ROCK[0])
            x += 1 if k % 2 else 0
    outline(img, OUT)
    if rim:
        outline(img, WHITE)
    return img


def flower(cells, petal, centre, size=16, leaves=True):
    img = blank(size, size)
    for cx, cy, big in cells:
        if leaves:
            for dx, dy, k in ((0, 2, 1), (0, 3, 1), (-1, 3, 3), (-2, 2, 3), (1, 3, 3), (2, 2, 3), (-2, 3, 2), (2, 3, 2)):
                img[cy + dy, cx + dx] = rgba(GRASS[k])
        pts = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        if big:
            pts += [(1, -1), (-1, -1), (1, 1), (-1, 1), (2, 0), (-2, 0), (0, -2)]
        for dx, dy in pts:
            img[cy + dy, cx + dx] = rgba(petal[1] if dy > 0 else petal[0])
        img[cy, cx] = rgba(centre)
    return outline(img, hexc("1d3c2a"))


def sunflower():  # 16x32
    img = blank(16, 32)
    shadow(img, 8, 30, 4, 1.4)
    for y in range(12, 30):
        img[y, 8] = rgba(GRASS[1])
        img[y, 7] = rgba(GRASS[2]) if y % 5 else rgba(GRASS[1])
    for (sx, ly, d) in ((7, 18, -1), (8, 22, 1), (7, 26, -1)):  # leaves angled up off the stem
        for k in range(1, 5):
            x = sx + d * k
            img[ly - k // 2, x] = rgba(GRASS[3] if k < 3 else GRASS[2])
            img[ly + 1 - k // 2, x] = rgba(GRASS[1])
    ys, xs = np.mgrid[0:16, 0:16]
    d = np.sqrt((xs + .5 - 8) ** 2 + (ys + .5 - 7) ** 2)
    head = blank(16, 16)
    pet = [hexc(c) for c in ("c88a20", "e8b030", "f6d258", "fff0a0")]
    ang = np.arctan2(ys + .5 - 7, xs + .5 - 8)
    petal = (d < 6.2 + .9 * np.sin(ang * 8)) & (d >= 3)
    head[petal] = rgba(pet[1])
    head[petal & ((ys + .5 - 7) < -1)] = rgba(pet[2])
    head[petal & ((xs - ys) < -6)] = rgba(pet[0])
    head[d < 3.2] = rgba(hexc("5a3a22"))
    head[(d < 2) & (xs + ys < 14)] = rgba(hexc("7a5230"))
    head[5, 6] = rgba(pet[3])
    outline(head, OUT)
    over(img, head, 0, 0)
    return outline(img, OUT)


def stump(w, h, ox, oy, size=16):
    img = blank(size, size)
    shadow(img, ox + w / 2, oy + h, w / 2 + 1, 1.6)
    for y in range(h):
        for x in range(w):
            rel = x / max(w - 1, 1)
            k = 3 if rel < .3 else 2 if rel < .7 else 1
            img[oy + y, ox + x] = rgba(BARK[k])
    img[oy + h - 1, ox - 1] = rgba(BARK[1])
    img[oy + h - 1, ox + w] = rgba(BARK[1])
    # cut top with rings
    for x in range(w):
        img[oy, ox + x] = rgba(hexc("d8b07a"))
        img[oy + 1, ox + x] = rgba(hexc("c0925e"))
    img[oy, ox + w // 2] = rgba(hexc("a0744a"))
    return outline(img, BARK[0])


def log_item():  # dropped by the tree when chopped (log.tscn region 80,32)
    img = blank(16, 16)
    shadow(img, 8, 12.5, 7, 1.6)
    for y in range(5, 12):
        for x in range(2, 13):
            k = 3 if y < 7 else 2 if y < 10 else 1
            if (x * 2 + y) % 6 == 0:
                k = max(1, k - 1)
            img[y, x] = rgba(BARK[k])
    for y in range(5, 12):  # cut end
        for x in range(12, 15):
            if (x - 13) ** 2 + ((y - 8) * .7) ** 2 <= 3.2:
                img[y, x] = rgba(hexc("d8b07a") if (x - 13) ** 2 + (y - 8) ** 2 > 1 else hexc("a0744a"))
    img[4, 6] = rgba(BARK[2])
    img[3, 7] = rgba(GRASS[3])
    img[4, 7] = rgba(BARK[2])
    return item_outline(img)


def apple_item():
    img = blank(16, 16)
    ys, xs = np.mgrid[0:16, 0:16]
    m = ((xs + .5 - 8) / 5.2) ** 2 + ((ys + .5 - 9) / 4.8) ** 2 < 1
    v = -(xs - 8) * .12 - (ys - 9) * .15
    img[m] = rgba(RED[1])
    img[m & (v > 0)] = rgba(RED[2])
    img[m & (v > .6)] = rgba(RED[3])
    img[m & (v < -.6)] = rgba(RED[0])
    img[3:5, 8] = rgba(BARK[1])
    img[3, 9:11] = rgba(GRASS[3])
    img[4, 10] = rgba(GRASS[2])
    return item_outline(img)


def berries(cells, pal=RED, size=16, leaf=True, rim=False):
    img = blank(size, size)
    for bx, by in cells:
        img[by, bx] = rgba(pal[3])
        img[by, bx + 1] = rgba(pal[2])
        img[by + 1, bx] = rgba(pal[2])
        img[by + 1, bx + 1] = rgba(pal[1])
        if leaf:
            img[by - 1, bx + 1] = rgba(GRASS[3])
            img[by - 2, bx + 2] = rgba(GRASS[2])
    return item_outline(img) if rim else outline(img, OUT)


def lily(w, h, ox, oy, seed, size=16, bud=False):
    img = blank(size, size)
    mask, nx, ny = wl.blob(w, h, seed, rough=.05)
    pal = [GRASS[0], GRASS[1], GRASS[2], GRASS[3], GRASS[4]]
    sub = np.zeros((h, w, 4), np.uint8)
    wl.shade_blob(sub, 0, 0, mask, nx, ny, pal, outline=False)
    # notch
    cx = w // 2
    for k in range(h // 2):
        sub[k, cx] = 0
    over(img, sub, ox, oy)
    outline(img, hexc("1d3c3a"))
    if bud:
        img[oy + 2, ox + 2] = rgba(hexc("f4b8c8"))
        img[oy + 2, ox + 3] = rgba(hexc("e888a8"))
        img[oy + 1, ox + 2] = rgba(WHITE)
    return img


def nature_props():
    """Same 9x5 layout (144x80) as 'Basic Grass Biom things 1.png'."""
    s = blank(144, 80)
    C = lambda c, r: (c * T, r * T)  # noqa: E731
    over(s, small_tree(), *C(0, 0))
    over(s, oak(), *C(1, 0))
    over(s, fruit_tree(), *C(3, 0))
    over(s, mushroom(BROWN_CAP, [(4, 10, 6, 4), (9, 12, 5, 3)]), *C(5, 0))
    over(s, mushroom(RED_CAP, [(7, 11, 8, 5)]), *C(6, 0))
    over(s, mushroom(GLOW_CAP, [(7, 10, 6, 4)], glow=True), *C(7, 0))
    over(s, mushroom(GLOW_CAP, [(4, 12, 5, 3), (10, 9, 6, 4)], glow=True), *C(8, 0))
    over(s, sprout([(8, 11)]), *C(5, 1))
    over(s, sprout([(5, 7), (11, 12)]), *C(6, 1))
    over(s, rock(8, 7, 3, 4, 6), *C(7, 1))
    over(s, rock(13, 10, 7, 1, 4), *C(8, 1))
    over(s, berries([(5, 8), (8, 9)], leaf=False), *C(0, 2))
    over(s, berries([(5, 8), (8, 9)]), *C(1, 2))
    over(s, apple_item(), *C(2, 2))
    over(s, stump(4, 6, 6, 6), *C(3, 2))
    over(s, stump(8, 7, 4, 6), *C(4, 2))
    over(s, log_item(), *C(5, 2))
    over(s, flower([(8, 9, False)], [hexc("f6dc6a"), hexc("dcb240")], hexc("f08a3a")), *C(6, 2))
    over(s, flower([(8, 8, True)], [hexc("f6dc6a"), hexc("dcb240")], hexc("f08a3a")), *C(7, 2))
    over(s, sunflower(), *C(8, 2))
    over(s, bush(16, 16, 2, berries=[(4, 6), (10, 5), (7, 10), (11, 10)]), *C(0, 3))
    over(s, bush(16, 16, 6), *C(1, 3))
    over(s, berries([(7, 8)], leaf=False), *C(2, 3))
    over(s, berries([(6, 9), (9, 8)]), *C(3, 3))
    over(s, berries([(4, 6), (8, 5), (6, 9), (10, 9), (8, 12)], pal=BERRY, rim=True), *C(4, 3))
    over(s, flower([(8, 8, True)], [hexc("9cc4f4"), hexc("6a94d8")], hexc("f6f0d0")), *C(5, 3))
    over(s, flower([(8, 9, False)], [hexc("f6b0c8"), hexc("dc7aa0")], hexc("fff0a0")), *C(6, 3))
    over(s, flower([(8, 8, True)], [hexc("f6b0c8"), hexc("dc7aa0")], hexc("fff0a0")), *C(7, 3))
    hedge = bush(28, 14, 12)
    over(s, hedge, 1, 64 + 1)
    over(s, stump(4, 5, 10, 7), 22, 64)
    over(s, bush(30, 15, 15), 34, 64)
    over(s, stump(4, 5, 4, 7), 60, 64)
    over(s, rock(12, 9, 11, 2, 5, rim=True), *C(5, 4))
    over(s, rock(7, 6, 13, 4, 8, rim=True), *C(6, 4))
    over(s, lily(12, 8, 2, 5, 4), *C(7, 4))
    over(s, lily(12, 9, 1, 2, 9, bud=True), *C(8, 4))
    over(s, lily(5, 4, 10, 11, 2), *C(8, 4))
    return s


# ---------------------------------------------------------------- Wildlands (extra terrains)
def wildlands_source_lines(tiles, terrain_set):
    """TileSetAtlasSource body lines for the Wildlands sheet, on a given terrain set."""
    lines = []
    seen_pure = set()
    for col, row, names, prob in tiles:
        pure = len(set(names)) == 1
        if pure and prob == 0.0:
            prob = 0.5 if names[0] not in seen_pure else 0.15
            seen_pure.add(names[0])
        centers = sorted(set(names), key=lambda n: (-names.count(n), wl.TERRAINS.index(n)))
        for alt, center in enumerate(centers):
            k = f"{col}:{row}/{alt}"
            lines.append(f"{k} = {alt}")
            if prob != 1.0:
                lines.append(f"{k}/probability = {prob}")
            lines.append(f"{k}/terrain_set = {terrain_set}")
            lines.append(f"{k}/terrain = {wl.TERRAINS.index(center)}")
            polys = []
            for ci, n in enumerate(names):
                lines.append(f"{k}/terrains_peering_bit/{wl.PEER[ci]} = {wl.TERRAINS.index(n)}")
                if n == "water":
                    polys.append(wl.QUAD[ci])
            if len(polys) == 4:
                polys = ["-8, -8, 8, -8, 8, 8, -8, 8"]
            for pi, pts in enumerate(polys):
                lines.append(f"{k}/physics_layer_0/polygon_{pi}/points = PackedVector2Array({pts})")
    return lines


def update_game_tileset(tiles):
    """Rewrite source 6 (Wildlands, terrain set 1) inside tilesets/game_tilesets.tres."""
    path = os.path.join(GAME, "tilesets", "game_tilesets.tres")
    text = open(path).read()
    head = '[sub_resource type="TileSetAtlasSource" id="TileSetAtlasSource_wild"]\ntexture = ExtResource("8_wild")\n'
    start = text.index(head) + len(head)
    end = text.index("\n[sub_resource", start)
    text = text[:start] + "\n".join(wildlands_source_lines(tiles, 1)) + "\n" + text[end:]
    open(path, "w").write(text)
    print("updated tilesets/game_tilesets.tres (source 6)")


def save(arr, *path):
    p = os.path.join(ASSETS, *path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    Image.fromarray(arr, "RGBA").save(p)
    print("wrote", os.path.relpath(p, GAME))


def main():
    save(grass_sheet(), "Tilesets", "Nature", "grass_terrain.png")
    save(dirt_sheet(), "Tilesets", "Nature", "tilled_dirt.png")
    save(water_sheet(), "Tilesets", "Nature", "water.png")
    save(nature_props(), "Objects", "Nature", "nature_props.png")

    sheet, tiles = wl.build_terrain_sheet()
    save(sheet, "Tilesets", "Wildlands", "wildlands_terrain.png")
    save(np.asarray(wl.grade_dusk(Image.fromarray(sheet, "RGBA"))), "Tilesets", "Wildlands", "wildlands_terrain_dusk.png")
    update_game_tileset(tiles)
    for suffix in ("", "_dusk"):  # standalone TileSets, same tiles as source 6 of game_tilesets.tres
        name = f"wildlands_terrain{suffix}"
        wl.write_tres(os.path.join(ASSETS, "Tilesets", "Wildlands", name + ".tres"),
                      f"res://assets/Tilesets/Wildlands/{name}.png", tiles)

    for name, arr in wl.build_props().items():
        save(arr, "Objects", "Wildlands", name + ".png")
        save(np.asarray(wl.grade_dusk(Image.fromarray(arr, "RGBA"))), "Objects", "Wildlands", name + "_dusk.png")


if __name__ == "__main__":
    main()
