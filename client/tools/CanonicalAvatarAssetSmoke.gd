extends Node

const AVATAR_PATH := "res://assets/visual/anime/avatar/canonical_anime_avatar.glb"
const REQUIRED_ANIMATIONS := ["idle", "walk", "sit", "phone", "talk"]
const REQUIRED_HAIR_GROUPS := [
	"HairShort01",
	"HairShort02",
	"HairMedium01",
	"HairMedium02",
	"HairLong01",
	"HairLong02",
	"HairBuzz01",
]
const MINIMUM_BONE_COUNT := 23


func _ready() -> void:
	call_deferred("_run_smoke")


func _run_smoke() -> void:
	var packed_scene := load(AVATAR_PATH) as PackedScene
	if packed_scene == null:
		_fail("cannot load %s" % AVATAR_PATH)
		return

	var avatar := packed_scene.instantiate()
	add_child(avatar)
	await get_tree().process_frame

	var skeleton := _find_type(avatar, "Skeleton3D") as Skeleton3D
	var animation_player := _find_type(avatar, "AnimationPlayer") as AnimationPlayer
	if skeleton == null:
		_fail("Skeleton3D not found")
		return
	if skeleton.get_bone_count() < MINIMUM_BONE_COUNT:
		_fail("expected at least %d bones, got %d" % [MINIMUM_BONE_COUNT, skeleton.get_bone_count()])
		return
	if animation_player == null:
		_fail("AnimationPlayer not found")
		return

	for animation_name in REQUIRED_ANIMATIONS:
		if not animation_player.has_animation(animation_name):
			_fail("missing animation: %s" % animation_name)
			return
		var animation := animation_player.get_animation(animation_name)
		if animation == null or animation.get_track_count() == 0:
			_fail("animation has no tracks: %s" % animation_name)
			return

	for hair_group in REQUIRED_HAIR_GROUPS:
		if not _has_name_prefix(avatar, hair_group):
			_fail("missing hair mesh group: %s" % hair_group)
			return

	print(
		"CANONICAL_AVATAR_SMOKE_OK bones=%d animations=%s hair_groups=%d"
		% [skeleton.get_bone_count(), ",".join(REQUIRED_ANIMATIONS), REQUIRED_HAIR_GROUPS.size()]
	)
	get_tree().quit()


func _find_type(root: Node, class_name_value: String) -> Node:
	if root.is_class(class_name_value):
		return root
	for child in root.get_children():
		var match := _find_type(child, class_name_value)
		if match != null:
			return match
	return null


func _has_name_prefix(root: Node, prefix: String) -> bool:
	if root.name.begins_with(prefix):
		return true
	for child in root.get_children():
		if _has_name_prefix(child, prefix):
			return true
	return false


func _fail(message: String) -> void:
	push_error("Canonical avatar smoke: %s" % message)
	get_tree().quit(2)
