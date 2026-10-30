SKYBLOOM GRASS PLACEHOLDER PACK

40 individual PNG tiles, each 32x32 RGBA. Atlas: 256x160, 8 columns x 5 rows, zero margins/spacing.

Godot 4.x import:
1. Extract ZIP into your project assets/terrain/ folder.
2. Add or select your Ground TileMapLayer.
3. Inspector > Tile Set > New TileSet > Tile Size = 32x32.
4. Bottom TileSet editor > Add Atlas Source > choose skybloom_grass_atlas_32.png.
5. Set texture region size to 32x32 and create tiles in the atlas.
6. Select TileMap painting mode and paint with grass_00 through grass_05 as the base.
7. Scatter grass_decor variants sparingly to make the field less repetitive.
8. Add dirt and stone paths manually. For real auto-tiling, configure Godot terrain peering bits or use a purpose-made Wang tileset.
9. Set texture filtering to Nearest on relevant nodes/project for crisp pixels.

IMPORTANT: These are illustrative placeholders derived from the reference palette/style, not exact pixel extractions. Transition tiles are visual prototypes and are NOT a fully seamless 47-tile auto-terrain set. Base grass tiles use matching boundary pixels for seamless alignment; decorative tiles keep consistent borders. Other transition arrangements can show seams; refine before production.

ATLAS INDEX (left-to-right, 8 columns per row):
0,0 : grass_00
0,1 : grass_01
0,2 : grass_02
0,3 : grass_03
0,4 : grass_04
0,5 : grass_05
0,6 : grass_decor_00
0,7 : grass_decor_01
1,0 : grass_decor_02
1,1 : grass_decor_03
1,2 : grass_decor_04
1,3 : grass_decor_05
1,4 : dirt_full
1,5 : dirt_center
1,6 : dirt_horizontal
1,7 : dirt_edge_left
2,0 : dirt_edge_right
2,1 : dirt_edge_top
2,2 : dirt_edge_bottom
2,3 : dirt_corner_tl
2,4 : dirt_corner_tr
2,5 : dirt_corner_bl
2,6 : dirt_corner_br
2,7 : dirt_island
3,0 : stone_full
3,1 : stone_center
3,2 : stone_horizontal
3,3 : stone_edge_left
3,4 : stone_edge_right
3,5 : stone_edge_top
3,6 : stone_edge_bottom
3,7 : stone_corner_tl
4,0 : stone_corner_tr
4,1 : stone_corner_bl
4,2 : stone_corner_br
4,3 : stone_island
4,4 : dirt_variation_00
4,5 : dirt_variation_01
4,6 : stone_variation_00
4,7 : stone_variation_01
