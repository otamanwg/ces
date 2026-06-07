using Godot;
using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Nodes;

public partial class CityDashboardController : Control
{
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

    private ApiClient _apiClient;
    private GameSession _session;
    private NetworkManager _networkManager;
    private ExamPanelController _examPanel;
    private CityVisualOverlay _cityVisualOverlay;
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
    private Control _playerAvatarProfile;
    private CharacterAvatarPreview _playerAvatarPreview;
    private SubViewport _playerAvatarViewport;
    private Label _playerAvatarIdentityLabel;
    private Control _streetAvatarContainer;
    private CharacterAvatarPreview _streetAvatarPreview;
    private SubViewport _streetAvatarViewport;
    private Label _streetAvatarNameLabel;
    private SubViewport _characterAvatarViewport;
    private DashboardStatusPresenter _statusPresenter;
    private DashboardActionPresenter _actionPresenter;
    private DashboardOnboardingState _onboardingState = new();
    private DashboardTutorialAgeGroup _tutorialAgeGroup = DashboardTutorialAgeGroup.Adult;
    private int _arrivalStoryBeat;
    private bool _arrivalStoryInitialized;
    private bool _applyFirstVacancy;
    private bool _buyFirstBusiness;
    private bool _joinFirstSportsClub;
    private bool _pendingApply;
    private bool _pendingBusinessMarket;
    private bool _pendingSportsClubs;
    private bool _pendingExamInfo;
    private bool _pendingRefresh;
    private bool _pendingBuildingPortfolio;
    private bool _pendingBusinessStatus;
    private bool _pendingBuildLandCatalog;
    private bool _pendingBuildBlueprintCatalog;
    private bool _pendingOnboarding;
    private bool _pendingRegistration;
    private bool _bootstrapPending = true;
    private bool _hasJob;
    private bool _canApplyJob;
    private bool _canWork;
    private bool _canSleep;
    private bool _canEat;
    private bool _canBuyBusiness;
    private bool _canCollectDividend;
    private bool _canJoinSports;
    private bool _canTrainSports;
    private bool _canTakeExam;
    private string _playerEducation = "High School";
    private string _ownedBusinessId = "";
    private string _pendingWorkKey = "";
    private string _pendingSleepKey = "";
    private string _pendingEatKey = "";
    private string _pendingBusinessBuyKey = "";
    private string _pendingDividendKey = "";
    private string _pendingSportsJoinKey = "";
    private string _pendingSportsTrainKey = "";
    private string _pendingExamKey = "";
    private string _pendingBuildingOpenKey = "";
    private string _pendingBuildingRepairKey = "";
    private string _pendingLandBuyKey = "";
    private string _pendingBuildingApplicationKey = "";
    private string _pendingBuildingActivationKey = "";
    private string _pendingPoliceRecoveryKey = "";
    private string _portfolioOpenBuildingId = "";
    private string _portfolioRepairBuildingId = "";
    private string _starterLandId = "";
    private string _starterBlueprintId = "";
    private string _approvedApplicationId = "";
    private string _buildFlowAction = "";
    private string _onboardingBackdropPath = "";
    private string _onboardingPortraitPath = "";
    private string _selectedCharacterAgeGroup = DashboardCharacterCreation.DefaultAgeGroup;
    private DashboardAvatarSelection _selectedAvatar = DashboardAvatarSelection.Default;
    private DashboardActiveAvatarState _activeAvatar = DashboardActiveAvatarState.Empty;
    private double _playerBalance;
    private JsonNode _landCatalogData;
    private JsonNode _blueprintCatalogData;
    private DashboardCityVisualModel _cityVisualModel = DashboardCityVisualModel.Empty;

    public override void _Ready()
    {
        BindUiNodes();
        ConfigureTextSafety();
        _statusPresenter = new DashboardStatusPresenter(StatusLabel, ErrorStateLabel, EventHistoryLabel);
        _actionPresenter = new DashboardActionPresenter(
            _applyJobButton,
            _workButton,
            _sleepButton,
            _eatButton,
            _buyBusinessButton,
            _collectDividendButton,
            _joinSportsButton,
            _trainSportsButton,
            _examButton,
            _refreshButton);
        if (_buyStarterLandButton != null)
        {
            _buyStarterLandButton.Pressed += OnBuyStarterLandButtonPressed;
        }
        if (_visualFocusButton != null)
        {
            _visualFocusButton.Pressed += OnVisualFocusButtonPressed;
            if (_cityVisualOverlay != null)
            {
                _visualFocusButton.Text = _cityVisualOverlay.FocusButtonText;
            }
        }
        if (_onboardingPoliceButton != null)
        {
            _onboardingPoliceButton.Pressed += OnOnboardingPoliceButtonPressed;
        }
        if (_onboardingHousingButton != null)
        {
            _onboardingHousingButton.Pressed += OnOnboardingHousingButtonPressed;
        }
        if (_onboardingContinueButton != null)
        {
            _onboardingContinueButton.Pressed += OnOnboardingContinueButtonPressed;
        }
        if (_policeRecoveryButton != null)
        {
            _policeRecoveryButton.Pressed += OnPoliceRecoveryButtonPressed;
        }
        if (_characterTeenButton != null)
        {
            _characterTeenButton.Pressed += OnCharacterTeenButtonPressed;
        }
        if (_characterAdultButton != null)
        {
            _characterAdultButton.Pressed += OnCharacterAdultButtonPressed;
        }
        if (_characterMatureButton != null)
        {
            _characterMatureButton.Pressed += OnCharacterMatureButtonPressed;
        }
        if (_characterCreateButton != null)
        {
            _characterCreateButton.Pressed += OnCharacterCreateButtonPressed;
        }
        if (_characterUkrainianButton != null)
        {
            _characterUkrainianButton.Pressed += OnCharacterUkrainianButtonPressed;
        }
        if (_characterEnglishButton != null)
        {
            _characterEnglishButton.Pressed += OnCharacterEnglishButtonPressed;
        }
        BindCharacterAvatarControls();
        if (_characterNameInput != null)
        {
            _characterNameInput.TextSubmitted += _ => OnCharacterCreateButtonPressed();
        }

        _apiClient = GetNodeOrNull<ApiClient>("/root/ApiClient");
        _session = GetNodeOrNull<GameSession>("/root/GameSession");
        _networkManager = GetNodeOrNull<NetworkManager>("/root/NetworkManager");
        _examPanel = GetNodeOrNull<ExamPanelController>("ExamOverlay");
        _cityVisualOverlay?.SetStyleCode(_session?.VisualStyleCode);
        ConfigureOnboardingPortraitMaterial();
        ConfigureCharacterCreationVisual();
        UpdateCharacterCreationUi();
        UpdateActiveAvatarPresentation();
        bool characterCreationVisible = _characterCreationOverlay?.Visible ?? false;
        SetViewportActive(_characterAvatarViewport, characterCreationVisible);
        _characterAvatarPreview?.SetPreviewActive(characterCreationVisible);

        if (_apiClient != null)
        {
            _apiClient.RequestFinished += OnApiRequestFinished;
        }

        if (_networkManager != null)
        {
            _networkManager.MessageReceived += OnServerMessageReceived;
        }

        if (_examPanel != null)
        {
            _examPanel.SubmitRequested += OnExamSubmitRequested;
            _examPanel.Closed += () => SetStatus("Іспит закрито.");
        }

        if (EnergyBar != null)
        {
            EnergyBar.MaxValue = 100;
        }

        if (MoodBar != null)
        {
            MoodBar.MaxValue = 100;
        }

        if (HungerBar != null)
        {
            HungerBar.MaxValue = 100;
        }

        SetStatus("Підключення до сервера...");
        UpdateActionButtons();
        _apiClient?.Get("/api/city/status");
    }

    private void ConfigureOnboardingPortraitMaterial()
    {
        if (_onboardingPortrait == null)
        {
            return;
        }

        var shader = ResourceLoader.Load<Shader>("res://shaders/onboarding_portrait_blend.gdshader");
        if (shader != null)
        {
            _onboardingPortrait.Material = new ShaderMaterial { Shader = shader };
        }
    }

