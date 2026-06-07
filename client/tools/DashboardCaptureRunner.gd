extends Node

const DASHBOARD_SCENE := "res://scenes/city_dashboard.tscn"
const DEFAULT_DELAY_SECONDS := 3.0


func _ready() -> void:
	call_deferred("_capture_dashboard")


func _capture_dashboard() -> void:
	_configure_locale()
	var packed_scene := load(DASHBOARD_SCENE) as PackedScene
	if packed_scene == null:
		push_error("Dashboard capture: cannot load %s" % DASHBOARD_SCENE)
		get_tree().quit(2)
		return

	var dashboard := packed_scene.instantiate()
	add_child(dashboard)

	await get_tree().process_frame
	await get_tree().create_timer(_capture_delay()).timeout
	if _has_argument("--stress-text"):
		_apply_stress_text(dashboard)
		await get_tree().create_timer(0.25).timeout
	if _has_argument("--onboarding"):
		_apply_onboarding_preview(dashboard)
		await get_tree().create_timer(0.25).timeout
	if _has_argument("--police-recovery"):
		_apply_police_recovery_preview(dashboard)
		await get_tree().create_timer(0.25).timeout
	if _has_argument("--arrival-story"):
		_apply_arrival_story_preview(dashboard)
		await get_tree().create_timer(0.25).timeout
	if _has_argument("--arrival-guidance"):
		_apply_arrival_guidance_preview(dashboard)
		await get_tree().create_timer(0.25).timeout
	if _has_argument("--taxi-story"):
		_apply_taxi_story_preview(dashboard)
		await get_tree().create_timer(0.25).timeout
	if _has_argument("--character-creation"):
		_apply_character_creation_preview(dashboard)
		await get_tree().create_timer(0.25).timeout
	if _has_argument("--character-avatar-variant"):
		_apply_character_avatar_variant(dashboard)
		await get_tree().create_timer(0.5).timeout
	if _has_argument("--street-focus"):
		_apply_street_focus(dashboard)
		await get_tree().create_timer(0.5).timeout
	var street_activity := _street_activity()
	if not street_activity.is_empty():
		_apply_street_activity(dashboard, street_activity)
		await get_tree().create_timer(0.5).timeout
	RenderingServer.force_draw(false)
	await RenderingServer.frame_post_draw

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


func _configure_locale() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--locale="):
			TranslationServer.set_locale(argument.trim_prefix("--locale="))
			return
	TranslationServer.set_locale("uk")


func _has_argument(expected: String) -> bool:
	return expected in OS.get_cmdline_user_args()


func _tutorial_age_group() -> String:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--tutorial-age-group="):
			return argument.trim_prefix("--tutorial-age-group=")
	return "adult"


func _street_activity() -> String:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--street-activity="):
			return argument.trim_prefix("--street-activity=")
	return ""


func _apply_stress_text(dashboard: Node) -> void:
	var applied := 0
	applied += int(_set_label(dashboard, "CityCaption", "STRESS: дуже довгий заголовок району перевіряє безпечну зону поруч із кнопкою"))
	applied += int(_set_label(dashboard, "UsernameLabel", "Гравець_із_дуже_довгим_іменем_без_скорочень"))
	applied += int(_set_label(dashboard, "CurrentJobLabel", "Старший координатор міської логістики та аварійної інфраструктури"))
	applied += int(_set_label(dashboard, "CurrentHostelLabel", "Тимчасове житло у віддаленому районі біля промислової зони"))
	applied += int(_set_label(dashboard, "OwnedBusinessLabel", "Бізнес: мережа цілодобових сервісних центрів та районних кав'ярень"))
	applied += int(_set_label(dashboard, "SportsLabel", "Спорт: міський клуб аматорської ліги, контракт очікує продовження"))
	applied += int(_set_label(dashboard, "StatusLabel", "Подія дня: через ремонт центральної дороги час поїздки на роботу збільшено, перевірте наступну дію."))
	applied += int(_set_label(dashboard, "EffectsLabel", "Ефекти: настрій +12, енергія -18, транспортні витрати +35%, репутація району +4"))
	applied += int(_set_label(dashboard, "ErrorStateLabel", "Попередження: частина сервісів району тимчасово перевантажена, але прогрес гравця збережено."))
	applied += int(_set_label(dashboard, "EventHistoryLabel", "Останні події:\nОтримано довгу пропозицію роботи з випробувальним терміном.\nМіська служба повідомила про зміну маршруту."))
	applied += int(_set_label(dashboard, "BuildingPortfolioLabel", "3 будівлі: районна кав'ярня працює | сервісний центр потребує ремонту | хостел очікує відкриття"))
	applied += int(_set_label(dashboard, "BuildPlanLabel", "План: придбати ділянку у комерційному районі, подати заявку меру та зберегти резерв на відкриття"))
	applied += int(_set_label(dashboard, "GoalLabel", "Ціль: накопичити резерв для першого стабільного бізнесу"))
	applied += int(_set_label(dashboard, "NextActionLabel", "Наступний крок: перевірити бюджет і подати заявку на будівництво"))
	print("DASHBOARD_STRESS_LABELS_APPLIED=", applied)


