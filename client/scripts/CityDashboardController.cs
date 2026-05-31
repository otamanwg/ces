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
	[Export] public Label GoalLabel;
	[Export] public ProgressBar GoalProgressBar;
	[Export] public TextureProgressBar EnergyBar;
	[Export] public TextureProgressBar MoodBar;
	[Export] public Label CityNameLabel;
	[Export] public Label TreasuryLabel;
	[Export] public Label InflationLabel;

	private ApiClient _apiClient;
	private GameSession _session;
	private NetworkManager _networkManager;
	private ExamPanelController _examPanel;
	private bool _applyFirstVacancy;
	private string _playerEducation = "High School";
	private string _pendingWorkKey = "";
	private string _pendingSleepKey = "";
	private string _pendingExamKey = "";

	public override void _Ready()
	{
		BindUiNodes();

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

		SetStatus("Підключення до сервера...");
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
		GoalLabel ??= GetNodeOrNull<Label>("%GoalLabel");
		GoalProgressBar ??= GetNodeOrNull<ProgressBar>("%GoalProgressBar");
		EnergyBar ??= GetNodeOrNull<TextureProgressBar>("%EnergyBar");
		MoodBar ??= GetNodeOrNull<TextureProgressBar>("%MoodBar");
		CityNameLabel ??= GetNodeOrNull<Label>("%CityNameLabel");
		TreasuryLabel ??= GetNodeOrNull<Label>("%TreasuryLabel");
		InflationLabel ??= GetNodeOrNull<Label>("%InflationLabel");
	}

	private void OnApiRequestFinished(string endpoint, bool success, string jsonBody)
	{
		ClearPendingAction(endpoint);

		if (!success)
		{
			SetStatus("Помилка API. Запусти: .\\scripts\\dev.ps1");
			_applyFirstVacancy = false;
			return;
		}

		var root = JsonNode.Parse(jsonBody);
		if (root == null)
		{
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
			SetStatus(message);
			return;
		}

		SetStatus(message);
		UpdateEffectsUI(root["effects"]);

		if (data != null && data["username"] != null)
		{
			UpdatePlayerUI(data);
		}

		if (data != null && data["name"] != null && data["treasury_balance"] != null)
		{
			UpdateCityUI(data);
		}

		if (endpoint == "/api/education/exam/submit")
		{
			_examPanel?.HidePanel();
			if (data?["passed"]?.GetValue<bool>() == true)
			{
				SetStatus($"Іспит здано! {data["score"]}. Тепер доступні кращі вакансії.");
			}
		}

		UpdateGoalUI(root["effects"]);
	}

	private void HandleCityStatus(JsonNode root)
	{
		if (root["success"]?.GetValue<bool>() != true)
		{
			SetStatus("Місто недоступне.");
			return;
		}

		var data = root["data"];
		if (data == null)
		{
			return;
		}

		UpdateCityUI(data);
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
			SetStatus("Не вдалось отримати вакансії.");
			return;
		}

		var vacancies = root["data"]?["vacancies"]?.AsArray();
		if (vacancies == null || vacancies.Count == 0)
		{
			SetStatus("Немає вільних вакансій.");
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
			return;
		}

		string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId, job_id = jobId });
		_apiClient?.PostAuthorized("/api/jobs/apply", _session.AuthToken, payload);
	}

	private void HandleExamInfo(JsonNode root)
	{
		if (root["success"]?.GetValue<bool>() != true)
		{
			SetStatus("Не вдалось завантажити іспит.");
			return;
		}

		_examPanel?.LoadExam(root["data"]);
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
		_apiClient?.PostAuthorizedIdempotent("/api/education/exam/submit", _session.AuthToken, _pendingExamKey, payload);
	}

	private void OnServerMessageReceived(string jsonMessage)
	{
		try
		{
			var node = JsonNode.Parse(jsonMessage);
			if (node?["type"]?.ToString() == "system")
			{
				SetStatus(node["content"]?.ToString() ?? "WS підключено.");
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
			CurrentJobLabel.Text = data["job"]?.ToString() ?? "Безробітний";
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

		string playerId = data["id"]?.ToString() ?? "";
		string username = data["username"]?.ToString() ?? "";
		string authToken = data["auth_token"]?.ToString() ?? "";
		if (!string.IsNullOrEmpty(playerId))
		{
			_session?.SetPlayer(playerId, username, authToken);
		}
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
			string label = effect?["label"]?.ToString();
			string value = effect?["value"]?.ToString();
			if (!string.IsNullOrEmpty(label))
			{
				parts.Add($"{label}: {value}");
			}
		}

		EffectsLabel.Text = parts.Count > 0 ? string.Join(" | ", parts) : "";
	}

	private void SetStatus(string message)
	{
		if (StatusLabel != null)
		{
			StatusLabel.Text = message;
		}
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
		else if (endpoint == "/api/education/exam/submit")
		{
			_pendingExamKey = "";
		}
	}

	public void OnApplyJobButtonPressed()
	{
		if (_session == null || !_session.HasAuthenticatedPlayer)
		{
			SetStatus("Спочатку потрібна реєстрація.");
			return;
		}

		_applyFirstVacancy = true;
		_apiClient?.Get("/api/jobs/vacancies");
	}

	public void OnWorkButtonPressed()
	{
		if (_session == null || !_session.HasAuthenticatedPlayer)
		{
			SetStatus("Немає активного гравця.");
			return;
		}

		if (!string.IsNullOrEmpty(_pendingWorkKey))
		{
			SetStatus("Зміна вже обробляється...");
			return;
		}

		_pendingWorkKey = BuildActionKey("work");
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
		_apiClient?.PostAuthorizedIdempotent($"/api/hostels/sleep/{_session.PlayerId}", _session.AuthToken, _pendingSleepKey);
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

		_apiClient?.Get("/api/education/exam/info");
	}

	public void OnRefreshButtonPressed()
	{
		_apiClient?.Get("/api/city/status");
		if (_session != null && _session.HasAuthenticatedPlayer)
		{
			_apiClient?.GetAuthorized($"/api/player/{_session.PlayerId}", _session.AuthToken);
		}
	}
}
