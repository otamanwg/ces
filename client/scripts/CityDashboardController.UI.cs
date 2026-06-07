using Godot;
using System;

public partial class CityDashboardController : Control
{
    // UI Elements - Exports
    [Export] public Label UsernameLabel;
    [Export] public Label BalanceLabel;
    [Export] public Label EducationLabel;
    [Export] public Label CurrentJobLabel;
    [Export] public Label CurrentHostelLabel;
    [Export] public Label OwnedBusinessLabel;
    [Export] public Label SportsLabel;
    [Export] public Label StatusLabel;
    [Export] public Label EffectsLabel;
    [Export] public Label ErrorStateLabel;
    [Export] public Label EventHistoryLabel;
    [Export] public Label BuildingPortfolioLabel;
    [Export] public Label BuildPlanLabel;
    [Export] public Label GoalLabel;
    [Export] public Label NextActionLabel;
    [Export] public ProgressBar GoalProgressBar;
    [Export] public TextureProgressBar EnergyBar;
    [Export] public TextureProgressBar MoodBar;
    [Export] public TextureProgressBar HungerBar;
    [Export] public Label CityNameLabel;
    [Export] public Label TreasuryLabel;
    [Export] public Label InflationLabel;

    // UI Elements - Buttons
    private Button _applyJobButton;
    private Button _workButton;
    private Button _sleepButton;
    private Button _eatButton;
    private Button _buyBusinessButton;
    private Button _collectDividendButton;
    private Button _joinSportsButton;
    private Button _trainSportsButton;
    private Button _examButton;
    private Button _refreshButton;
    private Button _openBuildingButton;
    private Button _repairBuildingButton;
    private Button _buyStarterLandButton;
    private Button _visualFocusButton;

    // UI Elements - Onboarding Overlay
    private Control _onboardingOverlay;
    private TextureRect _onboardingBackdrop;
    private TextureRect _onboardingPortrait;
    private Label _onboardingTitleLabel;
    private Label _onboardingNarrativeLabel;
    private Label _onboardingPoliceStatusLabel;
    private Button _onboardingPoliceButton;
    private Button _onboardingHousingButton;
    private Button _onboardingContinueButton;
    private Button _policeRecoveryButton;

    // UI Elements - Character Creation Overlay
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

    // UI Elements - Player Avatar Profile
    private Control _playerAvatarProfile;
    private CharacterAvatarPreview _playerAvatarPreview;
    private SubViewport _playerAvatarViewport;
    private Label _playerAvatarIdentityLabel;

    // UI Elements - Street Avatar Container
    private Control _streetAvatarContainer;
    private CharacterAvatarPreview _streetAvatarPreview;
    private SubViewport _streetAvatarViewport;
    private Label _streetAvatarNameLabel;

