extends Node

const TEST_SCENE := "res://tools/anime_avatar_street_test.tscn"
const DEFAULT_DELAY_SECONDS := 2.0


func _ready() -> void:
	call_deferred("_capture")


func _capture() -> void:
	var packed_scene := load(TEST_SCENE) as PackedScene
	if packed_scene == null:
		push_error("Anime avatar capture: cannot load %s" % TEST_SCENE)
		get_tree().quit(2)
		return

	var test_scene := packed_scene.instantiate()
	add_child(test_scene)
	await get_tree().process_frame
	await get_tree().create_timer(_capture_delay()).timeout
	RenderingServer.force_draw(false)
	await RenderingServer.frame_post_draw

	var output_path := _output_path()
	DirAccess.make_dir_recursive_absolute(output_path.get_base_dir())
	var image := get_viewport().get_texture().get_image()
	if image.is_empty():
		push_error("Anime avatar capture: viewport image is empty")
		get_tree().quit(3)
		return

	var save_error := image.save_png(output_path)
	if save_error != OK:
		push_error("Anime avatar capture: cannot save %s" % output_path)
		get_tree().quit(4)
		return

	print("ANIME_AVATAR_CAPTURE_SAVED=", output_path)
	get_tree().quit()


func _output_path() -> String:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--output="):
			return argument.trim_prefix("--output=")
	return ProjectSettings.globalize_path("user://anime_avatar_capture.png")


func _capture_delay() -> float:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--delay="):
			return maxf(argument.trim_prefix("--delay=").to_float(), 0.5)
	return DEFAULT_DELAY_SECONDS
