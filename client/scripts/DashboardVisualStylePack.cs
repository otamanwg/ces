using System;
using System.Collections.Generic;

#nullable enable

public enum DashboardArrivalVisual
{
	WaitingHall,
	TaxiRide,
	BaggageTheft,
}

public sealed record DashboardVisualStylePack(
	string Code,
	IReadOnlyDictionary<DashboardArrivalVisual, string> ArrivalAssets
);

public static class DashboardVisualStylePacks
{
	public static readonly DashboardVisualStylePack Core = new(
		DashboardVisualPalettes.Core.Code,
		new Dictionary<DashboardArrivalVisual, string>
		{
			[DashboardArrivalVisual.WaitingHall] = "res://assets/visual/core/arrival_waiting_hall_core.png",
			[DashboardArrivalVisual.TaxiRide] = "res://assets/visual/core/arrival_taxi_ride_core.png",
			[DashboardArrivalVisual.BaggageTheft] = "res://assets/visual/core/arrival_bus_station_core_v2.png",
		}
	);

	private static readonly IReadOnlyDictionary<string, DashboardVisualStylePack> Packs =
		new Dictionary<string, DashboardVisualStylePack>(StringComparer.OrdinalIgnoreCase)
		{
			[Core.Code] = Core,
			[DashboardVisualPalettes.Anime.Code] = new(DashboardVisualPalettes.Anime.Code, new Dictionary<DashboardArrivalVisual, string>()),
			[DashboardVisualPalettes.Hyperreal.Code] = new(DashboardVisualPalettes.Hyperreal.Code, new Dictionary<DashboardArrivalVisual, string>()),
			[DashboardVisualPalettes.Mafia.Code] = new(DashboardVisualPalettes.Mafia.Code, new Dictionary<DashboardArrivalVisual, string>()),
		};

	public static DashboardVisualStylePack Resolve(string? code)
	{
		string normalized = DashboardVisualPalettes.Resolve(code).Code;
		return Packs[normalized];
	}

	public static string ResolveArrivalAsset(string? styleCode, DashboardArrivalVisual visual)
	{
		var requestedPack = Resolve(styleCode);
		if (requestedPack.ArrivalAssets.TryGetValue(visual, out string? requestedPath) && !string.IsNullOrWhiteSpace(requestedPath))
		{
			return requestedPath;
		}
		return Core.ArrivalAssets[visual];
	}
}