func _apply_onboarding_preview(dashboard: Node) -> void:
	var overlay := dashboard.find_child("OnboardingOverlay", true, false) as Control
	if overlay == null:
		push_error("Dashboard capture: onboarding overlay not found")
		return

	overlay.visible = true
	_set_label(dashboard, "OnboardingTitleLabel", tr("ONBOARDING_ARRIVAL_CHOICE_TITLE"))
	_set_label(dashboard, "OnboardingNarrativeLabel", tr("ONBOARDING_ARRIVAL_CHOICE_NARRATIVE"))
	var police_status := dashboard.find_child("OnboardingPoliceStatusLabel", true, false) as Label
	if police_status != null:
		police_status.visible = false
	var police_button := dashboard.find_child("OnboardingPoliceButton", true, false) as Button
	if police_button != null:
		police_button.visible = true
		police_button.text = tr("ONBOARDING_POLICE_BUTTON")
	var housing_button := dashboard.find_child("OnboardingHousingButton", true, false) as Button
	if housing_button != null:
		housing_button.visible = true
		housing_button.text = tr("ONBOARDING_HOUSING_BUTTON")
	_set_onboarding_texture(dashboard, "res://assets/visual/core/arrival_bus_station_core_v2.png")
	_hide_onboarding_portrait(dashboard)
	print("DASHBOARD_ONBOARDING_PREVIEW_APPLIED=1")


func _apply_police_recovery_preview(dashboard: Node) -> void:
	var button := dashboard.find_child("PoliceRecoveryButton", true, false) as Button
	if button == null:
		push_error("Dashboard capture: police recovery button not found")
		return

	button.visible = true
	button.disabled = false
	button.text = tr("POLICE_RECOVERY_CLAIM").replace("{amount}", "75")
	button.tooltip_text = tr("POLICE_RECOVERY_CLAIM_TOOLTIP")
	print("DASHBOARD_POLICE_RECOVERY_PREVIEW_APPLIED=1")


func _apply_arrival_story_preview(dashboard: Node) -> void:
	var overlay := dashboard.find_child("OnboardingOverlay", true, false) as Control
	var continue_button := dashboard.find_child("OnboardingContinueButton", true, false) as Button
	var police_button := dashboard.find_child("OnboardingPoliceButton", true, false) as Button
	var housing_button := dashboard.find_child("OnboardingHousingButton", true, false) as Button
	if overlay == null or continue_button == null or police_button == null or housing_button == null:
		push_error("Dashboard capture: arrival story controls not found")
		return

	overlay.visible = true
	police_button.visible = false
	housing_button.visible = false
	continue_button.visible = true
	continue_button.text = tr("ARRIVAL_STORY_NEXT")
	_set_label(dashboard, "OnboardingTitleLabel", tr("ARRIVAL_BEAT_1_TITLE"))
	_set_label(dashboard, "OnboardingNarrativeLabel", tr("ARRIVAL_BEAT_1_NARRATIVE"))
	_set_onboarding_texture(dashboard, "res://assets/visual/core/arrival_waiting_hall_core.png")
	_set_onboarding_portrait(
		dashboard,
		"res://assets/visual/core/arrival_portrait_stranger_core.png",
		false
	)
	print("DASHBOARD_ARRIVAL_STORY_PREVIEW_APPLIED=1")


