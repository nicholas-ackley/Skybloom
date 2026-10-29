extends SceneTree
# Paints a small demo area with the reference tileset, prints the layer data,
# and with `-- --shot <png>` saves a screenshot.
const OX := -22
const OY := 2
const FY := 52

func rect(x0: int, y0: int, w: int, h: int) -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	for y in range(y0, y0 + h):
		for x in range(x0, x0 + w):
			out.append(Vector2i(x, y))
	return out

func _initialize():
	var ts = load("res://assets/Tilesets/Reference/reference_tileset.tres")
	var water := TileMapLayer.new(); water.tile_set = ts
	var ground := TileMapLayer.new(); ground.tile_set = ts
	for c in rect(OX, OY, 20, 16):
		water.set_cell(c, 0, Vector2i(2 + posmod(c.x * 7 + c.y * 3, 2), FY))
	ground.set_cells_terrain_connect(rect(OX + 2, OY + 2, 8, 7), 0, 0)   # grass island
	ground.set_cells_terrain_connect(rect(OX + 4, OY + 4, 4, 3), 0, 1)   # dirt clearing
	ground.set_cells_terrain_connect(rect(OX + 2, OY + 11, 7, 3), 0, 0)  # grass strip
	ground.set_cells_terrain_connect(rect(OX + 12, OY + 2, 6, 5), 1, 0)  # shore grass
	print("WATER_DATA ", Marshalls.raw_to_base64(water.tile_map_data))
	print("GROUND_DATA ", Marshalls.raw_to_base64(ground.tile_map_data))
	var args := OS.get_cmdline_user_args()
	if args.has("--shot"):
		var cam := Camera2D.new()
		cam.position = Vector2((OX + 10) * 16, (OY + 8) * 16)
		cam.zoom = Vector2(2, 2)
		root.add_child(water); root.add_child(ground); root.add_child(cam)
		cam.make_current()
		for i in 5:
			await process_frame
		await RenderingServer.frame_post_draw
		var img := root.get_texture().get_image()
		print("IMG save ", img.save_png(args[args.find("--shot") + 1]))
	quit()
