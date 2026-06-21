using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;

#nullable enable

/// <summary>
/// Court cases and prison sentence for the Sprint 61 Court/Prison panel.
/// Backed by /api/player/{id}/court-cases, /api/prison/sentence.
/// </summary>
public sealed class DashboardCourtModel
{
    public IReadOnlyList<DashboardCourtCase> Cases { get; init; } = Array.Empty<DashboardCourtCase>();
    public DashboardPrisonSentence? Sentence { get; init; }

    public bool HasCases => Cases.Count > 0;
    public bool IsImprisoned => Sentence != null && Sentence.Status == "serving";

    public static DashboardCourtModel FromJson(JsonNode? casesData, JsonNode? sentenceData)
    {
        return new DashboardCourtModel
        {
            Cases = ParseCases(casesData?["cases"]?.AsArray()),
            Sentence = DashboardPrisonSentence.FromJson(sentenceData?["sentence"]),
        };
    }

    private static IReadOnlyList<DashboardCourtCase> ParseCases(JsonArray? cases)
    {
        if (cases == null || cases.Count == 0)
        {
            return Array.Empty<DashboardCourtCase>();
        }

        var items = new List<DashboardCourtCase>();
        foreach (var courtCase in cases)
        {
            if (courtCase != null)
            {
                items.Add(DashboardCourtCase.FromJson(courtCase));
            }
        }

        return items;
    }
}

public sealed class DashboardCourtCase
{
    public string Id { get; init; } = "";
    public string Verdict { get; init; } = "";
    public bool IsAppealed { get; init; }
    public string? AppealDeadline { get; init; }
    public string? Judge1Vote { get; init; }
    public string? Judge2Vote { get; init; }
    public string? Judge3Vote { get; init; }
    public bool Judge1Bribed { get; init; }
    public bool Judge2Bribed { get; init; }
    public bool Judge3Bribed { get; init; }
    public string? FinalVerdict { get; init; }
    public string CreatedAt { get; init; } = "";

    public string VerdictLabel => Verdict switch
    {
        "fine" => "Штраф",
        "license_revoked" => "Ліцензію анульовано",
        "candidacy_revoked" => "Кандидатуру анульовано",
        "mandate_revoked" => "Мандат анульовано",
        "criminal_case" => "Кримінальна справа",
        "acquitted" => "Оправдано",
        _ => Verdict,
    };

    public string SummaryText => $"{VerdictLabel}{(IsAppealed ? " | апеляція" : "")}{(FinalVerdict != null ? $" | фінал: {FinalVerdict}" : "")}";

    public static DashboardCourtCase FromJson(JsonNode data)
    {
        return new DashboardCourtCase
        {
            Id = data["id"]?.ToString() ?? "",
            Verdict = data["verdict"]?.ToString() ?? "",
            IsAppealed = data["is_appealed"]?.GetValue<bool>() ?? false,
            AppealDeadline = data["appeal_deadline"]?.ToString(),
            Judge1Vote = data["judge_1_vote"]?.ToString(),
            Judge2Vote = data["judge_2_vote"]?.ToString(),
            Judge3Vote = data["judge_3_vote"]?.ToString(),
            Judge1Bribed = data["judge_1_bribed"]?.GetValue<bool>() ?? false,
            Judge2Bribed = data["judge_2_bribed"]?.GetValue<bool>() ?? false,
            Judge3Bribed = data["judge_3_bribed"]?.GetValue<bool>() ?? false,
            FinalVerdict = data["final_verdict"]?.ToString(),
            CreatedAt = data["created_at"]?.ToString() ?? "",
        };
    }
}

public sealed class DashboardPrisonSentence
{
    public string Id { get; init; } = "";
    public int DaysTotal { get; init; }
    public int DaysServed { get; init; }
    public int DaysRemaining { get; init; }
    public string Status { get; init; } = "serving";
    public string BusinessImpact { get; init; } = "none";

    public string SummaryText => $"Термін: {DaysRemaining}/{DaysTotal} днів | {Status}";
    public double ProgressPct => DaysTotal > 0 ? (double)DaysServed / DaysTotal : 0.0;

    public static DashboardPrisonSentence? FromJson(JsonNode? data)
    {
        if (data == null)
        {
            return null;
        }

        return new DashboardPrisonSentence
        {
            Id = data["id"]?.ToString() ?? "",
            DaysTotal = data["days_total"]?.GetValue<int>() ?? 0,
            DaysServed = data["days_served"]?.GetValue<int>() ?? 0,
            DaysRemaining = data["days_remaining"]?.GetValue<int>() ?? 0,
            Status = data["status"]?.ToString() ?? "serving",
            BusinessImpact = data["business_impact"]?.ToString() ?? "none",
        };
    }
}
