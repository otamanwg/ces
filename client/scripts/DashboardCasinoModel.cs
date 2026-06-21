using System;
using System.Collections.Generic;
using System.Text.Json.Nodes;

#nullable enable

/// <summary>
/// Casino system data for the Sprint 61 Casino panel.
/// Backed by /api/player/{id}/casino-games.
/// </summary>
public sealed class DashboardCasinoModel
{
    public IReadOnlyList<DashboardCasinoBusiness> Casinos { get; init; } = Array.Empty<DashboardCasinoBusiness>();
    public IReadOnlyList<DashboardCasinoGame> Games { get; init; } = Array.Empty<DashboardCasinoGame>();

    public bool HasCasinos => Casinos.Count > 0;
    public bool HasGames => Games.Count > 0;

    public static DashboardCasinoModel FromJson(JsonNode? data)
    {
        return new DashboardCasinoModel
        {
            Casinos = ParseCasinos(data?["casinos"]?.AsArray()),
            Games = ParseGames(data?["games"]?.AsArray()),
        };
    }

    private static IReadOnlyList<DashboardCasinoBusiness> ParseCasinos(JsonArray? casinos)
    {
        if (casinos == null || casinos.Count == 0)
        {
            return Array.Empty<DashboardCasinoBusiness>();
        }

        var items = new List<DashboardCasinoBusiness>();
        foreach (var casino in casinos)
        {
            if (casino != null)
            {
                items.Add(DashboardCasinoBusiness.FromJson(casino));
            }
        }

        return items;
    }

    private static IReadOnlyList<DashboardCasinoGame> ParseGames(JsonArray? games)
    {
        if (games == null || games.Count == 0)
        {
            return Array.Empty<DashboardCasinoGame>();
        }

        var items = new List<DashboardCasinoGame>();
        foreach (var game in games)
        {
            if (game != null)
            {
                items.Add(DashboardCasinoGame.FromJson(game));
            }
        }

        return items;
    }
}

public sealed class DashboardCasinoBusiness
{
    public string Id { get; init; } = "";
    public string Name { get; init; } = "";
    public double CashBalance { get; init; }
    public double DailyRevenue { get; init; }

    public string SummaryText => $"{Name} | каса: {CashBalance:N0} ₴ | дохід: {DailyRevenue:N0} ₴/день";

    public static DashboardCasinoBusiness FromJson(JsonNode data)
    {
        return new DashboardCasinoBusiness
        {
            Id = data["id"]?.ToString() ?? "",
            Name = data["name"]?.ToString() ?? "",
            CashBalance = data["cash_balance"]?.GetValue<double>() ?? 0.0,
            DailyRevenue = data["daily_revenue"]?.GetValue<double>() ?? 0.0,
        };
    }
}

public sealed class DashboardCasinoGame
{
    public string Id { get; init; } = "";
    public string CasinoBusinessId { get; init; } = "";
    public string GameType { get; init; } = "";
    public string Status { get; init; } = "waiting";
    public double Pot { get; init; }
    public double Rake { get; init; }
    public string CreatedAt { get; init; } = "";

    public string StatusLabel => Status switch
    {
        "waiting" => "Очікує гравців",
        "in_progress" => "Триває",
        "finished" => "Завершено",
        _ => Status,
    };

    public string SummaryText => $"{GameType} | {StatusLabel} | банк: {Pot:N0} ₴";

    public static DashboardCasinoGame FromJson(JsonNode data)
    {
        return new DashboardCasinoGame
        {
            Id = data["id"]?.ToString() ?? "",
            CasinoBusinessId = data["casino_business_id"]?.ToString() ?? "",
            GameType = data["game_type"]?.ToString() ?? "",
            Status = data["status"]?.ToString() ?? "waiting",
            Pot = data["pot"]?.GetValue<double>() ?? 0.0,
            Rake = data["rake"]?.GetValue<double>() ?? 0.0,
            CreatedAt = data["created_at"]?.ToString() ?? "",
        };
    }
}
