using Godot;
using System;
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
    private EducationPanelController _educationPanel;
    private BankPanelController _bankPanel;
    private PolicePanelController _policePanel;
    private CourtPanelController _courtPanel;
    private PoliticalPanelController _politicalPanel;
    private PressPanelController _pressPanel;
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
    private Button _visualFocusButton;
    private Button _educationButton;
    private Button _bankButton;
    private Button _policeButton;
    private Button _courtButton;
    private Button _politicalButton;
    private Button _pressButton;
    private Control _leftRail;
    private Control _centerScroll;
    private Control _actionRail;
    private Control _cityVisualPanel;
    private Label _cityCaptionLabel;
    private Control _buildingPortfolioPanel;
    private Control _buildFlowPanel;
    private Control _goalPanel;
    private Control _eventPanel;
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
    private Control _playerAvatarProfile;
    private CharacterAvatarPreview _playerAvatarPreview;
    private SubViewport _playerAvatarViewport;
    private Label _playerAvatarIdentityLabel;
    private Control _streetAvatarContainer;
    private CharacterAvatarPreview _streetAvatarPreview;
    private SubViewport _streetAvatarViewport;
    private Label _streetAvatarNameLabel;
    private DashboardStatusPresenter _statusPresenter;
    private DashboardActionPresenter _actionPresenter;
    private DashboardOnboardingState _onboardingState = new();
    private DashboardTutorialAgeGroup _tutorialAgeGroup = DashboardTutorialAgeGroup.Adult;
    private int _arrivalStoryBeat;
    private bool _arrivalStoryInitialized;
    private bool _onboardingCompleting;
    private bool _applyFirstVacancy;
    private bool _buyFirstBusiness;
    private bool _joinFirstSportsClub;
    private bool _pendingApply;
    private bool _pendingBusinessMarket;
    private bool _pendingSportsClubs;
    private bool _pendingExamInfo;
    private bool _pendingRefresh;
    private bool _pendingOnboarding;
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
    private string _pendingPoliceRecoveryKey = "";
    private string _onboardingBackdropPath = "";
    private string _onboardingPortraitPath = "";
    private DashboardActiveAvatarState _activeAvatar = DashboardActiveAvatarState.Empty;
    private double _playerBalance;
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
        if (_educationButton != null)
        {
            _educationButton.Pressed += OnEducationButtonPressed;
        }
        if (_bankButton != null)
        {
            _bankButton.Pressed += OnBankButtonPressed;
        }
        if (_policeButton != null)
        {
            _policeButton.Pressed += OnPoliceButtonPressed;
        }
        if (_courtButton != null)
        {
            _courtButton.Pressed += OnCourtButtonPressed;
        }
        if (_politicalButton != null)
        {
            _politicalButton.Pressed += OnPoliticalButtonPressed;
        }
        if (_pressButton != null)
        {
            _pressButton.Pressed += OnPressButtonPressed;
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
        _educationPanel = GetNodeOrNull<EducationPanelController>("EducationOverlay");
        _bankPanel = GetNodeOrNull<BankPanelController>("BankOverlay");
        _policePanel = GetNodeOrNull<PolicePanelController>("PoliceOverlay");
        _courtPanel = GetNodeOrNull<CourtPanelController>("CourtOverlay");
        _politicalPanel = GetNodeOrNull<PoliticalPanelController>("PoliticalOverlay");
        _pressPanel = GetNodeOrNull<PressPanelController>("PressOverlay");
        _cityVisualOverlay?.SetStyleCode(_session?.VisualStyleCode);
        ConfigureOnboardingPortraitMaterial();
        ConfigureCharacterCreationVisual();
        UpdateCharacterCreationUi();
        UpdateActiveAvatarPresentation();
        ApplyCityFocusLayout();
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

        if (_educationPanel != null)
        {
            _educationPanel.EnrollRequested += OnEducationEnrollRequested;
            _educationPanel.Closed += () => SetStatus("Освітню панель закрито.");
        }

        if (_bankPanel != null)
        {
            _bankPanel.DepositRequested += OnBankDepositRequested;
            _bankPanel.WithdrawRequested += OnBankWithdrawRequested;
            _bankPanel.LoanRequested += OnBankLoanRequested;
            _bankPanel.RepayRequested += OnBankRepayRequested;
            _bankPanel.BidRequested += OnBankBidRequested;
            _bankPanel.Closed += () => SetStatus("Банківську панель закрито.");
        }

        if (_policePanel != null)
        {
            _policePanel.HireRequested += OnPoliceHireRequested;
            _policePanel.PromoteRequested += OnPolicePromoteRequested;
            _policePanel.PatrolRequested += OnPolicePatrolRequested;
            _policePanel.Closed += () => SetStatus("Поліцейську панель закрито.");
        }

        if (_courtPanel != null)
        {
            _courtPanel.WorkRequested += OnCourtWorkRequested;
            _courtPanel.PokerRequested += OnCourtPokerRequested;
            _courtPanel.SocializeRequested += OnCourtSocializeRequested;
            _courtPanel.Closed += () => SetStatus("Судову панель закрито.");
        }

        if (_politicalPanel != null)
        {
            _politicalPanel.HireOfficeRequested += OnHireOfficeRequested;
            _politicalPanel.RegisterCandidateRequested += OnRegisterCandidateRequested;
            _politicalPanel.StartElectionRequested += OnStartElectionRequested;
            _politicalPanel.Closed += () => SetStatus("Політичну панель закрито.");
        }

        if (_pressPanel != null)
        {
            _pressPanel.InvestigateRequested += OnInvestigateRequested;
            _pressPanel.PublishRequested += OnPublishRequested;
            _pressPanel.BlackmailRequested += OnBlackmailRequested;
            _pressPanel.BlackmailRespondRequested += OnBlackmailRespondRequested;
            _pressPanel.Closed += () => SetStatus("Прес-панель закрито.");
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
        _leftRail ??= GetNodeOrNull<Control>("RootMargin/LandscapeGrid/LeftRail");
        _centerScroll ??= GetNodeOrNull<Control>("RootMargin/LandscapeGrid/CenterScroll");
        _actionRail ??= GetNodeOrNull<Control>("RootMargin/LandscapeGrid/ActionRail");
        _cityVisualPanel ??= GetNodeOrNull<Control>("RootMargin/LandscapeGrid/CenterScroll/CenterStage/CityVisualPanel");
        _cityCaptionLabel ??= GetNodeOrNull<Label>(
            "RootMargin/LandscapeGrid/CenterScroll/CenterStage/CityVisualPanel/CityVisual/CityCaption");
        _buildingPortfolioPanel ??= GetNodeOrNull<Control>(
            "RootMargin/LandscapeGrid/CenterScroll/CenterStage/BuildingPortfolioPanel");
        _buildFlowPanel ??= GetNodeOrNull<Control>(
            "RootMargin/LandscapeGrid/CenterScroll/CenterStage/BuildFlowPanel");
        _goalPanel ??= GetNodeOrNull<Control>("RootMargin/LandscapeGrid/CenterScroll/CenterStage/GoalPanel");
        _eventPanel ??= GetNodeOrNull<Control>("RootMargin/LandscapeGrid/CenterScroll/CenterStage/EventPanel");
        _openBuildingButton ??= GetNodeOrNull<Button>("%OpenBuildingButton");
        _repairBuildingButton ??= GetNodeOrNull<Button>("%RepairBuildingButton");
        _buyStarterLandButton ??= GetNodeOrNull<Button>("%BuyStarterLandButton");
        _visualFocusButton ??= GetNodeOrNull<Button>("%VisualFocusButton");
        _educationButton ??= GetNodeOrNull<Button>("%EducationButton");
        _bankButton ??= GetNodeOrNull<Button>("%BankButton");
        _policeButton ??= GetNodeOrNull<Button>("%PoliceButton");
        _courtButton ??= GetNodeOrNull<Button>("%CourtButton");
        _politicalButton ??= GetNodeOrNull<Button>("%PoliticalButton");
        _pressButton ??= GetNodeOrNull<Button>("%PressButton");
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

        if (_session != null && _session.HasAuthenticatedPlayer)
        {
            _networkManager?.ConnectToCity(cityId, _session.AuthToken);
            _apiClient?.GetAuthorized($"/api/player/{_session.PlayerId}", _session.AuthToken);
            return;
        }

        ShowCharacterCreation();
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

}
