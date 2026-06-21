using Godot;
using System.Text.Json.Nodes;

public partial class CityDashboardController
{
    private JsonNode _policeOfficerData;
    private JsonNode _policeRecordsData;
    private JsonNode _corruptionLogData;
    private bool _pendingPoliceCatalog;
    private string _pendingHireKey;
    private string _pendingPromoteKey;
    private string _pendingPatrolKey;

    public void OnPoliceButtonPressed()
    {
        if (_policePanel == null || _session == null || !_session.HasAuthenticatedPlayer)
        {
            return;
        }

        _pendingPoliceCatalog = true;
        ClearErrorState();
        _apiClient?.GetAuthorized($"/api/police/officer?player_id={_session.PlayerId}", _session.AuthToken);
        _apiClient?.GetAuthorized(
            $"/api/player/{_session.PlayerId}/police-records",
            _session.AuthToken);
        _apiClient?.GetAuthorized($"/api/police/corruption-log?player_id={_session.PlayerId}", _session.AuthToken);
    }

    public void OnPoliceHireRequested()
    {
        if (_session == null || !_session.HasAuthenticatedPlayer)
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingHireKey))
        {
            return;
        }

        _pendingHireKey = BuildActionKey("police-hire");
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId, game_day = 0 });
        _apiClient?.PostAuthorizedIdempotent("/api/police/hire", _session.AuthToken, _pendingHireKey, payload);
    }

    public void OnPolicePromoteRequested()
    {
        if (_session == null || !_session.HasAuthenticatedPlayer)
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingPromoteKey))
        {
            return;
        }

        _pendingPromoteKey = BuildActionKey("police-promote");
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId, game_day = 0 });
        _apiClient?.PostAuthorizedIdempotent("/api/police/promote", _session.AuthToken, _pendingPromoteKey, payload);
    }

    public void OnPolicePatrolRequested(string districtId)
    {
        if (_session == null || !_session.HasAuthenticatedPlayer || string.IsNullOrEmpty(districtId))
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingPatrolKey))
        {
            return;
        }

        _pendingPatrolKey = BuildActionKey($"police-patrol-{districtId}");
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId, district_id = districtId, game_day = 0 });
        _apiClient?.PostAuthorizedIdempotent("/api/police/patrol", _session.AuthToken, _pendingPatrolKey, payload);
    }

    private void HandlePoliceOfficerResponse(JsonNode data)
    {
        _policeOfficerData = data;
        TryShowPolicePanel();
    }

    private void HandlePoliceRecordsResponse(JsonNode data)
    {
        _policeRecordsData = data;
        TryShowPolicePanel();
    }

    private void HandleCorruptionLogResponse(JsonNode data)
    {
        _corruptionLogData = data;
        TryShowPolicePanel();
    }

    private void TryShowPolicePanel()
    {
        if (_policeOfficerData == null || _policeRecordsData == null || _corruptionLogData == null)
        {
            return;
        }

        _pendingPoliceCatalog = false;
        var model = DashboardPoliceModel.FromJson(_policeOfficerData, _policeRecordsData, _corruptionLogData);
        _policePanel?.LoadModel(model);
    }

    private void HandlePoliceActionResponse(JsonNode data)
    {
        _pendingHireKey = "";
        _pendingPromoteKey = "";
        _pendingPatrolKey = "";

        bool success = data?["success"]?.GetValue<bool>() ?? false;
        string message = data?["message"]?.ToString() ?? "Операцію завершено.";
        SetStatus(message, success);

        // Refresh police data after action.
        if (success && _session != null && _session.HasAuthenticatedPlayer)
        {
            RefreshPoliceData();
        }
    }

    private void RefreshPoliceData()
    {
        _policeOfficerData = null;
        _policeRecordsData = null;
        _corruptionLogData = null;
        _apiClient?.GetAuthorized($"/api/police/officer?player_id={_session.PlayerId}", _session.AuthToken);
        _apiClient?.GetAuthorized(
            $"/api/player/{_session.PlayerId}/police-records",
            _session.AuthToken);
        _apiClient?.GetAuthorized($"/api/police/corruption-log?player_id={_session.PlayerId}", _session.AuthToken);
    }

    private bool TryHandlePoliceResponse(string endpoint, JsonNode root)
    {
        if (endpoint.StartsWith("/api/police/officer"))
        {
            HandlePoliceOfficerResponse(root["data"]);
            return true;
        }

        if (endpoint.StartsWith("/api/player/") && endpoint.EndsWith("/police-records"))
        {
            HandlePoliceRecordsResponse(root["data"]);
            return true;
        }

        if (endpoint.StartsWith("/api/police/corruption-log"))
        {
            HandleCorruptionLogResponse(root["data"]);
            return true;
        }

        if (endpoint == "/api/police/hire" || endpoint == "/api/police/promote" || endpoint == "/api/police/patrol")
        {
            HandlePoliceActionResponse(root);
            return true;
        }

        return false;
    }
}
