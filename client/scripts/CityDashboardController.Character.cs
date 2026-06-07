using Godot;
using System;
using System.Threading.Tasks;

public partial class CityDashboardController : Control
{
    // Character Creation Methods
    private void OnCharacterAgeButtonPressed(DashboardTutorialAgeGroup ageGroup)
    {
        _tutorialAgeGroup = ageGroup;
        UpdateCharacterAgeDescription();
        UpdateCharacterPreview();
    }

    private void OnCharacterLocaleButtonPressed(string locale)
    {
        // Update locale preference
        if (_session != null)
        {
            _session.SetLocale(locale);
        }
        UpdateCharacterCreationUI();
    }

    private void OnCharacterCreateButtonPressed()
    {
        var playerName = _characterNameInput?.Text?.Trim();

        if (string.IsNullOrEmpty(playerName))
        {
            SetLabelText(_characterErrorLabel, "Please enter a character name");
            return;
        }

        if (playerName.Length < 2 || playerName.Length > 30)
        {
            SetLabelText(_characterErrorLabel, "Name must be between 2 and 30 characters");
            return;
        }

        CreateCharacter(playerName);
    }

    private void OnAvatarCustomizationButtonPressed(string type, int direction)
    {
        // Handle avatar customization
        UpdateAvatarCustomization(type, direction);
        UpdateCharacterPreview();
    }

    private async void CreateCharacter(string playerName)
    {
        SetButtonEnabled(_characterCreateButton, false);
        SetLabelText(_characterErrorLabel, "Creating character...");

        try
        {
            var avatarData = BuildAvatarData();
            var response = await _apiClient.PostAsync("/api/mvp/register", new
            {
                name = playerName,
                age_group = _tutorialAgeGroup.ToString().ToLower(),
                avatar = avatarData
            });

            if (response.Success)
            {
                SetLabelText(_characterErrorLabel, "Character created successfully!");
                SetLabelText(StatusLabel, "✅ Character created!");

                // Update session
                if (_session != null)
                {
                    _session.SetPlayerData(response.Data);
                }

                // Hide character creation overlay
                SetControlVisible(_characterCreationOverlay, false);

                // Start onboarding if needed
                await RefreshOnboardingData();

                AddEventToHistory($"👤 Created character: {playerName}");
            }
            else
            {
                SetLabelText(_characterErrorLabel, $"Creation failed: {response.Message}");
            }
        }
        catch (Exception ex)
        {
            GD.PrintErr($"Character creation error: {ex.Message}");
            SetLabelText(_characterErrorLabel, "Network error during character creation");
        }
        finally
        {
            SetButtonEnabled(_characterCreateButton, true);
        }
    }

    private object BuildAvatarData()
    {
        return new
        {
            body_preset_code = _characterBodyValueLabel?.Text ?? "body_standard",
            face_preset_code = _characterFaceValueLabel?.Text ?? "face_01",
            skin_tone_code = _characterSkinValueLabel?.Text ?? "skin_03",
            hair_style_code = _characterHairValueLabel?.Text ?? "hair_short_01",
            hair_color_code = _characterHairColorValueLabel?.Text ?? "hair_brown"
        };
    }

    private void UpdateCharacterAgeDescription()
    {
        var description = _tutorialAgeGroup switch
        {
            DashboardTutorialAgeGroup.Teen => "Young and energetic, ready to learn and grow. Start with extra energy but lower initial skills.",
            DashboardTutorialAgeGroup.Adult => "Balanced approach with moderate energy and skills. Good for general gameplay.",
            DashboardTutorialAgeGroup.Mature => "Experienced with higher initial skills but lower energy. Better for business-focused gameplay.",
            _ => "Choose your age group to begin your journey."
        };

        SetLabelText(_characterAgeDescriptionLabel, description);
    }

    private void UpdateCharacterPreview()
    {
        if (_characterAvatarPreview != null)
        {
            var avatarData = BuildAvatarData();
            _characterAvatarPreview.UpdateAvatar(avatarData);
        }
    }

    private void UpdateAvatarCustomization(string type, int direction)
    {
        // This would handle avatar customization logic
        // For now, it's a placeholder
        switch (type)
        {
            case "body":
                UpdateAvatarValue(_characterBodyValueLabel, direction, "body");
                break;
            case "face":
                UpdateAvatarValue(_characterFaceValueLabel, direction, "face");
                break;
            case "skin":
                UpdateAvatarValue(_characterSkinValueLabel, direction, "skin");
                break;
            case "hair":
                UpdateAvatarValue(_characterHairValueLabel, direction, "hair");
                break;
            case "hair_color":
                UpdateAvatarValue(_characterHairColorValueLabel, direction, "hair_color");
                break;
        }
    }

    private void UpdateAvatarValue(Label label, int direction, string category)
    {
        if (label == null) return;

        var currentValue = label.Text;
        var newValue = GetNextAvatarValue(currentValue, category, direction);
        SetLabelText(label, newValue);
    }

    private string GetNextAvatarValue(string current, string category, int direction)
    {
        // This would contain the logic to cycle through avatar options
        // For now, return current value
        return current;
    }

    private void UpdateCharacterCreationUI()
    {
        // Update character creation UI based on current state
        UpdateCharacterAgeDescription();
        UpdateCharacterPreview();

        // Update button states
        SetButtonEnabled(_characterCreateButton, !string.IsNullOrEmpty(_characterNameInput?.Text?.Trim()));
    }

    // Player Avatar Management
    private void UpdatePlayerAvatar(object playerData)
    {
        if (playerData == null || _playerAvatarPreview == null) return;

        try
        {
            var data = System.Text.Json.JsonSerializer.Deserialize<PlayerSnapshotData>(playerData.ToString());
            if (data?.Player?.Avatar != null)
            {
                _playerAvatarPreview.UpdateAvatar(data.Player.Avatar);
                SetLabelText(_playerAvatarIdentityLabel, data.Player.Identity?.Name ?? "Unknown");
            }
        }
        catch (Exception ex)
        {
            GD.PrintErr($"Player avatar update error: {ex.Message}");
        }
    }

    private void UpdateStreetAvatar(object playerData)
    {
        if (playerData == null || _streetAvatarPreview == null) return;

        try
        {
            var data = System.Text.Json.JsonSerializer.Deserialize<PlayerSnapshotData>(playerData.ToString());
            if (data?.Player?.Avatar != null)
            {
                _streetAvatarPreview.UpdateAvatar(data.Player.Avatar);
                SetLabelText(_streetAvatarNameLabel, data.Player.Identity?.Name ?? "Unknown");
            }
        }
        catch (Exception ex)
        {
            GD.PrintErr($"Street avatar update error: {ex.Message}");
        }
    }

    // Avatar Animation
    private void AnimatePlayerAvatar(string animation)
    {
        if (_playerAvatarPreview != null)
        {
            _playerAvatarPreview.PlayAnimation(animation);
        }
    }

    private void AnimateStreetAvatar(string animation)
    {
        if (_streetAvatarPreview != null)
        {
            _streetAvatarPreview.PlayAnimation(animation);
        }
    }

    // Character Events
    private void OnCharacterNameInputChanged(string newText)
    {
        SetButtonEnabled(_characterCreateButton, !string.IsNullOrEmpty(newText?.Trim()));
    }
}
