using Godot;
using System;
using System.Text.Json.Nodes;
using System.Threading.Tasks;

public partial class CityDashboardController
{
    // Note: Onboarding component fields are declared in main CityDashboardController.cs

    private void InitializeOnboarding()
    {
        // Get onboarding nodes
        _onboardingOverlay = GetNode<Control>("OnboardingOverlay");
        _onboardingBackdrop = GetNode<TextureRect>("OnboardingOverlay/OnboardingBackdrop");
        _onboardingPortrait = GetNode<TextureRect>("OnboardingOverlay/OnboardingPortrait");
        _onboardingTitleLabel = GetNode<Label>("OnboardingOverlay/StoryPanel/TitleLabel");
        _onboardingNarrativeLabel = GetNode<Label>("OnboardingOverlay/StoryPanel/NarrativeLabel");
        _onboardingPoliceStatusLabel = GetNode<Label>("OnboardingOverlay/StoryPanel/PoliceStatusLabel");
        _onboardingPoliceButton = GetNode<Button>("OnboardingOverlay/StoryPanel/PoliceButton");
        _onboardingHousingButton = GetNode<Button>("OnboardingOverlay/StoryPanel/HousingButton");
        _onboardingContinueButton = GetNode<Button>("OnboardingOverlay/StoryPanel/ContinueButton");
        _policeRecoveryButton = GetNode<Button>("MainContainer/PlayerRail/PoliceRecoveryButton");

        // Connect signals
        _onboardingPoliceButton.Pressed += OnOnboardingPolicePressed;
        _onboardingHousingButton.Pressed += OnOnboardingHousingPressed;
        _onboardingContinueButton.Pressed += OnOnboardingContinuePressed;
        _policeRecoveryButton.Pressed += OnPoliceRecoveryPressed;

        // Initially hide
        _onboardingOverlay.Visible = false;
        _policeRecoveryButton.Visible = false;
    }

    private async Task ShowOnboardingIfNeeded()
    {
        if (_session?.PlayerId == null) return;

        try
        {
            var response = await _apiClient.GetAsync($"/api/player/{_session.PlayerId}/onboarding");
            if (response?.TryGetValue("success", out var success) == true && success.GetValue<bool>())
            {
                var onboardingData = response?["data"];
                var stage = onboardingData?["current_stage"]?.GetValue<string>() ?? "completed";

                if (stage != "completed")
                {
                    await ShowOnboardingStage(stage, onboardingData);
                }
                else
                {
                    // Check for police recovery
                    await CheckPoliceRecovery();
                }
            }
        }
        catch (Exception ex)
        {
            GD.PrintErr($"Error checking onboarding: {ex.Message}");
        }
    }

    private async Task ShowOnboardingStage(string stage, JsonNode onboardingData)
    {
        _onboardingOverlay.Visible = true;

        switch (stage)
        {
            case "arrival":
                await ShowArrivalStory();
                break;
            case "police_choice":
                await ShowPoliceChoice(onboardingData);
                break;
            case "housing_choice":
                await ShowHousingChoice(onboardingData);
                break;
        }
    }

    private async Task ShowArrivalStory()
    {
        // Load localized story
        var locale = _session?.Locale ?? "uk";
        var titleKey = locale == "uk" ? "arrival_title_uk" : "arrival_title_en";
        var narrativeKey = locale == "uk" ? "arrival_narrative_uk" : "arrival_narrative_en";

        _onboardingTitleLabel.Text = Tr(titleKey);
        _onboardingNarrativeLabel.Text = Tr(narrativeKey);

        // Show arrival visual
        _onboardingBackdrop.Texture = GD.Load<Texture2D>($"res://assets/visual/core/bus_station_arrival.png");
        _onboardingPortrait.Texture = GD.Load<Texture2D>($"res://assets/visual/core/npc_conductor.png");

        // Hide choice buttons, show continue
        _onboardingPoliceButton.Visible = false;
        _onboardingHousingButton.Visible = false;
        _onboardingPoliceStatusLabel.Visible = false;
        _onboardingContinueButton.Visible = true;

        _onboardingState.CurrentStage = "arrival_shown";
    }

    private async Task ShowPoliceChoice(JsonNode onboardingData)
    {
        var locale = _session?.Locale ?? "uk";
        var titleKey = locale == "uk" ? "police_choice_title_uk" : "police_choice_title_en";
        var narrativeKey = locale == "uk" ? "police_choice_narrative_uk" : "police_choice_narrative_en";

        _onboardingTitleLabel.Text = Tr(titleKey);
        _onboardingNarrativeLabel.Text = Tr(narrativeKey);

        // Show taxi scene
        _onboardingBackdrop.Texture = GD.Load<Texture2D>($"res://assets/visual/core/taxi_scene.png");
        _onboardingPortrait.Texture = GD.Load<Texture2D>($"res://assets/visual/core/npc_taxi_driver.png");

        // Show choice buttons
        _onboardingPoliceButton.Visible = true;
        _onboardingHousingButton.Visible = true;
        _onboardingPoliceStatusLabel.Visible = false;
        _onboardingContinueButton.Visible = false;

        _onboardingState.CurrentStage = "police_choice_pending";
    }

