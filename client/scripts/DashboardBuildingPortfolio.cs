using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;

#nullable enable

public sealed class DashboardBuildingPortfolio
{
    public IReadOnlyList<DashboardBuildingItem> Buildings { get; init; } = Array.Empty<DashboardBuildingItem>();
    public DashboardBuildingItem? OpenCandidate => Buildings.FirstOrDefault(item => item.HasAction("open"));
    public DashboardBuildingItem? RepairCandidate => Buildings.FirstOrDefault(item => item.HasAction("repair"));

    public string SummaryText
    {
        get
        {
            if (Buildings.Count == 0)
            {
                return "Будівлі: немає";
            }

            var first = Buildings[0];
            string count = Buildings.Count == 1 ? "1 будівля" : $"{Buildings.Count} будівлі";
            return $"{count}: {first.DisplayName} | {first.StatusText} | {first.DistrictName} | upkeep {first.UpkeepDaily:N0} ₴";
        }
    }

    public static DashboardBuildingPortfolio FromJson(JsonNode data)
    {
        var buildings = data?["buildings"]?.AsArray();
        if (buildings == null || buildings.Count == 0)
        {
            return new DashboardBuildingPortfolio();
        }

        var items = new List<DashboardBuildingItem>();
        foreach (var building in buildings)
        {
            if (building != null)
            {
                items.Add(DashboardBuildingItem.FromJson(building));
            }
        }

        return new DashboardBuildingPortfolio { Buildings = items };
    }
}

public sealed class DashboardBuildingItem
{
    public string Id { get; init; } = "";
    public string DisplayName { get; init; } = "Будівля";
    public string DistrictCode { get; init; } = "";
    public string DistrictName { get; init; } = "Район";
    public string OperatingStatus { get; init; } = "";
    public string BlueprintCode { get; init; } = "";
    public string BlueprintName { get; init; } = "";
    public string BlueprintCategory { get; init; } = "";
    public string ProjectType { get; init; } = "";
    public double OpeningFee { get; init; }
    public double RepairFee { get; init; }
    public double UpkeepDaily { get; init; }
    public IReadOnlyList<string> AvailableActions { get; init; } = Array.Empty<string>();

    public string StatusText => OperatingStatus switch
    {
        "inactive" => $"не відкрита, відкриття {OpeningFee:N0} ₴",
        "active" => "працює",
        "maintenance_due" => $"потрібен ремонт {RepairFee:N0} ₴",
        _ => OperatingStatus
    };

    public bool HasAction(string action)
    {
        return AvailableActions.Contains(action);
    }

    public static DashboardBuildingItem FromJson(JsonNode data)
    {
        return new DashboardBuildingItem
        {
            Id = data["id"]?.ToString() ?? "",
            DisplayName = data["name"]?.ToString() ?? data["blueprint_name"]?.ToString() ?? "Будівля",
            DistrictCode = data["district_code"]?.ToString() ?? "",
            DistrictName = data["district_name"]?.ToString() ?? "Район",
            OperatingStatus = data["operating_status"]?.ToString() ?? "",
            BlueprintCode = data["blueprint_code"]?.ToString() ?? "",
            BlueprintName = data["blueprint_name"]?.ToString() ?? "",
            BlueprintCategory = data["blueprint_category"]?.ToString() ?? "",
            ProjectType = data["project_type"]?.ToString() ?? "",
            OpeningFee = data["opening_fee"]?.GetValue<double>() ?? 0.0,
            RepairFee = data["repair_fee"]?.GetValue<double>() ?? 0.0,
            UpkeepDaily = data["upkeep_daily"]?.GetValue<double>() ?? 0.0,
            AvailableActions = ParseActions(data["available_actions"]?.AsArray()),
        };
    }

    private static IReadOnlyList<string> ParseActions(JsonArray? actions)
    {
        if (actions == null || actions.Count == 0)
        {
            return Array.Empty<string>();
        }

        var parsed = new List<string>();
        foreach (var action in actions)
        {
            string value = action?.ToString() ?? "";
            if (!string.IsNullOrWhiteSpace(value))
            {
                parsed.Add(value);
            }
        }

        return parsed;
    }
}