    private void BindUiNodes()
    {
        UsernameLabel ??= GetNodeOrNull<Label>("%UsernameLabel");
        BalanceLabel ??= GetNodeOrNull<Label>("%BalanceLabel");
        EducationLabel ??= GetNodeOrNull<Label>("%EducationLabel");
        CurrentJobLabel ??= GetNodeOrNull<Label>("%CurrentJobLabel");
        CurrentHostelLabel ??= GetNodeOrNull<Label>("%CurrentHostelLabel");
        OwnedBusinessLabel ??= GetNodeOrNull<Label>("%OwnedBusinessLabel");
        SportsLabel ??= GetNodeOrNull<Label>("%SportsLabel");
        StatusLabel ??= GetNodeOrNull<Label>("%StatusLabel");
        EffectsLabel ??= GetNodeOrNull<Label>("%EffectsLabel");
        ErrorStateLabel ??= GetNodeOrNull<Label>("%ErrorStateLabel");
        EventHistoryLabel ??= GetNodeOrNull<Label>("%EventHistoryLabel");
        BuildingPortfolioLabel ??= GetNodeOrNull<Label>("%BuildingPortfolioLabel");
        BuildPlanLabel ??= GetNodeOrNull<Label>("%BuildPlanLabel");
        GoalLabel ??= GetNodeOrNull<Label>("%GoalLabel");
        NextActionLabel ??= GetNodeOrNull<Label>("%NextActionLabel");
        GoalProgressBar ??= GetNodeOrNull<ProgressBar>("%GoalProgressBar");
        EnergyBar ??= GetNodeOrNull<TextureProgressBar>("%EnergyBar");
        MoodBar ??= GetNodeOrNull<TextureProgressBar>("%MoodBar");
        HungerBar ??= GetNodeOrNull<TextureProgressBar>("%HungerBar");
        CityNameLabel ??= GetNodeOrNull<Label>("%CityNameLabel");
        TreasuryLabel ??= GetNodeOrNull<Label>("%TreasuryLabel");
        InflationLabel ??= GetNodeOrNull<Label>("%InflationLabel");
        _cityVisualOverlay ??= GetNodeOrNull<CityVisualOverlay>("%CityVisualOverlay");
        _applyJobButton ??= GetNodeOrNull<Button>("%ApplyJobButton");
        _workButton ??= GetNodeOrNull<Button>("%WorkButton");
        _sleepButton ??= GetNodeOrNull<Button>("%SleepButton");
        _eatButton ??= GetNodeOrNull<Button>("%EatButton");
        _buyBusinessButton ??= GetNodeOrNull<Button>("%BuyBusinessButton");
        _collectDividendButton ??= GetNodeOrNull<Button>("%CollectDividendButton");
        _joinSportsButton ??= GetNodeOrNull<Button>("%JoinSportsButton");
        _trainSportsButton ??= GetNodeOrNull<Button>("%TrainSportsButton");
        _examButton ??= GetNodeOrNull<Button>("%ExamButton");
        _refreshButton ??= GetNodeOrNull<Button>("%RefreshButton");
        _openBuildingButton ??= GetNodeOrNull<Button>("%OpenBuildingButton");
        _repairBuildingButton ??= GetNodeOrNull<Button>("%RepairBuildingButton");
        _buyStarterLandButton ??= GetNodeOrNull<Button>("%BuyStarterLandButton");
        _visualFocusButton ??= GetNodeOrNull<Button>("%VisualFocusButton");
        _onboardingOverlay ??= GetNodeOrNull<Control>("%OnboardingOverlay");
        _onboardingBackdrop ??= GetNodeOrNull<TextureRect>("%OnboardingBackdrop");
        _onboardingPortrait ??= GetNodeOrNull<TextureRect>("%OnboardingPortrait");
        _onboardingTitleLabel ??= GetNodeOrNull<Label>("%OnboardingTitleLabel");
        _onboardingNarrativeLabel ??= GetNodeOrNull<Label>("%OnboardingNarrativeLabel");
        _onboardingPoliceStatusLabel ??= GetNodeOrNull<Label>("%OnboardingPoliceStatusLabel");
        _onboardingPoliceButton ??= GetNodeOrNull<Button>("%OnboardingPoliceButton");
        _onboardingHousingButton ??= GetNodeOrNull<Button>("%OnboardingHousingButton");
        _onboardingContinueButton ??= GetNodeOrNull<Button>("%OnboardingContinueButton");
        _policeRecoveryButton ??= GetNodeOrNull<Button>("%PoliceRecoveryButton");
        _characterCreationOverlay ??= GetNodeOrNull<Control>("%CharacterCreationOverlay");
        _characterCreationBackdrop ??= GetNodeOrNull<TextureRect>("CharacterCreationOverlay/CharacterCreationBackdrop");
        _characterNameInput ??= GetNodeOrNull<LineEdit>("%CharacterNameInput");
        _characterAgeDescriptionLabel ??= GetNodeOrNull<Label>("%CharacterAgeDescriptionLabel");
        _characterErrorLabel ??= GetNodeOrNull<Label>("%CharacterErrorLabel");
        _characterTeenButton ??= GetNodeOrNull<Button>("%CharacterTeenButton");
        _characterAdultButton ??= GetNodeOrNull<Button>("%CharacterAdultButton");
        _characterMatureButton ??= GetNodeOrNull<Button>("%CharacterMatureButton");
        _characterCreateButton ??= GetNodeOrNull<Button>("%CharacterCreateButton");
        _characterUkrainianButton ??= GetNodeOrNull<Button>("%CharacterUkrainianButton");
        _characterEnglishButton ??= GetNodeOrNull<Button>("%CharacterEnglishButton");
        _characterAvatarPreview ??= GetNodeOrNull<CharacterAvatarPreview>("%CharacterAvatarPreview");
        _characterBodyValueLabel ??= GetNodeOrNull<Label>("%CharacterBodyValueLabel");
        _characterFaceValueLabel ??= GetNodeOrNull<Label>("%CharacterFaceValueLabel");
        _characterSkinValueLabel ??= GetNodeOrNull<Label>("%CharacterSkinValueLabel");
        _characterHairValueLabel ??= GetNodeOrNull<Label>("%CharacterHairValueLabel");
        _characterHairColorValueLabel ??= GetNodeOrNull<Label>("%CharacterHairColorValueLabel");
        _characterBodyPreviousButton ??= GetNodeOrNull<Button>("%CharacterBodyPreviousButton");
        _characterBodyNextButton ??= GetNodeOrNull<Button>("%CharacterBodyNextButton");
        _characterFacePreviousButton ??= GetNodeOrNull<Button>("%CharacterFacePreviousButton");
        _characterFaceNextButton ??= GetNodeOrNull<Button>("%CharacterFaceNextButton");
        _characterSkinPreviousButton ??= GetNodeOrNull<Button>("%CharacterSkinPreviousButton");
        _characterSkinNextButton ??= GetNodeOrNull<Button>("%CharacterSkinNextButton");
        _characterHairPreviousButton ??= GetNodeOrNull<Button>("%CharacterHairPreviousButton");
        _characterHairNextButton ??= GetNodeOrNull<Button>("%CharacterHairNextButton");
        _characterHairColorPreviousButton ??= GetNodeOrNull<Button>("%CharacterHairColorPreviousButton");
        _characterHairColorNextButton ??= GetNodeOrNull<Button>("%CharacterHairColorNextButton");
        _playerAvatarProfile ??= GetNodeOrNull<Control>("%PlayerAvatarProfile");
        _playerAvatarPreview ??= GetNodeOrNull<CharacterAvatarPreview>("%PlayerAvatarPreview");
        _playerAvatarViewport ??= GetNodeOrNull<SubViewport>(
            "RootMargin/LandscapeGrid/LeftRail/PlayerPanel/PlayerBox/PlayerAvatarProfile/PlayerAvatarViewportContainer/PlayerAvatarViewport");
        _playerAvatarIdentityLabel ??= GetNodeOrNull<Label>("%PlayerAvatarIdentityLabel");
        _streetAvatarContainer ??= GetNodeOrNull<Control>("%StreetAvatarContainer");
        _streetAvatarPreview ??= GetNodeOrNull<CharacterAvatarPreview>("%StreetAvatarPreview");
        _streetAvatarViewport ??= GetNodeOrNull<SubViewport>(
            "RootMargin/LandscapeGrid/CenterScroll/CenterStage/CityVisualPanel/CityVisual/StreetAvatarContainer/StreetAvatarViewportContainer/StreetAvatarViewport");
        _streetAvatarNameLabel ??= GetNodeOrNull<Label>("%StreetAvatarNameLabel");
        _characterAvatarViewport ??= GetNodeOrNull<SubViewport>(
            "CharacterCreationOverlay/CharacterCreationCenter/CharacterCreationPanel/CharacterCreationMargin/CharacterCreationBox/CharacterContentRow/CharacterPreviewColumn/CharacterPreviewFrame/CharacterPreviewViewportContainer/CharacterPreviewViewport");
    }

    private void ConfigureTextSafety()
    {
        ConfigureLabel(StatusLabel, 1, 20);
        ConfigureLabel(UsernameLabel, 1, 20);
        ConfigureLabel(CurrentJobLabel, 1, 20);
        ConfigureLabel(CurrentHostelLabel, 1, 20);
        ConfigureLabel(OwnedBusinessLabel, 1, 20);
        ConfigureLabel(SportsLabel, 1, 20);
        ConfigureLabel(CityNameLabel, 1, 20);
        ConfigureLabel(NextActionLabel, 2, 38);
        ConfigureLabel(BuildingPortfolioLabel, 2, 38);
        ConfigureLabel(BuildPlanLabel, 2, 38);
        ConfigureLabel(GoalLabel, 1, 20);
        ConfigureLabel(EffectsLabel, 2, 38);
        ConfigureLabel(EventHistoryLabel, 3, 56);
        ConfigureLabel(ErrorStateLabel, 2, 38);
        ConfigureLabel(_onboardingTitleLabel, 2, 52);
        ConfigureLabel(_onboardingNarrativeLabel, 5, 120);
        ConfigureLabel(_onboardingPoliceStatusLabel, 2, 48);
        ConfigureLabel(_characterAgeDescriptionLabel, 3, 62);
        ConfigureLabel(_characterErrorLabel, 2, 44);
        ConfigureLabel(_playerAvatarIdentityLabel, 2, 34);
        ConfigureLabel(_streetAvatarNameLabel, 1, 24);
    }

    private void ConfigureCharacterCreationVisual()
    {
        if (_characterCreationBackdrop == null)
        {
            return;
        }

        _characterCreationBackdrop.Texture = ResourceLoader.Load<Texture2D>(
            "res://assets/visual/core/arrival_waiting_hall_core.png");
    }

    private static void ConfigureLabel(Label label, int maxLines, float minimumHeight)
    {
        if (label == null)
        {
            return;
        }

        label.CustomMinimumSize = new Vector2(label.CustomMinimumSize.X, minimumHeight);
        label.AutowrapMode = maxLines == 1
            ? TextServer.AutowrapMode.Off
            : TextServer.AutowrapMode.WordSmart;
        label.TextOverrunBehavior = TextServer.OverrunBehavior.TrimEllipsis;
        label.MaxLinesVisible = maxLines;
    }

