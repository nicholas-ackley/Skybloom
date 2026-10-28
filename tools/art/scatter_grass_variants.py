"""Swap plain grass cells in a scene's Grass TileMapLayer for random grass variants.

Painting with the terrain tool in Godot already mixes the variants in; this is
for grass that was placed before the variants existed.

Usage (from the repo root):
  python3 tools/art/scatter_grass_variants.py skybloom-game/scenes/main/main_test_scene_objects_trees.tscn
"""
import base64
import random
import re
import struct
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
from generate_nature_assets import GRASS_VARIANT_PROB, DETAIL_PROB  # noqa: E402

GRASS_SOURCE = 2
PLAIN = (1, 1)
LAYER = "Grass"


def main(path):
    text = open(path).read()
    m = re.search(r'(\[node name="%s" type="TileMapLayer"[^\n]*\n(?:[^\[][^\n]*\n)*?tile_map_data = PackedByteArray\(")([^"]*)' % LAYER, text)
    data = bytearray(base64.b64decode(m.group(2)))
    choices = [PLAIN] + [(i % 6, 5 + i // 6) for i in range(12)]
    weights = [1.0] + [GRASS_VARIANT_PROB.get(i, DETAIL_PROB) for i in range(12)]
    rng = random.Random(7)
    swapped = 0
    for off in range(2, len(data), 12):
        x, y, src, ax, ay, alt = struct.unpack_from("<hhHHHH", data, off)
        if src == GRASS_SOURCE and alt == 0 and ((ax, ay) == PLAIN or (ax, ay) in choices):
            nx, ny = rng.choices(choices, weights)[0]
            struct.pack_into("<HH", data, off + 6, nx, ny)
            swapped += (nx, ny) != PLAIN
    text = text[:m.start(2)] + base64.b64encode(bytes(data)).decode() + text[m.end(2):]
    open(path, "w").write(text)
    print(f"{path}: {swapped} grass cells now use a variant")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        main(p)
