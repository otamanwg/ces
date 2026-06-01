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
	[Export] public Label StatusLabel;
	[Export] public Label EffectsLabel;
	[Export] public Label ErrorStateLabel;
	[Export] public Label EventHistoryLabel;
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
	private Button _applyJobButton;
	private Button _workButton;
	private Button _sleepButton;
	private Button _eatButton;
	private Button _examButton;
	private Button _refreshButton;
	private DashboardStatusPresenter _statusPresenter;
	private bool _applyFirstVacancy;
	private bool _pendingApply;
	private bool _pendingExamInfo;
	private bool _pendingRefresh;
	private bool _bootstrapPending = true;
	private bool _hasJob;
	private bool _canApplyJob;
	private bool _canWork;
	private bool _canSleep;
	private bool _canEat;
	private bool _canTakeExam;
	private string _playerEducation = "High School";
	private string _pendingWorkKey = "";
	private string _pendingSleepKey = "";
	private string _pendingEatKey = "";
	private string _pendingExamKey = "";
	private const string ApplyJobText = "Знайти роботу";
	private const string WorkText = "Працювати";
	private const string SleepText = "Спати";
	private const string EatText = "Поїсти";
	private const string ExamText = "Іспит";
	private const string RefreshText = "Оновити";

	public override void _Ready()
	{
		BindUiNodes();
		_statusPresenter = new DashboardStatusPresenter(StatusLabel, ErrorStateLabel, EventHistoryLabel);

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
		StatusLabel ??= GetNodeOrNull<Label>("%StatusLabel");
		EffectsLabel ??= GetNodeOrNull<Label>("%EffectsLabel");
		ErrorStateLabel ??= GetNodeOrNull<Label>("%ErrorStateLabel");
		EventHistoryLabel ??= GetNodeOrNull<Label>("%EventHistoryLabel");
		GoalLabel ??= GetNodeOrNull<Label>("%GoalLabel");
		NextActionLabel ??= GetNodeOrNull<Label>("%NextActionLabel");
		GoalProgressBar ??= GetNodeOrNull<ProgressBar>("%GoalProgressBar");
		EnergyBar ??= GetNodeOrNull<TextureProgressBar>("%EnergyBar");
		MoodBar ??= GetNodeOrNull<TextureProgressBar>("%MoodBar");
		HungerBar ??= GetNodeOrNull<TextureProgressBar>("%HungerBar");
		CityNameLabel ??= GetNodeOrNull<Label>("%CityNameLabel");
		TreasuryLabel ??= GetNodeOrNull<Label>("%TreasuryLabel");
		InflationLabel ??= GetNodeOrNull<Label>("%InflationLabel");
		_applyJobButton ??= GetNodeOrNull<Button>("%ApplyJobButton");
		_workButton ??= GetNodeOrNull<Button>("%WorkButton");
		_sleepButton ??= GetNodeOrNull<Button>("%SleepButton");
		_eatButton ??= GetNodeOrNull<Button>("%EatButton");
		_examButton ??= GetNodeOrNull<Button>("%ExamButton");
		_refreshButton ??= GetNodeOrNull<Button>("%RefreshButton");
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

		if (endpoint == "/api/jobs/vacancies" && _applyFirstVacancy)
		{
			HandleVacanciesForApply(root);
			return;
		}

		if (endpoint == "/api/education/exam/info")
		{
			HandleExamInfo(root);
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

		if (data != null && data["username"] != null)
		{
			UpdatePlayerUI(data);
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
		_pendingApply = false;
		_pendingExamInfo = false;
		_pendingRefresh = false;
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
		_canTakeExam = false;
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
		if (UsernameLabel != null)
		{
			UsernameLabel.Text = data["username"]?.ToString() ?? "Гість";
		}

		if (BalanceLabel != null)
		{
			double balance = data["balance"]?.GetValue<double>() ?? 0.0;
			BalanceLabel.Text = $"{balance:N2} ₴";
		}

		if (EducationLabel != null)
		{
			_playerEducation = data["education_level"]?.ToString() ?? "High School";
			EducationLabel.Text = _playerEducation;
		}

		if (CurrentJobLabel != null)
		{
			string job = data["job"]?.ToString() ?? "Безробітний";
			CurrentJobLabel.Text = job;
			_hasJob = job != "Безробітний";
		}

		if (CurrentHostelLabel != null)
		{
			CurrentHostelLabel.Text = data["hostel"]?.ToString() ?? "Вулиця";
		}

		if (EnergyBar != null)
		{
			EnergyBar.Value = data["energy"]?.GetValue<int>() ?? 0;
		}

		if (MoodBar != null)
		{
			MoodBar.Value = data["mood"]?.GetValue<int>() ?? 0;
		}

		if (HungerBar != null)
		{
			HungerBar.Value = data["hunger"]?.GetValue<int>() ?? 0;
		}

		UpdateAvailableActions(data["actions"]);

		string playerId = data["id"]?.ToString() ?? "";
		string username = data["username"]?.ToString() ?? "";
		string authToken = data["auth_token"]?.ToString() ?? "";
		if (!string.IsNullOrEmpty(playerId))
		{
			_session?.SetPlayer(playerId, username, authToken);
		}

		UpdateActionButtons();
	}

	private void UpdateAvailableActions(JsonNode actions)
	{
		if (actions == null)
		{
			_canApplyJob = true;
			_canWork = _hasJob;
			_canSleep = true;
			_canEat = false;
			_canTakeExam = _playerEducation == "High School";
			return;
		}

		_canApplyJob = actions["can_apply_job"]?.GetValue<bool>() ?? false;
		_canWork = actions["can_work"]?.GetValue<bool>() ?? false;
		_canSleep = actions["can_sleep"]?.GetValue<bool>() ?? false;
		_canEat = actions["can_eat"]?.GetValue<bool>() ?? false;
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
		bool actionBusy = _bootstrapPending
			|| _pendingApply
			|| _pendingExamInfo
			|| _pendingRefresh
			|| !string.IsNullOrEmpty(_pendingWorkKey)
			|| !string.IsNullOrEmpty(_pendingSleepKey)
			|| !string.IsNullOrEmpty(_pendingEatKey)
			|| !string.IsNullOrEmpty(_pendingExamKey);
		SetButtonState(_applyJobButton, !hasPlayer || !_canApplyJob || actionBusy, _pendingApply ? "Шукаємо..." : ApplyJobText);
		SetButtonState(_workButton, !hasPlayer || !_canWork || actionBusy, !string.IsNullOrEmpty(_pendingWorkKey) ? "Працюємо..." : WorkText);
		SetButtonState(_sleepButton, !hasPlayer || !_canSleep || actionBusy, !string.IsNullOrEmpty(_pendingSleepKey) ? "Спимо..." : SleepText);
		SetButtonState(_eatButton, !hasPlayer || !_canEat || actionBusy, !string.IsNullOrEmpty(_pendingEatKey) ? "Їмо..." : EatText);
		string examButtonText = !string.IsNullOrEmpty(_pendingExamKey)
			? "Надсилаємо..."
			: _pendingExamInfo ? "Завантаження..." : ExamText;
		SetButtonState(_examButton, !hasPlayer || !_canTakeExam || actionBusy, examButtonText);
		SetButtonState(_refreshButton, _bootstrapPending || _pendingRefresh, _pendingRefresh ? "Оновлюємо..." : RefreshText);
	}

	private static void SetButtonState(Button button, bool disabled, string text)
	{
		if (button != null)
		{
			button.Disabled = disabled;
			button.Text = text;
		}
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
		else if (endpoint.StartsWith("/api/jobs/apply"))
		{
			_pendingApply = false;
		}

		UpdateActionButtons();
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
		}
	}
}
