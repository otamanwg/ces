using Godot;
using System;
using System.Collections.Generic;

public partial class CityDashboardController
{
    private Control _characterCreationOverlay;
    private TextureRect _characterCreationBackdrop;
    private LineEdit _characterNameInput;
    private Label _characterAgeDescriptionLabel;
    private Label _characterErrorLabel;
    private Button _characterTeenButton;
    private Button _characterAdultButton;
    private Button _characterMatureButton;
    private Button _characterCreateButton;
    private Button _characterUkrainianButton;
    private Button _characterEnglishButton;
    private CharacterAvatarPreview _characterAvatarPreview;
    private Label _characterBodyValueLabel;
    private Label _characterFaceValueLabel;
    private Label _characterSkinValueLabel;
    private Label _characterHairValueLabel;
    private Label _characterHairColorValueLabel;
    private Button _characterBodyPreviousButton;
    private Button _characterBodyNextButton;
    private Button _characterFacePreviousButton;
    private Button _characterFaceNextButton;
    private Button _characterSkinPreviousButton;
    private Button _characterSkinNextButton;
    private Button _characterHairPreviousButton;
    private Button _characterHairNextButton;
    private Button _characterHairColorPreviousButton;
    private Button _characterHairColorNextButton;
    private SubViewport _characterAvatarViewport;
    private bool _pendingRegistration;
    private string _selectedCharacterAgeGroup = DashboardCharacterCreation.DefaultAgeGroup;
    private DashboardAvatarSelection _selectedAvatar = DashboardAvatarSelection.Default;

    private void ConfigureCharacterCreationVisual()
    {
        if (_characterCreationBackdrop == null)
        {
            return;
        }

        _characterCreationBackdrop.Texture = ResourceLoader.Load<Texture2D>(
            "res://assets/visual/core/arrival_waiting_hall_core.png");
    }

    private void ShowCharacterCreation(string errorMessage = "")
    {
        if (_characterCreationOverlay == null)
        {
            SetErrorState("Character creation UI is unavailable.");
            return;
        }

        _characterCreationOverlay.Visible = true;
        SetViewportActive(_characterAvatarViewport, true);
        _characterAvatarPreview?.SetPreviewActive(true);
        if (_characterErrorLabel != null)
        {
            _characterErrorLabel.Text = errorMessage;
            _characterErrorLabel.Visible = !string.IsNullOrWhiteSpace(errorMessage);
        }
        UpdateCharacterCreationUi();
    }

    private void HideCharacterCreation()
    {
        if (_characterCreationOverlay != null)
        {
            _characterCreationOverlay.Visible = false;
        }
        SetViewportActive(_characterAvatarViewport, false);
        _characterAvatarPreview?.SetPreviewActive(false);
    }

    private string LocalizeRegistrationError(string message)
    {
        if (message.Contains("від 2 до 24", StringComparison.Ordinal))
        {
            return Tr(DashboardCharacterCreation.InvalidUsernameKey);
        }
        if (message.Contains("вже зареєстрований", StringComparison.Ordinal))
        {
            return Tr("CHARACTER_ERROR_NAME_TAKEN");
        }
        return string.IsNullOrWhiteSpace(message) ? Tr("CHARACTER_ERROR_SERVER") : message;
    }

    private void SelectCharacterAgeGroup(string ageGroup)
    {
        if (_pendingRegistration)
        {
            return;
        }

        _selectedCharacterAgeGroup = DashboardCharacterCreation.NormalizeAgeGroup(ageGroup);
        UpdateCharacterCreationUi();
    }

