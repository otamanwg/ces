using Godot;
using System.Text.Json.Nodes;

public partial class CityDashboardController
{
    private JsonNode _educationCoursesData;
    private JsonNode _educationActiveData;
    private JsonNode _educationCompletedData;
    private bool _pendingEducationCatalog;
    private string _pendingEnrollKey;

    public void OnEducationButtonPressed()
    {
        if (_educationPanel == null || _session == null || !_session.HasAuthenticatedPlayer)
        {
            return;
        }

        // Load education data from API, then show panel.
        _pendingEducationCatalog = true;
        ClearErrorState();
        _apiClient?.GetAuthorized("/api/education/courses", _session.AuthToken);
        _apiClient?.GetAuthorized(
            $"/api/education/active?player_id={_session.PlayerId}",
            _session.AuthToken);
        _apiClient?.GetAuthorized(
            $"/api/education/completed?player_id={_session.PlayerId}",
            _session.AuthToken);
    }

    public void OnEducationEnrollRequested(string courseCode, string mode)
    {
        if (_session == null || !_session.HasAuthenticatedPlayer || string.IsNullOrEmpty(courseCode))
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingEnrollKey))
        {
            return;
        }

        _pendingEnrollKey = BuildActionKey($"enroll-{courseCode}-{mode}");
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId, course = courseCode, mode });
        _apiClient?.PostAuthorizedIdempotent(
            "/api/education/enroll",
            _session.AuthToken,
            _pendingEnrollKey,
            payload);
    }

    private void HandleEducationCoursesResponse(JsonNode data)
    {
        _educationCoursesData = data;
        TryShowEducationPanel();
    }

    private void HandleEducationActiveResponse(JsonNode data)
    {
        _educationActiveData = data;
        TryShowEducationPanel();
    }

    private void HandleEducationCompletedResponse(JsonNode data)
    {
        _educationCompletedData = data;
        TryShowEducationPanel();
    }

    private void TryShowEducationPanel()
    {
        if (_educationCoursesData == null || _educationActiveData == null || _educationCompletedData == null)
        {
            return;
        }

        _pendingEducationCatalog = false;
        var model = DashboardEducationModel.FromJson(_educationCoursesData, _educationActiveData, _educationCompletedData);
        _educationPanel?.LoadModel(model);
    }

    private void HandleEnrollResponse(JsonNode data)
    {
        _pendingEnrollKey = "";
        bool success = data?["success"]?.GetValue<bool>() ?? false;
        string message = data?["message"]?.ToString() ?? "Запис на курс завершено.";
        SetStatus(message, success);

        // Refresh education data after enrollment.
        if (success && _session != null && _session.HasAuthenticatedPlayer)
        {
            _educationCoursesData = null;
            _educationActiveData = null;
            _educationCompletedData = null;
            _apiClient?.GetAuthorized("/api/education/courses", _session.AuthToken);
            _apiClient?.GetAuthorized(
                $"/api/education/active?player_id={_session.PlayerId}",
                _session.AuthToken);
            _apiClient?.GetAuthorized(
                $"/api/education/completed?player_id={_session.PlayerId}",
                _session.AuthToken);
        }
    }

    private bool TryHandleEducationResponse(string endpoint, JsonNode root)
    {
        if (endpoint == "/api/education/courses")
        {
            HandleEducationCoursesResponse(root["data"]);
            return true;
        }

        if (endpoint.StartsWith("/api/education/active"))
        {
            HandleEducationActiveResponse(root["data"]);
            return true;
        }

        if (endpoint.StartsWith("/api/education/completed"))
        {
            HandleEducationCompletedResponse(root["data"]);
            return true;
        }

        if (endpoint == "/api/education/enroll")
        {
            HandleEnrollResponse(root);
            return true;
        }

        return false;
    }
}
