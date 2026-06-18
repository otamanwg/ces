using Godot;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Nodes;

public partial class CityDashboardController
{
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

	private bool TryHandlePlayerActionResponse(string endpoint, JsonNode root)
	{
		switch (DashboardPlayerActionEndpoints.Classify(endpoint))
		{
			case DashboardPlayerActionEndpoint.Vacancies when _applyFirstVacancy:
				HandleVacanciesForApply(root);
				return true;
			case DashboardPlayerActionEndpoint.BusinessMarket when _buyFirstBusiness:
				HandleBusinessMarketForBuy(root);
				return true;
			case DashboardPlayerActionEndpoint.SportsClubs when _joinFirstSportsClub:
				HandleSportsClubsForJoin(root);
				return true;
			case DashboardPlayerActionEndpoint.ExamInfo:
				HandleExamInfo(root);
				return true;
			default:
				return false;
		}
	}

	private bool ClearPlayerActionPending(string endpoint)
	{
		switch (DashboardPlayerActionEndpoints.Classify(endpoint))
		{
			case DashboardPlayerActionEndpoint.JobApply:
				_pendingApply = false;
				return true;
			case DashboardPlayerActionEndpoint.Work:
				_pendingWorkKey = "";
				return true;
			case DashboardPlayerActionEndpoint.Sleep:
				_pendingSleepKey = "";
				return true;
			case DashboardPlayerActionEndpoint.Eat:
				_pendingEatKey = "";
				return true;
			case DashboardPlayerActionEndpoint.BusinessMarket:
				_pendingBusinessMarket = false;
				return true;
			case DashboardPlayerActionEndpoint.BusinessBuy:
				_pendingBusinessBuyKey = "";
				return true;
			case DashboardPlayerActionEndpoint.BusinessDividend:
				_pendingDividendKey = "";
				return true;
			case DashboardPlayerActionEndpoint.SportsClubs:
				_pendingSportsClubs = false;
				return true;
			case DashboardPlayerActionEndpoint.SportsJoin:
				_pendingSportsJoinKey = "";
				return true;
			case DashboardPlayerActionEndpoint.SportsTrain:
				_pendingSportsTrainKey = "";
				return true;
			case DashboardPlayerActionEndpoint.ExamInfo:
				_pendingExamInfo = false;
				return true;
			case DashboardPlayerActionEndpoint.ExamSubmit:
				_pendingExamKey = "";
				return true;
			default:
				return false;
		}
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
}
