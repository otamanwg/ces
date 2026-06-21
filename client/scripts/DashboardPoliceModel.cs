using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;

#nullable enable

/// <summary>
/// Police officer status and records for the Sprint 61 Police panel.
/// Backed by /api/police/officer, /api/player/{id}/police-records, /api/police/corruption-log.
/// </summary>
public sealed class DashboardPoliceModel
{
    public DashboardPoliceOfficer? Officer { get; init; }
    public IReadOnlyList<DashboardPoliceRecord> Records { get; init; } = Array.Empty<DashboardPoliceRecord>();
    public IReadOnlyList<DashboardCorruptionLogItem> CorruptionLogs { get; init; } = Array.Empty<DashboardCorruptionLogItem>();

    public bool IsOfficer => Officer != null;
    public bool CanPatrol => Officer != null && Officer.IsActive && Officer.Rank is "patrol" or "detective" or "chief";
    public bool CanArrest => Officer != null && Officer.Rank is "detective" or "chief";
    public bool CanViewCorruptionLog => Officer != null && Officer.Rank is "detective" or "chief";
    public bool CanConfiscate => Officer != null && Officer.Rank == "chief";
    public bool CanPromote => Officer != null && Officer.Rank == "patrol" && Officer.SuccessfulInvestigations >= 5;

    public static DashboardPoliceModel FromJson(
        JsonNode? officerData,
        JsonNode? recordsData,
        JsonNode? corruptionLogData)
    {
        return new DashboardPoliceModel
        {
            Officer = DashboardPoliceOfficer.FromJson(officerData?["officer"]),
            Records = ParseRecords(recordsData?["records"]?.AsArray()),
            CorruptionLogs = ParseCorruptionLogs(corruptionLogData?["logs"]?.AsArray()),
        };
    }

    private static IReadOnlyList<DashboardPoliceRecord> ParseRecords(JsonArray? records)
    {
        if (records == null || records.Count == 0)
        {
            return Array.Empty<DashboardPoliceRecord>();
        }

        var items = new List<DashboardPoliceRecord>();
        foreach (var record in records)
        {
            if (record != null)
            {
                items.Add(DashboardPoliceRecord.FromJson(record));
            }
        }

        return items;
    }

    private static IReadOnlyList<DashboardCorruptionLogItem> ParseCorruptionLogs(JsonArray? logs)
    {
        if (logs == null || logs.Count == 0)
        {
            return Array.Empty<DashboardCorruptionLogItem>();
        }

        var items = new List<DashboardCorruptionLogItem>();
        foreach (var log in logs)
        {
            if (log != null)
            {
                items.Add(DashboardCorruptionLogItem.FromJson(log));
            }
        }

        return items;
    }
}

public sealed class DashboardPoliceOfficer
{
    public string Id { get; init; } = "";
    public string Rank { get; init; } = "patrol";
    public int SuccessfulInvestigations { get; init; }
    public int BribesTaken { get; init; }
    public bool IsActive { get; init; }
    public int HiredAtGameDay { get; init; }
    public int? PromotedAtGameDay { get; init; }
    public string? PatrolDistrictId { get; init; }

    public string RankLabel => Rank switch
    {
        "patrol" => "Патрульний",
        "detective" => "Детектив",
        "chief" => "Начальник",
        _ => Rank,
    };

    public string SummaryText => $"{RankLabel} | розслідувань: {SuccessfulInvestigations} | хабарів: {BribesTaken}";

    public static DashboardPoliceOfficer? FromJson(JsonNode? data)
    {
        if (data == null)
        {
            return null;
        }

        return new DashboardPoliceOfficer
        {
            Id = data["id"]?.ToString() ?? "",
            Rank = data["rank"]?.ToString() ?? "patrol",
            SuccessfulInvestigations = data["successful_investigations"]?.GetValue<int>() ?? 0,
            BribesTaken = data["bribes_taken"]?.GetValue<int>() ?? 0,
            IsActive = data["is_active"]?.GetValue<bool>() ?? false,
            HiredAtGameDay = data["hired_at_game_day"]?.GetValue<int>() ?? 0,
            PromotedAtGameDay = data["promoted_at_game_day"]?.GetValue<int>(),
            PatrolDistrictId = data["patrol_district_id"]?.ToString(),
        };
    }
}

public sealed class DashboardPoliceRecord
{
    public string Id { get; init; } = "";
    public string OffenseType { get; init; } = "";
    public double? FineAmount { get; init; }
    public string Status { get; init; } = "";
    public string CreatedAt { get; init; } = "";

    public string OffenseLabel => OffenseType switch
    {
        "fake_diploma" => "Фейковий диплом",
        "tax_evasion" => "Ухилення від податків",
        "minor_offense" => "Дрібне правопорушення",
        "arrest" => "Арешт",
        "arrival_baggage_theft" => "Крадіжка багажу",
        _ => OffenseType,
    };

    public string SummaryText => $"{OffenseLabel} | {Status}{(FineAmount > 0 ? $" | штраф {FineAmount:N0} ₴" : "")}";

    public static DashboardPoliceRecord FromJson(JsonNode data)
    {
        return new DashboardPoliceRecord
        {
            Id = data["id"]?.ToString() ?? "",
            OffenseType = data["offense_type"]?.ToString() ?? "",
            FineAmount = data["fine_amount"]?.GetValue<double>(),
            Status = data["status"]?.ToString() ?? "",
            CreatedAt = data["created_at"]?.ToString() ?? "",
        };
    }
}

public sealed class DashboardCorruptionLogItem
{
    public string Id { get; init; } = "";
    public string IncidentType { get; init; } = "";
    public double EvidenceStrength { get; init; }
    public bool IsInvestigated { get; init; }
    public bool IsProven { get; init; }

    public string IncidentLabel => IncidentType switch
    {
        "police_bribe" => "Хабар поліції",
        "minor_bribe" => "Дрібний хабар",
        "vote_bribe" => "Підкуп голосів",
        "blackmail" => "Шантаж",
        "judge_bribe" => "Хабар судді",
        "election_fraud" => "Виборче шахрайство",
        _ => IncidentType,
    };

    public string SummaryText => $"{IncidentLabel} | докази: {EvidenceStrength:P0}";

    public static DashboardCorruptionLogItem FromJson(JsonNode data)
    {
        return new DashboardCorruptionLogItem
        {
            Id = data["id"]?.ToString() ?? "",
            IncidentType = data["incident_type"]?.ToString() ?? "",
            EvidenceStrength = data["evidence_strength"]?.GetValue<double>() ?? 0.0,
            IsInvestigated = data["is_investigated"]?.GetValue<bool>() ?? false,
            IsProven = data["is_proven"]?.GetValue<bool>() ?? false,
        };
    }
}
