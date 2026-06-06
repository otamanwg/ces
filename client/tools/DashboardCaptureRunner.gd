extends Node

const DASHBOARD_SCENE := "res://scenes/city_dashboard.tscn"
const DEFAULT_DELAY_SECONDS := 3.0


func _ready() -> void:
	call_deferred("_capture_dashboard")


func _capture_dashboard() -> void:
	var packed_scene := load(DASHBOARD_SCENE) as PackedScene
	if packed_scene == null:
		push_error("Dashboard capture: cannot load %s" % DASHBOARD_SCENE)
		get_tree().quit(2)
		return

	var dashboard := packed_scene.instantiate()
	add_child(dashboard)

	await get_tree().process_frame
	await get_tree().create_timer(_capture_delay()).timeout
	RenderingServer.force_draw(false)
	await get_tree().process_frame

	var output_path := _output_path()
	var output_dir := output_path.get_base_dir()
	if not output_dir.is_empty():
		DirAccess.make_dir_recursive_absolute(output_dir)

	var image := get_viewport().get_texture().get_image()
	if image.is_empty():
		push_error("Dashboard capture: viewport image is empty")
		get_tree().quit(3)
		return

	var save_error := image.save_png(output_path)
	if save_error != OK:
		push_error("Dashboard capture: cannot save %s (error %d)" % [output_path, save_error])
		get_tree().quit(4)
		return

	print("DASHBOARD_CAPTURE_SAVED=", output_path)
	get_tree().quit()


func _output_path() -> String:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--output="):
			return argument.trim_prefix("--output=")
	return ProjectSettings.globalize_path("user://dashboard_capture.png")


func _capture_delay() -> float:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--delay="):
			return maxf(argument.trim_prefix("--delay=").to_float(), 0.5)
	return DEFAULT_DELAY_SECONDS
