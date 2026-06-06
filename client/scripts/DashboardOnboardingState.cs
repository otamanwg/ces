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
	public string Narrative { get; init; } = "";
	public string PoliceReportStatus { get; init; } = "not_filed";
	public string PoliceStatusText { get; init; } = "";
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
		string policeStatus = onboarding["police_report_status"]?.ToString() ?? "not_filed";

		return new DashboardOnboardingState
		{
			Stage = onboarding["stage"]?.ToString() ?? "completed",
			Completed = onboarding["completed"]?.GetValue<bool>() ?? true,
			Title = onboarding["title"]?.ToString() ?? "Прибуття завершено",
			Narrative = onboarding["narrative"]?.ToString() ?? "",
			PoliceReportStatus = policeStatus,
			PoliceStatusText = BuildPoliceStatusText(policeStatus),
			CanReportToPolice = choices.Contains(ReportToPoliceChoice),
			CanFindHousing = choices.Contains(FindHousingChoice),
		};
	}

	private static string BuildPoliceStatusText(string status)
	{
		return status switch
		{
			"pending" => "Поліція розслідує справу. Результат надійде окремо.",
			"closed_no_recovery" => "Заяву зареєстровано, але швидких зачіпок немає.",
			"recovered" => "Поліція вже повернула частину втрачених коштів.",
			_ => "",
		};
	}
}
