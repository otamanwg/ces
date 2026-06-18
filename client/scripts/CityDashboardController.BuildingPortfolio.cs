using Godot;
using System.Text.Json.Nodes;

public partial class CityDashboardController
{
	private Button _openBuildingButton;
	private Button _repairBuildingButton;
	private bool _pendingBuildingPortfolio;
	private string _pendingBuildingOpenKey = "";
	private string _pendingBuildingRepairKey = "";
	private string _portfolioOpenBuildingId = "";
	private string _portfolioRepairBuildingId = "";

	private bool TryHandleBuildingPortfolioResponse(string endpoint, JsonNode root)
	{
		if (!IsBuildingPortfolioEndpoint(endpoint))
		{
			return false;
		}

		HandleBuildingPortfolio(root);
		return true;
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

	private static bool IsBuildingPortfolioEndpoint(string endpoint)
	{
		return endpoint.StartsWith("/api/player/") && endpoint.EndsWith("/buildings");
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
