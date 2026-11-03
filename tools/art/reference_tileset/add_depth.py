"""Add depth to the reference tileset: a light green rim inside grass edges,
a little blade texture on the base grass, and specks/pebbles on the flat dirt.

Usage: python3 add_depth.py <in.png> <out.png>
Run it on the output of build_tileset.py (running it twice stacks the effect).
"""
import sys
from collections import deque
from PIL import Image
import numpy as np

T = 16
FILL_ROW = 52  # row of the generated fill tiles (grass, dirt, water x2, shore grass)
GRASS_BASE = np.array([162, 178, 90])
DIRT_BASE = np.array([180, 124, 68])
RIM_LIGHT = np.array([190, 204, 112])   # outermost band of the grass
RIM_MID = np.array([176, 192, 100])     # between the rim and the base green
BLADE_DARK = np.array([141, 161, 82])
BLADE_LIGHT = np.array([178, 193, 102])
DIRT_DARK = np.array([158, 103, 61])
DIRT_LIGHT = np.array([194, 139, 82])
PEBBLE_TOP = np.array([203, 160, 104])
PEBBLE_SHADOW = np.array([132, 84, 57])


def near(px, colour, tol):
    return np.abs(px[..., :3].astype(int) - colour).sum(-1) <= tol


def outside(px):
    """Where grass ends: empty, dirt, water or the dark outline."""
    rgb = px[..., :3].astype(int)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    empty = px[..., 3] == 0
    dirt = (r > g + 25) & (g > b)
    water = b > r + 40
    dark = rgb.sum(-1) < 210
    return empty | dirt | water | dark


def distance_to(mask, limit):
    """BFS distance (4-neighbour) inside one tile; tile borders are not 'outside'."""
    h, w = mask.shape
    d = np.full((h, w), limit + 1, int)
    q = deque()
    for y, x in zip(*np.nonzero(mask)):
        d[y, x] = 0
        q.append((y, x))
    while q:
        y, x = q.popleft()
        if d[y, x] >= limit:
            continue
        for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= ny < h and 0 <= nx < w and d[ny, nx] > d[y, x] + 1:
                d[ny, nx] = d[y, x] + 1
                q.append((ny, nx))
    return d


def tile(t, seed):
    rng = np.random.default_rng(seed)
    out = t.copy()
    grass = near(t, GRASS_BASE, 18) & (t[..., 3] > 0)
    dirt = near(t, DIRT_BASE, 16) & (t[..., 3] > 0)

    if grass.any():
        d = distance_to(outside(t), 6)
        # leaves sit on the edge, so the rim starts a few pixels in
        out[grass & (d <= 3)] = np.append(RIM_LIGHT, 255)
        out[grass & (d >= 4) & (d <= 5)] = np.append(RIM_MID, 255)
        inner = grass & (d > 5)
        # small two-pixel blades: a dark stem leaning left or right, sometimes a light tip
        for _ in range(int(inner.sum() / 45)):
            y, x = rng.integers(1, T - 1, 2)
            tx = x + (1 if rng.random() < .5 else -1)
            if inner[y, x] and inner[y - 1, tx]:
                out[y, x, :3] = BLADE_DARK
                out[y - 1, tx, :3] = BLADE_LIGHT if rng.random() < .35 else BLADE_DARK

    if dirt.any():
        for y, x in zip(*np.nonzero(dirt)):
            r = rng.random()
            if r < .07:
                out[y, x, :3] = DIRT_DARK
            elif r < .10:
                out[y, x, :3] = DIRT_LIGHT
        for _ in range(int(dirt.sum() / 90)):
            y, x = rng.integers(0, T - 1, 2)
            if dirt[y, x] and dirt[y, x + 1] and dirt[y + 1, x] and dirt[y + 1, x + 1]:
                out[y, x, :3] = PEBBLE_TOP
                out[y, x + 1, :3] = PEBBLE_TOP
                out[y + 1, x, :3] = PEBBLE_SHADOW
                out[y + 1, x + 1, :3] = PEBBLE_SHADOW
    return out


def main(src, dst):
    a = np.asarray(Image.open(src).convert('RGBA')).copy()
    h, w = a.shape[:2]
    # the dirt fill tile (1, FILL_ROW) picked up a light seam on its top row; copy the row below over it
    fy = FILL_ROW * T
    if near(a[fy:fy + 1, T:2 * T], np.array([188, 159, 93]), 12).all():
        a[fy, T:2 * T] = a[fy + 1, T:2 * T]
    for cy in range(h // T):
        for cx in range(w // T):
            sl = (slice(cy * T, (cy + 1) * T), slice(cx * T, (cx + 1) * T))
            if a[sl][..., 3].any():
                a[sl] = tile(a[sl], cy * 1000 + cx)
    Image.fromarray(a, 'RGBA').save(dst)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