    private async Task ShowHousingChoice(JsonNode onboardingData)
    {
        var locale = _session?.Locale ?? "uk";
        var titleKey = locale == "uk" ? "housing_choice_title_uk" : "housing_choice_title_en";
        var narrativeKey = locale == "uk" ? "housing_choice_narrative_uk" : "housing_choice_narrative_en";

        _onboardingTitleLabel.Text = Tr(titleKey);
        _onboardingNarrativeLabel.Text = Tr(narrativeKey);

        // Show city street
        _onboardingBackdrop.Texture = GD.Load<Texture2D>($"res://assets/visual/core/city_street.png");
        _onboardingPortrait.Visible = false;

        // Hide choice buttons, show continue
        _onboardingPoliceButton.Visible = false;
        _onboardingHousingButton.Visible = false;
        _onboardingPoliceStatusLabel.Visible = false;
        _onboardingContinueButton.Visible = true;

        _onboardingState.CurrentStage = "housing_choice_shown";
    }

    private async void OnOnboardingPolicePressed()
    {
        if (_session?.PlayerId == null) return;

        try
        {
            var response = await _apiClient.PostAsync($"/api/player/{_session.PlayerId}/onboarding/police-choice",
                new { choice = "report" });

            if (response?.TryGetValue("success", out var success) == true && success.GetValue<bool>())
            {
                _onboardingPoliceStatusLabel.Text = "✅ Заяву подано. Ми повідомимо вас про результат.";
                _onboardingPoliceStatusLabel.Visible = true;
                _onboardingPoliceButton.Disabled = true;
                _onboardingHousingButton.Disabled = false;

                _onboardingState.CurrentStage = "police_reported";
            }
        }
        catch (Exception ex)
        {
            ErrorStateLabel.Text = $"Помилка: {ex.Message}";
        }
    }

    private async void OnOnboardingHousingPressed()
    {
        if (_session?.PlayerId == null) return;

        try
        {
            var response = await _apiClient.PostAsync($"/api/player/{_session.PlayerId}/onboarding/housing-choice",
                new { choice = "hostel" });

            if (response?.TryGetValue("success", out var success) == true && success.GetValue<bool>())
            {
                _onboardingOverlay.Visible = false;
                await RefreshPlayerData();
            }
        }
        catch (Exception ex)
        {
            ErrorStateLabel.Text = $"Помилка: {ex.Message}";
        }
    }

    private async void OnOnboardingContinuePressed()
    {
        switch (_onboardingState.CurrentStage)
        {
            case "arrival_shown":
                await ShowOnboardingStage("police_choice", null);
                break;
            case "housing_choice_shown":
                _onboardingOverlay.Visible = false;
                await RefreshPlayerData();
                break;
        }
    }

    private async Task CheckPoliceRecovery()
    {
        if (_session?.PlayerId == null) return;

        try
        {
            var response = await _apiClient.GetAsync($"/api/player/{_session.PlayerId}/police-recovery");
            if (response?.TryGetValue("success", out var success) == true && success.GetValue<bool>())
            {
                var data = response?["data"];
                var isClaimable = data?["claimable"]?.GetValue<bool>() ?? false;

                if (isClaimable)
                {
                    var amount = data?["amount"]?.GetValue<int>() ?? 0;
                    _policeRecoveryButton.Text = $"Отримати {amount} ₴ від поліції";
                    _policeRecoveryButton.Visible = true;
                }
            }
        }
        catch (Exception ex)
        {
            GD.PrintErr($"Error checking police recovery: {ex.Message}");
        }
    }

    private async void OnPoliceRecoveryPressed()
    {
        if (_session?.PlayerId == null) return;

        try
        {
            var response = await _apiClient.PostAsync($"/api/player/{_session.PlayerId}/police-recovery/claim", new { });

            if (response?.TryGetValue("success", out var success) == true && success.GetValue<bool>())
            {
                var amount = response?["data"]?["amount"]?.GetValue<int>() ?? 0;
                EffectsLabel.Text = $"✅ Отримано {amount} ₴ від поліції!";
                _policeRecoveryButton.Visible = false;
                await RefreshPlayerData();
            }
        }
        catch (Exception ex)
        {
            ErrorStateLabel.Text = $"Помилка: {ex.Message}";
        }
    }
}
