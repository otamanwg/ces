using Godot;
using System.Text.Json.Nodes;

public partial class CityDashboardController
{
    private JsonNode _courtCasesData;
    private JsonNode _prisonSentenceData;
    private bool _pendingCourtCatalog;
    private string _pendingPrisonWorkKey;
    private string _pendingPokerKey;
    private string _pendingSocializeKey;

    public void OnCourtButtonPressed()
    {
        if (_courtPanel == null || _session == null || !_session.HasAuthenticatedPlayer)
        {
            return;
        }

        _pendingCourtCatalog = true;
        ClearErrorState();
        _apiClient?.GetAuthorized(
            $"/api/player/{_session.PlayerId}/court-cases",
            _session.AuthToken);
        _apiClient?.GetAuthorized($"/api/prison/sentence?player_id={_session.PlayerId}", _session.AuthToken);
    }

    public void OnCourtWorkRequested()
    {
        if (_session == null || !_session.HasAuthenticatedPlayer)
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingPrisonWorkKey))
        {
            return;
        }

        _pendingPrisonWorkKey = BuildActionKey("prison-work");
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId });
        _apiClient?.PostAuthorizedIdempotent("/api/prison/work", _session.AuthToken, _pendingPrisonWorkKey, payload);
    }

    public void OnCourtPokerRequested(double bet)
    {
        if (_session == null || !_session.HasAuthenticatedPlayer || bet <= 0)
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingPokerKey))
        {
            return;
        }

        _pendingPokerKey = BuildActionKey($"prison-poker-{bet}");
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId, bet });
        _apiClient?.PostAuthorizedIdempotent("/api/prison/poker", _session.AuthToken, _pendingPokerKey, payload);
    }

    public void OnCourtSocializeRequested()
    {
        if (_session == null || !_session.HasAuthenticatedPlayer)
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingSocializeKey))
        {
            return;
        }

        _pendingSocializeKey = BuildActionKey("prison-socialize");
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId });
        _apiClient?.PostAuthorizedIdempotent("/api/prison/socialize", _session.AuthToken, _pendingSocializeKey, payload);
    }

    private void HandleCourtCasesResponse(JsonNode data)
    {
        _courtCasesData = data;
        TryShowCourtPanel();
    }

    private void HandlePrisonSentenceResponse(JsonNode data)
    {
        _prisonSentenceData = data;
        TryShowCourtPanel();
    }

    private void TryShowCourtPanel()
    {
        if (_courtCasesData == null || _prisonSentenceData == null)
        {
            return;
        }

        _pendingCourtCatalog = false;
        var model = DashboardCourtModel.FromJson(_courtCasesData, _prisonSentenceData);
        _courtPanel?.LoadModel(model);
    }

    private void HandleCourtActionResponse(JsonNode data)
    {
        _pendingPrisonWorkKey = "";
        _pendingPokerKey = "";
        _pendingSocializeKey = "";

        bool success = data?["success"]?.GetValue<bool>() ?? false;
        string message = data?["message"]?.ToString() ?? "Операцію завершено.";
        SetStatus(message, success);

        // Refresh court/prison data after action.
        if (success && _session != null && _session.HasAuthenticatedPlayer)
        {
            RefreshCourtData();
        }
    }

    private void RefreshCourtData()
    {
        _courtCasesData = null;
        _prisonSentenceData = null;
        _apiClient?.GetAuthorized(
            $"/api/player/{_session.PlayerId}/court-cases",
            _session.AuthToken);
        _apiClient?.GetAuthorized($"/api/prison/sentence?player_id={_session.PlayerId}", _session.AuthToken);
    }

    private bool TryHandleCourtResponse(string endpoint, JsonNode root)
    {
        if (endpoint.StartsWith("/api/player/") && endpoint.EndsWith("/court-cases"))
        {
            HandleCourtCasesResponse(root["data"]);
            return true;
        }

        if (endpoint.StartsWith("/api/prison/sentence"))
        {
            HandlePrisonSentenceResponse(root["data"]);
            return true;
        }

        if (endpoint == "/api/prison/work" || endpoint == "/api/prison/poker" || endpoint == "/api/prison/socialize")
        {
            HandleCourtActionResponse(root);
            return true;
        }

        return false;
    }
}
