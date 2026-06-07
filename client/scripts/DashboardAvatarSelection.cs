using System;
using System.Collections.Generic;

#nullable enable

public sealed record DashboardAvatarSelection(
	string BodyPresetCode,
	string FacePresetCode,
	string SkinToneCode,
	string HairStyleCode,
	string HairColorCode
)
{
	public static IReadOnlyList<string> BodyPresetCodes { get; } =
		Array.AsReadOnly(new[] { "body_standard", "body_sturdy" });

	public static IReadOnlyList<string> FacePresetCodes { get; } =
		Array.AsReadOnly(CreateFacePresetCodes());

	public static IReadOnlyList<string> SkinToneCodes { get; } =
		Array.AsReadOnly(new[] { "skin_01", "skin_02", "skin_03", "skin_04", "skin_05", "skin_06" });

	public static IReadOnlyList<string> HairStyleCodes { get; } =
		Array.AsReadOnly(
			new[]
			{
				"hair_short_01",
				"hair_short_02",
				"hair_medium_01",
				"hair_medium_02",
				"hair_long_01",
				"hair_long_02",
				"hair_buzz_01",
				"hair_bald",
			}
		);

	public static IReadOnlyList<string> HairColorCodes { get; } =
		Array.AsReadOnly(
			new[]
			{
				"hair_black",
				"hair_brown",
				"hair_blond",
				"hair_auburn",
				"hair_gray",
				"hair_white",
			}
		);

	public static DashboardAvatarSelection Default { get; } = new(
		"body_standard",
		"face_01",
		"skin_03",
		"hair_short_01",
		"hair_brown"
	);

	public DashboardAvatarSelection CycleBody(int step) =>
		this with { BodyPresetCode = Cycle(BodyPresetCodes, BodyPresetCode, step) };

	public DashboardAvatarSelection CycleFace(int step) =>
		this with { FacePresetCode = Cycle(FacePresetCodes, FacePresetCode, step) };

	public DashboardAvatarSelection CycleSkin(int step) =>
		this with { SkinToneCode = Cycle(SkinToneCodes, SkinToneCode, step) };

	public DashboardAvatarSelection CycleHairStyle(int step) =>
		this with { HairStyleCode = Cycle(HairStyleCodes, HairStyleCode, step) };

	public DashboardAvatarSelection CycleHairColor(int step) =>
		this with { HairColorCode = Cycle(HairColorCodes, HairColorCode, step) };

	public DashboardAvatarProfile ToProfile()
	{
		return new DashboardAvatarProfile
		{
			BodyPresetCode = BodyPresetCode,
			FacePresetCode = FacePresetCode,
			SkinToneCode = SkinToneCode,
			HairStyleCode = HairStyleCode,
			HairColorCode = HairColorCode,
		};
	}

	public IReadOnlyDictionary<string, string> ToApiPayload()
	{
		return new Dictionary<string, string>
		{
			["body_preset_code"] = BodyPresetCode,
			["face_preset_code"] = FacePresetCode,
			["skin_tone_code"] = SkinToneCode,
			["hair_style_code"] = HairStyleCode,
			["hair_color_code"] = HairColorCode,
		};
	}

	public static int PositionOf(IReadOnlyList<string> codes, string code)
	{
		for (int index = 0; index < codes.Count; index++)
		{
			if (codes[index] == code)
			{
				return index + 1;
			}
		}
		return 1;
	}

	private static string Cycle(IReadOnlyList<string> codes, string current, int step)
	{
		int index = 0;
		for (int candidate = 0; candidate < codes.Count; candidate++)
		{
			if (codes[candidate] == current)
			{
				index = candidate;
				break;
			}
		}
		int next = ((index + step) % codes.Count + codes.Count) % codes.Count;
		return codes[next];
	}

	private static string[] CreateFacePresetCodes()
	{
		var codes = new string[20];
		for (int index = 0; index < codes.Length; index++)
		{
			codes[index] = $"face_{index + 1:00}";
		}
		return codes;
	}
}
