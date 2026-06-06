public enum DashboardPortraitSide
{
	Left,
	Right,
}

public sealed record DashboardArrivalBeat(
	string TitleKey,
	string NarrativeKey,
	DashboardArrivalVisual Visual,
	DashboardArrivalPortrait Portrait,
	DashboardPortraitSide PortraitSide
);

public static class DashboardArrivalStory
{
	private static readonly DashboardArrivalBeat[] Beats =
	{
		new(
			"ARRIVAL_BEAT_1_TITLE",
			"ARRIVAL_BEAT_1_NARRATIVE",
			DashboardArrivalVisual.WaitingHall,
			DashboardArrivalPortrait.Stranger,
			DashboardPortraitSide.Right),
		new(
			"ARRIVAL_BEAT_2_TITLE",
			"ARRIVAL_BEAT_2_ADULT_NARRATIVE",
			DashboardArrivalVisual.WaitingHall,
			DashboardArrivalPortrait.Stranger,
			DashboardPortraitSide.Right),
		new(
			"ARRIVAL_BEAT_3_TITLE",
			"ARRIVAL_BEAT_3_NARRATIVE",
			DashboardArrivalVisual.TaxiRide,
			DashboardArrivalPortrait.TaxiDriver,
			DashboardPortraitSide.Right),
	};

	public static int Count => Beats.Length;

	public static DashboardArrivalBeat Get(
		int index,
		DashboardTutorialAgeGroup ageGroup = DashboardTutorialAgeGroup.Adult)
	{
		var beat = Beats[index];
		if (index != 1)
		{
			return beat;
		}

		string narrativeKey = ageGroup switch
		{
			DashboardTutorialAgeGroup.Teen => "ARRIVAL_BEAT_2_TEEN_NARRATIVE",
			DashboardTutorialAgeGroup.Mature => "ARRIVAL_BEAT_2_MATURE_NARRATIVE",
			_ => "ARRIVAL_BEAT_2_ADULT_NARRATIVE",
		};
		return beat with { NarrativeKey = narrativeKey };
	}
}