func _apply_arrival_guidance_preview(dashboard: Node) -> void:
	var overlay := dashboard.find_child("OnboardingOverlay", true, false) as Control
	var continue_button := dashboard.find_child("OnboardingContinueButton", true, false) as Button
	var police_button := dashboard.find_child("OnboardingPoliceButton", true, false) as Button
	var housing_button := dashboard.find_child("OnboardingHousingButton", true, false) as Button
	if overlay == null or continue_button == null or police_button == null or housing_button == null:
		push_error("Dashboard capture: arrival guidance controls not found")
		return

	var narrative_key := "ARRIVAL_BEAT_2_ADULT_NARRATIVE"
	match _tutorial_age_group():
		"teen":
			narrative_key = "ARRIVAL_BEAT_2_TEEN_NARRATIVE"
		"mature":
			narrative_key = "ARRIVAL_BEAT_2_MATURE_NARRATIVE"

	overlay.visible = true
	police_button.visible = false
	housing_button.visible = false
	continue_button.visible = true
	continue_button.text = tr("ARRIVAL_STORY_NEXT")
	_set_label(dashboard, "OnboardingTitleLabel", tr("ARRIVAL_BEAT_2_TITLE"))
	_set_label(dashboard, "OnboardingNarrativeLabel", tr(narrative_key))
	_set_onboarding_texture(dashboard, "res://assets/visual/core/arrival_waiting_hall_core.png")
	_set_onboarding_portrait(
		dashboard,
		"res://assets/visual/core/arrival_portrait_stranger_core.png",
		false
	)
	print("DASHBOARD_ARRIVAL_GUIDANCE_PREVIEW_APPLIED=", _tutorial_age_group())


func _apply_taxi_story_preview(dashboard: Node) -> void:
	var overlay := dashboard.find_child("OnboardingOverlay", true, false) as Control
	var continue_button := dashboard.find_child("OnboardingContinueButton", true, false) as Button
	var police_button := dashboard.find_child("OnboardingPoliceButton", true, false) as Button
	var housing_button := dashboard.find_child("OnboardingHousingButton", true, false) as Button
	if overlay == null or continue_button == null or police_button == null or housing_button == null:
		push_error("Dashboard capture: taxi story controls not found")
		return

	overlay.visible = true
	police_button.visible = false
	housing_button.visible = false
	continue_button.visible = true
	continue_button.text = tr("ARRIVAL_STORY_ARRIVE")
	_set_label(dashboard, "OnboardingTitleLabel", tr("ARRIVAL_BEAT_3_TITLE"))
	_set_label(dashboard, "OnboardingNarrativeLabel", tr("ARRIVAL_BEAT_3_NARRATIVE"))
	_set_onboarding_texture(dashboard, "res://assets/visual/core/arrival_taxi_ride_core.png")
	_set_onboarding_portrait(
		dashboard,
		"res://assets/visual/core/arrival_portrait_taxi_driver_core.png",
		false
	)
	print("DASHBOARD_TAXI_STORY_PREVIEW_APPLIED=1")