    private void OnApiRequestFinished(string endpoint, bool success, string jsonBody)
    {
        if (!success)
        {
            HandleTransportError(endpoint, jsonBody);
            return;
        }

        var root = JsonNode.Parse(jsonBody);
        if (root == null)
        {
            SetErrorState("Порожня відповідь сервера.");
            ClearPendingAction(endpoint);
            return;
        }

        if (endpoint == "/api/city/status")
        {
            HandleCityStatus(root);
            return;
        }

        if (endpoint == "/api/land/parcels")
        {
            HandleLandParcels(root);
            return;
        }

        if (endpoint == "/api/business/blueprints")
        {
            HandleBusinessBlueprints(root);
            return;
        }

        if (endpoint == "/api/jobs/vacancies" && _applyFirstVacancy)
        {
            HandleVacanciesForApply(root);
            return;
        }

        if (endpoint == "/api/businesses/market" && _buyFirstBusiness)
        {
            HandleBusinessMarketForBuy(root);
            return;
        }

        if (endpoint == "/api/sports/clubs" && _joinFirstSportsClub)
        {
            HandleSportsClubsForJoin(root);
            return;
        }

        if (endpoint == "/api/education/exam/info")
        {
            HandleExamInfo(root);
            return;
        }

        if (IsBuildingPortfolioEndpoint(endpoint))
        {
            HandleBuildingPortfolio(root);
            return;
        }

        if (IsBusinessStatusEndpoint(endpoint))
        {
            HandleBusinessStatus(root);
            return;
        }

        bool apiSuccess = root["success"]?.GetValue<bool>() ?? false;
        string message = root["message"]?.ToString() ?? "";
        var data = root["data"];

        if (!apiSuccess)
        {
            if (endpoint == "/api/player/register")
            {
                _pendingRegistration = false;
                ShowCharacterCreation(LocalizeRegistrationError(message));
                return;
            }

            if (IsSessionError(message))
            {
                HandleInvalidSession(message);
            }
            else
            {
                SetErrorState(BuildActionErrorMessage(endpoint, message));
            }

            if (endpoint == "/api/education/exam/submit")
            {
                _examPanel?.SetSubmitEnabled(true);
            }

            ClearPendingAction(endpoint);
            return;
        }

        ClearPendingAction(endpoint);

        if (endpoint == "/api/player/register" || endpoint.StartsWith("/api/player/"))
        {
            _bootstrapPending = false;
        }
        if (endpoint == "/api/player/register")
        {
            _pendingRegistration = false;
        }

        ClearErrorState();
        SetStatus(message, true);
        UpdateEffectsUI(root["effects"]);
        AddNewsToHistory(data);

        if (data != null && data["username"] != null)
        {
            HideCharacterCreation();
            UpdatePlayerUI(data);
        }

        if (endpoint == "/api/land/buy")
        {
            RefreshBuildCatalog(forceLandRefresh: true);
        }

        if (endpoint == "/api/building/applications")
        {
            HandleBuildingApplicationSubmission(data);
        }

        if (IsBuildingActivationEndpoint(endpoint))
        {
            _approvedApplicationId = "";
            _buildFlowAction = "";
            RefreshBuildingPortfolio();
            RefreshBuildCatalog(forceLandRefresh: true);
        }

        if (data != null && data["name"] != null && data["treasury_balance"] != null)
        {
            UpdateCityUI(data);
        }

        if (endpoint.StartsWith("/api/jobs/apply"))
        {
            _pendingApply = false;
        }

        if (endpoint == "/api/education/exam/submit")
        {
            string resultMessage = message;
            if (data?["passed"]?.GetValue<bool>() == true)
            {
                resultMessage = $"Іспит здано! {data["score"]}. Тепер доступні кращі вакансії.";
            }

            _examPanel?.ShowResult(resultMessage);
            SetStatus(resultMessage, true);
        }

        UpdateNextActionHint(root["effects"]);
        UpdateGoalUI(root["effects"]);
        UpdateActionButtons();
    }

    private void HandleTransportError(string endpoint, string jsonBody)
    {
        _applyFirstVacancy = false;
        _buyFirstBusiness = false;
        _joinFirstSportsClub = false;
        _pendingApply = false;
        _pendingBusinessMarket = false;
        _pendingSportsClubs = false;
        _pendingExamInfo = false;
        _pendingRefresh = false;
        _pendingBuildingPortfolio = false;
        _pendingBusinessStatus = false;
        _pendingBuildLandCatalog = false;
        _pendingBuildBlueprintCatalog = false;
        _pendingOnboarding = false;
        _pendingRegistration = false;
        _pendingLandBuyKey = "";
        _pendingBuildingApplicationKey = "";
        _pendingBuildingActivationKey = "";
        ClearPendingAction(endpoint);
        _examPanel?.SetSubmitEnabled(true);

        if (endpoint == "/api/player/register")
        {
            ShowCharacterCreation(Tr("CHARACTER_ERROR_SERVER"));
            return;
        }

        if (!string.IsNullOrWhiteSpace(jsonBody))
        {
            try
            {
                var root = JsonNode.Parse(jsonBody);
                string message = root?["message"]?.ToString() ?? "";
                if (!string.IsNullOrEmpty(message))
                {
                    SetErrorState(BuildActionErrorMessage(endpoint, message));
                    UpdateActionButtons();
                    return;
                }
            }
            catch (Exception e)
            {
                GD.PrintErr($"CityDashboardController: error body parse failed: {e.Message}");
            }
        }

        SetErrorState("Backend недоступний. Запусти: .\\scripts\\play.ps1");
        UpdateActionButtons();
    }

    private static bool IsSessionError(string message)
    {
        return message.Contains("Сесія гравця недійсна", StringComparison.Ordinal);
    }

    private void HandleInvalidSession(string message)
    {
        _session?.ClearSession();
        _bootstrapPending = true;
        _hasJob = false;
        _canApplyJob = false;
        _canWork = false;
        _canSleep = false;
        _canEat = false;
        _canBuyBusiness = false;
        _canCollectDividend = false;
        _canJoinSports = false;
        _canTrainSports = false;
        _canTakeExam = false;
        _playerBalance = 0.0;
        _activeAvatar = DashboardActiveAvatarState.Empty;
        UpdateActiveAvatarPresentation();
        ClearBuildingPortfolio();
        ClearBuildFlow();
        SetErrorState(message);
        UpdateActionButtons();
        ShowCharacterCreation(Tr("CHARACTER_ERROR_SESSION"));
    }

