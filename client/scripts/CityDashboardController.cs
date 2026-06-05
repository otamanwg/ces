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
	private DashboardStatusPresenter _statusPresenter;
	private DashboardActionPresenter _actionPresenter;
	private bool _applyFirstVacancy;
	private bool _buyFirstBusiness;
	private bool _joinFirstSportsClub;
	private bool _pendingApply;
	private bool _pendingBusinessMarket;
	private bool _pendingSportsClubs;
	private bool _pendingExamInfo;
	private bool _pendingRefresh;
	private bool _pendingBuildingPortfolio;
	private bool _pendingBuildLandCatalog;
	private bool _pendingBuildBlueprintCatalog;
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
	private string _portfolioOpenBuildingId = "";
	private string _portfolioRepairBuildingId = "";
	private string _starterLandId = "";
	private string _starterBlueprintId = "";
	private string _approvedApplicationId = "";
	private string _buildFlowAction = "";
	private double _playerBalance;
	private JsonNode _landCatalogData;
	private JsonNode _blueprintCatalogData;
	private DashboardCityVisualModel _cityVisualModel = DashboardCityVisualModel.Empty;

	public override void _Ready()
	{
		BindUiNodes();
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

		_apiClient = GetNodeOrNull<ApiClient>("/root/ApiClient");
		_session = GetNodeOrNull<GameSession>("/root/GameSession");
		_networkManager = GetNodeOrNull<NetworkManager>("/root/NetworkManager");
		_examPanel = GetNodeOrNull<ExamPanelController>("ExamOverlay");

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

		bool apiSuccess = root["success"]?.GetValue<bool>() ?? false;
		string message = root["message"]?.ToString() ?? "";
		var data = root["data"];

		if (!apiSuccess)
		{
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

		ClearErrorState();
		SetStatus(message, true);
		UpdateEffectsUI(root["effects"]);
		AddNewsToHistory(data);

		if (data != null && data["username"] != null)
		{
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
		_pendingBuildLandCatalog = false;
		_pendingBuildBlueprintCatalog = false;
		_pendingLandBuyKey = "";
		_pendingBuildingApplicationKey = "";
		_pendingBuildingActivationKey = "";
		ClearPendingAction(endpoint);
		_examPanel?.SetSubmitEnabled(true);

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
		ClearBuildingPortfolio();
		ClearBuildFlow();
		SetErrorState($"{message} Створюємо нового гравця...");
		UpdateActionButtons();
		RegisterNewPlayer();
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

		RegisterNewPlayer();
	}

	private void RegisterNewPlayer()
	{
		string username = $"Гравець_{DateTimeOffset.UtcNow.ToUnixTimeSeconds()}";
		string payload = ApiClient.BuildJson(new { username });
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
		if (!string.IsNullOrEmpty(snapshot.Id))
		{
			_session?.SetPlayer(snapshot.Id, snapshot.Username, snapshot.AuthToken);
			RefreshBuildingPortfolio();
			RefreshBuildCatalog();
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
		if (endpoint.StartsWith("/api/jobs/work/"))
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

	private static bool IsBuildingPortfolioEndpoint(string endpoint)
	{
		return endpoint.StartsWith("/api/player/") && endpoint.EndsWith("/buildings");
	}

	private static bool IsBuildingActivationEndpoint(string endpoint)
	{
		return endpoint.StartsWith("/api/building/applications/") && endpoint.EndsWith("/activate");
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
			_apiClient?.GetAuthorized($"/api/player/{_session.PlayerId}", _session.AuthToken);
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
