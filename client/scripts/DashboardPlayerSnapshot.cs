using System.Text.Json.Nodes;

public sealed class DashboardPlayerSnapshot
{
    public string Id { get; init; } = "";
    public string Username { get; init; } = "Гість";
    public string AuthToken { get; init; } = "";
    public DashboardTutorialAgeGroup TutorialAgeGroup { get; init; } = DashboardTutorialAgeGroup.Adult;
    public DashboardAvatarProfile Avatar { get; init; } = new();
    public double Balance { get; init; }
    public string EducationLevel { get; init; } = "High School";
    public string Job { get; init; } = "Безробітний";
    public string Hostel { get; init; } = "Вулиця";
    public string OwnedBusinessId { get; init; } = "";
    public string OwnedBusinessText { get; init; } = "Бізнес: немає";
    public string SportsText { get; init; } = "Спорт: немає";
    public int Energy { get; init; }
    public int Mood { get; init; }
    public int Hunger { get; init; }
    public JsonNode Actions { get; init; } = new JsonObject();
    public DashboardOnboardingState Onboarding { get; init; } = new();

    public bool HasJob => Job != "Безробітний";

    public static DashboardPlayerSnapshot FromJson(JsonNode data)
    {
        string ownedBusinessId = "";
        string ownedBusinessText = "Бізнес: немає";
        var businesses = data["owned_businesses"]?.AsArray();
        if (businesses != null && businesses.Count > 0)
        {
            ownedBusinessId = businesses[0]?["id"]?.ToString() ?? "";
            ownedBusinessText = $"Бізнес: {businesses[0]?["name"]}";
        }

        string sportsText = "Спорт: немає";
        var sports = data["sports_contract"];
        if (sports != null)
        {
            sportsText = $"Спорт: {sports["club"]} STR {sports["strength"]} / STA {sports["stamina"]}";
        }

        return new DashboardPlayerSnapshot
        {
            Id = data["id"]?.ToString() ?? "",
            Username = data["username"]?.ToString() ?? "Гість",
            AuthToken = data["auth_token"]?.ToString() ?? "",
            TutorialAgeGroup = DashboardTutorialProfile.ParseAgeGroup(data["tutorial_age_group"]?.ToString() ?? ""),
            Avatar = DashboardAvatarProfile.FromJson(data),
            Balance = data["balance"]?.GetValue<double>() ?? 0.0,
            EducationLevel = data["education_level"]?.ToString() ?? "High School",
            Job = data["job"]?.ToString() ?? "Безробітний",
            Hostel = data["hostel"]?.ToString() ?? "Вулиця",
            OwnedBusinessId = ownedBusinessId,
            OwnedBusinessText = ownedBusinessText,
            SportsText = sportsText,
            Energy = data["energy"]?.GetValue<int>() ?? 0,
            Mood = data["mood"]?.GetValue<int>() ?? 0,
            Hunger = data["hunger"]?.GetValue<int>() ?? 0,
            Actions = data["actions"] ?? new JsonObject(),
            Onboarding = DashboardOnboardingState.FromJson(data),
        };
    }
}
