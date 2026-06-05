using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;

#nullable enable

public sealed class DashboardCityVisualModel
{
	public static DashboardCityVisualModel Empty { get; } = new();

	public string CityName { get; init; } = "Місто";
	public IReadOnlyList<DashboardCityVisualDistrict> Districts { get; init; } = Array.Empty<DashboardCityVisualDistrict>();
	public int BuildingCount { get; init; }
	public int ActiveBuildingCount { get; init; }
	public int InactiveBuildingCount { get; init; }
	public int ProblemBuildingCount { get; init; }

	public string HeadlineText
	{
		get
		{
			if (Districts.Count == 0)
			{
				return $"{CityName}: райони завантажуються";
			}

			int jobSupply = Districts.Sum(district => district.JobSupply);
			int maxCrime = Districts.Max(district => district.CrimeRisk);
			return $"{CityName}: {Districts.Count} районів | робота {jobSupply} | злочинність max {maxCrime}";
		}
	}

	public DashboardCityVisualModel WithPortfolio(DashboardBuildingPortfolio portfolio)
	{
		return new DashboardCityVisualModel
		{
			CityName = CityName,
			Districts = Districts,
			BuildingCount = portfolio.Buildings.Count,
			ActiveBuildingCount = portfolio.Buildings.Count(building => building.OperatingStatus == "active"),
			InactiveBuildingCount = portfolio.Buildings.Count(building => building.OperatingStatus == "inactive"),
			ProblemBuildingCount = portfolio.Buildings.Count(building => building.OperatingStatus == "maintenance_due"),
		};
	}

	public static DashboardCityVisualModel FromCityStatus(JsonNode? data)
	{
		var districts = data?["districts"]?.AsArray();
		if (districts == null || districts.Count == 0)
		{
			return new DashboardCityVisualModel
			{
				CityName = data?["name"]?.ToString() ?? "Місто",
			};
		}

		var items = new List<DashboardCityVisualDistrict>();
		foreach (var district in districts)
		{
			if (district != null)
			{
				items.Add(DashboardCityVisualDistrict.FromJson(district));
			}
		}

		return new DashboardCityVisualModel
		{
			CityName = data?["name"]?.ToString() ?? "Місто",
			Districts = items,
		};
	}
}

public sealed record DashboardCityVisualDistrict(
	string Code,
	string Name,
	int RentLevel,
	int JobSupply,
	int CrimeRisk,
	int Traffic,
	int ServiceCoverage,
	int MedicalCoverage,
	int LandValue,
	int Desirability)
{
	public string ShortLabel => Code switch
	{
		"bus_station" => "Вокзал",
		"commercial_core" => "Комерція",
		"highrise_residential" => "Житло",
		"industrial_edge" => "Промка",
		"suburb_private_sector" => "Передмістя",
		"outer_land" => "Розширення",
		_ => Name,
	};

	public int PressureScore => CrimeRisk + Traffic + Math.Max(0, 60 - ServiceCoverage) + Math.Max(0, 60 - MedicalCoverage);

	public static DashboardCityVisualDistrict FromJson(JsonNode data)
	{
		return new DashboardCityVisualDistrict(
			Code: data["code"]?.ToString() ?? "",
			Name: data["name"]?.ToString() ?? "Район",
			RentLevel: data["rent_level"]?.GetValue<int>() ?? 0,
			JobSupply: data["job_supply"]?.GetValue<int>() ?? 0,
			CrimeRisk: data["crime_risk"]?.GetValue<int>() ?? 0,
			Traffic: data["traffic"]?.GetValue<int>() ?? 0,
			ServiceCoverage: data["service_coverage"]?.GetValue<int>() ?? 0,
			MedicalCoverage: data["medical_coverage"]?.GetValue<int>() ?? 0,
			LandValue: data["land_value"]?.GetValue<int>() ?? 0,
			Desirability: data["desirability"]?.GetValue<int>() ?? 0
		);
	}
}