    private void UpdateCharacterCreationUi()
    {
        string localeCode = DashboardLocaleProfile.Normalize(TranslationServer.GetLocale());
        if (_characterUkrainianButton != null)
        {
            _characterUkrainianButton.ButtonPressed = localeCode == DashboardLocaleProfile.Ukrainian;
        }
        if (_characterEnglishButton != null)
        {
            _characterEnglishButton.ButtonPressed = localeCode == DashboardLocaleProfile.English;
        }
        if (_characterTeenButton != null)
        {
            _characterTeenButton.ButtonPressed = _selectedCharacterAgeGroup == "teen";
            _characterTeenButton.Disabled = _pendingRegistration;
        }
        if (_characterAdultButton != null)
        {
            _characterAdultButton.ButtonPressed = _selectedCharacterAgeGroup == "adult";
            _characterAdultButton.Disabled = _pendingRegistration;
        }
        if (_characterMatureButton != null)
        {
            _characterMatureButton.ButtonPressed = _selectedCharacterAgeGroup == "mature";
            _characterMatureButton.Disabled = _pendingRegistration;
        }
        if (_characterNameInput != null)
        {
            _characterNameInput.Editable = !_pendingRegistration;
        }
        if (_characterAgeDescriptionLabel != null)
        {
            string descriptionKey = _selectedCharacterAgeGroup switch
            {
                "teen" => "CHARACTER_AGE_TEEN_DESCRIPTION",
                "mature" => "CHARACTER_AGE_MATURE_DESCRIPTION",
                _ => "CHARACTER_AGE_ADULT_DESCRIPTION",
            };
            _characterAgeDescriptionLabel.Text = Tr(descriptionKey);
        }
        if (_characterCreateButton != null)
        {
            _characterCreateButton.Disabled = _pendingRegistration;
            _characterCreateButton.Text = Tr(
                _pendingRegistration ? "CHARACTER_CREATING_BUTTON" : "CHARACTER_CREATE_BUTTON");
        }
        UpdateCharacterAvatarUi();
    }

    private void BindCharacterAvatarControls()
    {
        if (_characterBodyPreviousButton != null)
        {
            _characterBodyPreviousButton.Pressed += () => CycleCharacterAvatar(selection => selection.CycleBody(-1));
        }
        if (_characterBodyNextButton != null)
        {
            _characterBodyNextButton.Pressed += () => CycleCharacterAvatar(selection => selection.CycleBody(1));
        }
        if (_characterFacePreviousButton != null)
        {
            _characterFacePreviousButton.Pressed += () => CycleCharacterAvatar(selection => selection.CycleFace(-1));
        }
        if (_characterFaceNextButton != null)
        {
            _characterFaceNextButton.Pressed += () => CycleCharacterAvatar(selection => selection.CycleFace(1));
        }
        if (_characterSkinPreviousButton != null)
        {
            _characterSkinPreviousButton.Pressed += () => CycleCharacterAvatar(selection => selection.CycleSkin(-1));
        }
        if (_characterSkinNextButton != null)
        {
            _characterSkinNextButton.Pressed += () => CycleCharacterAvatar(selection => selection.CycleSkin(1));
        }
        if (_characterHairPreviousButton != null)
        {
            _characterHairPreviousButton.Pressed += () => CycleCharacterAvatar(selection => selection.CycleHairStyle(-1));
        }
        if (_characterHairNextButton != null)
        {
            _characterHairNextButton.Pressed += () => CycleCharacterAvatar(selection => selection.CycleHairStyle(1));
        }
        if (_characterHairColorPreviousButton != null)
        {
            _characterHairColorPreviousButton.Pressed += () => CycleCharacterAvatar(selection => selection.CycleHairColor(-1));
        }
        if (_characterHairColorNextButton != null)
        {
            _characterHairColorNextButton.Pressed += () => CycleCharacterAvatar(selection => selection.CycleHairColor(1));
        }
    }

    private void CycleCharacterAvatar(
        Func<DashboardAvatarSelection, DashboardAvatarSelection> update
    )
    {
        if (_pendingRegistration)
        {
            return;
        }
        _selectedAvatar = update(_selectedAvatar);
        UpdateCharacterAvatarUi();
    }

    private void UpdateCharacterAvatarUi()
    {
        if (_characterBodyValueLabel != null)
        {
            _characterBodyValueLabel.Text = Tr(
                _selectedAvatar.BodyPresetCode == "body_sturdy"
                    ? "CHARACTER_BODY_STURDY"
                    : "CHARACTER_BODY_STANDARD"
            );
        }
        if (_characterFaceValueLabel != null)
        {
            int position = DashboardAvatarSelection.PositionOf(
                DashboardAvatarSelection.FacePresetCodes,
                _selectedAvatar.FacePresetCode
            );
            _characterFaceValueLabel.Text = $"{Tr("CHARACTER_FACE_VALUE")} {position}/20";
        }
        if (_characterSkinValueLabel != null)
        {
            int position = DashboardAvatarSelection.PositionOf(
                DashboardAvatarSelection.SkinToneCodes,
                _selectedAvatar.SkinToneCode
            );
            _characterSkinValueLabel.Text = $"{Tr("CHARACTER_SKIN_VALUE")} {position}/6";
        }
        if (_characterHairValueLabel != null)
        {
            _characterHairValueLabel.Text = Tr(HairStyleTranslationKey(_selectedAvatar.HairStyleCode));
        }
        if (_characterHairColorValueLabel != null)
        {
            _characterHairColorValueLabel.Text = Tr(HairColorTranslationKey(_selectedAvatar.HairColorCode));
        }

        foreach (var button in CharacterAvatarButtons())
        {
            if (button != null)
            {
                button.Disabled = _pendingRegistration;
            }
        }
        _characterAvatarPreview?.SetSelection(_selectedAvatar);
    }

