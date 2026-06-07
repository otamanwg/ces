public enum DashboardTutorialAgeGroup
{
    Teen,
    Adult,
    Mature,
}

public static class DashboardTutorialProfile
{
    public static DashboardTutorialAgeGroup ParseAgeGroup(string value)
    {
        return value?.Trim().ToLowerInvariant() switch
        {
            "teen" => DashboardTutorialAgeGroup.Teen,
            "mature" => DashboardTutorialAgeGroup.Mature,
            _ => DashboardTutorialAgeGroup.Adult,
        };
    }

    public static string ToApiValue(DashboardTutorialAgeGroup ageGroup)
    {
        return ageGroup switch
        {
            DashboardTutorialAgeGroup.Teen => "teen",
            DashboardTutorialAgeGroup.Mature => "mature",
            _ => "adult",
        };
    }
}
