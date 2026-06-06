using Godot;
using System;
using System.Collections.Generic;
using System.Linq;

#nullable enable

public partial class CityVisualOverlay : Control
{
	private const double VisualFrameIntervalSeconds = 1.0 / 20.0;

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
	private DashboardVisualPalette _palette = DashboardVisualPalettes.Core;
	private bool _streetFocus;
	private double _animationSeconds;
	private double _redrawElapsedSeconds;

	public override void _Ready()
	{
		MouseFilter = MouseFilterEnum.Ignore;
		ClipContents = true;
		SetProcess(true);
	}

	public override void _Process(double delta)
	{
		_animationSeconds += delta;
		_redrawElapsedSeconds += delta;
		if (_redrawElapsedSeconds < VisualFrameIntervalSeconds)
		{
			return;
		}

		_redrawElapsedSeconds %= VisualFrameIntervalSeconds;
		QueueRedraw();
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

	public string SetStyleCode(string? styleCode)
	{
		_palette = DashboardVisualPalettes.Resolve(styleCode);
		QueueRedraw();
		return _palette.Code;
	}

	public string ToggleFocusMode()
	{
		_streetFocus = !_streetFocus;
		QueueRedraw();
		return FocusButtonText;
	}

	public string FocusButtonText => _streetFocus ? "Огляд" : "Вулиця";

	public override void _Draw()
	{
		Vector2 size = Size;
		if (size.X < 120 || size.Y < 120)
		{
			return;
		}

		DrawRect(new Rect2(Vector2.Zero, size), AsGodot(_palette.CanvasShade), true);
		if (_streetFocus)
		{
			DrawStreetFocus(size);
			return;
		}

		DrawRoadNetwork(size);
		DrawDistricts(size);
		DrawPlayerAssets(size);
		DrawLegend(size);
	}

	private void DrawStreetFocus(Vector2 size)
	{
		Font font = GetThemeDefaultFont();
		DrawRect(new Rect2(Vector2.Zero, size), AsGodot(_palette.CanvasShade.WithAlpha(0.30f)), true);

		Rect2 street = new(new Vector2(0, size.Y * 0.70f), new Vector2(size.X, size.Y * 0.30f));
		DrawRect(street, AsGodot(_palette.SurfaceDeep), true);
		DrawLine(new Vector2(24, street.Position.Y + street.Size.Y * 0.48f), new Vector2(size.X - 24, street.Position.Y + street.Size.Y * 0.48f), AsGodot(_palette.RoadLine), 3.0f, true);
		DrawLine(new Vector2(0, street.Position.Y), new Vector2(size.X, street.Position.Y), new Color(0.70f, 0.72f, 0.66f, 0.72f), 7.0f, true);
		DrawStreetTraffic(size, street);

		DrawString(font, new Vector2(22, 32), "Street focus: вокзал / комерційне ядро", HorizontalAlignment.Left, size.X - 44, 15, AsGodot(_palette.PrimaryText));
		DrawString(font, new Vector2(22, 54), _model.HeadlineText, HorizontalAlignment.Left, size.X - 44, 13, AsGodot(_palette.SecondaryText));

		var buildings = _model.Buildings.Take(5).ToArray();
		if (buildings.Length == 0)
		{
			DrawEmptyStreetLots(size, font);
			return;
		}

		float lotWidth = Math.Min(112.0f, (size.X - 90.0f) / buildings.Length);
		float startX = (size.X - (lotWidth * buildings.Length + 14.0f * (buildings.Length - 1))) / 2.0f;
		for (int index = 0; index < buildings.Length; index++)
		{
			Rect2 lot = new(
				new Vector2(startX + index * (lotWidth + 14.0f), size.Y * 0.38f),
				new Vector2(lotWidth, size.Y * 0.28f)
			);
			DrawStreetBuilding(buildings[index], lot, font);
		}
	}

	private void DrawEmptyStreetLots(Vector2 size, Font font)
	{
		string[] labels = { "Вокзал", "Вільна земля", "Мерія", "Комерція" };
		float lotWidth = Math.Min(118.0f, (size.X - 110.0f) / labels.Length);
		float startX = (size.X - (lotWidth * labels.Length + 14.0f * (labels.Length - 1))) / 2.0f;
		for (int index = 0; index < labels.Length; index++)
		{
			Rect2 lot = new(
				new Vector2(startX + index * (lotWidth + 14.0f), size.Y * 0.40f),
				new Vector2(lotWidth, size.Y * 0.24f)
			);
			DrawRect(lot, new Color(0.22f, 0.28f, 0.30f, 0.72f), true);
			DrawRect(lot, new Color(1.0f, 1.0f, 1.0f, 0.18f), false, 2.0f);
			DrawString(font, lot.Position + new Vector2(8, lot.Size.Y - 16), labels[index], HorizontalAlignment.Left, lot.Size.X - 16, 12, new Color(0.96f, 0.96f, 0.90f, 0.86f));
		}
	}

	private void DrawStreetBuilding(DashboardCityVisualBuilding building, Rect2 lot, Font font)
	{
		Color fill = BuildingColor(building.BlueprintCode, building.ProjectType);
		if (building.OperatingStatus == "inactive")
		{
			fill.A = 0.62f;
		}

		DrawRect(lot, fill, true);
		DrawRect(lot, building.OperatingStatus == "maintenance_due" ? new Color(0.98f, 0.23f, 0.18f, 0.96f) : new Color(1.0f, 1.0f, 1.0f, 0.24f), false, 2.0f);

		for (int floor = 0; floor < 2; floor++)
		{
			for (int window = 0; window < 3; window++)
			{
				Vector2 windowPos = lot.Position + new Vector2(12 + window * 28, 14 + floor * 26);
				DrawRect(new Rect2(windowPos, new Vector2(16, 14)), AsGodot(_palette.WindowLight), true);
			}
		}

		DrawString(font, lot.Position + new Vector2(0, lot.Size.Y - 30), building.ArchetypeLabel, HorizontalAlignment.Center, lot.Size.X, 16, new Color(0.98f, 0.98f, 0.94f, 0.94f));
		DrawString(font, lot.Position + new Vector2(8, lot.Size.Y - 10), building.OperatingStatus, HorizontalAlignment.Left, lot.Size.X - 16, 11, new Color(0.96f, 0.96f, 0.90f, 0.82f));
	}

	private void DrawRoadNetwork(Vector2 size)
	{
		Vector2 station = CenterOf("bus_station", size);
		Vector2 commercial = CenterOf("commercial_core", size);
		Vector2 residential = CenterOf("highrise_residential", size);
		Vector2 industrial = CenterOf("industrial_edge", size);
		Vector2 suburb = CenterOf("suburb_private_sector", size);
		Vector2 outer = CenterOf("outer_land", size);

		DrawRoad(station, commercial, 0.00);
		DrawRoad(commercial, residential, 0.23);
		DrawRoad(commercial, industrial, 0.47);
		DrawRoad(station, suburb, 0.68);
		DrawRoad(suburb, outer, 0.84);
	}

	private void DrawRoad(Vector2 from, Vector2 to, double phase)
	{
		DrawLine(from, to, AsGodot(_palette.RoadSurface), 12.0f, true);
		DrawLine(from, to, AsGodot(_palette.RoadLine), 2.0f, true);

		float travel = DashboardVisualAnimation.TravelFraction(_animationSeconds, 0.08, phase);
		Vector2 trafficMarker = from.Lerp(to, travel);
		DrawCircle(trafficMarker, 4.5f, AsGodot(_palette.Traffic));
		DrawCircle(trafficMarker, 2.0f, AsGodot(_palette.TrafficHighlight));
	}

	private void DrawStreetTraffic(Vector2 size, Rect2 street)
	{
		float travel = DashboardVisualAnimation.TravelFraction(_animationSeconds, 0.10);
		float x = Mathf.Lerp(24.0f, size.X - 38.0f, travel);
		float y = street.Position.Y + street.Size.Y * 0.36f;
		Rect2 vehicle = new(new Vector2(x, y), new Vector2(14, 7));
		DrawRect(vehicle, AsGodot(_palette.Traffic), true);
		DrawCircle(vehicle.Position + new Vector2(3, 8), 2.0f, new Color(0.04f, 0.05f, 0.06f, 0.95f));
		DrawCircle(vehicle.Position + new Vector2(11, 8), 2.0f, new Color(0.04f, 0.05f, 0.06f, 0.95f));
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
		Color fill = baseColor.Lerp(AsGodot(_palette.Danger.WithAlpha(0.82f)), pressure * 0.32f);
		fill.A = 0.72f;

		DrawRect(rect, fill, true);
		DrawRect(rect, new Color(1.0f, 1.0f, 1.0f, 0.22f), false, 2.0f);

		Font font = GetThemeDefaultFont();
		Vector2 labelPos = rect.Position + new Vector2(8, 18);
		DrawString(font, labelPos, district.ShortLabel, HorizontalAlignment.Left, rect.Size.X - 16, 13, new Color(0.96f, 0.96f, 0.91f, 0.94f));

		DrawMetricBar(rect.Position + new Vector2(8, rect.Size.Y - 18), rect.Size.X - 16, district.JobSupply, AsGodot(_palette.Success));
		DrawMetricBar(rect.Position + new Vector2(8, rect.Size.Y - 10), rect.Size.X - 16, district.Traffic, AsGodot(_palette.Warning));
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
			? AsGodot(_palette.Danger)
			: AsGodot(_palette.Accent);

		DrawCircle(marker, 15.0f, new Color(0.0f, 0.0f, 0.0f, 0.42f));
		DrawCircle(marker, 11.0f, markerColor);
		DrawCircle(marker, 4.0f, new Color(1.0f, 1.0f, 1.0f, 0.9f));
		if (_model.ProblemBuildingCount > 0)
		{
			float pulse = DashboardVisualAnimation.Pulse(_animationSeconds, 0.72);
			DrawArc(marker, 17.0f + pulse * 5.0f, 0.0f, MathF.Tau, 32, AsGodot(_palette.Danger.WithAlpha(0.35f + pulse * 0.45f)), 2.0f, true);
		}
		DrawBuildingMarkers(size);
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
			? AsGodot(_palette.Danger)
			: new Color(1.0f, 1.0f, 1.0f, 0.72f);

		DrawRect(new Rect2(rect.Position + new Vector2(2, 3), rect.Size), new Color(0.0f, 0.0f, 0.0f, 0.32f), true);
		DrawRect(rect, fill, true);
		DrawRect(rect, border, false, 2.0f);
		DrawString(font, rect.Position + new Vector2(0, 17), building.ArchetypeLabel, HorizontalAlignment.Center, rect.Size.X, 13, new Color(0.98f, 0.98f, 0.94f, 0.96f));
		if (building.OperatingStatus == "maintenance_due")
		{
			float pulse = DashboardVisualAnimation.Pulse(_animationSeconds, 0.80, position.X * 0.01);
			DrawArc(position, 16.0f + pulse * 4.0f, 0.0f, MathF.Tau, 28, AsGodot(_palette.Danger.WithAlpha(0.32f + pulse * 0.48f)), 2.0f, true);
		}
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

	private static Color AsGodot(DashboardVisualColor color)
	{
		return new Color(color.Red, color.Green, color.Blue, color.Alpha);
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
