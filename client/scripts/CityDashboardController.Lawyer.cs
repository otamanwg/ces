using Godot;
using System.Text.Json.Nodes;

public partial class CityDashboardController
{
    private JsonNode _lawyerEngagementsData;
    private bool _pendingLawyerCatalog;
    private string _pendingEngageKey;
    private string _pendingAppealKey;
    private string _pendingLicenseKey;

    public void OnLawyerButtonPressed()
    {
        if (_lawyerPanel == null || _session == null || !_session.HasAuthenticatedPlayer)
        {
            return;
        }

        _pendingLawyerCatalog = true;
        ClearErrorState();
        _apiClient?.GetAuthorized(
            $"/api/player/{_session.PlayerId}/lawyer-engagements",
            _session.AuthToken);
    }

    public void OnEngageRequested(double amount, string dealType)
    {
        if (_session == null || !_session.HasAuthenticatedPlayer || amount < 0)
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingEngageKey))
        {
            return;
        }

        _pendingEngageKey = BuildActionKey($"engage-{amount}-{dealType}");
        ClearErrorState();
        // Placeholder: player hires themselves as lawyer for now; real flow needs lawyer search
        string payload = ApiClient.BuildJson(new { lawyer_id = _session.PlayerId, client_id = _session.PlayerId, deal_type = dealType, amount, game_day = 0 });
        _apiClient?.PostAuthorizedIdempotent("/api/lawyer/engage", _session.AuthToken, _pendingEngageKey, payload);
    }

    public void OnAppealRequested()
    {
        if (_session == null || !_session.HasAuthenticatedPlayer)
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingAppealKey))
        {
            return;
        }

        _pendingAppealKey = BuildActionKey("lawyer-appeal");
        ClearErrorState();
        // Placeholder: needs case_id selection; real flow would integrate with Court panel
        SetStatus("Виберіть справу для апеляції у судовій панелі.", false);
        _pendingAppealKey = "";
    }

    public void OnLicenseRequested()
    {
        if (_session == null || !_session.HasAuthenticatedPlayer)
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingLicenseKey))
        {
            return;
        }

        _pendingLicenseKey = BuildActionKey("lawyer-license");
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId });
        _apiClient?.PostAuthorizedIdempotent("/api/education/license/lawyer", _session.AuthToken, _pendingLicenseKey, payload);
    }

    private void HandleLawyerEngagementsResponse(JsonNode data)
    {
        _lawyerEngagementsData = data;
        _pendingLawyerCatalog = false;
        var model = DashboardLawyerModel.FromJson(_lawyerEngagementsData);
        _lawyerPanel?.LoadModel(model);
    }

    private void HandleLawyerActionResponse(JsonNode data)
    {
        _pendingEngageKey = "";
        _pendingAppealKey = "";
        _pendingLicenseKey = "";

        bool success = data?["success"]?.GetValue<bool>() ?? false;
        string message = data?["message"]?.ToString() ?? "Операцію завершено.";
        SetStatus(message, success);

        if (success && _session != null && _session.HasAuthenticatedPlayer)
        {
            RefreshLawyerData();
        }
    }

    private void RefreshLawyerData()
    {
        _lawyerEngagementsData = null;
        _apiClient?.GetAuthorized(
            $"/api/player/{_session.PlayerId}/lawyer-engagements",
            _session.AuthToken);
    }

    private bool TryHandleLawyerResponse(string endpoint, JsonNode root)
    {
        if (endpoint.StartsWith("/api/player/") && endpoint.EndsWith("/lawyer-engagements"))
        {
            HandleLawyerEngagementsResponse(root["data"]);
            return true;
        }

        if (endpoint == "/api/lawyer/engage" || endpoint == "/api/lawyer/appeal" || endpoint == "/api/education/license/lawyer")
        {
            HandleLawyerActionResponse(root);
            return true;
        }

        return false;
    }
}
