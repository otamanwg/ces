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
	_set_label(dashboard, "OnboardingTitleLabel", "Новий початок")
	_set_label(
		dashboard,
		"OnboardingNarrativeLabel",
		"Таксі зникло разом із вашим багажем. У телефоні залишились фото документів, "
		+ "а в кишені лише стартові гроші. Можна звернутись у поліцію або негайно шукати житло."
	)
	var police_status := dashboard.find_child("OnboardingPoliceStatusLabel", true, false) as Label
	if police_status != null:
		police_status.visible = false
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
	button.text = "Забрати 75 ₴"
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
