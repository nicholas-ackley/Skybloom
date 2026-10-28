class_name CollectableComponent
extends Area2D

## Put this on anything the player can pick up (a dropped log, an egg...).
## Set "item" in the Inspector to the ItemData it gives. If "item" is empty,
## it falls back to res://resources/items/<collectable_name>.tres.

@export var collectable_name: String
@export var item: ItemData
@export var amount: int = 1
## Short wait after spawning so you can see the drop before it's picked up
@export var pickup_delay: float = 0.4


func _ready() -> void:
	if item == null and collectable_name != "":
		var path := "res://resources/items/%s.tres" % collectable_name
		if ResourceLoader.exists(path):
			item = load(path)
		else:
			push_warning("No ItemData found at " + path)

	set_deferred("monitoring", false)
	await get_tree().create_timer(pickup_delay).timeout
	set_deferred("monitoring", true)


func _on_body_entered(body: Node2D) -> void:
	if body is Player and item != null:
		var leftover := Inventory.add_item(item, amount)
		if leftover == 0:
			get_parent().queue_free()
		else:
			# Inventory full: leave the rest on the ground
			amount = leftover
