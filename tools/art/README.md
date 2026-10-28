# Art generators

`generate_nature_assets.py` draws the nature art used by `tilesets/game_tilesets.tres`
and the tree/log scenes (Python 3 + Pillow + numpy):

| Output | Replaces | Notes |
|---|---|---|
| `assets/Tilesets/Nature/grass_terrain.png` | `Tilesets/Grass.png` | same 176x112 layout, so the terrain bits still match |
| `assets/Tilesets/Nature/tilled_dirt.png` | `Tilesets/Tilled_Dirt_Wide.png` | same layout |
| `assets/Tilesets/Nature/water.png` | `Tilesets/Water.png` | 4 animation frames, 16x16 each |
| `assets/Objects/Nature/nature_props.png` | `Objects/Basic Grass Biom things 1.png` | same 9x5 grid of 16px cells: trees, bushes, flowers, mushrooms, rocks, stumps, log, lily pads |
| `assets/Tilesets/Wildlands/*`, `assets/Objects/Wildlands/*` | new | extra terrains and props, see the README there |

`wildlands.py` holds the Wildlands terrain and prop code it builds on.

Run from the repo root: `python3 tools/art/generate_nature_assets.py`.
The old sheets are left in place, so you can point the tileset back at them any time.
