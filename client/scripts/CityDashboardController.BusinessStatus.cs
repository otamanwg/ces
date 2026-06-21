using System.Text.Json.Nodes;

public partial class CityDashboardController
{
    private bool _pendingBusinessStatus;

    private bool TryHandleBusinessStatusResponse(string endpoint, JsonNode root)
    {
        if (!IsBusinessStatusEndpoint(endpoint))
        {
            return false;
        }

        HandleBusinessStatus(root);
        return true;
    }

    private void RefreshBusinessStatus()
    {
        if (_session == null || !_session.HasAuthenticatedPlayer
            || string.IsNullOrEmpty(_ownedBusinessId) || _pendingBusinessStatus)
        {
            return;
        }

        _pendingBusinessStatus = true;
        _apiClient?.GetAuthorized(
            $"/api/business/{_ownedBusinessId}/status?player_id={_session.PlayerId}",
            _session.AuthToken
        );
    }

    private static bool IsBusinessStatusEndpoint(string endpoint)
    {
        return endpoint.StartsWith("/api/business/") && endpoint.Contains("/status");
    }

    private void HandleBusinessStatus(JsonNode root)
    {
        _pendingBusinessStatus = false;
        if (root["success"]?.GetValue<bool>() != true || OwnedBusinessLabel == null)
        {
            return;
        }

        var data = root["data"];
        if (data == null)
        {
            return;
        }

        string name = data["name"]?.ToString() ?? "";
        string mode = data["management_mode"]?.ToString() ?? "";
        double daily = data["daily_revenue"]?.GetValue<double>() ?? 0.0;
        string modeLabel = mode switch
        {
            "ai" => "AI",
            "manual" => "Ручний",
            "shadow" => "Тіньовий",
            _ => mode,
        };
        string revenueText = daily > 0 ? $" | {daily:N0} ₴/день" : "";
        OwnedBusinessLabel.Text = $"Бізнес: {name} [{modeLabel}{revenueText}]";
    }
}
