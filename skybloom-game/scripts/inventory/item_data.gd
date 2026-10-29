class_name ItemData
extends Resource

## One kind of item (a log, an axe...). Make a new one in the FileSystem dock:
## right-click > New > Resource > ItemData, then fill in the fields.

## Must be unique. Items with the same id stack together.
@export var id: String
@export var display_name: String
@export_multiline var description: String
@export var icon: Texture2D
@export var max_stack: int = 99
## If this item is a tool, holding it in the hotbar lets the player use that tool.
@export var tool: DataTypes.Tools = DataTypes.Tools.None
