extends CanvasLayer

## The hotbar (always on screen) and the inventory book (I or Tab to open, Esc to close).
## Loaded as an autoload named "InventoryUI", so it shows up in every level.
##
## In the hotbar: 1-9 or the mouse wheel pick a slot. The selected item is the tool you use.
## In the open book: click an item to pick it up, then click another slot to move it.
## Dropping onto the same item stacks them, onto a different item swaps them.

const EQUIPMENT_SLOTS := 6

var slot_uis: Array[InventorySlotUI] = []
var held_index := -1
var hovered_index := -1

@onready var book: TextureRect = $Root/Book
@onready var equipment_grid: GridContainer = $Root/Book/EquipmentGrid
@onready var item_grid: GridContainer = $Root/Book/ItemGrid
@onready var item_name_label: Label = $Root/Book/ItemName
@onready var item_info_label: Label = $Root/Book/ItemInfo
@onready var hotbar: PanelContainer = $Root/Hotbar
@onready var hotbar_slots: HBoxContainer = $Root/Hotbar/Slots
@onready var selected_name_label: Label = $Root/SelectedName
@onready var pickup_label: Label = $Root/PickupLabel
@onready var held_icon: TextureRect = $Root/HeldIcon

var pickup_tween: Tween


func _ready() -> void:
	for i in Inventory.SLOT_COUNT:
		var slot_ui := InventorySlotUI.new()
		slot_ui.index = i
		slot_ui.clicked.connect(_on_slot_clicked)
		slot_ui.hovered.connect(_on_slot_hovered)
		if i < Inventory.HOTBAR_SIZE:
			hotbar_slots.add_child(slot_ui)
		else:
			item_grid.add_child(slot_ui)
		slot_uis.append(slot_ui)

	# Equipment is only a placeholder for now: empty slots with no logic behind them
	for i in EQUIPMENT_SLOTS:
		equipment_grid.add_child(InventorySlotUI.new())

	Inventory.inventory_changed.connect(refresh)
	Inventory.selected_slot_changed.connect(func(_index): refresh())
	Inventory.item_added.connect(_on_item_added)
	set_open(false)


func _process(_delta: float) -> void:
	var mouse := hotbar.get_global_mouse_position()
	Inventory.mouse_over_ui = Inventory.is_open or hotbar.get_global_rect().has_point(mouse)
	held_icon.position = mouse - held_icon.size / 2


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("toggle_inventory"):
		set_open(!Inventory.is_open)
		get_viewport().set_input_as_handled()
		return
	if Inventory.is_open and event.is_action_pressed("ui_cancel"):
		set_open(false)
		get_viewport().set_input_as_handled()
		return

	# Number keys 1-9 pick a hotbar slot
	if event is InputEventKey and event.pressed and !event.echo:
		if event.keycode >= KEY_1 and event.keycode <= KEY_9:
			Inventory.select_slot(event.keycode - KEY_1)

	# Mouse wheel cycles through the hotbar
	if event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			Inventory.select_slot(Inventory.selected_index + 1)
		elif event.button_index == MOUSE_BUTTON_WHEEL_UP:
			Inventory.select_slot(Inventory.selected_index - 1)


func set_open(open: bool) -> void:
	Inventory.is_open = open
	book.visible = open
	held_index = -1
	hovered_index = -1
	refresh()


func _on_slot_clicked(index: int) -> void:
	if !Inventory.is_open:
		# Book closed: clicking the hotbar just selects
		if index < Inventory.HOTBAR_SIZE:
			Inventory.select_slot(index)
		return

	if held_index == -1:
		if Inventory.slots[index] != null:
			held_index = index
	else:
		var from := held_index
		held_index = -1
		Inventory.move_slot(from, index)
	refresh()


func _on_slot_hovered(index: int) -> void:
	hovered_index = index
	_show_item_info()


func _on_item_added(item: ItemData, amount: int) -> void:
	pickup_label.text = "+%d %s" % [amount, item.display_name]
	pickup_label.modulate.a = 1.0
	if pickup_tween:
		pickup_tween.kill()
	pickup_tween = create_tween()
	pickup_tween.tween_interval(1.0)
	pickup_tween.tween_property(pickup_label, "modulate:a", 0.0, 0.5)


func refresh() -> void:
	for i in slot_uis.size():
		var is_selected := i == Inventory.selected_index
		slot_uis[i].show_slot(Inventory.slots[i], is_selected, i == held_index)

	var item := Inventory.get_selected_item()
	selected_name_label.text = item.display_name if item != null and !Inventory.is_open else ""

	var held = Inventory.slots[held_index] if held_index != -1 else null
	held_icon.texture = held.item.icon if held != null else null
	_show_item_info()


## Fills the box at the bottom of the left page with whatever the mouse is over.
func _show_item_info() -> void:
	var slot = Inventory.slots[hovered_index] if hovered_index != -1 else null
	if slot == null:
		item_name_label.text = ""
		item_info_label.text = "Click an item to pick it up,\nthen click a slot to place it."
		return
	item_name_label.text = slot.item.display_name
	if slot.count > 1:
		item_name_label.text += "  x%d" % slot.count
	item_info_label.text = slot.item.description
