using System;
using System.Collections.Generic;

#nullable enable

public readonly record struct DashboardVisualColor(float Red, float Green, float Blue, float Alpha = 1.0f)
{
    public DashboardVisualColor WithAlpha(float alpha)
    {
        return this with { Alpha = Math.Clamp(alpha, 0.0f, 1.0f) };
    }
}

public sealed record DashboardVisualPalette(
    string Code,
    string DisplayName,
    DashboardVisualColor CanvasShade,
    DashboardVisualColor SurfaceDeep,
    DashboardVisualColor RoadSurface,
    DashboardVisualColor RoadLine,
    DashboardVisualColor Traffic,
    DashboardVisualColor TrafficHighlight,
    DashboardVisualColor PrimaryText,
    DashboardVisualColor SecondaryText,
    DashboardVisualColor Accent,
    DashboardVisualColor Success,
    DashboardVisualColor Warning,
    DashboardVisualColor Danger,
    DashboardVisualColor WindowLight
);

public static class DashboardVisualPalettes
{
    public static readonly DashboardVisualPalette Core = new(
        "core",
        "Core",
        new DashboardVisualColor(0.02f, 0.03f, 0.04f, 0.20f),
        new DashboardVisualColor(0.03f, 0.04f, 0.05f, 0.86f),
        new DashboardVisualColor(0.05f, 0.06f, 0.07f, 0.72f),
        new DashboardVisualColor(0.84f, 0.80f, 0.67f, 0.62f),
        new DashboardVisualColor(0.98f, 0.76f, 0.28f, 0.92f),
        new DashboardVisualColor(1.00f, 0.96f, 0.74f, 0.98f),
        new DashboardVisualColor(0.96f, 0.96f, 0.91f, 0.94f),
        new DashboardVisualColor(0.86f, 0.88f, 0.82f, 0.78f),
        new DashboardVisualColor(0.98f, 0.78f, 0.28f, 0.95f),
        new DashboardVisualColor(0.36f, 0.80f, 0.55f, 0.85f),
        new DashboardVisualColor(0.95f, 0.70f, 0.28f, 0.82f),
        new DashboardVisualColor(0.98f, 0.23f, 0.18f, 0.96f),
        new DashboardVisualColor(1.00f, 0.90f, 0.54f, 0.42f)
    );

    public static readonly DashboardVisualPalette Anime = new(
        "anime",
        "Anime",
        new DashboardVisualColor(0.72f, 0.88f, 0.96f, 0.18f),
        new DashboardVisualColor(0.12f, 0.18f, 0.27f, 0.84f),
        new DashboardVisualColor(0.16f, 0.22f, 0.30f, 0.74f),
        new DashboardVisualColor(0.86f, 0.95f, 0.96f, 0.74f),
        new DashboardVisualColor(0.98f, 0.45f, 0.48f, 0.94f),
        new DashboardVisualColor(1.00f, 0.88f, 0.56f, 1.00f),
        new DashboardVisualColor(0.98f, 0.98f, 1.00f, 0.96f),
        new DashboardVisualColor(0.78f, 0.88f, 0.94f, 0.84f),
        new DashboardVisualColor(0.24f, 0.76f, 0.84f, 0.96f),
        new DashboardVisualColor(0.34f, 0.84f, 0.58f, 0.88f),
        new DashboardVisualColor(1.00f, 0.70f, 0.27f, 0.90f),
        new DashboardVisualColor(0.96f, 0.30f, 0.42f, 0.98f),
        new DashboardVisualColor(1.00f, 0.90f, 0.62f, 0.52f)
    );

    public static readonly DashboardVisualPalette Hyperreal = new(
        "hyperreal",
        "Hyperreal",
        new DashboardVisualColor(0.01f, 0.02f, 0.025f, 0.24f),
        new DashboardVisualColor(0.025f, 0.03f, 0.035f, 0.90f),
        new DashboardVisualColor(0.06f, 0.065f, 0.07f, 0.82f),
        new DashboardVisualColor(0.78f, 0.76f, 0.68f, 0.58f),
        new DashboardVisualColor(0.92f, 0.64f, 0.20f, 0.94f),
        new DashboardVisualColor(1.00f, 0.91f, 0.66f, 0.98f),
        new DashboardVisualColor(0.93f, 0.94f, 0.92f, 0.96f),
        new DashboardVisualColor(0.72f, 0.75f, 0.72f, 0.82f),
        new DashboardVisualColor(0.86f, 0.70f, 0.30f, 0.96f),
        new DashboardVisualColor(0.30f, 0.70f, 0.48f, 0.88f),
        new DashboardVisualColor(0.92f, 0.64f, 0.20f, 0.88f),
        new DashboardVisualColor(0.88f, 0.24f, 0.18f, 0.98f),
        new DashboardVisualColor(0.96f, 0.82f, 0.52f, 0.38f)
    );

    public static readonly DashboardVisualPalette Mafia = new(
        "mafia",
        "Mafia",
        new DashboardVisualColor(0.025f, 0.025f, 0.025f, 0.28f),
        new DashboardVisualColor(0.055f, 0.05f, 0.045f, 0.90f),
        new DashboardVisualColor(0.08f, 0.075f, 0.07f, 0.84f),
        new DashboardVisualColor(0.72f, 0.60f, 0.38f, 0.66f),
        new DashboardVisualColor(0.80f, 0.58f, 0.24f, 0.94f),
        new DashboardVisualColor(0.98f, 0.86f, 0.60f, 0.98f),
        new DashboardVisualColor(0.94f, 0.90f, 0.82f, 0.96f),
        new DashboardVisualColor(0.72f, 0.68f, 0.60f, 0.82f),
        new DashboardVisualColor(0.72f, 0.52f, 0.24f, 0.96f),
        new DashboardVisualColor(0.34f, 0.66f, 0.42f, 0.88f),
        new DashboardVisualColor(0.82f, 0.62f, 0.26f, 0.88f),
        new DashboardVisualColor(0.62f, 0.10f, 0.12f, 0.98f),
        new DashboardVisualColor(0.92f, 0.72f, 0.38f, 0.42f)
    );

    public static IReadOnlyList<string> Codes { get; } = Array.AsReadOnly(
        new[] { Core.Code, Anime.Code, Hyperreal.Code, Mafia.Code }
    );

    public static DashboardVisualPalette Resolve(string? code)
    {
        return code?.Trim().ToLowerInvariant() switch
        {
            "anime" => Anime,
            "hyperreal" => Hyperreal,
            "mafia" => Mafia,
            _ => Core,
        };
    }
}
