using Godot;
using System;
using System.Collections.Generic;
using System.Linq;

#nullable enable

public partial class CityVisualOverlay : Control
{
	private static readonly string[] DistrictOrder =
	{
		"outer_land",
		"suburb_private_sector",
		"industrial_edge",
		"highrise_residential",
		"commercial_core",
		"bus_station",
	};

	private static readonly Dictionary<string, Rect2> DistrictRects = new()
	{
		["outer_land"] = new Rect2(0.05f, 0.10f, 0.30f, 0.24f),
		["suburb_private_sector"] = new Rect2(0.07f, 0.50f, 0.28f, 0.25f),
		["industrial_edge"] = new Rect2(0.66f, 0.16f, 0.27f, 0.24f),
		["highrise_residential"] = new Rect2(0.40f, 0.12f, 0.22f, 0.22f),
		["commercial_core"] = new Rect2(0.39f, 0.38f, 0.26f, 0.22f),
		["bus_station"] = new Rect2(0.40f, 0.68f, 0.23f, 0.17f),
	};

	private DashboardCityVisualModel _model = DashboardCityVisualModel.Empty;

	public override void _Ready()
	{
		MouseFilter = MouseFilterEnum.Ignore;
		ClipContents = true;
	}

	public void SetCityModel(DashboardCityVisualModel model)
	{
		_model = model ?? DashboardCityVisualModel.Empty;
		QueueRedraw();
	}

	public void SetBuildingPortfolio(DashboardBuildingPortfolio portfolio)
	{
		_model = _model.WithPortfolio(portfolio);
		QueueRedraw();
	}

	public override void _Draw()
	{
		Vector2 size = Size;
		if (size.X < 120 || size.Y < 120)
		{
			return;
		}

		DrawRect(new Rect2(Vector2.Zero, size), new Color(0.02f, 0.03f, 0.04f, 0.20f), true);
		DrawRoadNetwork(size);
		DrawDistricts(size);
		DrawPlayerAssets(size);
		DrawLegend(size);
	}

	private void DrawRoadNetwork(Vector2 size)
	{
		Vector2 station = CenterOf("bus_station", size);
		Vector2 commercial = CenterOf("commercial_core", size);
		Vector2 residential = CenterOf("highrise_residential", size);
		Vector2 industrial = CenterOf("industrial_edge", size);
		Vector2 suburb = CenterOf("suburb_private_sector", size);
		Vector2 outer = CenterOf("outer_land", size);

		DrawRoad(station, commercial);
		DrawRoad(commercial, residential);
		DrawRoad(commercial, industrial);
		DrawRoad(station, suburb);
		DrawRoad(suburb, outer);
	}

	private void DrawRoad(Vector2 from, Vector2 to)
	{
		DrawLine(from, to, new Color(0.05f, 0.06f, 0.07f, 0.72f), 12.0f, true);
		DrawLine(from, to, new Color(0.84f, 0.80f, 0.67f, 0.62f), 2.0f, true);
	}

	private void DrawDistricts(Vector2 size)
	{
		var districtsByCode = _model.Districts.ToDictionary(district => district.Code, district => district);
		foreach (string code in DistrictOrder)
		{
			if (!DistrictRects.ContainsKey(code))
			{
				continue;
			}

			var district = districtsByCode.GetValueOrDefault(code) ?? FallbackDistrict(code);
			DrawDistrict(district, ScaleRect(DistrictRects[code], size));
		}
	}

