using System;
using System.Collections.Generic;
using System.Text.Json.Nodes;

#nullable enable

/// <summary>
/// Shadow economy data for the Sprint 61 Shadow panel.
/// Backed by /api/player/{id}/shadow-businesses, /api/shadow/market.
/// </summary>
public sealed class DashboardShadowModel
{
    public double CriminalRep { get; init; }
    public IReadOnlyList<DashboardShadowBusiness> Businesses { get; init; } = Array.Empty<DashboardShadowBusiness>();
    public IReadOnlyList<DashboardShadowMarketItem> MarketItems { get; init; } = Array.Empty<DashboardShadowMarketItem>();

    public bool HasMarketAccess => CriminalRep >= 30.0;
    public bool HasBusinesses => Businesses.Count > 0;

    public static DashboardShadowModel FromJson(JsonNode? businessesData, JsonNode? marketData)
    {
        return new DashboardShadowModel
        {
            CriminalRep = businessesData?["criminal_rep"]?.GetValue<double>() ?? 0.0,
            Businesses = ParseBusinesses(businessesData?["businesses"]?.AsArray()),
            MarketItems = ParseMarketItems(marketData?["items"]?.AsArray()),
        };
    }

    private static IReadOnlyList<DashboardShadowBusiness> ParseBusinesses(JsonArray? businesses)
    {
        if (businesses == null || businesses.Count == 0)
        {
            return Array.Empty<DashboardShadowBusiness>();
        }

        var items = new List<DashboardShadowBusiness>();
        foreach (var business in businesses)
        {
            if (business != null)
            {
                items.Add(DashboardShadowBusiness.FromJson(business));
            }
        }

        return items;
    }

    private static IReadOnlyList<DashboardShadowMarketItem> ParseMarketItems(JsonArray? items)
    {
        if (items == null || items.Count == 0)
        {
            return Array.Empty<DashboardShadowMarketItem>();
        }

        var result = new List<DashboardShadowMarketItem>();
        foreach (var item in items)
        {
            if (item != null)
            {
                result.Add(DashboardShadowMarketItem.FromJson(item));
            }
        }

        return result;
    }
}

public sealed class DashboardShadowBusiness
{
    public string Id { get; init; } = "";
    public string Type { get; init; } = "";
    public string DistrictId { get; init; } = "";
    public double CashBalance { get; init; }
    public bool IsDiscovered { get; init; }
    public string CreatedAt { get; init; } = "";

    public string TypeLabel => Type switch
    {
        "illegal_bar" => "Нелегальний бар",
        "illegal_casino" => "Нелегальне казино",
        "smuggling" => "Контрабанда",
        "shadow_pharmacy" => "Тіньова аптека",
        "money_laundering" => "Відмивання грошей",
        _ => Type,
    };

    public string SummaryText => $"{TypeLabel} | каса: {CashBalance:N0} ₴{(IsDiscovered ? " | ВИЯВЛЕНО" : "")}";

    public static DashboardShadowBusiness FromJson(JsonNode data)
    {
        return new DashboardShadowBusiness
        {
            Id = data["id"]?.ToString() ?? "",
            Type = data["type"]?.ToString() ?? "",
            DistrictId = data["district_id"]?.ToString() ?? "",
            CashBalance = data["cash_balance"]?.GetValue<double>() ?? 0.0,
            IsDiscovered = data["is_discovered"]?.GetValue<bool>() ?? false,
            CreatedAt = data["created_at"]?.ToString() ?? "",
        };
    }
}

public sealed class DashboardShadowMarketItem
{
    public string Type { get; init; } = "";
    public double PriceModifier { get; init; }

    public string TypeLabel => Type switch
    {
        "contraband_electronics" => "Контрабандна електроніка",
        "stolen_goods" => "Вкрадені товари",
        "fake_medicine" => "Підроблені ліки",
        _ => Type,
    };

    public string SummaryText => $"{TypeLabel} | ціна: {PriceModifier:P0} від легальної";

    public static DashboardShadowMarketItem FromJson(JsonNode data)
    {
        return new DashboardShadowMarketItem
        {
            Type = data["type"]?.ToString() ?? "",
            PriceModifier = data["price_modifier"]?.GetValue<double>() ?? 0.0,
        };
    }
}
