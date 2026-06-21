using Godot;
using System.Text.Json.Nodes;

public partial class CityDashboardController
{
    private JsonNode _atelierShopData;
    private JsonNode _atelierPlayerSkinsData;
    private bool _pendingAtelierCatalog;
    private string _pendingBuySkinKey;
    private string _pendingEquipSkinKey;
    private string _pendingUnequipAllKey;
    private string _pendingCreateSkinKey;

    public void OnAtelierButtonPressed()
    {
        if (_atelierPanel == null || _session == null || !_session.HasAuthenticatedPlayer)
        {
            return;
        }

        _pendingAtelierCatalog = true;
        ClearErrorState();
        // Get player's owned skins
        _apiClient?.GetAuthorized(
            $"/api/atelier/player-skins?player_id={_session.PlayerId}",
            _session.AuthToken);
        // For shop, we need an atelier_id; for now use empty (will show empty shop)
        // Real flow would need atelier business selection
        _atelierShopData = JsonNode.Parse("""{"skins": []}""");
        TryShowAtelierPanel();
    }

    public void OnBuyRequested(string skinId)
    {
        if (_session == null || !_session.HasAuthenticatedPlayer || string.IsNullOrEmpty(skinId))
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingBuySkinKey))
        {
            return;
        }

        _pendingBuySkinKey = BuildActionKey($"buy-skin-{skinId}");
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { buyer_id = _session.PlayerId, skin_id = skinId, atelier_id = "" });
        _apiClient?.PostAuthorizedIdempotent("/api/atelier/buy-skin", _session.AuthToken, _pendingBuySkinKey, payload);
    }

    public void OnEquipRequested(string playerSkinId)
    {
        if (_session == null || !_session.HasAuthenticatedPlayer || string.IsNullOrEmpty(playerSkinId))
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingEquipSkinKey))
        {
            return;
        }

        _pendingEquipSkinKey = BuildActionKey($"equip-skin-{playerSkinId}");
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId, player_skin_id = playerSkinId });
        _apiClient?.PostAuthorizedIdempotent("/api/atelier/equip-skin", _session.AuthToken, _pendingEquipSkinKey, payload);
    }

    public void OnUnequipAllRequested()
    {
        if (_session == null || !_session.HasAuthenticatedPlayer)
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingUnequipAllKey))
        {
            return;
        }

        _pendingUnequipAllKey = BuildActionKey("unequip-all");
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId });
        _apiClient?.PostAuthorizedIdempotent("/api/atelier/unequip-all", _session.AuthToken, _pendingUnequipAllKey, payload);
    }

    private void HandleAtelierPlayerSkinsResponse(JsonNode data)
    {
        _atelierPlayerSkinsData = data;
        TryShowAtelierPanel();
    }

    private void TryShowAtelierPanel()
    {
        if (_atelierShopData == null || _atelierPlayerSkinsData == null)
        {
            return;
        }

        _pendingAtelierCatalog = false;
        var model = DashboardAtelierModel.FromJson(_atelierShopData, _atelierPlayerSkinsData);
        _atelierPanel?.LoadModel(model);
    }

    private void HandleAtelierActionResponse(JsonNode data)
    {
        _pendingBuySkinKey = "";
        _pendingEquipSkinKey = "";
        _pendingUnequipAllKey = "";
        _pendingCreateSkinKey = "";

        bool success = data?["success"]?.GetValue<bool>() ?? false;
        string message = data?["message"]?.ToString() ?? "Операцію завершено.";
        SetStatus(message, success);

        if (success && _session != null && _session.HasAuthenticatedPlayer)
        {
            RefreshAtelierData();
        }
    }

    private void RefreshAtelierData()
    {
        _atelierPlayerSkinsData = null;
        _apiClient?.GetAuthorized(
            $"/api/atelier/player-skins?player_id={_session.PlayerId}",
            _session.AuthToken);
    }

    private bool TryHandleAtelierResponse(string endpoint, JsonNode root)
    {
        if (endpoint.StartsWith("/api/atelier/player-skins"))
        {
            HandleAtelierPlayerSkinsResponse(root["data"] ?? root);
            return true;
        }

        if (endpoint.StartsWith("/api/atelier/skins"))
        {
            _atelierShopData = root["data"] ?? root;
            TryShowAtelierPanel();
            return true;
        }

        if (endpoint == "/api/atelier/buy-skin" || endpoint == "/api/atelier/equip-skin" || endpoint == "/api/atelier/unequip-all" || endpoint == "/api/atelier/create-skin")
        {
            HandleAtelierActionResponse(root);
            return true;
        }

        return false;
    }
}