func _apply_character_creation_preview(dashboard: Node) -> void:
	var overlay := dashboard.find_child("CharacterCreationOverlay", true, false) as Control
	var name_input := dashboard.find_child("CharacterNameInput", true, false) as LineEdit
	var adult_button := dashboard.find_child("CharacterAdultButton", true, false) as Button
	var description := dashboard.find_child("CharacterAgeDescriptionLabel", true, false) as Label
	var error_label := dashboard.find_child("CharacterErrorLabel", true, false) as Label
	var create_button := dashboard.find_child("CharacterCreateButton", true, false) as Button
	if (
		overlay == null
		or name_input == null
		or adult_button == null
		or description == null
		or error_label == null
		or create_button == null
	):
		push_error("Dashboard capture: character creation controls not found")
		return

	overlay.visible = true
	var avatar_viewport := dashboard.find_child("CharacterPreviewViewport", true, false) as SubViewport
	if avatar_viewport != null:
		avatar_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	var avatar_preview := dashboard.find_child("CharacterAvatarPreview", true, false) as Node
	if avatar_preview != null:
		avatar_preview.process_mode = Node.PROCESS_MODE_INHERIT
	name_input.text = "Alex"
	adult_button.button_pressed = true
	description.text = tr("CHARACTER_AGE_ADULT_DESCRIPTION")
	error_label.visible = false
	create_button.text = tr("CHARACTER_CREATE_BUTTON")
	print("DASHBOARD_CHARACTER_CREATION_PREVIEW_APPLIED=1")


func _apply_character_avatar_variant(dashboard: Node) -> void:
	var steps := {
		"CharacterBodyNextButton": 1,
		"CharacterFaceNextButton": 19,
		"CharacterSkinNextButton": 3,
		"CharacterHairNextButton": 5,
		"CharacterHairColorNextButton": 2,
	}
	for button_name in steps:
		var button := dashboard.find_child(button_name, true, false) as Button
		if button == null:
			push_error("Dashboard capture: avatar selector not found: %s" % button_name)
			return
		for _step in range(steps[button_name]):
			button.emit_signal("pressed")
	print("DASHBOARD_CHARACTER_AVATAR_VARIANT_APPLIED=1")


func _apply_street_focus(dashboard: Node) -> void:
	var focus_button := dashboard.find_child("VisualFocusButton", true, false) as Button
	if focus_button == null:
		push_error("Dashboard capture: visual focus button not found")
		return
	focus_button.emit_signal("pressed")
	print("DASHBOARD_STREET_FOCUS_APPLIED=1")


func _apply_street_activity(dashboard: Node, activity_code: String) -> void:
	var avatar_preview := dashboard.find_child("StreetAvatarPreview", true, false)
	if avatar_preview == null:
		push_error("Dashboard capture: street avatar preview not found")
		return
	var method_name := &"SetActivityCode"
	if not avatar_preview.has_method(method_name):
		method_name = &"set_activity_code"
	if not avatar_preview.has_method(method_name):
		push_error("Dashboard capture: street avatar activity API not found")
		return
	avatar_preview.call(method_name, activity_code)
	print("DASHBOARD_STREET_ACTIVITY_APPLIED=", activity_code)


func _set_onboarding_texture(dashboard: Node, resource_path: String) -> void:
	var backdrop := dashboard.find_child("OnboardingBackdrop", true, false) as TextureRect
	var texture := load(resource_path) as Texture2D
	if backdrop == null or texture == null:
		push_error("Dashboard capture: onboarding texture unavailable: %s" % resource_path)
		return
	backdrop.texture = texture


func _set_onboarding_portrait(dashboard: Node, resource_path: String, on_left: bool) -> void:
	var portrait := dashboard.find_child("OnboardingPortrait", true, false) as TextureRect
	var texture := load(resource_path) as Texture2D
	if portrait == null or texture == null:
		push_error("Dashboard capture: onboarding portrait unavailable: %s" % resource_path)
		return
	portrait.position = Vector2(32 if on_left else 988, 230)
	portrait.size = Vector2(260, 325)
	portrait.texture = texture
	portrait.visible = true


func _hide_onboarding_portrait(dashboard: Node) -> void:
	var portrait := dashboard.find_child("OnboardingPortrait", true, false) as TextureRect
	if portrait != null:
		portrait.visible = false


func _set_label(root_node: Node, unique_name: String, value: String) -> bool:
	var label := root_node.find_child(unique_name, true, false) as Label
	if label != null:
		label.text = value
		return true
	return false
