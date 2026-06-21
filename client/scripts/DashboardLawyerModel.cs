using System;
using System.Collections.Generic;
using System.Text.Json.Nodes;

#nullable enable

/// <summary>
/// Lawyer system data for the Sprint 61 Lawyer panel.
/// Backed by /api/player/{id}/lawyer-engagements.
/// </summary>
public sealed class DashboardLawyerModel
{
    public int SuccessfulDeals { get; init; }
    public IReadOnlyList<DashboardLawyerEngagement> Engagements { get; init; } = Array.Empty<DashboardLawyerEngagement>();

    public int LawyerLevel => SuccessfulDeals / 10;
    public bool HasEngagements => Engagements.Count > 0;
    public double SuccessChanceBonus => LawyerLevel * 0.05;
    public double DetectionChanceReduction => LawyerLevel * 0.03;

    public static DashboardLawyerModel FromJson(JsonNode? data)
    {
        return new DashboardLawyerModel
        {
            SuccessfulDeals = data?["successful_deals"]?.GetValue<int>() ?? 0,
            Engagements = ParseEngagements(data?["engagements"]?.AsArray()),
        };
    }

    private static IReadOnlyList<DashboardLawyerEngagement> ParseEngagements(JsonArray? engagements)
    {
        if (engagements == null || engagements.Count == 0)
        {
            return Array.Empty<DashboardLawyerEngagement>();
        }

        var items = new List<DashboardLawyerEngagement>();
        foreach (var engagement in engagements)
        {
            if (engagement != null)
            {
                items.Add(DashboardLawyerEngagement.FromJson(engagement));
            }
        }

        return items;
    }
}

public sealed class DashboardLawyerEngagement
{
    public string Id { get; init; } = "";
    public string LawyerId { get; init; } = "";
    public string ClientId { get; init; } = "";
    public string DealType { get; init; } = "";
    public double Amount { get; init; }
    public double Commission { get; init; }
    public double SuccessChanceBonus { get; init; }
    public bool? IsSuccessful { get; init; }
    public string CreatedAt { get; init; } = "";
    public string Role { get; init; } = "client";

    public string DealTypeLabel => DealType switch
    {
        "general" => "Загальне доручення",
        "shadow_deal" => "Тіньова угода",
        "police_defense" => "Захист від поліції",
        "appeal" => "Апеляція",
        _ => DealType,
    };

    public string StatusLabel => IsSuccessful switch
    {
        null => "Очікує",
        true => "Успішно",
        false => "Невдало",
    };

    public string RoleLabel => Role == "lawyer" ? "Адвокат" : "Клієнт";

    public string SummaryText => $"{RoleLabel} | {DealTypeLabel} | {StatusLabel} | комісія: {Commission:N0} ₴";

    public static DashboardLawyerEngagement FromJson(JsonNode data)
    {
        return new DashboardLawyerEngagement
        {
            Id = data["id"]?.ToString() ?? "",
            LawyerId = data["lawyer_id"]?.ToString() ?? "",
            ClientId = data["client_id"]?.ToString() ?? "",
            DealType = data["deal_type"]?.ToString() ?? "",
            Amount = data["amount"]?.GetValue<double>() ?? 0.0,
            Commission = data["commission"]?.GetValue<double>() ?? 0.0,
            SuccessChanceBonus = data["success_chance_bonus"]?.GetValue<double>() ?? 0.0,
            IsSuccessful = data["is_successful"]?.GetValue<bool?>(),
            CreatedAt = data["created_at"]?.ToString() ?? "",
            Role = data["role"]?.ToString() ?? "client",
        };
    }
}
