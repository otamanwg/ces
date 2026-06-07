using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;

#nullable enable

public sealed class DashboardBuildCatalog
{
    public IReadOnlyList<DashboardLandOption> LandOptions { get; init; } = Array.Empty<DashboardLandOption>();
    public IReadOnlyList<DashboardBusinessBlueprintOption> Blueprints { get; init; } = Array.Empty<DashboardBusinessBlueprintOption>();

    public DashboardLandOption? StarterLandFor(double playerBalance)
    {
        return LandOptions
            .Where(land => land.IsCityOwned && land.CurrentPrice <= playerBalance)
            .OrderBy(land => land.CurrentPrice)
            .ThenBy(land => land.AreaHectares)
            .FirstOrDefault();
    }

    public DashboardLandOption? OwnedLandFor(string playerId)
    {
        if (string.IsNullOrWhiteSpace(playerId))
        {
            return null;
        }

        return LandOptions
            .Where(land => land.IsOwnedBy(playerId))
            .OrderBy(land => land.CurrentPrice)
            .ThenBy(land => land.AreaHectares)
            .FirstOrDefault();
    }

    public IReadOnlyList<DashboardBusinessBlueprintOption> BlueprintsFor(DashboardLandOption land)
    {
        return Blueprints
            .Where(blueprint => blueprint.CanUseLand(land))
            .OrderBy(blueprint => blueprint.TotalRecommendedBudget)
            .ThenBy(blueprint => blueprint.RiskLevel)
            .ToArray();
    }

    public DashboardStarterBuildPlan? StarterPlanFor(double playerBalance)
    {
        var land = StarterLandFor(playerBalance);
        if (land == null)
        {
            return null;
        }

        var blueprint = BlueprintsFor(land).FirstOrDefault();
        if (blueprint == null)
        {
            return null;
        }

        return new DashboardStarterBuildPlan(land, blueprint);
    }

    public DashboardStarterBuildPlan? StarterApplicationPlanFor(string playerId)
    {
        var land = OwnedLandFor(playerId);
        if (land == null)
        {
            return null;
        }

        var blueprint = BlueprintsFor(land).FirstOrDefault();
        if (blueprint == null)
        {
            return null;
        }

        return new DashboardStarterBuildPlan(land, blueprint);
    }

    public string SummaryFor(double playerBalance)
    {
        if (LandOptions.Count == 0 || Blueprints.Count == 0)
        {
            return "Будівництво: каталог недоступний";
        }

        var plan = StarterPlanFor(playerBalance);
        if (plan == null)
        {
            return "Будівництво: бракує коштів або сумісної ділянки";
        }

        return plan.BuySummaryText;
    }

    public static DashboardBuildCatalog FromJson(JsonNode? landData, JsonNode? blueprintData)
    {
        return new DashboardBuildCatalog
        {
            LandOptions = ParseLandOptions(landData?["parcels"]?.AsArray()),
            Blueprints = ParseBlueprints(blueprintData?["blueprints"]?.AsArray()),
        };
    }

    private static IReadOnlyList<DashboardLandOption> ParseLandOptions(JsonArray? parcels)
    {
        if (parcels == null || parcels.Count == 0)
        {
            return Array.Empty<DashboardLandOption>();
        }

        var options = new List<DashboardLandOption>();
        foreach (var parcel in parcels)
        {
            if (parcel != null)
            {
                options.Add(DashboardLandOption.FromJson(parcel));
            }
        }

        return options;
    }

    private static IReadOnlyList<DashboardBusinessBlueprintOption> ParseBlueprints(JsonArray? blueprints)
    {
        if (blueprints == null || blueprints.Count == 0)
        {
            return Array.Empty<DashboardBusinessBlueprintOption>();
        }

        var options = new List<DashboardBusinessBlueprintOption>();
        foreach (var blueprint in blueprints)
        {
            if (blueprint != null)
            {
                options.Add(DashboardBusinessBlueprintOption.FromJson(blueprint));
            }
        }

        return options;
    }
}

public sealed class DashboardLandOption
{
    public string Id { get; init; } = "";
    public string Code { get; init; } = "";
    public string Label { get; init; } = "Ділянка";
    public string DistrictName { get; init; } = "Район";
    public string LandType { get; init; } = "";
    public string ZoningType { get; init; } = "";
    public double AreaHectares { get; init; }
    public double CurrentPrice { get; init; }
    public string Status { get; init; } = "";
    public string? OwnerPlayerId { get; init; }

    public bool IsCityOwned => Status == "city_owned" && string.IsNullOrWhiteSpace(OwnerPlayerId);
    public bool IsOwnedBy(string playerId) => Status == "owned" && OwnerPlayerId == playerId;

    public string SummaryText => $"{Label} | {DistrictName} | {AreaHectares:N2} га | {CurrentPrice:N0} ₴";