    private void HandleCityStatus(JsonNode root)
    {
        if (root["success"]?.GetValue<bool>() != true)
        {
            _pendingRefresh = false;
            SetErrorState("Місто недоступне.");
            UpdateActionButtons();
            return;
        }

        var data = root["data"];
        if (data == null)
        {
            _pendingRefresh = false;
            return;
        }

        UpdateCityUI(data);
        UpdateCityVisual(data);
        AddNewsToHistory(data);
        _pendingRefresh = false;
        string cityId = data["id"]?.ToString() ?? "";
        _session?.SetCityId(cityId);
        _networkManager?.ConnectToCity(cityId);

        if (_session != null && _session.HasAuthenticatedPlayer)
        {
            _apiClient?.GetAuthorized($"/api/player/{_session.PlayerId}", _session.AuthToken);
            return;
        }

        ShowCharacterCreation();
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

    private void HandleVacanciesForApply(JsonNode root)
    {
        _applyFirstVacancy = false;

        if (root["success"]?.GetValue<bool>() != true)
        {
            _pendingApply = false;
            SetErrorState("Не вдалось отримати вакансії.");
            UpdateActionButtons();
            return;
        }

        var vacancies = root["data"]?["vacancies"]?.AsArray();
        if (vacancies == null || vacancies.Count == 0)
        {
            _pendingApply = false;
            SetErrorState("Немає вільних вакансій. Спробуйте оновити статус міста або повернутися пізніше.");
            UpdateActionButtons();
            return;
        }

        JsonNode picked = null;
        foreach (var vacancy in vacancies)
        {
            if (vacancy?["min_education"]?.ToString() == _playerEducation)
            {
                picked = vacancy;
                break;
            }
        }

        picked ??= vacancies[0];
        string jobId = picked?["id"]?.ToString() ?? "";
        if (string.IsNullOrEmpty(jobId) || _session == null)
        {
            _pendingApply = false;
            UpdateActionButtons();
            return;
        }

        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId, job_id = jobId });
        _apiClient?.PostAuthorized("/api/jobs/apply", _session.AuthToken, payload);
    }

    private void HandleBusinessMarketForBuy(JsonNode root)
    {
        _buyFirstBusiness = false;
        _pendingBusinessMarket = false;

        if (root["success"]?.GetValue<bool>() != true)
        {
            SetErrorState("Не вдалось отримати бізнеси.");
            UpdateActionButtons();
            return;
        }

        var businesses = root["data"]?["businesses"]?.AsArray();
        if (businesses == null || businesses.Count == 0)
        {
            SetErrorState("Немає доступних бізнесів для купівлі.");
            UpdateActionButtons();
            return;
        }

        JsonNode picked = businesses[0];
        string businessId = picked?["id"]?.ToString() ?? "";
        if (string.IsNullOrEmpty(businessId) || _session == null)
        {
            UpdateActionButtons();
            return;
        }

        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId, business_id = businessId });
        _pendingBusinessBuyKey = BuildActionKey("business");
        UpdateActionButtons();
        _apiClient?.PostAuthorizedIdempotent("/api/businesses/buy", _session.AuthToken, _pendingBusinessBuyKey, payload);
    }

    private void HandleSportsClubsForJoin(JsonNode root)
    {
        _joinFirstSportsClub = false;
        _pendingSportsClubs = false;

        if (root["success"]?.GetValue<bool>() != true)
        {
            SetErrorState("Не вдалось отримати спортивні клуби.");
            UpdateActionButtons();
            return;
        }

        var clubs = root["data"]?["clubs"]?.AsArray();
        if (clubs == null || clubs.Count == 0)
        {
            SetErrorState("Немає доступних спортивних клубів.");
            UpdateActionButtons();
            return;
        }

        string clubId = clubs[0]?["id"]?.ToString() ?? "";
        if (string.IsNullOrEmpty(clubId) || _session == null)
        {
            UpdateActionButtons();
            return;
        }

        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId, club_id = clubId });
        _pendingSportsJoinKey = BuildActionKey("sports-join");
        UpdateActionButtons();
        _apiClient?.PostAuthorizedIdempotent("/api/sports/join", _session.AuthToken, _pendingSportsJoinKey, payload);
    }

    private void HandleExamInfo(JsonNode root)
    {
        _pendingExamInfo = false;
        if (root["success"]?.GetValue<bool>() != true)
        {
            SetErrorState("Не вдалось завантажити іспит.");
            UpdateActionButtons();
            return;
        }

        ClearErrorState();
        _examPanel?.LoadExam(root["data"]);
        UpdateActionButtons();
    }

    private void HandleBuildingPortfolio(JsonNode root)
    {
        _pendingBuildingPortfolio = false;
        if (root["success"]?.GetValue<bool>() != true)
        {
            string message = root["message"]?.ToString() ?? "Не вдалось завантажити будівлі.";
            if (IsSessionError(message))
            {
                HandleInvalidSession(message);
            }
            else
            {
                SetErrorState(message);
            }

            UpdateBuildingPortfolioButtons();
            return;
        }

        var portfolio = DashboardBuildingPortfolio.FromJson(root["data"]);
        if (BuildingPortfolioLabel != null)
        {
            BuildingPortfolioLabel.Text = portfolio.SummaryText;
        }

        _cityVisualOverlay?.SetBuildingPortfolio(portfolio);

        _portfolioOpenBuildingId = portfolio.OpenCandidate?.Id ?? "";
        _portfolioRepairBuildingId = portfolio.RepairCandidate?.Id ?? "";
        UpdateBuildingPortfolioButtons();
    }

    private void HandleLandParcels(JsonNode root)
    {
        _pendingBuildLandCatalog = false;
        if (root["success"]?.GetValue<bool>() != true)
        {
            _landCatalogData = null;
            SetErrorState(root["message"]?.ToString() ?? "Не вдалось завантажити землю.");
            UpdateBuildFlowUi();
            return;
        }

        _landCatalogData = root["data"]?.DeepClone();
        UpdateBuildFlowUi();
    }

    private void HandleBusinessBlueprints(JsonNode root)
    {
        _pendingBuildBlueprintCatalog = false;
        if (root["success"]?.GetValue<bool>() != true)
        {
            _blueprintCatalogData = null;
            SetErrorState(root["message"]?.ToString() ?? "Не вдалось завантажити бізнес-шаблони.");
            UpdateBuildFlowUi();
            return;
        }

        _blueprintCatalogData = root["data"]?.DeepClone();
        UpdateBuildFlowUi();
    }

    private void HandleBuildingApplicationSubmission(JsonNode data)
    {
        if (data == null)
        {
            UpdateBuildFlowUi();
            return;
        }

        string status = data["status"]?.ToString() ?? "";
        string applicationId = data["id"]?.ToString() ?? "";
        string summary = data["mayor_summary"]?.ToString() ?? "Заявку опрацьовано.";
        if (status == "approved" && !string.IsNullOrEmpty(applicationId))
        {
            _approvedApplicationId = applicationId;
            _buildFlowAction = "activate_application";
            if (BuildPlanLabel != null)
            {
                string name = data["proposed_name"]?.ToString() ?? "Будівлю";
                BuildPlanLabel.Text = $"Погоджено: {name} | можна створити будівлю";
            }

            UpdateBuildFlowButtons();
            return;
        }

        _approvedApplicationId = "";
        _buildFlowAction = "";
        if (BuildPlanLabel != null)
        {
            BuildPlanLabel.Text = $"Мерія: {summary}";
        }

        UpdateBuildFlowButtons();
    }

    private void OnExamSubmitRequested(string answersJson)
    {
        if (_session == null || !_session.HasAuthenticatedPlayer)
        {
            SetStatus("Немає активного гравця.");
            return;
        }

        if (!string.IsNullOrEmpty(_pendingExamKey))
        {
            SetStatus("Іспит уже надсилається...");
            return;
        }

        var answers = JsonSerializer.Deserialize<Dictionary<string, int>>(answersJson);
        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId, answers });
        _pendingExamKey = BuildActionKey("exam");
        _examPanel?.SetSubmitEnabled(false);
        UpdateActionButtons();
        _apiClient?.PostAuthorizedIdempotent("/api/education/exam/submit", _session.AuthToken, _pendingExamKey, payload);
    }

    private void OnServerMessageReceived(string jsonMessage)
    {
        try
        {
            var node = JsonNode.Parse(jsonMessage);
            if (node?["type"]?.ToString() == "system")
            {
                SetStatus(node["content"]?.ToString() ?? "WS підключено.", true);
            }
        }
        catch (Exception e)
        {
            GD.PrintErr($"CityDashboardController: WS parse error: {e.Message}");
        }
    }

    private void UpdatePlayerUI(JsonNode data)
    {
        var snapshot = DashboardPlayerSnapshot.FromJson(data);

        if (UsernameLabel != null)
        {
            UsernameLabel.Text = snapshot.Username;
        }

        _playerBalance = snapshot.Balance;
        if (BalanceLabel != null)
        {
            BalanceLabel.Text = $"{snapshot.Balance:N2} ₴";
        }

        if (EducationLabel != null)
        {
            _playerEducation = snapshot.EducationLevel;
            EducationLabel.Text = _playerEducation;
        }

        if (CurrentJobLabel != null)
        {
            CurrentJobLabel.Text = snapshot.Job;
            _hasJob = snapshot.HasJob;
        }

        if (CurrentHostelLabel != null)
        {
            CurrentHostelLabel.Text = snapshot.Hostel;
        }

        if (OwnedBusinessLabel != null)
        {
            _ownedBusinessId = snapshot.OwnedBusinessId;
            OwnedBusinessLabel.Text = snapshot.OwnedBusinessText;
        }

        if (SportsLabel != null)
        {
            SportsLabel.Text = snapshot.SportsText;
        }

        if (EnergyBar != null)
        {
            EnergyBar.Value = snapshot.Energy;
        }

        if (MoodBar != null)
        {
            MoodBar.Value = snapshot.Mood;
        }

        if (HungerBar != null)
        {
            HungerBar.Value = snapshot.Hunger;
        }

        UpdateAvailableActions(snapshot.Actions);
        _tutorialAgeGroup = snapshot.TutorialAgeGroup;
        _onboardingState = snapshot.Onboarding;
        _activeAvatar = DashboardActiveAvatarState.FromSnapshot(snapshot);
        UpdateActiveAvatarPresentation();
        UpdateOnboardingUi();
        UpdatePoliceRecoveryButton();
        if (!string.IsNullOrEmpty(snapshot.Id))
        {
            _session?.SetPlayer(snapshot.Id, snapshot.Username, snapshot.AuthToken);
            if (snapshot.Onboarding.Completed)
            {
                RefreshBuildingPortfolio();
                RefreshBuildCatalog();
                RefreshBusinessStatus();
            }
        }

        UpdateActionButtons();
    }

    private void RefreshBuildingPortfolio()
    {
        if (_session == null || !_session.HasAuthenticatedPlayer || _pendingBuildingPortfolio)
        {
            return;
        }

        _pendingBuildingPortfolio = true;
        UpdateBuildingPortfolioButtons();
        _apiClient?.GetAuthorized($"/api/player/{_session.PlayerId}/buildings", _session.AuthToken);
    }

    private void RefreshBusinessStatus()
    {
        if (_session == null || !_session.HasAuthenticatedPlayer
            || string.IsNullOrEmpty(_ownedBusinessId) || _pendingBusinessStatus)
        {
            return;
        }

        _pendingBusinessStatus = true;
        _apiClient?.GetAuthorized(
            $"/api/business/{_ownedBusinessId}/status?player_id={_session.PlayerId}",
            _session.AuthToken
        );
    }

    private void RefreshBuildCatalog(bool forceLandRefresh = false)
    {
        if (forceLandRefresh)
        {
            _landCatalogData = null;
        }

        if (_landCatalogData == null && !_pendingBuildLandCatalog)
        {
            _pendingBuildLandCatalog = true;
            _apiClient?.Get("/api/land/parcels");
        }

        if (_blueprintCatalogData == null && !_pendingBuildBlueprintCatalog)
        {
            _pendingBuildBlueprintCatalog = true;
            _apiClient?.Get("/api/business/blueprints");
        }

        UpdateBuildFlowUi();
    }

    private void ClearBuildFlow()
    {
        _pendingBuildLandCatalog = false;
        _pendingBuildBlueprintCatalog = false;
        _pendingLandBuyKey = "";
        _pendingBuildingApplicationKey = "";
        _pendingBuildingActivationKey = "";
        _starterLandId = "";
        _starterBlueprintId = "";
        _approvedApplicationId = "";
        _buildFlowAction = "";
        if (BuildPlanLabel != null)
        {
            BuildPlanLabel.Text = "Будівництво: каталог недоступний";
        }
        UpdateBuildFlowButtons();
    }

    private void UpdateBuildFlowUi()
    {
        if (_pendingBuildLandCatalog || _pendingBuildBlueprintCatalog)
        {
            if (BuildPlanLabel != null)
            {
                BuildPlanLabel.Text = "Будівництво: завантаження каталогу...";
            }

            _starterLandId = "";
            _starterBlueprintId = "";
            if (string.IsNullOrEmpty(_approvedApplicationId))
            {
                _buildFlowAction = "";
            }
            UpdateBuildFlowButtons();
            return;
        }

        var catalog = DashboardBuildCatalog.FromJson(_landCatalogData, _blueprintCatalogData);
        if (!string.IsNullOrEmpty(_approvedApplicationId))
        {
            _buildFlowAction = "activate_application";
            UpdateBuildFlowButtons();
            return;
        }

        string playerId = _session?.PlayerId ?? "";
        var applicationPlan = catalog.StarterApplicationPlanFor(playerId);
        if (applicationPlan != null)
        {
            _starterLandId = applicationPlan.Land.Id;
            _starterBlueprintId = applicationPlan.Blueprint.Id;
            _buildFlowAction = "submit_application";
            if (BuildPlanLabel != null)
            {
                BuildPlanLabel.Text = applicationPlan.ApplicationSummaryText;
            }

            UpdateBuildFlowButtons();
            return;
        }

        var plan = catalog.StarterPlanFor(_playerBalance);
        _starterLandId = plan?.Land.Id ?? "";
        _starterBlueprintId = plan?.Blueprint.Id ?? "";
        _buildFlowAction = string.IsNullOrEmpty(_starterLandId) ? "" : "buy_land";
        if (BuildPlanLabel != null)
        {
            BuildPlanLabel.Text = catalog.SummaryFor(_playerBalance);
        }

        UpdateBuildFlowButtons();
    }

    private void ClearBuildingPortfolio()
    {
        _pendingBuildingPortfolio = false;
        _portfolioOpenBuildingId = "";
        _portfolioRepairBuildingId = "";
        if (BuildingPortfolioLabel != null)
        {
            BuildingPortfolioLabel.Text = "Будівлі: немає";
        }
        _cityVisualOverlay?.SetBuildingPortfolio(new DashboardBuildingPortfolio());
        UpdateBuildingPortfolioButtons();
    }

    private void UpdateAvailableActions(JsonNode actions)
    {
        if (actions == null)
        {
            _canApplyJob = true;
            _canWork = _hasJob;
            _canSleep = true;
            _canEat = false;
            _canBuyBusiness = false;
            _canCollectDividend = false;
            _canJoinSports = true;
            _canTrainSports = false;
            _canTakeExam = _playerEducation == "High School";
            return;
        }

        _canApplyJob = actions["can_apply_job"]?.GetValue<bool>() ?? false;
        _canWork = actions["can_work"]?.GetValue<bool>() ?? false;
        _canSleep = actions["can_sleep"]?.GetValue<bool>() ?? false;
        _canEat = actions["can_eat"]?.GetValue<bool>() ?? false;
        _canBuyBusiness = actions["can_buy_business"]?.GetValue<bool>() ?? false;
        _canCollectDividend = actions["can_collect_dividend"]?.GetValue<bool>() ?? false;
        _canJoinSports = actions["can_join_sports"]?.GetValue<bool>() ?? false;
        _canTrainSports = actions["can_train_sports"]?.GetValue<bool>() ?? false;
        _canTakeExam = actions["can_take_exam"]?.GetValue<bool>() ?? false;
    }

    private void UpdateCityUI(JsonNode data)
    {
        if (CityNameLabel != null)
        {
            CityNameLabel.Text = data["name"]?.ToString() ?? "Місто";
        }

        if (TreasuryLabel != null)
        {
            double treasury = data["treasury_balance"]?.GetValue<double>() ?? 0.0;
            TreasuryLabel.Text = $"{treasury:N2} ₴";
        }

        if (InflationLabel != null)
        {
            double inflation = data["inflation_rate"]?.GetValue<double>() ?? 0.0;
            InflationLabel.Text = $"{inflation:F1}%";
        }
    }

    private void UpdateCityVisual(JsonNode data)
    {
        _cityVisualModel = DashboardCityVisualModel.FromCityStatus(data);
        _cityVisualOverlay?.SetCityModel(_cityVisualModel);
    }

    private void AddNewsToHistory(JsonNode data)
    {
        var news = data?["news"]?.AsArray();
        if (news == null)
        {
            return;
        }

        foreach (var item in news)
        {
            string title = item?["title"]?.ToString() ?? "";
            string message = item?["message"]?.ToString() ?? "";
            if (string.IsNullOrWhiteSpace(message))
            {
                continue;
            }

            string severity = item?["severity"]?.ToString() ?? "info";
            _statusPresenter?.AddEvent(FormatNewsEvent(title, message, severity));
        }
    }

    private static string FormatNewsEvent(string title, string message, string severity)
    {
        string prefix = severity switch
        {
            "warning" => "[!]",
            "watch" => "[~]",
            _ => "[i]",
        };
        string body = string.IsNullOrWhiteSpace(title) ? message : $"{title}: {message}";
        return $"{prefix} {body}";
    }

    private void UpdateNextActionHint(JsonNode effects)
    {
        if (NextActionLabel == null || effects == null)
        {
            return;
        }

        foreach (var effect in effects.AsArray())
        {
            if (effect?["key"]?.ToString() != "next_action")
            {
                continue;
            }

            string value = effect["value"]?.ToString() ?? "—";
            string delta = effect["delta"]?.ToString() ?? "";
            NextActionLabel.Text = string.IsNullOrEmpty(delta)
                ? $"→ {value}"
                : $"→ {value} ({delta})";
            return;
        }

        NextActionLabel.Text = "Наступний крок: —";
    }

    private void UpdateGoalUI(JsonNode effects)
    {
        if (GoalLabel == null || effects == null)
        {
            return;
        }

        foreach (var effect in effects.AsArray())
        {
            string key = effect?["key"]?.ToString() ?? "";
            if (key == "goal_manager_cert")
            {
                GoalLabel.Text = $"{effect["label"]}: {effect["value"]} ({effect["delta"]})";
                if (GoalProgressBar != null)
                {
                    string pctText = effect["value"]?.ToString()?.Replace("%", "") ?? "0";
                    if (double.TryParse(pctText, out double pct))
                    {
                        GoalProgressBar.Value = pct;
                    }
                }

                return;
            }

            if (key == "goal_better_job")
            {
                GoalLabel.Text = $"{effect["label"]}: {effect["value"]}";
                if (GoalProgressBar != null)
                {
                    GoalProgressBar.Value = 100;
                }

                return;
            }

            if (key == "goal_first_business" || key == "goal_business_owner")
            {
                GoalLabel.Text = $"{effect["label"]}: {effect["value"]} ({effect["delta"]})";
                if (GoalProgressBar != null)
                {
                    if (key == "goal_business_owner")
                    {
                        GoalProgressBar.Value = 100;
                    }
                    else
                    {
                        string pctText = effect["value"]?.ToString()?.Replace("%", "") ?? "0";
                        if (double.TryParse(pctText, out double pct))
                        {
                            GoalProgressBar.Value = pct;
                        }
                    }
                }

                return;
            }
        }
    }

    private void UpdateEffectsUI(JsonNode effects)
    {
        if (EffectsLabel == null || effects == null)
        {
            return;
        }

        var parts = new List<string>();
        foreach (var effect in effects.AsArray())
        {
            string key = effect?["key"]?.ToString() ?? "";
            if (key == "next_action" || key.StartsWith("stability_"))
            {
                continue;
            }

            string label = effect?["label"]?.ToString();
            string value = effect?["value"]?.ToString();
            if (!string.IsNullOrEmpty(label))
            {
                parts.Add($"{label}: {value}");
            }
        }

        EffectsLabel.Text = parts.Count > 0 ? string.Join(" | ", parts) : "";
    }

    private void UpdateActionButtons()
    {
        bool hasPlayer = _session != null && _session.HasAuthenticatedPlayer;
        _actionPresenter?.Update(
            new DashboardActionState(
                hasPlayer,
                _bootstrapPending,
                _pendingApply,
                _pendingBusinessMarket,
                _pendingSportsClubs,
                _pendingExamInfo,
                _pendingRefresh,
                !string.IsNullOrEmpty(_pendingWorkKey),
                !string.IsNullOrEmpty(_pendingSleepKey),
                !string.IsNullOrEmpty(_pendingEatKey),
                !string.IsNullOrEmpty(_pendingBusinessBuyKey),
                !string.IsNullOrEmpty(_pendingDividendKey),
                !string.IsNullOrEmpty(_pendingSportsJoinKey),
                !string.IsNullOrEmpty(_pendingSportsTrainKey),
                !string.IsNullOrEmpty(_pendingExamKey),
                _canApplyJob,
                _canWork,
                _canSleep,
                _canEat,
                _canBuyBusiness,
                _canCollectDividend,
                _canJoinSports,
                _canTrainSports,
                _canTakeExam,
                !string.IsNullOrEmpty(_ownedBusinessId)));
        UpdateBuildingPortfolioButtons();
        UpdateBuildFlowButtons();
    }

    private void UpdateBuildingPortfolioButtons()
    {
        bool hasPlayer = _session != null && _session.HasAuthenticatedPlayer;
        bool busy = _bootstrapPending || _pendingBuildingPortfolio || !string.IsNullOrEmpty(_pendingBuildingOpenKey) || !string.IsNullOrEmpty(_pendingBuildingRepairKey);

        if (_openBuildingButton != null)
        {
            _openBuildingButton.Text = !string.IsNullOrEmpty(_pendingBuildingOpenKey) ? "Відкриваємо..." : "Відкрити";
            _openBuildingButton.Disabled = !hasPlayer || busy || string.IsNullOrEmpty(_portfolioOpenBuildingId);
            _openBuildingButton.TooltipText = _openBuildingButton.Disabled
                ? (_pendingBuildingPortfolio ? "Оновлюємо список будівель." : "Немає будівлі, готової до відкриття.")
                : "Відкрити вибрану готову будівлю.";
        }

        if (_repairBuildingButton != null)
        {
            _repairBuildingButton.Text = !string.IsNullOrEmpty(_pendingBuildingRepairKey) ? "Ремонтуємо..." : "Ремонт";
            _repairBuildingButton.Disabled = !hasPlayer || busy || string.IsNullOrEmpty(_portfolioRepairBuildingId);
            _repairBuildingButton.TooltipText = _repairBuildingButton.Disabled
                ? (_pendingBuildingPortfolio ? "Оновлюємо список будівель." : "Немає будівлі, що потребує ремонту.")
                : "Повернути проблемну будівлю в роботу.";
        }
    }

    private void UpdateBuildFlowButtons()
    {
        bool hasPlayer = _session != null && _session.HasAuthenticatedPlayer;
        bool busy = _bootstrapPending
            || _pendingBuildLandCatalog
            || _pendingBuildBlueprintCatalog
            || !string.IsNullOrEmpty(_pendingLandBuyKey)
            || !string.IsNullOrEmpty(_pendingBuildingApplicationKey)
            || !string.IsNullOrEmpty(_pendingBuildingActivationKey);

        if (_buyStarterLandButton != null)
        {
            _buyStarterLandButton.Text = BuildFlowButtonText();
            _buyStarterLandButton.Disabled = !hasPlayer || busy || string.IsNullOrEmpty(_buildFlowAction);
            _buyStarterLandButton.TooltipText = _buyStarterLandButton.Disabled
                ? (busy ? "Каталог або дія ще обробляється." : "Немає доступного будівельного кроку.")
                : BuildFlowButtonTooltip();
        }
    }

    private string BuildFlowButtonText()
    {
        if (!string.IsNullOrEmpty(_pendingLandBuyKey))
        {
            return "Купуємо...";
        }

        if (!string.IsNullOrEmpty(_pendingBuildingApplicationKey))
        {
            return "Подаємо...";
        }

        if (!string.IsNullOrEmpty(_pendingBuildingActivationKey))
        {
            return "Створюємо...";
        }

        return _buildFlowAction switch
        {
            "submit_application" => "Подати заявку",
            "activate_application" => "Створити",
            _ => "Купити землю",
        };
    }

    private string BuildFlowButtonTooltip()
    {
        return _buildFlowAction switch
        {
            "submit_application" => "Подати заявку AI-меру на власну ділянку.",
            "activate_application" => "Створити погоджену фізичну будівлю на сервері.",
            _ => "Купити рекомендовану стартову ділянку у мерії.",
        };
    }

    private void SetStatus(string message, bool addToHistory = false)
    {
        _statusPresenter?.SetStatus(message, addToHistory);
    }

    private void SetErrorState(string message)
    {
        _statusPresenter?.SetError(message);
    }

    private void ClearErrorState()
    {
        _statusPresenter?.ClearError();
    }

    private static string BuildActionErrorMessage(string endpoint, string message)
    {
        if (message.Contains("Недостатньо енергії", StringComparison.Ordinal))
        {
            return $"{message} Натисніть «Спати», щоб відновитись.";
        }

        if (endpoint == "/api/jobs/vacancies")
        {
            return string.IsNullOrWhiteSpace(message) ? "Немає доступних вакансій." : message;
        }

        return string.IsNullOrWhiteSpace(message) ? "Дія не виконана. Спробуйте ще раз." : message;
    }

    private static string BuildActionKey(string action)
    {
        return $"{action}-{Guid.NewGuid():N}";
    }

    private void ClearPendingAction(string endpoint)
    {
        if (endpoint == "/api/player/onboarding/choose")
        {
            _pendingOnboarding = false;
            UpdateOnboardingUi();
        }
        else if (endpoint == "/api/player/onboarding/police-recovery")
        {
            _pendingPoliceRecoveryKey = "";
            UpdatePoliceRecoveryButton();
        }
        else if (endpoint.StartsWith("/api/jobs/work/"))
        {
            _pendingWorkKey = "";
        }
        else if (endpoint.StartsWith("/api/hostels/sleep/"))
        {
            _pendingSleepKey = "";
        }
        else if (endpoint.StartsWith("/api/needs/eat/"))
        {
            _pendingEatKey = "";
        }
        else if (endpoint == "/api/businesses/buy")
        {
            _pendingBusinessBuyKey = "";
        }
        else if (endpoint == "/api/businesses/dividend")
        {
            _pendingDividendKey = "";
        }
        else if (endpoint == "/api/businesses/market")
        {
            _pendingBusinessMarket = false;
        }
        else if (endpoint == "/api/sports/join")
        {
            _pendingSportsJoinKey = "";
        }
        else if (endpoint == "/api/sports/train")
        {
            _pendingSportsTrainKey = "";
        }
        else if (endpoint == "/api/sports/clubs")
        {
            _pendingSportsClubs = false;
        }
        else if (endpoint.StartsWith("/api/player/") && endpoint != "/api/player/register" && !IsBuildingPortfolioEndpoint(endpoint) && !endpoint.Contains("/onboarding"))
        {
            _pendingRefresh = false;
        }
        else if (endpoint == "/api/education/exam/submit")
        {
            _pendingExamKey = "";
        }
        else if (endpoint == "/api/education/exam/info")
        {
            _pendingExamInfo = false;
        }
        else if (endpoint == "/api/city/status")
        {
            _pendingRefresh = false;
        }
        else if (endpoint.StartsWith("/api/buildings/") && endpoint.EndsWith("/open"))
        {
            _pendingBuildingOpenKey = "";
        }
        else if (endpoint.StartsWith("/api/buildings/") && endpoint.EndsWith("/repair"))
        {
            _pendingBuildingRepairKey = "";
        }
        else if (IsBuildingPortfolioEndpoint(endpoint))
        {
            _pendingBuildingPortfolio = false;
        }
        else if (endpoint == "/api/land/parcels")
        {
            _pendingBuildLandCatalog = false;
        }
        else if (endpoint == "/api/business/blueprints")
        {
            _pendingBuildBlueprintCatalog = false;
        }
        else if (endpoint == "/api/land/buy")
        {
            _pendingLandBuyKey = "";
        }
        else if (endpoint == "/api/building/applications")
        {
            _pendingBuildingApplicationKey = "";
        }
        else if (IsBuildingActivationEndpoint(endpoint))
        {
            _pendingBuildingActivationKey = "";
        }
        else if (endpoint.StartsWith("/api/jobs/apply"))
        {
            _pendingApply = false;
        }

        UpdateActionButtons();
    }

    private void UpdateOnboardingUi()
    {
        if (_onboardingOverlay == null)
        {
            return;
        }

        _onboardingOverlay.Visible = !_onboardingState.Completed;
        if (_onboardingState.Completed)
        {
            _arrivalStoryInitialized = false;
            _arrivalStoryBeat = 0;
            return;
        }

        bool showingStory = _onboardingState.Stage == "arrival_choice"
            && _arrivalStoryInitialized
            && _arrivalStoryBeat < DashboardArrivalStory.Count;
        if (_onboardingState.Stage == "arrival_choice" && !_arrivalStoryInitialized)
        {
            _arrivalStoryInitialized = true;
            _arrivalStoryBeat = 0;
            showingStory = true;
        }

        var storyBeat = showingStory ? DashboardArrivalStory.Get(_arrivalStoryBeat, _tutorialAgeGroup) : null;
        UpdateOnboardingBackdrop(storyBeat?.Visual ?? DashboardArrivalVisual.BaggageTheft);
        UpdateOnboardingPortrait(
            storyBeat?.Portrait ?? DashboardArrivalPortrait.None,
            storyBeat?.PortraitSide ?? DashboardPortraitSide.Right);
        if (_onboardingTitleLabel != null)
        {
            _onboardingTitleLabel.Text = storyBeat == null
                ? TranslateOrFallback(_onboardingState.TitleKey, _onboardingState.Title)
                : Tr(storyBeat.TitleKey);
        }
        if (_onboardingNarrativeLabel != null)
        {
            _onboardingNarrativeLabel.Text = storyBeat == null
                ? TranslateOrFallback(_onboardingState.NarrativeKey, _onboardingState.Narrative)
                : Tr(storyBeat.NarrativeKey);
        }
        if (_onboardingPoliceStatusLabel != null)
        {
            string policeStatusText = TranslateOrFallback(_onboardingState.PoliceStatusKey, "");
            _onboardingPoliceStatusLabel.Text = policeStatusText;
            _onboardingPoliceStatusLabel.Visible = !string.IsNullOrWhiteSpace(policeStatusText);
        }
        if (_onboardingPoliceButton != null)
        {
            _onboardingPoliceButton.Visible = !showingStory && _onboardingState.CanReportToPolice;
            _onboardingPoliceButton.Disabled = _pendingOnboarding;
            _onboardingPoliceButton.Text = Tr(
                _pendingOnboarding ? "ONBOARDING_POLICE_PENDING_BUTTON" : "ONBOARDING_POLICE_BUTTON");
        }
        if (_onboardingHousingButton != null)
        {
            _onboardingHousingButton.Visible = !showingStory && _onboardingState.CanFindHousing;
            _onboardingHousingButton.Disabled = _pendingOnboarding;
            _onboardingHousingButton.Text = Tr(
                _pendingOnboarding ? "ONBOARDING_HOUSING_PENDING_BUTTON" : "ONBOARDING_HOUSING_BUTTON");
        }
        if (_onboardingContinueButton != null)
        {
            _onboardingContinueButton.Visible = showingStory;
            _onboardingContinueButton.Disabled = _pendingOnboarding;
            _onboardingContinueButton.Text = _arrivalStoryBeat + 1 < DashboardArrivalStory.Count
                ? Tr("ARRIVAL_STORY_NEXT")
                : Tr("ARRIVAL_STORY_ARRIVE");
        }
    }

    private void UpdateOnboardingBackdrop(DashboardArrivalVisual visual)
    {
        if (_onboardingBackdrop == null)
        {
            return;
        }

        string assetPath = DashboardVisualStylePacks.ResolveArrivalAsset(_session?.VisualStyleCode, visual);
        if (assetPath == _onboardingBackdropPath)
        {
            return;
        }

        var texture = ResourceLoader.Load<Texture2D>(assetPath);
        if (texture == null)
        {
            GD.PushError($"Не вдалося завантажити arrival asset: {assetPath}");
            return;
        }

        _onboardingBackdrop.Texture = texture;
        _onboardingBackdropPath = assetPath;
    }

    private void UpdateOnboardingPortrait(DashboardArrivalPortrait portrait, DashboardPortraitSide side)
    {
        if (_onboardingPortrait == null)
        {
            return;
        }

        if (portrait == DashboardArrivalPortrait.None)
        {
            _onboardingPortrait.Visible = false;
            return;
        }

        const float width = 260.0f;
        const float height = 325.0f;
        const float margin = 32.0f;
        const float top = 230.0f;
        float viewportWidth = GetViewportRect().Size.X;
        float left = side == DashboardPortraitSide.Left
            ? margin
            : Math.Max(margin, viewportWidth - margin - width);
        _onboardingPortrait.Position = new Vector2(left, top);
        _onboardingPortrait.Size = new Vector2(width, height);
        _onboardingPortrait.Visible = true;

        string assetPath = DashboardVisualStylePacks.ResolveArrivalPortrait(_session?.VisualStyleCode, portrait);
        if (assetPath == _onboardingPortraitPath)
        {
            return;
        }

        var texture = ResourceLoader.Load<Texture2D>(assetPath);
        if (texture == null)
        {
            _onboardingPortrait.Visible = false;
            GD.PushError($"Не вдалося завантажити arrival portrait: {assetPath}");
            return;
        }

        _onboardingPortrait.Texture = texture;
        _onboardingPortraitPath = assetPath;
    }

    private void SubmitOnboardingChoice(string choice)
    {
        if (_pendingOnboarding || _session == null || !_session.HasAuthenticatedPlayer)
        {
            return;
        }

        _pendingOnboarding = true;
        UpdateOnboardingUi();
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId, choice });
        _apiClient?.PostAuthorizedIdempotent(
            "/api/player/onboarding/choose",
            _session.AuthToken,
            BuildActionKey($"onboarding-{choice}"),
            payload);
    }

    public void OnOnboardingPoliceButtonPressed()
    {
        SubmitOnboardingChoice(DashboardOnboardingState.ReportToPoliceChoice);
    }

    public void OnOnboardingHousingButtonPressed()
    {
        SubmitOnboardingChoice(DashboardOnboardingState.FindHousingChoice);
    }

    public void OnOnboardingContinueButtonPressed()
    {
        if (
            _pendingOnboarding
            || _onboardingState.Stage != "arrival_choice"
            || _arrivalStoryBeat >= DashboardArrivalStory.Count)
        {
            return;
        }

        _arrivalStoryBeat += 1;
        UpdateOnboardingUi();
    }

    private void UpdatePoliceRecoveryButton()
    {
        if (_policeRecoveryButton == null)
        {
            return;
        }

        bool pending = !string.IsNullOrEmpty(_pendingPoliceRecoveryKey);
        _policeRecoveryButton.Visible = _onboardingState.PoliceRecoveryClaimable || pending;
        _policeRecoveryButton.Disabled = pending;
        _policeRecoveryButton.Text = pending
            ? Tr("POLICE_RECOVERY_PENDING")
            : Tr("POLICE_RECOVERY_CLAIM").Replace(
                "{amount}",
                $"{_onboardingState.PoliceRecoveryAmount:N0}");
        _policeRecoveryButton.TooltipText = pending
            ? Tr("POLICE_RECOVERY_PENDING_TOOLTIP")
            : Tr("POLICE_RECOVERY_CLAIM_TOOLTIP");
    }

    private string TranslateOrFallback(string key, string fallback)
    {
        if (string.IsNullOrWhiteSpace(key))
        {
            return fallback;
        }

        string translated = Tr(key);
        return translated == key ? fallback : translated;
    }

    public void OnPoliceRecoveryButtonPressed()
    {
        if (
            !_onboardingState.PoliceRecoveryClaimable
            || !string.IsNullOrEmpty(_pendingPoliceRecoveryKey)
            || _session == null
            || !_session.HasAuthenticatedPlayer)
        {
            return;
        }

        _pendingPoliceRecoveryKey = BuildActionKey("police-recovery");
        UpdatePoliceRecoveryButton();
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId });
        _apiClient?.PostAuthorizedIdempotent(
            "/api/player/onboarding/police-recovery",
            _session.AuthToken,
            _pendingPoliceRecoveryKey,
            payload);
    }

    private static bool IsBuildingPortfolioEndpoint(string endpoint)
    {
        return endpoint.StartsWith("/api/player/") && endpoint.EndsWith("/buildings");
    }

    private static bool IsBuildingActivationEndpoint(string endpoint)
    {
        return endpoint.StartsWith("/api/building/applications/") && endpoint.EndsWith("/activate");
    }

    private static bool IsBusinessStatusEndpoint(string endpoint)
    {
        return endpoint.StartsWith("/api/business/") && endpoint.Contains("/status");
    }

    private void HandleBusinessStatus(JsonNode root)
    {
        _pendingBusinessStatus = false;
        if (root["success"]?.GetValue<bool>() != true || OwnedBusinessLabel == null)
        {
            return;
        }

        var data = root["data"];
        if (data == null) return;

        string name = data["name"]?.ToString() ?? "";
        string mode = data["management_mode"]?.ToString() ?? "";
        double daily = data["daily_revenue"]?.GetValue<double>() ?? 0.0;
        string modeLabel = mode switch
        {
            "ai" => "AI",
            "manual" => "Ручний",
            "shadow" => "Тіньовий",
            _ => mode,
        };
        string revenueText = daily > 0 ? $" | {daily:N0} ₴/день" : "";
        OwnedBusinessLabel.Text = $"Бізнес: {name} [{modeLabel}{revenueText}]";
    }

    public void OnApplyJobButtonPressed()
    {
        if (_session == null || !_session.HasAuthenticatedPlayer)
        {
            SetStatus("Спочатку потрібна реєстрація.");
            return;
        }

        if (_pendingApply)
        {
            SetStatus("Влаштування вже обробляється...");
            return;
        }

        _pendingApply = true;
        _applyFirstVacancy = true;
        UpdateActionButtons();
        ClearErrorState();
        SetStatus("Шукаємо вакансію...");
        _apiClient?.Get("/api/jobs/vacancies");
    }

    public void OnWorkButtonPressed()
    {
        if (_session == null || !_session.HasAuthenticatedPlayer)
        {
            SetStatus("Немає активного гравця.");
            return;
        }

        if (!_hasJob)
        {
            SetStatus("Спочатку влаштуйтесь на роботу.");
            return;
        }

        if (!string.IsNullOrEmpty(_pendingWorkKey))
        {
            SetStatus("Зміна вже обробляється...");
            return;
        }

        _pendingWorkKey = BuildActionKey("work");
        UpdateActionButtons();
        ClearErrorState();
        SetStatus("Відпрацьовуємо зміну...");
        _apiClient?.PostAuthorizedIdempotent($"/api/jobs/work/{_session.PlayerId}", _session.AuthToken, _pendingWorkKey);
    }

    public void OnSleepButtonPressed()
    {
        if (_session == null || !_session.HasAuthenticatedPlayer)
        {
            SetStatus("Немає активного гравця.");
            return;
        }

        if (!string.IsNullOrEmpty(_pendingSleepKey))
        {
            SetStatus("Сон уже обробляється...");
            return;
        }

        _pendingSleepKey = BuildActionKey("sleep");
        UpdateActionButtons();
        ClearErrorState();
        SetStatus("Спимо та сплачуємо оренду...");
        _apiClient?.PostAuthorizedIdempotent($"/api/hostels/sleep/{_session.PlayerId}", _session.AuthToken, _pendingSleepKey);
    }

    public void OnEatButtonPressed()
    {
        if (_session == null || !_session.HasAuthenticatedPlayer)
        {
            SetStatus("Немає активного гравця.");
            return;
        }

        if (!string.IsNullOrEmpty(_pendingEatKey))
        {
            SetStatus("Їжа вже обробляється...");
            return;
        }

        _pendingEatKey = BuildActionKey("eat");
        UpdateActionButtons();
        ClearErrorState();
        SetStatus("Купуємо обід...");
        _apiClient?.PostAuthorizedIdempotent($"/api/needs/eat/{_session.PlayerId}", _session.AuthToken, _pendingEatKey);
    }

    public void OnBuyBusinessButtonPressed()
    {
        if (_session == null || !_session.HasAuthenticatedPlayer)
        {
            SetStatus("Немає активного гравця.");
            return;
        }

        if (_pendingBusinessMarket || !string.IsNullOrEmpty(_pendingBusinessBuyKey))
        {
            SetStatus("Купівля бізнесу вже обробляється...");
            return;
        }

        _pendingBusinessMarket = true;
        _buyFirstBusiness = true;
        UpdateActionButtons();
        ClearErrorState();
        SetStatus("Шукаємо доступний бізнес...");
        _apiClient?.Get("/api/businesses/market");
    }

    public void OnCollectDividendButtonPressed()
    {
        if (_session == null || !_session.HasAuthenticatedPlayer)
        {
            SetStatus("Немає активного гравця.");
            return;
        }

        if (string.IsNullOrEmpty(_ownedBusinessId))
        {
            SetStatus("Спочатку купіть бізнес.");
            return;
        }

        if (!string.IsNullOrEmpty(_pendingDividendKey))
        {
            SetStatus("Дивіденд уже збирається...");
            return;
        }

        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId, business_id = _ownedBusinessId });
        _pendingDividendKey = BuildActionKey("dividend");
        UpdateActionButtons();
        ClearErrorState();
        SetStatus("Збираємо дивіденд...");
        _apiClient?.PostAuthorizedIdempotent("/api/businesses/dividend", _session.AuthToken, _pendingDividendKey, payload);
    }

    public void OnJoinSportsButtonPressed()
    {
        if (_session == null || !_session.HasAuthenticatedPlayer)
        {
            SetStatus("Немає активного гравця.");
            return;
        }

        if (_pendingSportsClubs || !string.IsNullOrEmpty(_pendingSportsJoinKey))
        {
            SetStatus("Спортивний контракт уже обробляється...");
            return;
        }

        _pendingSportsClubs = true;
        _joinFirstSportsClub = true;
        UpdateActionButtons();
        ClearErrorState();
        SetStatus("Шукаємо спортивний клуб...");
        _apiClient?.Get("/api/sports/clubs");
    }

    public void OnTrainSportsButtonPressed()
    {
        if (_session == null || !_session.HasAuthenticatedPlayer)
        {
            SetStatus("Немає активного гравця.");
            return;
        }

        if (!string.IsNullOrEmpty(_pendingSportsTrainKey))
        {
            SetStatus("Тренування вже обробляється...");
            return;
        }

        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId, stat_type = "strength" });
        _pendingSportsTrainKey = BuildActionKey("sports-train");
        UpdateActionButtons();
        ClearErrorState();
        SetStatus("Тренуємо силу...");
        _apiClient?.PostAuthorizedIdempotent("/api/sports/train", _session.AuthToken, _pendingSportsTrainKey, payload);
    }

    public void OnExamButtonPressed()
    {
        if (_session == null || !_session.HasAuthenticatedPlayer)
        {
            SetStatus("Немає активного гравця.");
            return;
        }

        if (_playerEducation != "High School")
        {
            SetStatus("Іспит потрібен лише для переходу з High School на College.");
            return;
        }

        SetStatus("Завантажуємо іспит...");
        _pendingExamInfo = true;
        ClearErrorState();
        UpdateActionButtons();
        _apiClient?.Get("/api/education/exam/info");
    }

    public void OnRefreshButtonPressed()
    {
        SetStatus("Оновлюємо статус...");
        _pendingRefresh = true;
        ClearErrorState();
        UpdateActionButtons();
        _apiClient?.Get("/api/city/status");
        if (_session != null && _session.HasAuthenticatedPlayer)
        {
            RefreshBuildingPortfolio();
            RefreshBuildCatalog(forceLandRefresh: true);
        }
    }

    public void OnVisualFocusButtonPressed()
    {
        if (_cityVisualOverlay == null)
        {
            return;
        }

        string nextText = _cityVisualOverlay.ToggleFocusMode();
        if (_visualFocusButton != null)
        {
            _visualFocusButton.Text = nextText;
        }
        UpdateActiveAvatarPresentation();
    }

    private void UpdateActiveAvatarPresentation()
    {
        bool hasIdentity = _activeAvatar.HasPlayerIdentity;
        if (_playerAvatarProfile != null)
        {
            _playerAvatarProfile.Visible = hasIdentity;
        }
        SetViewportActive(_playerAvatarViewport, hasIdentity);
        _playerAvatarPreview?.SetPreviewActive(hasIdentity);
        if (_playerAvatarIdentityLabel != null)
        {
            _playerAvatarIdentityLabel.Text =
                $"{Tr("PLAYER_AVATAR_FACE")} {_activeAvatar.FaceNumber:00} | " +
                $"{Tr("PLAYER_AVATAR_FASHION")} {_activeAvatar.Profile.FashionScore}";
        }
        if (_streetAvatarNameLabel != null)
        {
            _streetAvatarNameLabel.Text = _activeAvatar.Username;
        }
        if (hasIdentity)
        {
            _playerAvatarPreview?.SetProfile(_activeAvatar.Profile);
            _streetAvatarPreview?.SetProfile(_activeAvatar.Profile);
            _streetAvatarPreview?.SetActivity(_activeAvatar.Activity.Activity);
        }
        if (_streetAvatarContainer != null)
        {
            bool showStreetAvatar = _activeAvatar.ShowsFullAvatar(
                _cityVisualOverlay?.IsStreetFocus ?? false
            );
            _streetAvatarContainer.Visible = showStreetAvatar;
            SetViewportActive(_streetAvatarViewport, showStreetAvatar);
            _streetAvatarPreview?.SetPreviewActive(showStreetAvatar);
        }
    }

    private static void SetViewportActive(SubViewport viewport, bool active)
    {
        if (viewport != null)
        {
            viewport.RenderTargetUpdateMode = active
                ? SubViewport.UpdateMode.Always
                : SubViewport.UpdateMode.Disabled;
        }
    }

    public void OnBuyStarterLandButtonPressed()
    {
        if (_session == null || !_session.HasAuthenticatedPlayer)
        {
            SetStatus("Немає активного гравця.");
            return;
        }

        if (string.IsNullOrEmpty(_buildFlowAction))
        {
            SetStatus("Немає доступного будівельного кроку.");
            RefreshBuildCatalog();
            return;
        }

        if (!string.IsNullOrEmpty(_pendingLandBuyKey)
            || !string.IsNullOrEmpty(_pendingBuildingApplicationKey)
            || !string.IsNullOrEmpty(_pendingBuildingActivationKey))
        {
            SetStatus("Будівельна дія вже обробляється...");
            return;
        }

        if (_buildFlowAction == "submit_application")
        {
            SubmitStarterBuildingApplication();
            return;
        }

        if (_buildFlowAction == "activate_application")
        {
            ActivateApprovedBuildingApplication();
            return;
        }

        if (string.IsNullOrEmpty(_starterLandId))
        {
            SetStatus("Немає доступної стартової ділянки.");
            RefreshBuildCatalog();
            return;
        }

        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId, land_parcel_id = _starterLandId });
        _pendingLandBuyKey = BuildActionKey("land-buy");
        UpdateBuildFlowButtons();
        ClearErrorState();
        SetStatus("Купуємо стартову ділянку...");
        _apiClient?.PostAuthorizedIdempotent("/api/land/buy", _session.AuthToken, _pendingLandBuyKey, payload);
    }

    private void SubmitStarterBuildingApplication()
    {
        if (_session == null || string.IsNullOrEmpty(_starterLandId) || string.IsNullOrEmpty(_starterBlueprintId))
        {
            SetStatus("Не вистачає даних для заявки.");
            RefreshBuildCatalog();
            return;
        }

        string payload = ApiClient.BuildJson(new
        {
            player_id = _session.PlayerId,
            land_parcel_id = _starterLandId,
            business_blueprint_id = _starterBlueprintId,
        });
        _pendingBuildingApplicationKey = BuildActionKey("building-application");
        UpdateBuildFlowButtons();
        ClearErrorState();
        SetStatus("Подаємо заявку в мерію...");
        _apiClient?.PostAuthorizedIdempotent("/api/building/applications", _session.AuthToken, _pendingBuildingApplicationKey, payload);
    }

    private void ActivateApprovedBuildingApplication()
    {
        if (_session == null || string.IsNullOrEmpty(_approvedApplicationId))
        {
            SetStatus("Немає погодженої заявки для створення.");
            UpdateBuildFlowUi();
            return;
        }

        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId });
        _pendingBuildingActivationKey = BuildActionKey("building-activate");
        UpdateBuildFlowButtons();
        ClearErrorState();
        SetStatus("Створюємо будівлю...");
        _apiClient?.PostAuthorizedIdempotent($"/api/building/applications/{_approvedApplicationId}/activate", _session.AuthToken, _pendingBuildingActivationKey, payload);
    }

    public void OnOpenBuildingButtonPressed()
    {
        if (_session == null || !_session.HasAuthenticatedPlayer)
        {
            SetStatus("Немає активного гравця.");
            return;
        }

        if (string.IsNullOrEmpty(_portfolioOpenBuildingId))
        {
            SetStatus("Немає будівлі, готової до відкриття.");
            return;
        }

        if (!string.IsNullOrEmpty(_pendingBuildingOpenKey))
        {
            SetStatus("Відкриття будівлі вже обробляється...");
            return;
        }

        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId });
        _pendingBuildingOpenKey = BuildActionKey("building-open");
        UpdateBuildingPortfolioButtons();
        ClearErrorState();
        SetStatus("Відкриваємо будівлю...");
        _apiClient?.PostAuthorizedIdempotent($"/api/buildings/{_portfolioOpenBuildingId}/open", _session.AuthToken, _pendingBuildingOpenKey, payload);
    }

    public void OnRepairBuildingButtonPressed()
    {
        if (_session == null || !_session.HasAuthenticatedPlayer)
        {
            SetStatus("Немає активного гравця.");
            return;
        }

        if (string.IsNullOrEmpty(_portfolioRepairBuildingId))
        {
            SetStatus("Немає будівлі, що потребує ремонту.");
            return;
        }

        if (!string.IsNullOrEmpty(_pendingBuildingRepairKey))
        {
            SetStatus("Ремонт будівлі вже обробляється...");
            return;
        }

        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId });
        _pendingBuildingRepairKey = BuildActionKey("building-repair");
        UpdateBuildingPortfolioButtons();
        ClearErrorState();
        SetStatus("Ремонтуємо будівлю...");
        _apiClient?.PostAuthorizedIdempotent($"/api/buildings/{_portfolioRepairBuildingId}/repair", _session.AuthToken, _pendingBuildingRepairKey, payload);
    }
}
