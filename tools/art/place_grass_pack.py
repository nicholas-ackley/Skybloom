"""Swap the plain grass already placed in a scene for tiles from the grass pack.

Every full-grass cell in the scene's Grass TileMapLayer becomes a quarter of a
32px pack tile (source 7 in game_tilesets.tres). Cells are grouped in 2x2
blocks, and each block gets one whole pack tile, so the pack's seamless 32px
tiles line up. Edge tiles (where the grass meets water) are left alone.

Usage (from the repo root):
  python3 tools/art/place_grass_pack.py skybloom-game/scenes/main/main_test_scene_objects_trees.tscn
"""
import base64
import random
import re
import struct
import sys

LAYER = "Grass"
OLD_SOURCE = 2                # Nature/grass_terrain.png
PLAIN = {(1, 1)} | {(x, y) for x in range(6) for y in (5, 6)}  # full-grass cells
PACK_SOURCE = 7
PACK_COLS = 8                 # 32px tiles per row in skybloom_grass_atlas_32.png
BASE = list(range(0, 6))      # grass_00..05
DECOR = list(range(6, 12))    # grass_decor_00..05
DECOR_WEIGHT = 0.15           # each decor tile vs 1.0 for each base tile


def pick(bx, by):
    rng = random.Random(bx * 73856093 ^ by * 19349663)
    return rng.choices(BASE + DECOR, [1.0] * len(BASE) + [DECOR_WEIGHT] * len(DECOR))[0]


def main(path):
    text = open(path).read()
    m = re.search(r'(\[node name="%s" type="TileMapLayer"[^\n]*\n(?:[^\[][^\n]*\n)*?tile_map_data = PackedByteArray\(")([^"]*)' % LAYER, text)
    data = bytearray(base64.b64decode(m.group(2)))
    swapped = 0
    for off in range(2, len(data), 12):
        x, y, src, ax, ay, alt = struct.unpack_from("<hhHHHH", data, off)
        if not ((src == OLD_SOURCE and (ax, ay) in PLAIN and alt == 0) or src == PACK_SOURCE):
            continue
        i = pick(x // 2, y // 2)
        cx, cy = (i % PACK_COLS) * 2 + x % 2, (i // PACK_COLS) * 2 + y % 2
        struct.pack_into("<HHHH", data, off + 4, PACK_SOURCE, cx, cy, 0)
        swapped += 1
    text = text[:m.start(2)] + base64.b64encode(bytes(data)).decode() + text[m.end(2):]
    open(path, "w").write(text)
    print(f"{path}: {swapped} grass cells now use the grass pack")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        main(p)
