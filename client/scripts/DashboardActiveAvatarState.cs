#nullable enable

public sealed record DashboardActiveAvatarState(
	string Username,
	DashboardAvatarProfile Profile,
	DashboardAvatarActivityState Activity
)
{
	public static DashboardActiveAvatarState Empty { get; } =
		new(
			"Гість",
			new DashboardAvatarProfile(),
			new DashboardAvatarActivityState(AvatarActivity.Idle, DashboardAvatarActivityResolver.AmbientIdleReason)
		);

	public string IdentityText =>
		$"{Username} | face {FaceNumber:00} | fashion {Profile.FashionScore}";

	public int FaceNumber => AvatarAppearanceResolver.Resolve(Profile).Face.PresetIndex;

	public bool HasPlayerIdentity =>
		!string.IsNullOrWhiteSpace(Username)
		&& Username != "Гість";

	public static DashboardActiveAvatarState FromSnapshot(DashboardPlayerSnapshot snapshot)
	{
		return new DashboardActiveAvatarState(
			snapshot.Username,
			snapshot.Avatar,
			DashboardAvatarActivityResolver.Resolve(snapshot)
		);
	}

	public bool ShowsFullAvatar(bool streetFocus)
	{
		return HasPlayerIdentity && streetFocus;
	}
}
