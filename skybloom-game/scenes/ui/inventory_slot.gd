class_name InventorySlotUI
extends TextureRect

## One square in the hotbar or the inventory book. Built in code by inventory_ui.gd.

signal clicked(index: int)
signal hovered(index: int)

const SLOT_TEXTURE := preload("res://assets/UI/inventory/slot.png")
const SLOT_SELECTED_TEXTURE := preload("res://assets/UI/inventory/slot_selected.png")

## Which Inventory.slots entry this shows. -1 = decoration only (equipment placeholders).
var index := -1
var icon_rect := TextureRect.new()
var count_label := Label.new()


func _ready() -> void:
	texture = SLOT_TEXTURE
	custom_minimum_size = SLOT_TEXTURE.get_size()
	mouse_filter = Control.MOUSE_FILTER_STOP

	icon_rect.position = Vector2(1, 1)
	icon_rect.size = Vector2(16, 16)
	icon_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(icon_rect)

	count_label.position = Vector2(0, 7)
	count_label.size = Vector2(18, 11)
	count_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	count_label.add_theme_font_size_override("font_size", 8)
	count_label.add_theme_color_override("font_color", Color.WHITE)
	count_label.add_theme_color_override("font_outline_color", Color(0.17, 0.09, 0.06))
	count_label.add_theme_constant_override("outline_size", 3)
	count_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(count_label)

	mouse_entered.connect(func(): hovered.emit(index))


func show_slot(slot, is_selected: bool, is_held: bool) -> void:
	texture = SLOT_SELECTED_TEXTURE if is_selected or is_held else SLOT_TEXTURE
	icon_rect.texture = slot.item.icon if slot != null else null
	# The picked-up item fades in its old slot so you can see where it came from
	icon_rect.modulate.a = 0.4 if is_held else 1.0
	count_label.text = str(slot.count) if slot != null and slot.count > 1 else ""


func _gui_input(event: InputEvent) -> void:
	if index < 0:
		return
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		clicked.emit(index)
		accept_event()
