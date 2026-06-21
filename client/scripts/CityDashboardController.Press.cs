using Godot;
using System.Text.Json.Nodes;

public partial class CityDashboardController
{
    private JsonNode _pressInvestigationsData;
    private JsonNode _pressBlackmailsData;
    private bool _pendingPressCatalog;
    private string _pendingInvestigateKey;
    private string _pendingPublishKey;
    private string _pendingBlackmailKey;
    private string _pendingBlackmailRespondKey;

    public void OnPressButtonPressed()
    {
        if (_pressPanel == null || _session == null || !_session.HasAuthenticatedPlayer)
        {
            return;
        }

        _pendingPressCatalog = true;
        ClearErrorState();
        _apiClient?.GetAuthorized(
            $"/api/player/{_session.PlayerId}/press-investigations",
            _session.AuthToken);
        _apiClient?.GetAuthorized(
            $"/api/player/{_session.PlayerId}/press-blackmails",
            _session.AuthToken);
    }

    public void OnInvestigateRequested()
    {
        if (_session == null || !_session.HasAuthenticatedPlayer)
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingInvestigateKey))
        {
            return;
        }

        // For now, investigate self as a placeholder; real flow would need target selection
        _pendingInvestigateKey = BuildActionKey("press-investigate");
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { journalist_id = _session.PlayerId, target_id = _session.PlayerId, incident_type = "corruption" });
        _apiClient?.PostAuthorizedIdempotent("/api/press/investigate", _session.AuthToken, _pendingInvestigateKey, payload);
    }

    public void OnPublishRequested(string investigationId)
    {
        if (_session == null || !_session.HasAuthenticatedPlayer || string.IsNullOrEmpty(investigationId))
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingPublishKey))
        {
            return;
        }

        _pendingPublishKey = BuildActionKey($"press-publish-{investigationId}");
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { investigation_id = investigationId, target_id = _session.PlayerId, article_title = "Скандал у місті!" });
        _apiClient?.PostAuthorizedIdempotent("/api/press/publish", _session.AuthToken, _pendingPublishKey, payload);
    }

    public void OnBlackmailRequested(string investigationId)
    {
        if (_session == null || !_session.HasAuthenticatedPlayer || string.IsNullOrEmpty(investigationId))
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingBlackmailKey))
        {
            return;
        }

        _pendingBlackmailKey = BuildActionKey($"press-blackmail-{investigationId}");
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { investigation_id = investigationId, journalist_id = _session.PlayerId, target_id = _session.PlayerId, amount = 1000.0 });
        _apiClient?.PostAuthorizedIdempotent("/api/press/blackmail", _session.AuthToken, _pendingBlackmailKey, payload);
    }

    public void OnBlackmailRespondRequested(string blackmailId, string action)
    {
        if (_session == null || !_session.HasAuthenticatedPlayer || string.IsNullOrEmpty(blackmailId))
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingBlackmailRespondKey))
        {
            return;
        }

        _pendingBlackmailRespondKey = BuildActionKey($"press-respond-{blackmailId}-{action}");
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { action });
        _apiClient?.PostAuthorizedIdempotent($"/api/press/blackmail/{blackmailId}/respond", _session.AuthToken, _pendingBlackmailRespondKey, payload);
    }

    private void HandlePressInvestigationsResponse(JsonNode data)
    {
        _pressInvestigationsData = data;
        TryShowPressPanel();
    }

    private void HandlePressBlackmailsResponse(JsonNode data)
    {
        _pressBlackmailsData = data;
        TryShowPressPanel();
    }

    private void TryShowPressPanel()
    {
        if (_pressInvestigationsData == null || _pressBlackmailsData == null)
        {
            return;
        }

        _pendingPressCatalog = false;
        var model = DashboardPressModel.FromJson(_pressInvestigationsData, _pressBlackmailsData);
        _pressPanel?.LoadModel(model);
    }

    private void HandlePressActionResponse(JsonNode data)
    {
        _pendingInvestigateKey = "";
        _pendingPublishKey = "";
        _pendingBlackmailKey = "";
        _pendingBlackmailRespondKey = "";

        bool success = data?["success"]?.GetValue<bool>() ?? false;
        string message = data?["message"]?.ToString() ?? "Операцію завершено.";
        SetStatus(message, success);

        if (success && _session != null && _session.HasAuthenticatedPlayer)
        {
            RefreshPressData();
        }
    }

    private void RefreshPressData()
    {
        _pressInvestigationsData = null;
        _pressBlackmailsData = null;
        _apiClient?.GetAuthorized(
            $"/api/player/{_session.PlayerId}/press-investigations",
            _session.AuthToken);
        _apiClient?.GetAuthorized(
            $"/api/player/{_session.PlayerId}/press-blackmails",
            _session.AuthToken);
    }

    private bool TryHandlePressResponse(string endpoint, JsonNode root)
    {
        if (endpoint.StartsWith("/api/player/") && endpoint.EndsWith("/press-investigations"))
        {
            HandlePressInvestigationsResponse(root["data"]);
            return true;
        }

        if (endpoint.StartsWith("/api/player/") && endpoint.EndsWith("/press-blackmails"))
        {
            HandlePressBlackmailsResponse(root["data"]);
            return true;
        }

        if (endpoint == "/api/press/investigate" || endpoint == "/api/press/publish" || endpoint == "/api/press/blackmail" || endpoint.StartsWith("/api/press/blackmail/") || endpoint == "/api/press/advertising")
        {
            HandlePressActionResponse(root);
            return true;
        }

        return false;
    }
}
