using System;
using System.Collections.Generic;

#nullable enable

public enum AvatarActivity
{
	Idle,
	Walk,
	Sit,
	Phone,
	Talk,
}

public enum AvatarLodLevel
{
	Cinematic,
	Street,
	Distance,
	Marker,
}

public static class AvatarPresentationRules
{
	public static IReadOnlyList<AvatarActivity> ActivitySequence { get; } = Array.AsReadOnly(
		new[]
		{
			AvatarActivity.Idle,
			AvatarActivity.Walk,
			AvatarActivity.Sit,
			AvatarActivity.Phone,
			AvatarActivity.Talk,
		}
	);

	public static AvatarActivity ParseActivity(string? code)
	{
		return code?.Trim().ToLowerInvariant() switch
		{
			"walk" => AvatarActivity.Walk,
			"sit" => AvatarActivity.Sit,
			"phone" => AvatarActivity.Phone,
			"talk" => AvatarActivity.Talk,
			_ => AvatarActivity.Idle,
		};
	}

	public static AvatarActivity NextActivity(AvatarActivity current)
	{
		int index = 0;
		for (int candidate = 0; candidate < ActivitySequence.Count; candidate++)
		{
			if (ActivitySequence[candidate] == current)
			{
				index = candidate;
				break;
			}
		}
		return ActivitySequence[(index + 1 + ActivitySequence.Count) % ActivitySequence.Count];
	}

	public static AvatarLodLevel ResolveLod(float cameraDistance, bool cinematic = false)
	{
		if (cinematic)
		{
			return AvatarLodLevel.Cinematic;
		}
		if (!float.IsFinite(cameraDistance) || cameraDistance < 0.0f)
		{
			return AvatarLodLevel.Marker;
		}
		if (cameraDistance <= 10.0f)
		{
			return AvatarLodLevel.Street;
		}
		if (cameraDistance <= 24.0f)
		{
			return AvatarLodLevel.Distance;
		}
		return AvatarLodLevel.Marker;
	}

	public static bool UsesSkinnedAvatar(AvatarLodLevel lod)
	{
		return lod is AvatarLodLevel.Cinematic or AvatarLodLevel.Street;
	}

	public static string ActivityCode(AvatarActivity activity)
	{
		return activity.ToString().ToLowerInvariant();
	}
}
