public static class DashboardLocaleProfile
{
    public const string Ukrainian = "uk";
    public const string English = "en";
    public const string Default = Ukrainian;

    public static string Normalize(string localeCode)
    {
        return localeCode?.Trim().ToLowerInvariant() switch
        {
            English => English,
            Ukrainian => Ukrainian,
            _ => Default,
        };
    }
}
