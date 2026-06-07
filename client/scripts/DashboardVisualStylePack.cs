using System;
using System.Collections.Generic;

#nullable enable

public enum DashboardArrivalVisual
{
    WaitingHall,
    TaxiRide,
    BaggageTheft,
}

public enum DashboardArrivalPortrait
{
    None,
    Stranger,
    TaxiDriver,
}

public sealed record DashboardVisualStylePack(
    string Code,
    IReadOnlyDictionary<DashboardArrivalVisual, string> ArrivalAssets,
    IReadOnlyDictionary<DashboardArrivalPortrait, string> ArrivalPortraits
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
        },
        new Dictionary<DashboardArrivalPortrait, string>
        {
            [DashboardArrivalPortrait.Stranger] = "res://assets/visual/core/arrival_portrait_stranger_core.png",
            [DashboardArrivalPortrait.TaxiDriver] = "res://assets/visual/core/arrival_portrait_taxi_driver_core.png",
        }
    );

    private static readonly IReadOnlyDictionary<string, DashboardVisualStylePack> Packs =
        new Dictionary<string, DashboardVisualStylePack>(StringComparer.OrdinalIgnoreCase)
        {
            [Core.Code] = Core,
            [DashboardVisualPalettes.Anime.Code] = EmptyPack(DashboardVisualPalettes.Anime.Code),
            [DashboardVisualPalettes.Hyperreal.Code] = EmptyPack(DashboardVisualPalettes.Hyperreal.Code),
            [DashboardVisualPalettes.Mafia.Code] = EmptyPack(DashboardVisualPalettes.Mafia.Code),
        };

    private static DashboardVisualStylePack EmptyPack(string code)
    {
        return new DashboardVisualStylePack(
            code,
            new Dictionary<DashboardArrivalVisual, string>(),
            new Dictionary<DashboardArrivalPortrait, string>());
    }

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

    public static string ResolveArrivalPortrait(string? styleCode, DashboardArrivalPortrait portrait)
    {
        if (portrait == DashboardArrivalPortrait.None)
        {
            return "";
        }

        var requestedPack = Resolve(styleCode);
        if (requestedPack.ArrivalPortraits.TryGetValue(portrait, out string? requestedPath)
            && !string.IsNullOrWhiteSpace(requestedPath))
        {
            return requestedPath;
        }
        return Core.ArrivalPortraits[portrait];
    }
}
