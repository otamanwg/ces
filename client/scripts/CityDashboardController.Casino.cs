using Godot;
using System.Text.Json.Nodes;

public partial class CityDashboardController
{
    private JsonNode _casinoGamesData;
    private bool _pendingCasinoCatalog;
    private string _pendingBlackjackKey;
    private string _pendingRouletteKey;
    private string _pendingCreatePokerKey;

    public void OnCasinoButtonPressed()
    {
        if (_casinoPanel == null || _session == null || !_session.HasAuthenticatedPlayer)
        {
            return;
        }

        _pendingCasinoCatalog = true;
        ClearErrorState();
        _apiClient?.GetAuthorized(
            $"/api/player/{_session.PlayerId}/casino-games",
            _session.AuthToken);
    }

    public void OnBlackjackRequested(string casinoId, double bet)
    {
        if (_session == null || !_session.HasAuthenticatedPlayer || string.IsNullOrEmpty(casinoId) || bet <= 0)
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingBlackjackKey))
        {
            return;
        }

        _pendingBlackjackKey = BuildActionKey($"blackjack-{casinoId}-{bet}");
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { casino_id = casinoId, player_id = _session.PlayerId, bet });
        _apiClient?.PostAuthorizedIdempotent("/api/casino/blackjack", _session.AuthToken, _pendingBlackjackKey, payload);
    }

    public void OnRouletteRequested(string casinoId, double bet, string betType)
    {
        if (_session == null || !_session.HasAuthenticatedPlayer || string.IsNullOrEmpty(casinoId) || bet <= 0)
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingRouletteKey))
        {
            return;
        }

        _pendingRouletteKey = BuildActionKey($"roulette-{casinoId}-{bet}-{betType}");
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { casino_id = casinoId, player_id = _session.PlayerId, bet, bet_type = betType });
        _apiClient?.PostAuthorizedIdempotent("/api/casino/roulette", _session.AuthToken, _pendingRouletteKey, payload);
    }

    public void OnCreatePokerRequested(string casinoId)
    {
        if (_session == null || !_session.HasAuthenticatedPlayer || string.IsNullOrEmpty(casinoId))
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingCreatePokerKey))
        {
            return;
        }

        _pendingCreatePokerKey = BuildActionKey($"create-poker-{casinoId}");
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { casino_id = casinoId, min_buyin = 100.0 });
        _apiClient?.PostAuthorizedIdempotent("/api/casino/poker/create", _session.AuthToken, _pendingCreatePokerKey, payload);
    }

    private void HandleCasinoGamesResponse(JsonNode data)
    {
        _casinoGamesData = data;
        _pendingCasinoCatalog = false;
        var model = DashboardCasinoModel.FromJson(_casinoGamesData);
        _casinoPanel?.LoadModel(model);
    }

    private void HandleCasinoActionResponse(JsonNode data)
    {
        _pendingBlackjackKey = "";
        _pendingRouletteKey = "";
        _pendingCreatePokerKey = "";

        bool success = data?["success"]?.GetValue<bool>() ?? false;
        string message = data?["message"]?.ToString() ?? "Операцію завершено.";
        SetStatus(message, success);

        if (success && _session != null && _session.HasAuthenticatedPlayer)
        {
            RefreshCasinoData();
        }
    }

    private void RefreshCasinoData()
    {
        _casinoGamesData = null;
        _apiClient?.GetAuthorized(
            $"/api/player/{_session.PlayerId}/casino-games",
            _session.AuthToken);
    }

    private bool TryHandleCasinoResponse(string endpoint, JsonNode root)
    {
        if (endpoint.StartsWith("/api/player/") && endpoint.EndsWith("/casino-games"))
        {
            HandleCasinoGamesResponse(root["data"]);
            return true;
        }

        if (endpoint == "/api/casino/blackjack" || endpoint == "/api/casino/roulette" || endpoint == "/api/casino/poker/create" || endpoint == "/api/casino/tax")
        {
            HandleCasinoActionResponse(root);
            return true;
        }

        return false;
    }
}
