using System;
using System.Collections.Generic;
using System.Text.Json.Nodes;

#nullable enable

/// <summary>
/// Political system data for the Sprint 61 Political panel.
/// Backed by /api/city/election, /api/player/{id}/city-office, /api/education/mayor-eligibility.
/// </summary>
public sealed class DashboardPoliticalModel
{
    public DashboardCityOffice? Office { get; init; }
    public bool IsMayor { get; init; }
    public string? MayorName { get; init; }
    public int? MayorTermStartedGameDay { get; init; }
    public DashboardElection? Election { get; init; }
    public IReadOnlyList<DashboardElectionCandidate> Candidates { get; init; } = Array.Empty<DashboardElectionCandidate>();
    public bool MayorEligible { get; init; }

    public bool HasActiveElection => Election != null && Election.Status == "active";
    public bool HasOffice => Office != null;

    public static DashboardPoliticalModel FromJson(
        JsonNode? officeData,
        JsonNode? electionData,
        JsonNode? eligibilityData)
    {
        return new DashboardPoliticalModel
        {
            Office = DashboardCityOffice.FromJson(officeData?["office"]),
            IsMayor = officeData?["is_mayor"]?.GetValue<bool>() ?? false,
            MayorName = officeData?["mayor_name"]?.ToString(),
            MayorTermStartedGameDay = officeData?["mayor_term_started_game_day"]?.GetValue<int>(),
            Election = DashboardElection.FromJson(electionData?["election"]),
            Candidates = ParseCandidates(electionData?["candidates"]?.AsArray()),
            MayorEligible = eligibilityData?["eligible"]?.GetValue<bool>() ?? false,
        };
    }

    private static IReadOnlyList<DashboardElectionCandidate> ParseCandidates(JsonArray? candidates)
    {
        if (candidates == null || candidates.Count == 0)
        {
            return Array.Empty<DashboardElectionCandidate>();
        }

        var items = new List<DashboardElectionCandidate>();
        foreach (var candidate in candidates)
        {
            if (candidate != null)
            {
                items.Add(DashboardElectionCandidate.FromJson(candidate));
            }
        }

        return items;
    }
}

public sealed class DashboardCityOffice
{
    public string Id { get; init; } = "";
    public string Position { get; init; } = "";
    public string? Department { get; init; }
    public int HiredAtGameDay { get; init; }
    public bool IsActive { get; init; }

    public string PositionLabel => Position switch
    {
        "worker" => "Працівник",
        "department_head" => "Начальник відділу",
        "deputy" => "Заступник мера",
        "mayor" => "Мер",
        _ => Position,
    };

    public string SummaryText => Department != null
        ? $"{PositionLabel} | {Department}"
        : PositionLabel;

    public static DashboardCityOffice? FromJson(JsonNode? data)
    {
        if (data == null)
        {
            return null;
        }

        return new DashboardCityOffice
        {
            Id = data["id"]?.ToString() ?? "",
            Position = data["position"]?.ToString() ?? "",
            Department = data["department"]?.ToString(),
            HiredAtGameDay = data["hired_at_game_day"]?.GetValue<int>() ?? 0,
            IsActive = data["is_active"]?.GetValue<bool>() ?? false,
        };
    }
}

public sealed class DashboardElection
{
    public string Id { get; init; } = "";
    public int StartedAtGameDay { get; init; }
    public int EndsAtGameDay { get; init; }
    public string Status { get; init; } = "active";

    public static DashboardElection? FromJson(JsonNode? data)
    {
        if (data == null)
        {
            return null;
        }

        return new DashboardElection
        {
            Id = data["id"]?.ToString() ?? "",
            StartedAtGameDay = data["started_at_game_day"]?.GetValue<int>() ?? 0,
            EndsAtGameDay = data["ends_at_game_day"]?.GetValue<int>() ?? 0,
            Status = data["status"]?.ToString() ?? "active",
        };
    }
}

public sealed class DashboardElectionCandidate
{
    public string CandidateId { get; init; } = "";
    public string PlayerId { get; init; } = "";
    public string PlayerName { get; init; } = "";
    public int Votes { get; init; }
    public string? Platform { get; init; }

    public string SummaryText => $"{PlayerName} | голосів: {Votes}";

    public static DashboardElectionCandidate FromJson(JsonNode data)
    {
        return new DashboardElectionCandidate
        {
            CandidateId = data["candidate_id"]?.ToString() ?? "",
            PlayerId = data["player_id"]?.ToString() ?? "",
            PlayerName = data["player_name"]?.ToString() ?? "",
            Votes = data["votes"]?.GetValue<int>() ?? 0,
            Platform = data["platform"]?.ToString(),
        };
    }
}
