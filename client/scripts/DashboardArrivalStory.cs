public sealed record DashboardArrivalBeat(
	string TitleKey,
	string NarrativeKey,
	DashboardArrivalVisual Visual
);

public static class DashboardArrivalStory
{
	private static readonly DashboardArrivalBeat[] Beats =
	{
		new(
			"ARRIVAL_BEAT_1_TITLE",
			"ARRIVAL_BEAT_1_NARRATIVE",
			DashboardArrivalVisual.WaitingHall),
		new(
			"ARRIVAL_BEAT_2_TITLE",
			"ARRIVAL_BEAT_2_NARRATIVE",
			DashboardArrivalVisual.WaitingHall),
		new(
			"ARRIVAL_BEAT_3_TITLE",
			"ARRIVAL_BEAT_3_NARRATIVE",
			DashboardArrivalVisual.TaxiRide),
	};

	public static int Count => Beats.Length;

	public static DashboardArrivalBeat Get(int index)
	{
		return Beats[index];
	}
}
