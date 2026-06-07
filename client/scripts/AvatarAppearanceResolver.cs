using System;
using System.Collections.Generic;

#nullable enable

public readonly record struct AvatarColorToken(float Red, float Green, float Blue);

public sealed record AvatarFaceShape(
    int PresetIndex,
    float HeadWidthScale,
    float HeadHeightScale,
    float EyeSpacingScale,
    float EyeScale,
    float EyeHeightOffset,
    float MouthWidthScale
);

public sealed record AvatarAppearance(
    string BodyPresetCode,
    AvatarFaceShape Face,
    string SkinToneCode,
    AvatarColorToken SkinColor,
    string HairStyleCode,
    AvatarColorToken HairColor,
    IReadOnlyList<string> VisibleHairGroups,
    float TorsoWidthScale,
    float LimbWidthScale,
    AvatarColorToken UpperColor,
    AvatarColorToken LowerColor,
    AvatarColorToken FootwearColor
);

public static class AvatarAppearanceResolver
{
    private static readonly HashSet<string> BodyPresetCodes = new(StringComparer.Ordinal)
    {
        "body_standard",
        "body_sturdy",
    };

    private static readonly Dictionary<string, AvatarColorToken> SkinColors = new(StringComparer.Ordinal)
    {
        ["skin_01"] = new(0.98f, 0.82f, 0.70f),
        ["skin_02"] = new(0.94f, 0.72f, 0.58f),
        ["skin_03"] = new(0.90f, 0.62f, 0.48f),
        ["skin_04"] = new(0.72f, 0.43f, 0.30f),
        ["skin_05"] = new(0.50f, 0.28f, 0.19f),
        ["skin_06"] = new(0.30f, 0.16f, 0.12f),
    };

    private static readonly Dictionary<string, AvatarColorToken> HairColors = new(StringComparer.Ordinal)
    {
        ["hair_black"] = new(0.035f, 0.045f, 0.065f),
        ["hair_brown"] = new(0.19f, 0.10f, 0.065f),
        ["hair_blond"] = new(0.88f, 0.66f, 0.28f),
        ["hair_auburn"] = new(0.54f, 0.16f, 0.08f),
        ["hair_gray"] = new(0.38f, 0.42f, 0.48f),
        ["hair_white"] = new(0.84f, 0.88f, 0.92f),
    };

    private static readonly Dictionary<string, string[]> HairGroups = new(StringComparer.Ordinal)
    {
        ["hair_short_01"] = new[] { "HairShort01" },
        ["hair_short_02"] = new[] { "HairShort02" },
        ["hair_medium_01"] = new[] { "HairMedium01" },
        ["hair_medium_02"] = new[] { "HairMedium02" },
        ["hair_long_01"] = new[] { "HairLong01" },
        ["hair_long_02"] = new[] { "HairLong02" },
        ["hair_buzz_01"] = new[] { "HairBuzz01" },
        ["hair_bald"] = Array.Empty<string>(),
    };

    public static AvatarAppearance Resolve(DashboardAvatarProfile? profile)
    {
        profile ??= new DashboardAvatarProfile();
        string bodyCode = BodyPresetCodes.Contains(profile.BodyPresetCode)
            ? profile.BodyPresetCode
            : "body_standard";
        string skinCode = SkinColors.ContainsKey(profile.SkinToneCode)
            ? profile.SkinToneCode
            : "skin_03";
        string hairStyleCode = HairGroups.ContainsKey(profile.HairStyleCode)
            ? profile.HairStyleCode
            : "hair_short_01";
        string hairColorCode = HairColors.ContainsKey(profile.HairColorCode)
            ? profile.HairColorCode
            : "hair_brown";
        int faceIndex = ParseFaceIndex(profile.FacePresetCode);
        bool sturdy = bodyCode == "body_sturdy";

        return new AvatarAppearance(
            bodyCode,
            BuildFaceShape(faceIndex),
            skinCode,
            SkinColors[skinCode],
            hairStyleCode,
            HairColors[hairColorCode],
            HairGroups[hairStyleCode],
            sturdy ? 1.14f : 1.0f,
            sturdy ? 1.10f : 1.0f,
            new AvatarColorToken(0.05f, 0.62f, 0.70f),
            new AvatarColorToken(0.035f, 0.08f, 0.16f),
            new AvatarColorToken(0.92f, 0.22f, 0.29f)
        );
    }

    private static int ParseFaceIndex(string? code)
    {
        if (code != null
            && code.StartsWith("face_", StringComparison.Ordinal)
            && int.TryParse(code.AsSpan("face_".Length), out int value)
            && value is >= 1 and <= 20)
        {
            return value;
        }
        return 1;
    }

    private static AvatarFaceShape BuildFaceShape(int presetIndex)
    {
        int zeroBased = presetIndex - 1;
        int row = zeroBased / 5;
        int column = zeroBased % 5;
        return new AvatarFaceShape(
            presetIndex,
            0.92f + column * 0.04f,
            0.95f + row * 0.035f,
            0.91f + (zeroBased % 4) * 0.055f,
            0.90f + ((zeroBased * 3) % 5) * 0.04f,
            -0.012f + ((zeroBased * 7) % 5) * 0.006f,
            0.88f + ((zeroBased * 2) % 5) * 0.05f
        );
    }
}
