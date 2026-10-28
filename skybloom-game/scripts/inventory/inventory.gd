extends Node

## Autoload named "Inventory" (Project > Project Settings > Globals).
## Holds the player's items. Slots 0-8 are the hotbar, the rest are the bag
## shown on the right page of the inventory book.
## Call Inventory.add_item(...) from anywhere.

signal inventory_changed
signal selected_slot_changed(index: int)
signal item_added(item: ItemData, amount: int)

const HOTBAR_SIZE := 9
const BAG_SIZE := 25
const SLOT_COUNT := HOTBAR_SIZE + BAG_SIZE

const STARTING_ITEMS: Array[ItemData] = [
	preload("res://resources/items/axe.tres"),
	preload("res://resources/items/hoe.tres"),
	preload("res://resources/items/watering_can.tres"),
]

# Each slot is either null (empty) or {"item": ItemData, "count": int}
var slots: Array = []
var selected_index := 0
var is_open := false
## True while the mouse is over the inventory UI, so clicks there don't swing tools.
var mouse_over_ui := false


func _ready() -> void:
	slots.resize(SLOT_COUNT)
	for item in STARTING_ITEMS:
		add_item(item, 1)


## Adds items, stacking onto matching slots first. Returns how many did not fit.
func add_item(item: ItemData, amount: int = 1) -> int:
	var start_amount := amount

	# 1. Top up stacks of the same item that aren't full yet
	for i in SLOT_COUNT:
		if amount <= 0:
			break
		var slot = slots[i]
		if slot != null and slot.item.id == item.id and slot.count < item.max_stack:
			var added: int = min(amount, item.max_stack - slot.count)
			slot.count += added
			amount -= added

	# 2. Put whatever is left into empty slots (hotbar first, then the bag)
	for i in SLOT_COUNT:
		if amount <= 0:
			break
		if slots[i] == null:
			var added: int = min(amount, item.max_stack)
			slots[i] = {"item": item, "count": added}
			amount -= added

	if amount < start_amount:
		item_added.emit(item, start_amount - amount)
		inventory_changed.emit()
	return amount


## Removes items (for crafting, selling...). Returns false and removes nothing if there aren't enough.
func remove_item(item: ItemData, amount: int = 1) -> bool:
	if get_count(item) < amount:
		return false

	for i in range(SLOT_COUNT - 1, -1, -1):
		var slot = slots[i]
		if amount <= 0:
			break
		if slot != null and slot.item.id == item.id:
			var removed: int = min(amount, slot.count)
			slot.count -= removed
			amount -= removed
			if slot.count == 0:
				slots[i] = null

	inventory_changed.emit()
	return true


func get_count(item: ItemData) -> int:
	var total := 0
	for slot in slots:
		if slot != null and slot.item.id == item.id:
			total += slot.count
	return total


## Moves slot a into slot b. Matching items stack together, otherwise they swap places.
func move_slot(from_index: int, to_index: int) -> void:
	if from_index == to_index:
		return
	var from_slot = slots[from_index]
	var to_slot = slots[to_index]

	if from_slot != null and to_slot != null and from_slot.item.id == to_slot.item.id:
		var moved: int = min(from_slot.count, to_slot.item.max_stack - to_slot.count)
		to_slot.count += moved
		from_slot.count -= moved
		if from_slot.count == 0:
			slots[from_index] = null
	else:
		slots[from_index] = to_slot
		slots[to_index] = from_slot

	inventory_changed.emit()


func select_slot(index: int) -> void:
	selected_index = wrapi(index, 0, HOTBAR_SIZE)
	selected_slot_changed.emit(selected_index)


func get_selected_item() -> ItemData:
	var slot = slots[selected_index]
	return slot.item if slot != null else null


func get_selected_tool() -> DataTypes.Tools:
	var item := get_selected_item()
	return item.tool if item != null else DataTypes.Tools.None