	private void DrawDistrict(DashboardCityVisualDistrict district, Rect2 rect)
	{
		Color baseColor = DistrictBaseColor(district.Code);
		float pressure = Math.Clamp(district.PressureScore / 240.0f, 0.0f, 1.0f);
		Color fill = baseColor.Lerp(new Color(0.67f, 0.20f, 0.18f, 0.82f), pressure * 0.32f);
		fill.A = 0.72f;

		DrawRect(rect, fill, true);
		DrawRect(rect, new Color(1.0f, 1.0f, 1.0f, 0.22f), false, 2.0f);

		Font font = GetThemeDefaultFont();
		Vector2 labelPos = rect.Position + new Vector2(8, 18);
		DrawString(font, labelPos, district.ShortLabel, HorizontalAlignment.Left, rect.Size.X - 16, 13, new Color(0.96f, 0.96f, 0.91f, 0.94f));

		DrawMetricBar(rect.Position + new Vector2(8, rect.Size.Y - 18), rect.Size.X - 16, district.JobSupply, new Color(0.36f, 0.80f, 0.55f, 0.85f));
		DrawMetricBar(rect.Position + new Vector2(8, rect.Size.Y - 10), rect.Size.X - 16, district.Traffic, new Color(0.95f, 0.70f, 0.28f, 0.82f));
	}

	private void DrawMetricBar(Vector2 origin, float width, int value, Color color)
	{
		float clamped = Math.Clamp(value, 0, 100) / 100.0f;
		DrawRect(new Rect2(origin, new Vector2(width, 4)), new Color(0.0f, 0.0f, 0.0f, 0.32f), true);
		DrawRect(new Rect2(origin, new Vector2(width * clamped, 4)), color, true);
	}

	private void DrawPlayerAssets(Vector2 size)
	{
		Vector2 station = CenterOf("bus_station", size);
		Vector2 marker = station + new Vector2(34, -18);
		Color markerColor = _model.ProblemBuildingCount > 0
			? new Color(0.95f, 0.27f, 0.22f, 0.95f)
			: new Color(0.98f, 0.78f, 0.28f, 0.95f);

		DrawCircle(marker, 15.0f, new Color(0.0f, 0.0f, 0.0f, 0.42f));
		DrawCircle(marker, 11.0f, markerColor);
		DrawCircle(marker, 4.0f, new Color(1.0f, 1.0f, 1.0f, 0.9f));
		DrawBuildingMarkers(size);

		Font font = GetThemeDefaultFont();
		string assetText = _model.BuildingCount > 0
			? $"Активи: {_model.BuildingCount} | active {_model.ActiveBuildingCount} | repair {_model.ProblemBuildingCount}"
			: "Активи: ще немає";
		DrawString(font, new Vector2(size.X - 250, 28), assetText, HorizontalAlignment.Left, 230, 13, new Color(0.96f, 0.96f, 0.91f, 0.92f));
	}

	private void DrawBuildingMarkers(Vector2 size)
	{
		if (_model.Buildings.Count == 0)
		{
			return;
		}

		Font font = GetThemeDefaultFont();
		int count = Math.Min(_model.Buildings.Count, 8);
		for (int index = 0; index < count; index++)
		{
			var building = _model.Buildings[index];
			Vector2 position = BuildingMarkerPosition(building, index, size);
			DrawBuildingMarker(building, position, font);
		}
	}

	private void DrawBuildingMarker(DashboardCityVisualBuilding building, Vector2 position, Font font)
	{
		Vector2 markerSize = new(24, 24);
		Rect2 rect = new(position - markerSize / 2.0f, markerSize);
		Color fill = BuildingColor(building.BlueprintCode, building.ProjectType);
		if (building.OperatingStatus == "inactive")
		{
			fill.A = 0.58f;
		}

		Color border = building.OperatingStatus == "maintenance_due"
			? new Color(0.98f, 0.23f, 0.18f, 0.96f)
			: new Color(1.0f, 1.0f, 1.0f, 0.72f);

		DrawRect(new Rect2(rect.Position + new Vector2(2, 3), rect.Size), new Color(0.0f, 0.0f, 0.0f, 0.32f), true);
		DrawRect(rect, fill, true);
		DrawRect(rect, border, false, 2.0f);
		DrawString(font, rect.Position + new Vector2(0, 17), building.ArchetypeLabel, HorizontalAlignment.Center, rect.Size.X, 13, new Color(0.98f, 0.98f, 0.94f, 0.96f));
	}

