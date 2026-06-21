using Godot;
using System.Text.Json.Nodes;

public partial class CityDashboardController
{
    private JsonNode _shadowBusinessesData;
    private JsonNode _shadowMarketData;
    private bool _pendingShadowCatalog;
    private string _pendingOpenBusinessKey;
    private string _pendingFraudAcceptKey;
    private string _pendingFraudRefuseKey;
    private string _pendingMarketBuyKey;
    private string _pendingMarketSellKey;

    public void OnShadowButtonPressed()
    {
        if (_shadowPanel == null || _session == null || !_session.HasAuthenticatedPlayer)
        {
            return;
        }

        _pendingShadowCatalog = true;
        ClearErrorState();
        _apiClient?.GetAuthorized(
            $"/api/player/{_session.PlayerId}/shadow-businesses",
            _session.AuthToken);
        _apiClient?.GetAuthorized($"/api/shadow/market?player_id={_session.PlayerId}", _session.AuthToken);
    }

    public void OnOpenBusinessRequested()
    {
        if (_session == null || !_session.HasAuthenticatedPlayer)
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingOpenBusinessKey))
        {
            return;
        }

        _pendingOpenBusinessKey = BuildActionKey("open-shadow-business");
        ClearErrorState();
        // Placeholder: use first district; real flow would need district selection
        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId, district_id = "", business_type = "illegal_bar" });
        _apiClient?.PostAuthorizedIdempotent("/api/shadow/open-business", _session.AuthToken, _pendingOpenBusinessKey, payload);
    }

    public void OnFraudAcceptRequested()
    {
        if (_session == null || !_session.HasAuthenticatedPlayer)
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingFraudAcceptKey))
        {
            return;
        }

        _pendingFraudAcceptKey = BuildActionKey("fraud-accept");
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId, amount = 0, game_day = 0 });
        _apiClient?.PostAuthorizedIdempotent("/api/shadow/fraud-accept", _session.AuthToken, _pendingFraudAcceptKey, payload);
    }

    public void OnFraudRefuseRequested()
    {
        if (_session == null || !_session.HasAuthenticatedPlayer)
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingFraudRefuseKey))
        {
            return;
        }

        _pendingFraudRefuseKey = BuildActionKey("fraud-refuse");
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId });
        _apiClient?.PostAuthorizedIdempotent("/api/shadow/fraud-refuse", _session.AuthToken, _pendingFraudRefuseKey, payload);
    }

    public void OnMarketBuyRequested(string itemType, int quantity)
    {
        if (_session == null || !_session.HasAuthenticatedPlayer || string.IsNullOrEmpty(itemType) || quantity <= 0)
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingMarketBuyKey))
        {
            return;
        }

        _pendingMarketBuyKey = BuildActionKey($"market-buy-{itemType}-{quantity}");
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId, item_type = itemType, quantity });
        _apiClient?.PostAuthorizedIdempotent("/api/shadow/market/buy", _session.AuthToken, _pendingMarketBuyKey, payload);
    }

    public void OnMarketSellRequested(string itemType, int quantity)
    {
        if (_session == null || !_session.HasAuthenticatedPlayer || string.IsNullOrEmpty(itemType) || quantity <= 0)
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingMarketSellKey))
        {
            return;
        }

        _pendingMarketSellKey = BuildActionKey($"market-sell-{itemType}-{quantity}");
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId, item_type = itemType, quantity });
        _apiClient?.PostAuthorizedIdempotent("/api/shadow/market/sell", _session.AuthToken, _pendingMarketSellKey, payload);
    }

    private void HandleShadowBusinessesResponse(JsonNode data)
    {
        _shadowBusinessesData = data;
        TryShowShadowPanel();
    }

    private void HandleShadowMarketResponse(JsonNode data)
    {
        _shadowMarketData = data;
        TryShowShadowPanel();
    }

    private void TryShowShadowPanel()
    {
        if (_shadowBusinessesData == null || _shadowMarketData == null)
        {
            return;
        }

        _pendingShadowCatalog = false;
        var model = DashboardShadowModel.FromJson(_shadowBusinessesData, _shadowMarketData);
        _shadowPanel?.LoadModel(model);
    }

    private void HandleShadowActionResponse(JsonNode data)
    {
        _pendingOpenBusinessKey = "";
        _pendingFraudAcceptKey = "";
        _pendingFraudRefuseKey = "";
        _pendingMarketBuyKey = "";
        _pendingMarketSellKey = "";

        bool success = data?["success"]?.GetValue<bool>() ?? false;
        string message = data?["message"]?.ToString() ?? "Операцію завершено.";
        SetStatus(message, success);

        if (success && _session != null && _session.HasAuthenticatedPlayer)
        {
            RefreshShadowData();
        }
    }

    private void RefreshShadowData()
    {
        _shadowBusinessesData = null;
        _shadowMarketData = null;
        _apiClient?.GetAuthorized(
            $"/api/player/{_session.PlayerId}/shadow-businesses",
            _session.AuthToken);
        _apiClient?.GetAuthorized($"/api/shadow/market?player_id={_session.PlayerId}", _session.AuthToken);
    }

    private bool TryHandleShadowResponse(string endpoint, JsonNode root)
    {
        if (endpoint.StartsWith("/api/player/") && endpoint.EndsWith("/shadow-businesses"))
        {
            HandleShadowBusinessesResponse(root["data"]);
            return true;
        }

        if (endpoint.StartsWith("/api/shadow/market") && !endpoint.Contains("/buy") && !endpoint.Contains("/sell"))
        {
            HandleShadowMarketResponse(root["data"] ?? root);
            return true;
        }

        if (endpoint == "/api/shadow/open-business" || endpoint == "/api/shadow/fraud-accept" || endpoint == "/api/shadow/fraud-refuse" || endpoint == "/api/shadow/market/buy" || endpoint == "/api/shadow/market/sell" || endpoint == "/api/shadow/business-income" || endpoint == "/api/shadow/check-discovery" || endpoint == "/api/shadow/fraud-offer" || endpoint == "/api/shadow/money-laundering")
        {
            HandleShadowActionResponse(root);
            return true;
        }

        return false;
    }
}