    // UI Initialization
    private void InitializeUIReferences()
    {
        // Find main buttons
        _applyJobButton = GetNode<Button>("MainPanel/ActionsContainer/ApplyJobButton");
        _workButton = GetNode<Button>("MainPanel/ActionsContainer/WorkButton");
        _sleepButton = GetNode<Button>("MainPanel/ActionsContainer/SleepButton");
        _eatButton = GetNode<Button>("MainPanel/ActionsContainer/EatButton");
        _buyBusinessButton = GetNode<Button>("MainPanel/ActionsContainer/BuyBusinessButton");
        _collectDividendButton = GetNode<Button>("MainPanel/ActionsContainer/CollectDividendButton");
        _joinSportsButton = GetNode<Button>("MainPanel/ActionsContainer/JoinSportsButton");
        _trainSportsButton = GetNode<Button>("MainPanel/ActionsContainer/TrainSportsButton");
        _examButton = GetNode<Button>("MainPanel/ActionsContainer/ExamButton");
        _refreshButton = GetNode<Button>("MainPanel/ActionsContainer/RefreshButton");
        _openBuildingButton = GetNode<Button>("MainPanel/ActionsContainer/OpenBuildingButton");
        _repairBuildingButton = GetNode<Button>("MainPanel/ActionsContainer/RepairBuildingButton");
        _buyStarterLandButton = GetNode<Button>("MainPanel/ActionsContainer/BuyStarterLandButton");
        _visualFocusButton = GetNode<Button>("MainPanel/ActionsContainer/VisualFocusButton");

        // Find onboarding overlay elements
        _onboardingOverlay = GetNode<Control>("OnboardingOverlay");
        _onboardingBackdrop = GetNode<TextureRect>("OnboardingOverlay/Backdrop");
        _onboardingPortrait = GetNode<TextureRect>("OnboardingOverlay/Portrait");
        _onboardingTitleLabel = GetNode<Label>("OnboardingOverlay/TitleLabel");
        _onboardingNarrativeLabel = GetNode<Label>("OnboardingOverlay/NarrativeLabel");
        _onboardingPoliceStatusLabel = GetNode<Label>("OnboardingOverlay/PoliceStatusLabel");
        _onboardingPoliceButton = GetNode<Button>("OnboardingOverlay/PoliceButton");
        _onboardingHousingButton = GetNode<Button>("OnboardingOverlay/HousingButton");
        _onboardingContinueButton = GetNode<Button>("OnboardingOverlay/ContinueButton");
        _policeRecoveryButton = GetNode<Button>("OnboardingOverlay/PoliceRecoveryButton");

        // Find character creation overlay elements
        _characterCreationOverlay = GetNode<Control>("CharacterCreationOverlay");
        _characterCreationBackdrop = GetNode<TextureRect>("CharacterCreationOverlay/Backdrop");
        _characterNameInput = GetNode<LineEdit>("CharacterCreationOverlay/NameInput");
        _characterAgeDescriptionLabel = GetNode<Label>("CharacterCreationOverlay/AgeDescriptionLabel");
        _characterErrorLabel = GetNode<Label>("CharacterCreationOverlay/ErrorLabel");
        _characterTeenButton = GetNode<Button>("CharacterCreationOverlay/TeenButton");
        _characterAdultButton = GetNode<Button>("CharacterCreationOverlay/AdultButton");
        _characterMatureButton = GetNode<Button>("CharacterCreationOverlay/MatureButton");
        _characterCreateButton = GetNode<Button>("CharacterCreationOverlay/CreateButton");
        _characterUkrainianButton = GetNode<Button>("CharacterCreationOverlay/UkrainianButton");
        _characterEnglishButton = GetNode<Button>("CharacterCreationOverlay/EnglishButton");
        _characterAvatarPreview = GetNode<CharacterAvatarPreview>("CharacterCreationOverlay/AvatarPreview");
        _characterBodyValueLabel = GetNode<Label>("CharacterCreationOverlay/BodyValueLabel");
        _characterFaceValueLabel = GetNode<Label>("CharacterCreationOverlay/FaceValueLabel");
        _characterSkinValueLabel = GetNode<Label>("CharacterCreationOverlay/SkinValueLabel");
        _characterHairValueLabel = GetNode<Label>("CharacterCreationOverlay/HairValueLabel");
        _characterHairColorValueLabel = GetNode<Label>("CharacterCreationOverlay/HairColorValueLabel");
        _characterBodyPreviousButton = GetNode<Button>("CharacterCreationOverlay/BodyPreviousButton");
        _characterBodyNextButton = GetNode<Button>("CharacterCreationOverlay/BodyNextButton");
        _characterFacePreviousButton = GetNode<Button>("CharacterCreationOverlay/FacePreviousButton");
        _characterFaceNextButton = GetNode<Button>("CharacterCreationOverlay/FaceNextButton");
        _characterSkinPreviousButton = GetNode<Button>("CharacterCreationOverlay/SkinPreviousButton");
        _characterSkinNextButton = GetNode<Button>("CharacterCreationOverlay/SkinNextButton");
        _characterHairPreviousButton = GetNode<Button>("CharacterCreationOverlay/HairPreviousButton");
        _characterHairNextButton = GetNode<Button>("CharacterCreationOverlay/HairNextButton");
        _characterHairColorPreviousButton = GetNode<Button>("CharacterCreationOverlay/HairColorPreviousButton");
        _characterHairColorNextButton = GetNode<Button>("CharacterCreationOverlay/HairColorNextButton");

        // Find player avatar profile elements
        _playerAvatarProfile = GetNode<Control>("MainPanel/PlayerAvatarProfile");
        _playerAvatarPreview = GetNode<CharacterAvatarPreview>("MainPanel/PlayerAvatarProfile/AvatarPreview");
        _playerAvatarViewport = GetNode<SubViewport>("MainPanel/PlayerAvatarProfile/AvatarViewport");
        _playerAvatarIdentityLabel = GetNode<Label>("MainPanel/PlayerAvatarProfile/IdentityLabel");

        // Find street avatar container elements
        _streetAvatarContainer = GetNode<Control>("StreetAvatarContainer");
        _streetAvatarPreview = GetNode<CharacterAvatarPreview>("StreetAvatarContainer/AvatarPreview");
        _streetAvatarViewport = GetNode<SubViewport>("StreetAvatarContainer/AvatarViewport");
        _streetAvatarNameLabel = GetNode<Label>("StreetAvatarContainer/NameLabel");
    }

    // UI State Management
    private void SetButtonEnabled(Button button, bool enabled)
    {
        if (button != null)
        {
            button.Disabled = !enabled;
        }
    }

    private void SetLabelText(Label label, string text)
    {
        if (label != null)
        {
            label.Text = text;
        }
    }

    private void SetProgressBarValue(ProgressBar progressBar, float value)
    {
        if (progressBar != null)
        {
            progressBar.Value = value;
        }
    }

    private void SetTextureProgressBarValue(TextureProgressBar progressBar, float value)
    {
        if (progressBar != null)
        {
            progressBar.Value = value;
        }
    }

    // UI Visibility Controls
    private void SetControlVisible(Control control, bool visible)
    {
        if (control != null)
        {
            control.Visible = visible;
        }
    }

    private void SetOverlayVisible(bool visible)
    {
        SetControlVisible(_onboardingOverlay, visible);
        SetControlVisible(_characterCreationOverlay, !visible && _bootstrapPending);
    }
}