	private static Vector2 BuildingMarkerPosition(DashboardCityVisualBuilding building, int index, Vector2 size)
	{
		string districtCode = DistrictRects.ContainsKey(building.DistrictCode)
			? building.DistrictCode
			: building.ProjectType switch
			{
				"industrial" => "industrial_edge",
				"residential" => "highrise_residential",
				"medical" => "commercial_core",
				_ => "commercial_core",
			};

		Vector2 center = CenterOf(districtCode, size);
		Vector2[] offsets =
		{
			new(-34, -14),
			new(0, -20),
			new(34, -10),
			new(-22, 20),
			new(24, 22),
			new(-50, 14),
			new(52, 16),
			new(0, 34),
		};
		return center + offsets[index % offsets.Length];
	}

	private void DrawLegend(Vector2 size)
	{
		Font font = GetThemeDefaultFont();
		DrawString(font, new Vector2(18, size.Y - 44), _model.HeadlineText, HorizontalAlignment.Left, size.X - 36, 13, new Color(0.96f, 0.96f, 0.91f, 0.92f));
		DrawString(font, new Vector2(18, size.Y - 24), "зелена шкала: робота | жовта шкала: трафік | червоний відтінок: навантаження", HorizontalAlignment.Left, size.X - 36, 12, new Color(0.86f, 0.88f, 0.82f, 0.78f));
	}

	private static Rect2 ScaleRect(Rect2 unit, Vector2 size)
	{
		return new Rect2(
			new Vector2(unit.Position.X * size.X, unit.Position.Y * size.Y),
			new Vector2(unit.Size.X * size.X, unit.Size.Y * size.Y)
		);
	}

	private static Vector2 CenterOf(string code, Vector2 size)
	{
		Rect2 rect = ScaleRect(DistrictRects[code], size);
		return rect.Position + rect.Size / 2.0f;
	}

	private static DashboardCityVisualDistrict FallbackDistrict(string code)
	{
		return new DashboardCityVisualDistrict(code, code, 0, 0, 0, 0, 0, 0, 0, 0);
	}

	private static Color DistrictBaseColor(string code)
	{
		return code switch
		{
			"bus_station" => new Color(0.86f, 0.55f, 0.26f, 0.75f),
			"commercial_core" => new Color(0.25f, 0.55f, 0.78f, 0.75f),
			"highrise_residential" => new Color(0.42f, 0.49f, 0.62f, 0.75f),
			"industrial_edge" => new Color(0.52f, 0.48f, 0.43f, 0.75f),
			"suburb_private_sector" => new Color(0.36f, 0.66f, 0.42f, 0.75f),
			"outer_land" => new Color(0.26f, 0.52f, 0.31f, 0.75f),
			_ => new Color(0.34f, 0.40f, 0.46f, 0.75f),
		};
	}

	private static Color BuildingColor(string blueprintCode, string projectType)
	{
		return blueprintCode switch
		{
			"station_kiosk" => new Color(0.92f, 0.62f, 0.22f, 0.94f),
			"coffee_shop" => new Color(0.56f, 0.36f, 0.24f, 0.94f),
			"neighborhood_market" => new Color(0.22f, 0.64f, 0.42f, 0.94f),
			"repair_workshop" => new Color(0.46f, 0.50f, 0.56f, 0.94f),
			"private_hostel" => new Color(0.42f, 0.52f, 0.82f, 0.94f),
			"pharmacy" => new Color(0.20f, 0.72f, 0.76f, 0.94f),
			"small_factory" => new Color(0.62f, 0.44f, 0.34f, 0.94f),
			_ => projectType switch
			{
				"industrial" => new Color(0.50f, 0.50f, 0.52f, 0.94f),
				"residential" => new Color(0.42f, 0.52f, 0.78f, 0.94f),
				"medical" => new Color(0.20f, 0.72f, 0.76f, 0.94f),
				_ => new Color(0.34f, 0.58f, 0.82f, 0.94f),
			},
		};
	}
}
