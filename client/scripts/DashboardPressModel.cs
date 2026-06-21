using System;
using System.Collections.Generic;
using System.Text.Json.Nodes;

#nullable enable

/// <summary>
/// Press/media system data for the Sprint 61 Press panel.
/// Backed by /api/player/{id}/press-investigations, /api/player/{id}/press-blackmails.
/// </summary>
public sealed class DashboardPressModel
{
    public IReadOnlyList<DashboardPressInvestigation> Investigations { get; init; } = Array.Empty<DashboardPressInvestigation>();
    public IReadOnlyList<DashboardPressBlackmail> Blackmails { get; init; } = Array.Empty<DashboardPressBlackmail>();

    public bool HasInvestigations => Investigations.Count > 0;
    public bool HasBlackmails => Blackmails.Count > 0;
    public bool HasPendingBlackmails => Blackmails.Count > 0 && Blackmails[0].Status == "pending";

    public static DashboardPressModel FromJson(JsonNode? investigationsData, JsonNode? blackmailsData)
    {
        return new DashboardPressModel
        {
            Investigations = ParseInvestigations(investigationsData?["investigations"]?.AsArray()),
            Blackmails = ParseBlackmails(blackmailsData?["blackmails"]?.AsArray()),
        };
    }

    private static IReadOnlyList<DashboardPressInvestigation> ParseInvestigations(JsonArray? investigations)
    {
        if (investigations == null || investigations.Count == 0)
        {
            return Array.Empty<DashboardPressInvestigation>();
        }

        var items = new List<DashboardPressInvestigation>();
        foreach (var investigation in investigations)
        {
            if (investigation != null)
            {
                items.Add(DashboardPressInvestigation.FromJson(investigation));
            }
        }

        return items;
    }

    private static IReadOnlyList<DashboardPressBlackmail> ParseBlackmails(JsonArray? blackmails)
    {
        if (blackmails == null || blackmails.Count == 0)
        {
            return Array.Empty<DashboardPressBlackmail>();
        }

        var items = new List<DashboardPressBlackmail>();
        foreach (var blackmail in blackmails)
        {
            if (blackmail != null)
            {
                items.Add(DashboardPressBlackmail.FromJson(blackmail));
            }
        }

        return items;
    }
}

public sealed class DashboardPressInvestigation
{
    public string Id { get; init; } = "";
    public string TargetPlayerId { get; init; } = "";
    public string IncidentType { get; init; } = "";
    public double PressEvidence { get; init; }
    public bool IsPublished { get; init; }
    public string? ArticleTitle { get; init; }
    public string Scale { get; init; } = "local";
    public int HappinessImpact { get; init; }
    public int ReputationImpact { get; init; }
    public string CreatedAt { get; init; } = "";

    public bool CanPublish => PressEvidence >= 0.7 && !IsPublished;
    public bool CanBlackmail => PressEvidence >= 0.7 && !IsPublished;

    public string SummaryText => IsPublished
        ? $"Опубліковано: {ArticleTitle ?? "Скандал"} | щастя {HappinessImpact} | реп {ReputationImpact}"
        : $"Розслідування | докази: {PressEvidence:P0}{(CanPublish ? " | готово" : "")}";

    public static DashboardPressInvestigation FromJson(JsonNode data)
    {
        return new DashboardPressInvestigation
        {
            Id = data["id"]?.ToString() ?? "",
            TargetPlayerId = data["target_player_id"]?.ToString() ?? "",
            IncidentType = data["incident_type"]?.ToString() ?? "",
            PressEvidence = data["press_evidence"]?.GetValue<double>() ?? 0.0,
            IsPublished = data["is_published"]?.GetValue<bool>() ?? false,
            ArticleTitle = data["article_title"]?.ToString(),
            Scale = data["scale"]?.ToString() ?? "local",
            HappinessImpact = data["happiness_impact"]?.GetValue<int>() ?? 0,
            ReputationImpact = data["reputation_impact"]?.GetValue<int>() ?? 0,
            CreatedAt = data["created_at"]?.ToString() ?? "",
        };
    }
}

public sealed class DashboardPressBlackmail
{
    public string Id { get; init; } = "";
    public string JournalistId { get; init; } = "";
    public double AmountDemanded { get; init; }
    public string Status { get; init; } = "pending";
    public string CreatedAt { get; init; } = "";
    public string? ResolvedAt { get; init; }

    public string StatusLabel => Status switch
    {
        "pending" => "Очікує",
        "accepted" => "Прийнято",
        "refused" => "Відхилено",
        "reported_to_police" => "Повідомлено поліцію",
        _ => Status,
    };

    public string SummaryText => $"{StatusLabel} | сума: {AmountDemanded:N0} ₴";

    public static DashboardPressBlackmail FromJson(JsonNode data)
    {
        return new DashboardPressBlackmail
        {
            Id = data["id"]?.ToString() ?? "",
            JournalistId = data["journalist_id"]?.ToString() ?? "",
            AmountDemanded = data["amount_demanded"]?.GetValue<double>() ?? 0.0,
            Status = data["status"]?.ToString() ?? "pending",
            CreatedAt = data["created_at"]?.ToString() ?? "",
            ResolvedAt = data["resolved_at"]?.ToString(),
        };
    }
}
