public sealed record DashboardArrivalBeat(
	string Title,
	string Narrative,
	DashboardArrivalVisual Visual
);

public static class DashboardArrivalStory
{
	private static readonly DashboardArrivalBeat[] Beats =
	{
		new(
			"Новий маршрут",
			"У залі очікування автовокзалу випадковий співрозмовник помічає ваш квиток. "
			+ "Ви кажете, що їдете починати нове життя у місті, де нікого не знаєте.",
			DashboardArrivalVisual.WaitingHall),
		new(
			"Місто живе без пауз",
			"«Не поспішайте», — відповідає він. «Тут усе росте поступово: робота, зв'язки, "
			+ "власна справа і вплив. Місто житиме навіть тоді, коли ви вийдете з гри».",
			DashboardArrivalVisual.WaitingHall),
		new(
			"Перші хвилини",
			"Автобус прибуває надвечір. Ви ловите таксі біля вокзалу, кладете багаж у машину "
			+ "і називаєте адресу. За кілька кварталів водій раптом зупиняється.",
			DashboardArrivalVisual.TaxiRide),
	};

	public static int Count => Beats.Length;

	public static DashboardArrivalBeat Get(int index)
	{
		return Beats[index];
	}
}
