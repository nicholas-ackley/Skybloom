# Wildlands tiles and props

Original 16px pixel art inspired by a top-down river/cliff reference. Made by
`tools/art/generate_nature_assets.py` (re-run it from the repo root to regenerate everything).
Each sheet has a `_dusk` version with a darker, teal-shadow palette for the ground world.

## Terrain (`wildlands_terrain.tres`)

A ready TileSet with one terrain set in **Match Corners** mode and four terrains:
Dirt, Grass, Golden Meadow, River. River tiles have collision on physics layer 1.

How to use it:
1. Add a `TileMapLayer` node and set its Tile Set to `wildlands_terrain.tres`
   (or `wildlands_terrain_dusk.tres`).
2. Open the TileMap panel, go to the **Terrains** tab, pick terrain set 0 and a terrain.
3. Paint with **Connect** mode. Edges, cliffs and corners pick themselves.

Transitions that exist: Dirt-Grass, Dirt-Meadow, Dirt-River, Meadow-River, Grass-River.
There is no Grass-Meadow transition, so keep a strip of dirt between those two,
and avoid three terrains meeting on the same corner.

Sheet layout (`wildlands_terrain.png`, 320x80): five 4x4 blocks, one per transition,
then a bottom row of full-tile variants (dirt, grass, meadow, river) that Godot
mixes in at random.

## Props (`assets/Objects/Wildlands/`)

| File | Cell size | Contents |
|---|---|---|
| rocks_32.png | 32x32 | large, medium, small boulder, boulder pair |
| rocks_16.png | 16x16 | 2 small rocks, 2 pebble clusters |
| shrubs_24.png | 24x24 | green bush, leafy bush, golden bush, teal bush |
| mushrooms_16.png | 16x16 | 2 brown clusters, 2 glowing teal clusters |
| wheat_stages_16x32.png | 16x32 | 4 growth stages (sprout to ripe) |
| tufts_16.png | 16x16 | 2 grass tufts, 2 meadow tufts |

Use them as `Sprite2D` (set Hframes to the number of cells and pick a Frame), or
add them to a TileSet as a separate atlas with the cell size above.

## Inside game_tilesets.tres

The day sheet is also added to `tilesets/game_tilesets.tres` as **source 6**, on
**terrain set 1** (Dirt, Grass, Golden Meadow, River), so any TileMapLayer that
already uses the game tileset can paint these terrains. Terrain set 0 (the
original grass and tilled dirt terrains) is unchanged.
