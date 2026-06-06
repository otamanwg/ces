public static class DashboardCharacterCreation
{
	public const int UsernameMinLength = 2;
	public const int UsernameMaxLength = 24;
	public const string DefaultAgeGroup = "adult";
	public const string InvalidUsernameKey = "CHARACTER_ERROR_NAME_LENGTH";

	public static string NormalizeUsername(string username)
	{
		return username?.Trim() ?? "";
	}

	public static string ValidateUsername(string username)
	{
		int length = NormalizeUsername(username).Length;
		return length >= UsernameMinLength && length <= UsernameMaxLength
			? ""
			: InvalidUsernameKey;
	}

	public static string NormalizeAgeGroup(string ageGroup)
	{
		return DashboardTutorialProfile.ToApiValue(
			DashboardTutorialProfile.ParseAgeGroup(ageGroup));
	}
}
