using Godot;
using System;

public partial class CityDashboardController : Control
{
    // Lifecycle Methods
    public override void _Ready()
    {
        GD.Print("CityDashboardController: Initializing...");

        // Initialize core components
        InitializeCoreComponents();

        // Initialize UI references
        InitializeUIReferences();

        // Connect event handlers
        ConnectEventHandlers();

        // Start bootstrap process
        StartBootstrapProcess();

        GD.Print("CityDashboardController: Initialization complete");
    }

    public override void _Process(double delta)
    {
        // Handle bootstrap process
        if (_bootstrapPending)
        {
            ProcessBootstrap();
            return;
        }

        // Handle pending operations
        ProcessPendingOperations();

        // Update UI based on state
        UpdateUIState();
    }

    public override void _ExitTree()
    {
        // Cleanup resources
        CleanupResources();
    }

    // Initialization Methods
    private void InitializeCoreComponents()
    {
        // Get existing components
        _apiClient = GetNode<ApiClient>("/root/ApiClient");
        _session = GetNode<GameSession>("/root/GameSession");
        _networkManager = GetNode<NetworkManager>("/root/NetworkManager");

        // Find optional components
        _examPanel = GetNode<ExamPanelController>("ExamPanel");
        _cityVisualOverlay = GetNode<CityVisualOverlay>("CityVisualOverlay");

        // Initialize presenters
        _statusPresenter = new DashboardStatusPresenter(this);
        _actionPresenter = new DashboardActionPresenter(this);

        GD.Print("CityDashboardController: Core components initialized");
    }

    private void ConnectEventHandlers()
    {
        // Connect action buttons
        ConnectActionButtons();

        // Connect onboarding buttons
        ConnectOnboardingButtons();

        // Connect character creation buttons
        ConnectCharacterCreationButtons();

        // Connect network events
        if (_networkManager != null)
        {
            _networkManager.ConnectionStateChanged += OnConnectionStateChanged;
            _networkManager.MessageReceived += OnNetworkMessageReceived;
        }

        // Connect session events
        if (_session != null)
        {
            _session.PlayerRegistered += OnPlayerRegistered;
            _session.PlayerDataUpdated += OnPlayerDataUpdated;
        }

        GD.Print("CityDashboardController: Event handlers connected");
    }

    private void ConnectOnboardingButtons()
    {
        _onboardingPoliceButton.Pressed += OnOnboardingPoliceButtonPressed;
        _onboardingHousingButton.Pressed += OnOnboardingHousingButtonPressed;
        _onboardingContinueButton.Pressed += OnOnboardingContinueButtonPressed;
        _policeRecoveryButton.Pressed += OnPoliceRecoveryButtonPressed;
    }

    private void ConnectCharacterCreationButtons()
    {
        _characterTeenButton.Pressed += () => OnCharacterAgeButtonPressed(DashboardTutorialAgeGroup.Teen);
        _characterAdultButton.Pressed += () => OnCharacterAgeButtonPressed(DashboardTutorialAgeGroup.Adult);
        _characterMatureButton.Pressed += () => OnCharacterAgeButtonPressed(DashboardTutorialAgeGroup.Mature);
        _characterCreateButton.Pressed += OnCharacterCreateButtonPressed;
        _characterUkrainianButton.Pressed += OnCharacterLocaleButtonPressed("uk");
        _characterEnglishButton.Pressed += OnCharacterLocaleButtonPressed("en");

        // Avatar customization buttons
        _characterBodyPreviousButton.Pressed += () => OnAvatarCustomizationButtonPressed("body", -1);
        _characterBodyNextButton.Pressed += () => OnAvatarCustomizationButtonPressed("body", 1);
        _characterFacePreviousButton.Pressed += () => OnAvatarCustomizationButtonPressed("face", -1);
        _characterFaceNextButton.Pressed += () => OnAvatarCustomizationButtonPressed("face", 1);
        _characterSkinPreviousButton.Pressed += () => OnAvatarCustomizationButtonPressed("skin", -1);
        _characterSkinNextButton.Pressed += () => OnAvatarCustomizationButtonPressed("skin", 1);
        _characterHairPreviousButton.Pressed += () => OnAvatarCustomizationButtonPressed("hair", -1);
        _characterHairNextButton.Pressed += () => OnAvatarCustomizationButtonPressed("hair", 1);
        _characterHairColorPreviousButton.Pressed += () => OnAvatarCustomizationButtonPressed("hair_color", -1);
        _characterHairColorNextButton.Pressed += () => OnAvatarCustomizationButtonPressed("hair_color", 1);
    }

