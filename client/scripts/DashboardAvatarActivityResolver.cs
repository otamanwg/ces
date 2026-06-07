#nullable enable

public sealed record DashboardAvatarActivityState(
	AvatarActivity Activity,
	string ReasonCode
);

public static class DashboardAvatarActivityResolver
{
	public const string ArrivalConversationReason = "arrival_conversation";
	public const string HousingSearchReason = "housing_search";
	public const string LowEnergyReason = "low_energy";
	public const string NoHousingReason = "no_housing";
	public const string BusinessOperationsReason = "business_operations";
	public const string WorkCommuteReason = "work_commute";
	public const string AmbientIdleReason = "ambient_idle";

	public static DashboardAvatarActivityState Resolve(DashboardPlayerSnapshot snapshot)
	{
		if (!snapshot.Onboarding.Completed)
		{
			return snapshot.Onboarding.Stage switch
			{
				"arrival_choice" => new(AvatarActivity.Talk, ArrivalConversationReason),
				"housing_search" => new(AvatarActivity.Phone, HousingSearchReason),
				_ => new(AvatarActivity.Idle, AmbientIdleReason),
			};
		}
		if (snapshot.Energy <= 20)
		{
			return new DashboardAvatarActivityState(AvatarActivity.Sit, LowEnergyReason);
		}
		if (IsWithoutHousing(snapshot.Hostel))
		{
			return new DashboardAvatarActivityState(AvatarActivity.Phone, NoHousingReason);
		}
		if (!string.IsNullOrWhiteSpace(snapshot.OwnedBusinessId))
		{
			return new DashboardAvatarActivityState(AvatarActivity.Talk, BusinessOperationsReason);
		}
		if (snapshot.HasJob)
		{
			return new DashboardAvatarActivityState(AvatarActivity.Walk, WorkCommuteReason);
		}
		return new DashboardAvatarActivityState(AvatarActivity.Idle, AmbientIdleReason);
	}

	private static bool IsWithoutHousing(string hostel)
	{
		return string.IsNullOrWhiteSpace(hostel)
			|| hostel.Trim().Equals("Вулиця", System.StringComparison.OrdinalIgnoreCase);
	}
}
