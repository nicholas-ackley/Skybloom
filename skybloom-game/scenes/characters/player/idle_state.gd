
extends NodeState

@export var player: Player
@export var animated_sprite_2d: AnimatedSprite2D


func _on_process(_delta : float) -> void:
	pass



func _on_physics_process(_delta : float) -> void:
	if player.player_direction == Vector2.UP:
		animated_sprite_2d.play("idle_back")
	elif player.player_direction == Vector2.UP:
		animated_sprite_2d.play("idle_right")
	elif player.player_direction == Vector2.UP:
		animated_sprite_2d.play("idle_front")
	elif player.player_direction == Vector2.UP:
		animated_sprite_2d.play("idle_left")
	else:
		animated_sprite_2d.play("idle_front")
		

		
func _on_next_transitions() -> void:
	GameInputEvents.movement_input()
	# If we detect any movement input, leave Idle and go to Walk
	if GameInputEvents.is_movement_input():
		transition.emit("Walk")


func _on_enter() -> void:
	pass


func _on_exit() -> void:
	animated_sprite_2d.stop()
