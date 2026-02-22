class_name Player
extends CharacterBody2D

@export var current_tool: DataTypes.Tools = DataTypes.Tools.None

var player_direction: Vector2

func _physics_process(_delta: float) -> void:
	var input_dir := GameInputEvents.movement_input()

	if input_dir != Vector2.ZERO:
		player_direction = input_dir
