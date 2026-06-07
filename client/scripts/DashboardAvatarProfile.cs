using System.Collections.Generic;
using System.Text.Json.Nodes;

public sealed class DashboardAvatarProfile
{
    public string BodyPresetCode { get; init; } = "body_standard";
    public string FacePresetCode { get; init; } = "face_01";
    public string SkinToneCode { get; init; } = "skin_03";
    public string HairStyleCode { get; init; } = "hair_short_01";
    public string HairColorCode { get; init; } = "hair_brown";
    public IReadOnlyDictionary<string, string> EquippedOutfit { get; init; } =
        CreateDefaultOutfit();
    public string AnimationProfileCode { get; init; } = "humanoid_context_v1";
    public int FashionScore { get; init; }

    public static DashboardAvatarProfile FromJson(JsonNode data)
    {
        var avatar = data?["avatar"];
        if (avatar == null)
        {
            return new DashboardAvatarProfile();
        }

        var outfit = new Dictionary<string, string>();
        if (avatar["equipped_outfit"] is JsonObject outfitData)
        {
            foreach (var item in outfitData)
            {
                if (!string.IsNullOrWhiteSpace(item.Value?.ToString()))
                {
                    outfit[item.Key] = item.Value!.ToString();
                }
            }
        }

        return new DashboardAvatarProfile
        {
            BodyPresetCode = avatar["body_preset_code"]?.ToString() ?? "body_standard",
            FacePresetCode = avatar["face_preset_code"]?.ToString() ?? "face_01",
            SkinToneCode = avatar["skin_tone_code"]?.ToString() ?? "skin_03",
            HairStyleCode = avatar["hair_style_code"]?.ToString() ?? "hair_short_01",
            HairColorCode = avatar["hair_color_code"]?.ToString() ?? "hair_brown",
            EquippedOutfit = outfit,
            AnimationProfileCode = avatar["animation_profile_code"]?.ToString() ?? "humanoid_context_v1",
            FashionScore = avatar["fashion_score"]?.GetValue<int>() ?? 0,
        };
    }

    private static Dictionary<string, string> CreateDefaultOutfit()
    {
        return new Dictionary<string, string>
        {
            ["upper"] = "upper_stock_jacket",
            ["lower"] = "lower_stock_jeans",
            ["footwear"] = "footwear_stock_sneakers",
        };
    }
}
