# Reference tileset (rough-draft placeholder)

Third-party tileset art, rebuilt from a preview image for rough-draft level testing.
16px grid. Terrain set 0: Grass, Dirt (paint dirt inside grass). Terrain set 1: Shore Grass.
Water fill tiles are at atlas row 52. Painted on the RefWater / RefGround / RefDecor layers
in scenes/main/main_test_scene_objects_trees.tscn.

Rebuild scripts: tools/art/reference_tileset/ (extract.py -> pack.py -> build_tileset.py -> add_depth.py).
add_depth.py adds the light green rim inside grass edges, grass blades and dirt specks/pebbles.