    // Bootstrap Process
    private void StartBootstrapProcess()
    {
        GD.Print("CityDashboardController: Starting bootstrap process");
        _bootstrapPending = true;
        SetOverlayVisible(true);
    }

    private void ProcessBootstrap()
    {
        if (!_bootstrapPending) return;

        // Check if network is ready
        if (_networkManager == null || !_networkManager.IsConnected)
        {
            SetLabelText(StatusLabel, "🔄 Connecting to server...");
            return;
        }

        // Check if session is ready
        if (_session == null)
        {
            SetLabelText(StatusLabel, "🔄 Initializing session...");
            return;
        }

        // Check if player is registered
        if (!_session.IsRegistered)
        {
            SetLabelText(StatusLabel, "🔄 Please register or login...");
            SetOverlayVisible(true);
            return;
        }

        // Bootstrap complete
        _bootstrapPending = false;
        SetOverlayVisible(false);
        SetLabelText(StatusLabel, "✅ Ready to play!");

        // Load initial data
        _ = RefreshPlayerData();

        GD.Print("CityDashboardController: Bootstrap complete");
    }

    // Process Management
    private void ProcessPendingOperations()
    {
        // This would handle any pending async operations
        // For now, it's a placeholder for future implementation
    }

    private void UpdateUIState()
    {
        // Update UI based on current state
        if (IsBootstrapComplete())
        {
            // Show main game UI
            SetControlVisible(_onboardingOverlay, false);
            SetControlVisible(_characterCreationOverlay, false);
        }
        else if (_bootstrapPending)
        {
            // Show appropriate overlay
            UpdateBootstrapUI();
        }
    }

    private void UpdateBootstrapUI()
    {
        if (_session == null || !_session.IsRegistered)
        {
            // Show character creation
            SetControlVisible(_characterCreationOverlay, true);
            SetControlVisible(_onboardingOverlay, false);
        }
        else if (_pendingOnboarding)
        {
            // Show onboarding
            SetControlVisible(_onboardingOverlay, true);
            SetControlVisible(_characterCreationOverlay, false);
        }
    }

    // Event Handlers
    private void OnConnectionStateChanged(bool connected)
    {
        if (connected)
        {
            SetLabelText(StatusLabel, "🌐 Connected to server");
            AddEventToHistory("🌐 Connected to server");
        }
        else
        {
            SetLabelText(StatusLabel, "❌ Disconnected from server");
            AddEventToHistory("❌ Disconnected from server");
        }
    }

    private void OnNetworkMessageReceived(string message)
    {
        try
        {
            // Handle real-time messages
            AddEventToHistory($"📨 {message}");
        }
        catch (Exception ex)
        {
            GD.PrintErr($"Network message error: {ex.Message}");
        }
    }

    private void OnPlayerRegistered()
    {
        SetLabelText(StatusLabel, "✅ Player registered!");
        AddEventToHistory("✅ Player registered");
        _ = RefreshPlayerData();
    }

    private void OnPlayerDataUpdated()
    {
        _ = RefreshPlayerData();
    }

    // Cleanup
    private void CleanupResources()
    {
        // Disconnect event handlers
        if (_networkManager != null)
        {
            _networkManager.ConnectionStateChanged -= OnConnectionStateChanged;
            _networkManager.MessageReceived -= OnNetworkMessageReceived;
        }

        if (_session != null)
        {
            _session.PlayerRegistered -= OnPlayerRegistered;
            _session.PlayerDataUpdated -= OnPlayerDataUpdated;
        }

        // Cleanup presenters
        _statusPresenter?.Dispose();
        _actionPresenter?.Dispose();

        GD.Print("CityDashboardController: Cleanup complete");
    }
}
