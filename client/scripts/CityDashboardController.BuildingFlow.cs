using Godot;
using System.Text.Json.Nodes;

public partial class CityDashboardController
{
	private Button _buyStarterLandButton;
	private bool _pendingBuildLandCatalog;
	private bool _pendingBuildBlueprintCatalog;
	private string _pendingLandBuyKey = "";
	private string _pendingBuildingApplicationKey = "";
	private string _pendingBuildingActivationKey = "";
	private string _starterLandId = "";
	private string _starterBlueprintId = "";
	private string _approvedApplicationId = "";
	private string _buildFlowAction = "";
	private JsonNode _landCatalogData;
	private JsonNode _blueprintCatalogData;

	private bool TryHandleBuildingFlowResponse(string endpoint, JsonNode root)
	{
		if (endpoint == "/api/land/parcels")
		{
			HandleLandParcels(root);
			return true;
		}
		if (endpoint == "/api/business/blueprints")
		{
			HandleBusinessBlueprints(root);
			return true;
		}
		return false;
	}

	private void HandleBuildingFlowSuccess(string endpoint, JsonNode data)
	{
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

	private static bool IsBuildingActivationEndpoint(string endpoint)
	{
		return endpoint.StartsWith("/api/building/applications/") && endpoint.EndsWith("/activate");
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
}
