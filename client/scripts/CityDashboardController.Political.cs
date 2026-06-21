using Godot;
using System.Text.Json.Nodes;

public partial class CityDashboardController
{
    private JsonNode _politicalOfficeData;
    private JsonNode _electionData;
    private JsonNode _mayorEligibilityData;
    private bool _pendingPoliticalCatalog;
    private string _pendingHireOfficeKey;
    private string _pendingRegisterCandidateKey;
    private string _pendingStartElectionKey;
    private string _pendingVoteKey;

    public void OnPoliticalButtonPressed()
    {
        if (_politicalPanel == null || _session == null || !_session.HasAuthenticatedPlayer)
        {
            return;
        }

        _pendingPoliticalCatalog = true;
        ClearErrorState();
        _apiClient?.GetAuthorized(
            $"/api/player/{_session.PlayerId}/city-office",
            _session.AuthToken);
        _apiClient?.GetAuthorized("/api/city/election", _session.AuthToken);
        _apiClient?.GetAuthorized($"/api/education/mayor-eligibility?player_id={_session.PlayerId}", _session.AuthToken);
    }

    public void OnHireOfficeRequested()
    {
        if (_session == null || !_session.HasAuthenticatedPlayer)
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingHireOfficeKey))
        {
            return;
        }

        _pendingHireOfficeKey = BuildActionKey("hire-office");
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId, position = "worker", department = "economy", game_day = 0 });
        _apiClient?.PostAuthorizedIdempotent("/api/city/offices/hire", _session.AuthToken, _pendingHireOfficeKey, payload);
    }

    public void OnRegisterCandidateRequested()
    {
        if (_session == null || !_session.HasAuthenticatedPlayer)
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingRegisterCandidateKey))
        {
            return;
        }

        _pendingRegisterCandidateKey = BuildActionKey("register-candidate");
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId, platform_text = "", game_day = 0 });
        _apiClient?.PostAuthorizedIdempotent("/api/city/election/register", _session.AuthToken, _pendingRegisterCandidateKey, payload);
    }

    public void OnStartElectionRequested()
    {
        if (_session == null || !_session.HasAuthenticatedPlayer)
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingStartElectionKey))
        {
            return;
        }

        _pendingStartElectionKey = BuildActionKey("start-election");
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { game_day = 0 });
        _apiClient?.PostAuthorizedIdempotent("/api/city/election/start", _session.AuthToken, _pendingStartElectionKey, payload);
    }

    private void HandlePoliticalOfficeResponse(JsonNode data)
    {
        _politicalOfficeData = data;
        TryShowPoliticalPanel();
    }

    private void HandleElectionResponse(JsonNode data)
    {
        _electionData = data;
        TryShowPoliticalPanel();
    }

    private void HandleMayorEligibilityResponse(JsonNode data)
    {
        _mayorEligibilityData = data;
        TryShowPoliticalPanel();
    }

    private void TryShowPoliticalPanel()
    {
        if (_politicalOfficeData == null || _electionData == null || _mayorEligibilityData == null)
        {
            return;
        }

        _pendingPoliticalCatalog = false;
        var model = DashboardPoliticalModel.FromJson(_politicalOfficeData, _electionData, _mayorEligibilityData);
        _politicalPanel?.LoadModel(model);
    }

    private void HandlePoliticalActionResponse(JsonNode data)
    {
        _pendingHireOfficeKey = "";
        _pendingRegisterCandidateKey = "";
        _pendingStartElectionKey = "";
        _pendingVoteKey = "";

        bool success = data?["success"]?.GetValue<bool>() ?? false;
        string message = data?["message"]?.ToString() ?? "Операцію завершено.";
        SetStatus(message, success);

        if (success && _session != null && _session.HasAuthenticatedPlayer)
        {
            RefreshPoliticalData();
        }
    }

    private void RefreshPoliticalData()
    {
        _politicalOfficeData = null;
        _electionData = null;
        _mayorEligibilityData = null;
        _apiClient?.GetAuthorized(
            $"/api/player/{_session.PlayerId}/city-office",
            _session.AuthToken);
        _apiClient?.GetAuthorized("/api/city/election", _session.AuthToken);
        _apiClient?.GetAuthorized($"/api/education/mayor-eligibility?player_id={_session.PlayerId}", _session.AuthToken);
    }

    private bool TryHandlePoliticalResponse(string endpoint, JsonNode root)
    {
        if (endpoint.StartsWith("/api/player/") && endpoint.EndsWith("/city-office"))
        {
            HandlePoliticalOfficeResponse(root["data"]);
            return true;
        }

        if (endpoint.StartsWith("/api/city/election") && !endpoint.Contains("/register") && !endpoint.Contains("/vote") && !endpoint.Contains("/bribe") && !endpoint.Contains("/conclude") && !endpoint.Contains("/start"))
        {
            HandleElectionResponse(root["data"]);
            return true;
        }

        if (endpoint.StartsWith("/api/education/mayor-eligibility"))
        {
            HandleMayorEligibilityResponse(root["data"] ?? root);
            return true;
        }

        if (endpoint == "/api/city/offices/hire" || endpoint == "/api/city/election/register" || endpoint == "/api/city/election/start" || endpoint == "/api/city/election/vote")
        {
            HandlePoliticalActionResponse(root);
            return true;
        }

        return false;
    }
}