    public static DashboardLandOption FromJson(JsonNode data)
    {
        return new DashboardLandOption
        {
            Id = data["id"]?.ToString() ?? "",
            Code = data["code"]?.ToString() ?? "",
            Label = data["label"]?.ToString() ?? "Ділянка",
            DistrictName = data["district_name"]?.ToString() ?? "Район",
            LandType = data["land_type"]?.ToString() ?? "",
            ZoningType = data["zoning_type"]?.ToString() ?? "",
            AreaHectares = data["area_hectares"]?.GetValue<double>() ?? 0.0,
            CurrentPrice = data["current_price"]?.GetValue<double>() ?? 0.0,
            Status = data["status"]?.ToString() ?? "",
            OwnerPlayerId = data["owner_player_id"]?.ToString(),
        };
    }
}

public sealed class DashboardBusinessBlueprintOption
{
    public string Id { get; init; } = "";
    public string Code { get; init; } = "";
    public string Name { get; init; } = "Бізнес";
    public string Category { get; init; } = "";
    public string ProjectType { get; init; } = "";
    public string Description { get; init; } = "";
    public string Difficulty { get; init; } = "";
    public IReadOnlyList<string> AllowedLandTypes { get; init; } = Array.Empty<string>();
    public IReadOnlyList<string> AllowedZoningTypes { get; init; } = Array.Empty<string>();
    public double MinAreaHectares { get; init; }
    public double ConstructionCost { get; init; }
    public double OpeningFee { get; init; }
    public double RecommendedCashReserve { get; init; }
    public double DailyProfitMin { get; init; }
    public double DailyProfitMax { get; init; }
    public double UpkeepDaily { get; init; }
    public int RiskLevel { get; init; }
    public IReadOnlyList<string> Risks { get; init; } = Array.Empty<string>();
    public IReadOnlyList<string> PlayerHints { get; init; } = Array.Empty<string>();

    public double TotalRecommendedBudget => ConstructionCost + OpeningFee + RecommendedCashReserve;
    public string ProfitText => $"{DailyProfitMin:N0}-{DailyProfitMax:N0} ₴/день";
    public string RiskText => $"ризик {RiskLevel}/5";

    public bool CanUseLand(DashboardLandOption land)
    {
        bool landTypeAllowed = AllowedLandTypes.Count == 0 || AllowedLandTypes.Contains(land.LandType);
        bool zoningAllowed = AllowedZoningTypes.Count == 0 || AllowedZoningTypes.Contains(land.ZoningType);
        return landTypeAllowed && zoningAllowed && land.AreaHectares >= MinAreaHectares;
    }

    public static DashboardBusinessBlueprintOption FromJson(JsonNode data)
    {
        return new DashboardBusinessBlueprintOption
        {
            Id = data["id"]?.ToString() ?? "",
            Code = data["code"]?.ToString() ?? "",
            Name = data["name"]?.ToString() ?? "Бізнес",
            Category = data["category"]?.ToString() ?? "",
            ProjectType = data["project_type"]?.ToString() ?? "",
            Description = data["description"]?.ToString() ?? "",
            Difficulty = data["difficulty"]?.ToString() ?? "",
            AllowedLandTypes = ParseStringArray(data["allowed_land_types"]?.AsArray()),
            AllowedZoningTypes = ParseStringArray(data["allowed_zoning_types"]?.AsArray()),
            MinAreaHectares = data["min_area_hectares"]?.GetValue<double>() ?? 0.0,
            ConstructionCost = data["construction_cost"]?.GetValue<double>() ?? 0.0,
            OpeningFee = data["opening_fee"]?.GetValue<double>() ?? 0.0,
            RecommendedCashReserve = data["recommended_cash_reserve"]?.GetValue<double>() ?? 0.0,
            DailyProfitMin = data["daily_profit_min"]?.GetValue<double>() ?? 0.0,
            DailyProfitMax = data["daily_profit_max"]?.GetValue<double>() ?? 0.0,
            UpkeepDaily = data["upkeep_daily"]?.GetValue<double>() ?? 0.0,
            RiskLevel = data["risk_level"]?.GetValue<int>() ?? 0,
            Risks = ParseStringArray(data["risks"]?.AsArray()),
            PlayerHints = ParseStringArray(data["player_hints"]?.AsArray()),
        };
    }

    private static IReadOnlyList<string> ParseStringArray(JsonArray? values)
    {
        if (values == null || values.Count == 0)
        {
            return Array.Empty<string>();
        }

        var parsed = new List<string>();
        foreach (var value in values)
        {
            string text = value?.ToString() ?? "";
            if (!string.IsNullOrWhiteSpace(text))
            {
                parsed.Add(text);
            }
        }

        return parsed;
    }
}

public sealed record DashboardStarterBuildPlan(DashboardLandOption Land, DashboardBusinessBlueprintOption Blueprint)
{
    public string BuySummaryText => $"Перший план: {Blueprint.Name} | земля {Land.CurrentPrice:N0} ₴ | будівництво {Blueprint.ConstructionCost:N0} ₴ | відкриття {Blueprint.OpeningFee:N0} ₴ | резерв {Blueprint.RecommendedCashReserve:N0} ₴";
    public string ApplicationSummaryText => $"Заявка: {Blueprint.Name} | {Land.Label} | {Blueprint.ProfitText} | {Blueprint.RiskText}";
    public string ActivationSummaryText => $"Погоджено: {Blueprint.Name} | можна створити будівлю";
}