    private IEnumerable<Button> CharacterAvatarButtons()
    {
        yield return _characterBodyPreviousButton;
        yield return _characterBodyNextButton;
        yield return _characterFacePreviousButton;
        yield return _characterFaceNextButton;
        yield return _characterSkinPreviousButton;
        yield return _characterSkinNextButton;
        yield return _characterHairPreviousButton;
        yield return _characterHairNextButton;
        yield return _characterHairColorPreviousButton;
        yield return _characterHairColorNextButton;
    }

    private static string HairStyleTranslationKey(string code)
    {
        return code switch
        {
            "hair_short_02" => "CHARACTER_HAIR_SHORT_02",
            "hair_medium_01" => "CHARACTER_HAIR_MEDIUM_01",
            "hair_medium_02" => "CHARACTER_HAIR_MEDIUM_02",
            "hair_long_01" => "CHARACTER_HAIR_LONG_01",
            "hair_long_02" => "CHARACTER_HAIR_LONG_02",
            "hair_buzz_01" => "CHARACTER_HAIR_BUZZ",
            "hair_bald" => "CHARACTER_HAIR_BALD",
            _ => "CHARACTER_HAIR_SHORT_01",
        };
    }

    private static string HairColorTranslationKey(string code)
    {
        return code switch
        {
            "hair_black" => "CHARACTER_HAIR_COLOR_BLACK",
            "hair_blond" => "CHARACTER_HAIR_COLOR_BLOND",
            "hair_auburn" => "CHARACTER_HAIR_COLOR_AUBURN",
            "hair_gray" => "CHARACTER_HAIR_COLOR_GRAY",
            "hair_white" => "CHARACTER_HAIR_COLOR_WHITE",
            _ => "CHARACTER_HAIR_COLOR_BROWN",
        };
    }

    public void OnCharacterTeenButtonPressed()
    {
        SelectCharacterAgeGroup("teen");
    }

    public void OnCharacterAdultButtonPressed()
    {
        SelectCharacterAgeGroup("adult");
    }

    public void OnCharacterMatureButtonPressed()
    {
        SelectCharacterAgeGroup("mature");
    }

    private void SelectCharacterLocale(string localeCode)
    {
        string normalized = DashboardLocaleProfile.Normalize(localeCode);
        if (_session != null)
        {
            _session.SetLocaleCode(normalized);
        }
        else
        {
            TranslationServer.SetLocale(normalized);
        }

        if (_characterErrorLabel != null)
        {
            _characterErrorLabel.Visible = false;
        }
        UpdateCharacterCreationUi();
    }

    public void OnCharacterUkrainianButtonPressed()
    {
        SelectCharacterLocale(DashboardLocaleProfile.Ukrainian);
    }

    public void OnCharacterEnglishButtonPressed()
    {
        SelectCharacterLocale(DashboardLocaleProfile.English);
    }

    public void OnCharacterCreateButtonPressed()
    {
        if (_pendingRegistration || _characterNameInput == null)
        {
            return;
        }

        string username = DashboardCharacterCreation.NormalizeUsername(_characterNameInput.Text);
        string validationKey = DashboardCharacterCreation.ValidateUsername(username);
        if (!string.IsNullOrEmpty(validationKey))
        {
            ShowCharacterCreation(Tr(validationKey));
            return;
        }

        _pendingRegistration = true;
        if (_characterErrorLabel != null)
        {
            _characterErrorLabel.Visible = false;
        }
        UpdateCharacterCreationUi();
        string payload = ApiClient.BuildJson(new
        {
            username,
            tutorial_age_group = _selectedCharacterAgeGroup,
            avatar = _selectedAvatar.ToApiPayload(),
        });
        _apiClient?.Post("/api/player/register", payload);
    }
}
