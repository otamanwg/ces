using System;
using System.Linq;
using System.Text.Json.Nodes;

public sealed class DashboardOnboardingState
{
    public const string ReportToPoliceChoice = "report_to_police";
    public const string FindHousingChoice = "find_housing";

    public string Stage { get; init; } = "completed";
    public bool Completed { get; init; } = true;
    public string Title { get; init; } = "Прибуття завершено";
    public string TitleKey { get; init; } = "ONBOARDING_COMPLETED_TITLE";
    public string Narrative { get; init; } = "";
    public string NarrativeKey { get; init; } = "ONBOARDING_COMPLETED_NARRATIVE";
    public string PoliceReportStatus { get; init; } = "not_filed";
    public string PoliceStatusKey { get; init; } = "";
    public double PoliceRecoveryAmount { get; init; }
    public bool PoliceRecoveryClaimable { get; init; }
    public bool CanReportToPolice { get; init; }
    public bool CanFindHousing { get; init; }

    public static DashboardOnboardingState FromJson(JsonNode data)
    {
        var onboarding = data?["onboarding"];
        if (onboarding == null)
        {
            return new DashboardOnboardingState();
        }

        var choices = onboarding["available_choices"]?.AsArray()
            .Select(choice => choice?.ToString() ?? "")
            .Where(choice => !string.IsNullOrWhiteSpace(choice))
            .ToArray() ?? Array.Empty<string>();
        string stage = onboarding["stage"]?.ToString() ?? "completed";
        string policeStatus = onboarding["police_report_status"]?.ToString() ?? "not_filed";

        return new DashboardOnboardingState
        {
            Stage = stage,
            Completed = onboarding["completed"]?.GetValue<bool>() ?? true,
            Title = onboarding["title"]?.ToString() ?? "Прибуття завершено",
            TitleKey = BuildStageKey(stage, "TITLE"),
            Narrative = onboarding["narrative"]?.ToString() ?? "",
            NarrativeKey = BuildStageKey(stage, "NARRATIVE"),
            PoliceReportStatus = policeStatus,
            PoliceStatusKey = BuildPoliceStatusKey(policeStatus),
            PoliceRecoveryAmount = onboarding["police_recovery_amount"]?.GetValue<double>() ?? 0.0,
            PoliceRecoveryClaimable = onboarding["police_recovery_claimable"]?.GetValue<bool>() ?? false,
            CanReportToPolice = choices.Contains(ReportToPoliceChoice),
            CanFindHousing = choices.Contains(FindHousingChoice),
        };
    }

    private static string BuildStageKey(string stage, string suffix)
    {
        string prefix = stage switch
        {
            "arrival_choice" => "ONBOARDING_ARRIVAL_CHOICE",
            "housing_search" => "ONBOARDING_HOUSING_SEARCH",
            "completed" => "ONBOARDING_COMPLETED",
            _ => "",
        };
        return string.IsNullOrEmpty(prefix) ? "" : $"{prefix}_{suffix}";
    }

    private static string BuildPoliceStatusKey(string status)
    {
        return status switch
        {
            "pending" => "ONBOARDING_POLICE_PENDING",
            "closed_no_recovery" => "ONBOARDING_POLICE_CLOSED",
            "recovered" => "ONBOARDING_POLICE_RECOVERED",
            _ => "",
        };
    }
}
