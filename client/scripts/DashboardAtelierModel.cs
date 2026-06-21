using System;
using System.Collections.Generic;
using System.Text.Json.Nodes;

#nullable enable

/// <summary>
/// Atelier (skins) data for the Sprint 61 Atelier panel.
/// Backed by /api/atelier/skins, /api/atelier/player-skins.
/// </summary>
public sealed class DashboardAtelierModel
{
    public IReadOnlyList<DashboardAtelierSkin> ShopSkins { get; init; } = Array.Empty<DashboardAtelierSkin>();
    public IReadOnlyList<DashboardPlayerSkin> PlayerSkins { get; init; } = Array.Empty<DashboardPlayerSkin>();

    public bool HasShopSkins => ShopSkins.Count > 0;
    public bool HasPlayerSkins => PlayerSkins.Count > 0;
    public bool HasEquippedSkin
    {
        get
        {
            foreach (var skin in PlayerSkins)
            {
                if (skin.IsEquipped)
                {
                    return true;
                }
            }

            return false;
        }
    }

    public static DashboardAtelierModel FromJson(JsonNode? shopData, JsonNode? playerSkinsData)
    {
        return new DashboardAtelierModel
        {
            ShopSkins = ParseShopSkins(shopData?["skins"]?.AsArray()),
            PlayerSkins = ParsePlayerSkins(playerSkinsData?["skins"]?.AsArray()),
        };
    }

    private static IReadOnlyList<DashboardAtelierSkin> ParseShopSkins(JsonArray? skins)
    {
        if (skins == null || skins.Count == 0)
        {
            return Array.Empty<DashboardAtelierSkin>();
        }

        var items = new List<DashboardAtelierSkin>();
        foreach (var skin in skins)
        {
            if (skin != null)
            {
                items.Add(DashboardAtelierSkin.FromJson(skin));
            }
        }

        return items;
    }

    private static IReadOnlyList<DashboardPlayerSkin> ParsePlayerSkins(JsonArray? skins)
    {
        if (skins == null || skins.Count == 0)
        {
            return Array.Empty<DashboardPlayerSkin>();
        }

        var items = new List<DashboardPlayerSkin>();
        foreach (var skin in skins)
        {
            if (skin != null)
            {
                items.Add(DashboardPlayerSkin.FromJson(skin));
            }
        }

        return items;
    }
}

public sealed class DashboardAtelierSkin
{
    public string SkinId { get; init; } = "";
    public string Name { get; init; } = "";
    public string Rarity { get; init; } = "common";
    public bool IsUnique { get; init; }
    public double Price { get; init; }
    public int CopiesTotal { get; init; }
    public int CopiesSold { get; init; }
    public int CopiesAvailable { get; init; }
    public string DesignerId { get; init; } = "";
    public string CreatedAt { get; init; } = "";

    public string RarityLabel => Rarity switch
    {
        "common" => "Звичайний",
        "rare" => "Рідкісний",
        "epic" => "Епічний",
        "legendary" => "Легендарний",
        _ => Rarity,
    };

    public string SummaryText => $"{Name} | {RarityLabel}{(IsUnique ? " (унікальний)" : "")} | {Price:N0} ₴ | залишилось: {CopiesAvailable}";

    public static DashboardAtelierSkin FromJson(JsonNode data)
    {
        return new DashboardAtelierSkin
        {
            SkinId = data["skin_id"]?.ToString() ?? "",
            Name = data["name"]?.ToString() ?? "",
            Rarity = data["rarity"]?.ToString() ?? "common",
            IsUnique = data["is_unique"]?.GetValue<bool>() ?? false,
            Price = data["price"]?.GetValue<double>() ?? 0.0,
            CopiesTotal = data["copies_total"]?.GetValue<int>() ?? 0,
            CopiesSold = data["copies_sold"]?.GetValue<int>() ?? 0,
            CopiesAvailable = data["copies_available"]?.GetValue<int>() ?? 0,
            DesignerId = data["designer_id"]?.ToString() ?? "",
            CreatedAt = data["created_at"]?.ToString() ?? "",
        };
    }
}

public sealed class DashboardPlayerSkin
{
    public string PlayerSkinId { get; init; } = "";
    public string SkinId { get; init; } = "";
    public string Name { get; init; } = "";
    public string Rarity { get; init; } = "common";
    public bool IsUnique { get; init; }
    public bool IsEquipped { get; init; }
    public string AcquiredAt { get; init; } = "";

    public string RarityLabel => Rarity switch
    {
        "common" => "Звичайний",
        "rare" => "Рідкісний",
        "epic" => "Епічний",
        "legendary" => "Легендарний",
        _ => Rarity,
    };

    public string SummaryText => $"{Name} | {RarityLabel}{(IsEquipped ? " | Екіпіровано" : "")}";

    public static DashboardPlayerSkin FromJson(JsonNode data)
    {
        return new DashboardPlayerSkin
        {
            PlayerSkinId = data["player_skin_id"]?.ToString() ?? "",
            SkinId = data["skin_id"]?.ToString() ?? "",
            Name = data["name"]?.ToString() ?? "",
            Rarity = data["rarity"]?.ToString() ?? "common",
            IsUnique = data["is_unique"]?.GetValue<bool>() ?? false,
            IsEquipped = data["is_equipped"]?.GetValue<bool>() ?? false,
            AcquiredAt = data["acquired_at"]?.ToString() ?? "",
        };
    }
}
