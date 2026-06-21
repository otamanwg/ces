using System;
using System.Linq;
using System.Text.Json.Nodes;

static void AssertEqual<T>(T expected, T actual, string message)
{
	if (!Equals(expected, actual))
	{
		throw new InvalidOperationException($"{message}: expected {expected}, got {actual}");
	}
}

static void AssertSequence(string[] expected, string[] actual, string message)
{
	if (!expected.SequenceEqual(actual))
	{
		throw new InvalidOperationException(
			$"{message}: expected [{string.Join(", ", expected)}], got [{string.Join(", ", actual)}]"
		);
	}
}

static void AssertNear(double expected, double actual, double tolerance, string message)
{
	if (Math.Abs(expected - actual) > tolerance)
	{
		throw new InvalidOperationException($"{message}: expected {expected}, got {actual}");
	}
}

static DashboardActionState ActionState(
	bool hasPlayer = true,
	bool bootstrapPending = false,
	bool pendingApply = false,
	bool pendingBusinessMarket = false,
	bool pendingSportsClubs = false,
	bool pendingExamInfo = false,
	bool pendingRefresh = false,
	bool pendingWork = false,
	bool pendingSleep = false,
	bool pendingEat = false,
	bool pendingBusinessBuy = false,
	bool pendingDividend = false,
	bool pendingSportsJoin = false,
	bool pendingSportsTrain = false,
	bool pendingExam = false,
	bool canApplyJob = true,
	bool canWork = true,
	bool canSleep = true,
	bool canEat = true,
	bool canBuyBusiness = true,
	bool canCollectDividend = true,
	bool canJoinSports = true,
	bool canTrainSports = true,
	bool canTakeExam = true,
	bool hasOwnedBusiness = true)
{
	return new DashboardActionState(
		hasPlayer,
		bootstrapPending,
		pendingApply,
		pendingBusinessMarket,
		pendingSportsClubs,
		pendingExamInfo,
		pendingRefresh,
		pendingWork,
		pendingSleep,
		pendingEat,
		pendingBusinessBuy,
		pendingDividend,
		pendingSportsJoin,
		pendingSportsTrain,
		pendingExam,
		canApplyJob,
		canWork,
		canSleep,
		canEat,
		canBuyBusiness,
		canCollectDividend,
		canJoinSports,
		canTrainSports,
		canTakeExam,
		hasOwnedBusiness
	);
}

var history = new DashboardEventHistory();

AssertEqual(false, history.Add(""), "Empty messages are ignored");
AssertEqual(false, history.Add("   "), "Whitespace messages are ignored");

AssertEqual(
	"ws://127.0.0.1:8000/ws/city/city-1?token=token-1",
	CityWebSocketEndpoint.BuildUrl("city-1", "token-1"),
	"WebSocket URL includes player token"
);
AssertEqual(
	"wss://game.example/ws/city/city%20id?token=a%2Bb%2Fc%3D",
	CityWebSocketEndpoint.BuildUrl("city id", "a+b/c=", "wss://game.example/"),
	"WebSocket URL encodes city and token"
);
AssertEqual("", CityWebSocketEndpoint.BuildUrl("", "token-1"), "Missing city id blocks websocket URL");
AssertEqual("", CityWebSocketEndpoint.BuildUrl("city-1", ""), "Missing token blocks websocket URL");
AssertEqual(true, history.Add("Registered"), "First event is accepted");
AssertEqual(false, history.Add("Registered"), "Consecutive duplicate is ignored");
AssertSequence(new[] { "Registered" }, history.Events.ToArray(), "Duplicate does not change history");

history.Add("Applied job");
history.Add("Worked");
history.Add("Slept");
history.Add("Ate");
history.Add("Bought business");

AssertSequence(
	new[] { "Applied job", "Worked", "Slept", "Ate", "Bought business" },
	history.Events.ToArray(),
	"History keeps the newest five events"
);

var noPlayerActions = DashboardActionViewModel.Build(ActionState(hasPlayer: false));
AssertEqual(true, noPlayerActions.ApplyJob.Disabled, "Apply job disabled without player");
AssertEqual(true, noPlayerActions.Work.Disabled, "Work disabled without player");
AssertEqual("Потрібен зареєстрований гравець.", noPlayerActions.Work.Tooltip, "Work explains missing player");
AssertEqual(false, noPlayerActions.Refresh.Disabled, "Refresh stays available without player");

var readyActions = DashboardActionViewModel.Build(ActionState());
AssertEqual(false, readyActions.Work.Disabled, "Work enabled when allowed");
AssertEqual("Працювати", readyActions.Work.Text, "Work default label");
AssertEqual("", readyActions.Work.Tooltip, "Enabled work has no warning tooltip");
AssertEqual(false, readyActions.CollectDividend.Disabled, "Dividend enabled with owned business");

var noBusinessActions = DashboardActionViewModel.Build(ActionState(hasOwnedBusiness: false));
AssertEqual(true, noBusinessActions.CollectDividend.Disabled, "Dividend disabled without owned business");
AssertEqual("Спочатку купіть бізнес.", noBusinessActions.CollectDividend.Tooltip, "Dividend explains missing business");

var needsBusinessMoneyActions = DashboardActionViewModel.Build(ActionState(canBuyBusiness: false));
AssertEqual(true, needsBusinessMoneyActions.BuyBusiness.Disabled, "Business buy disabled without enough balance");
AssertEqual("Накопичте достатньо коштів для першого бізнесу.", needsBusinessMoneyActions.BuyBusiness.Tooltip, "Business buy explains balance gate");

var needsTrainingResourcesActions = DashboardActionViewModel.Build(ActionState(canTrainSports: false));
AssertEqual(true, needsTrainingResourcesActions.TrainSports.Disabled, "Training disabled without resources");
AssertEqual("Потрібен спортивний контракт, 40 ₴ і 40 енергії.", needsTrainingResourcesActions.TrainSports.Tooltip, "Training explains requirements");

var pendingWorkActions = DashboardActionViewModel.Build(ActionState(pendingWork: true));
AssertEqual(true, pendingWorkActions.ApplyJob.Disabled, "Pending work disables other actions");
AssertEqual(true, pendingWorkActions.Sleep.Disabled, "Pending work disables sleep");
AssertEqual("Працюємо...", pendingWorkActions.Work.Text, "Pending work label");
AssertEqual(true, pendingWorkActions.Work.Disabled, "Pending work button is disabled while busy");
AssertEqual("Дочекайтесь завершення поточної дії.", pendingWorkActions.Sleep.Tooltip, "Busy state explains disabled actions");

var pendingMarketActions = DashboardActionViewModel.Build(ActionState(pendingBusinessMarket: true));
AssertEqual("Шукаємо...", pendingMarketActions.BuyBusiness.Text, "Pending business market label");

var pendingExamActions = DashboardActionViewModel.Build(ActionState(pendingExamInfo: true));
AssertEqual("Завантаження...", pendingExamActions.Exam.Text, "Pending exam info label");

var richSnapshotJson = JsonNode.Parse(
	"""
	{
		"id": "player-1",
		"username": "solo-dev",
		"auth_token": "token-1",
		"balance": 1234.5,
		"education_level": "College",
		"job": "Бариста",
		"hostel": "Hostel A",
		"owned_businesses": [
			{"id": "business-1", "name": "Coffee Shop"}
		],
		"sports_contract": {
			"club": "FC Test",
			"strength": 12,
			"stamina": 15
		},
		"energy": 80,
		"mood": 70,
		"hunger": 25,
		"avatar": {
			"body_preset_code": "body_sturdy",
			"face_preset_code": "face_20",
			"skin_tone_code": "skin_06",
			"hair_style_code": "hair_long_02",
			"hair_color_code": "hair_auburn",
			"equipped_outfit": {
				"upper": "upper_designer_coat",
				"lower": "lower_stock_jeans",
				"footwear": "footwear_stock_sneakers"
			},
			"animation_profile_code": "humanoid_context_v1",
			"fashion_score": 42
		},
		"onboarding": {
			"stage": "housing_search",
			"completed": false,
			"title": "Нічліг у новому місті",
			"narrative": "Після заяви потрібно знайти житло.",
			"available_choices": ["find_housing"],
			"police_report_status": "pending",
			"police_recovery_amount": 75,
			"police_recovery_claimable": true
		},
		"actions": {"can_work": true}
	}
	"""
)!;
var richSnapshot = DashboardPlayerSnapshot.FromJson(richSnapshotJson);
AssertEqual("player-1", richSnapshot.Id, "Snapshot id parsed");
AssertEqual("solo-dev", richSnapshot.Username, "Snapshot username parsed");
AssertEqual("token-1", richSnapshot.AuthToken, "Snapshot auth token parsed");
AssertEqual(1234.5, richSnapshot.Balance, "Snapshot balance parsed");
AssertEqual("College", richSnapshot.EducationLevel, "Snapshot education parsed");
AssertEqual("Бариста", richSnapshot.Job, "Snapshot job parsed");
AssertEqual(true, richSnapshot.HasJob, "Snapshot detects active job");
AssertEqual("business-1", richSnapshot.OwnedBusinessId, "Snapshot owned business id parsed");
AssertEqual("Бізнес: Coffee Shop", richSnapshot.OwnedBusinessText, "Snapshot owned business label parsed");
AssertEqual("Спорт: FC Test STR 12 / STA 15", richSnapshot.SportsText, "Snapshot sports label parsed");
AssertEqual(80, richSnapshot.Energy, "Snapshot energy parsed");
AssertEqual(70, richSnapshot.Mood, "Snapshot mood parsed");
AssertEqual(25, richSnapshot.Hunger, "Snapshot hunger parsed");
AssertEqual("body_sturdy", richSnapshot.Avatar.BodyPresetCode, "Snapshot avatar body parsed");
AssertEqual("face_20", richSnapshot.Avatar.FacePresetCode, "Snapshot avatar face parsed");
AssertEqual("hair_long_02", richSnapshot.Avatar.HairStyleCode, "Snapshot avatar hair parsed");
AssertEqual("upper_designer_coat", richSnapshot.Avatar.EquippedOutfit["upper"], "Snapshot equipped upper parsed");
AssertEqual("humanoid_context_v1", richSnapshot.Avatar.AnimationProfileCode, "Snapshot animation profile parsed");
AssertEqual(42, richSnapshot.Avatar.FashionScore, "Snapshot fashion score parsed");
AssertEqual(false, richSnapshot.Onboarding.Completed, "Snapshot onboarding completion parsed");
AssertEqual("housing_search", richSnapshot.Onboarding.Stage, "Snapshot onboarding stage parsed");
AssertEqual(false, richSnapshot.Onboarding.CanReportToPolice, "Police choice removed after report");
AssertEqual(true, richSnapshot.Onboarding.CanFindHousing, "Housing choice remains available");
AssertEqual(75.0, richSnapshot.Onboarding.PoliceRecoveryAmount, "Police recovery amount parsed");
AssertEqual(true, richSnapshot.Onboarding.PoliceRecoveryClaimable, "Due police recovery parsed");
AssertEqual(
	"ONBOARDING_HOUSING_SEARCH_TITLE",
	richSnapshot.Onboarding.TitleKey,
	"Housing stage maps to a localized title key"
);
AssertEqual(
	"ONBOARDING_HOUSING_SEARCH_NARRATIVE",
	richSnapshot.Onboarding.NarrativeKey,
	"Housing stage maps to a localized narrative key"
);
AssertEqual(
	"ONBOARDING_POLICE_PENDING",
	richSnapshot.Onboarding.PoliceStatusKey,
	"Police status maps to a localized status key"
);

var defaultSnapshotJson = JsonNode.Parse(
	"""
	{
		"owned_businesses": [],
		"sports_contract": null
	}
	"""
)!;
var defaultSnapshot = DashboardPlayerSnapshot.FromJson(defaultSnapshotJson);
AssertEqual("Гість", defaultSnapshot.Username, "Snapshot default username");
AssertEqual("High School", defaultSnapshot.EducationLevel, "Snapshot default education");
AssertEqual("Безробітний", defaultSnapshot.Job, "Snapshot default job");
AssertEqual(false, defaultSnapshot.HasJob, "Snapshot default has no job");
AssertEqual("Вулиця", defaultSnapshot.Hostel, "Snapshot default hostel");
AssertEqual("", defaultSnapshot.OwnedBusinessId, "Snapshot default owned business id");
AssertEqual("Бізнес: немає", defaultSnapshot.OwnedBusinessText, "Snapshot default owned business text");
AssertEqual("Спорт: немає", defaultSnapshot.SportsText, "Snapshot default sports text");
AssertEqual(true, defaultSnapshot.Onboarding.Completed, "Legacy snapshot defaults to completed onboarding");
AssertEqual("body_standard", defaultSnapshot.Avatar.BodyPresetCode, "Legacy snapshot uses default avatar body");
AssertEqual("face_01", defaultSnapshot.Avatar.FacePresetCode, "Legacy snapshot uses default avatar face");
AssertEqual("upper_stock_jacket", defaultSnapshot.Avatar.EquippedOutfit["upper"], "Legacy snapshot uses default outfit");

var arrivalSnapshot = DashboardPlayerSnapshot.FromJson(JsonNode.Parse(
	"""
	{
		"onboarding": {
			"stage": "arrival_choice",
			"completed": false,
			"title": "Новий початок",
			"narrative": "Таксі зникло разом із багажем.",
			"available_choices": ["report_to_police", "find_housing"],
			"police_report_status": "not_filed",
			"police_recovery_claimable": false
		}
	}
	"""
)!);
AssertEqual(false, arrivalSnapshot.Onboarding.Completed, "Arrival snapshot keeps onboarding open");
AssertEqual(true, arrivalSnapshot.Onboarding.CanReportToPolice, "Arrival offers police choice");
AssertEqual(true, arrivalSnapshot.Onboarding.CanFindHousing, "Arrival offers housing choice");
AssertEqual(
	"ONBOARDING_ARRIVAL_CHOICE_TITLE",
	arrivalSnapshot.Onboarding.TitleKey,
	"Arrival choice maps to a localized title key"
);
AssertEqual(
	"ONBOARDING_ARRIVAL_CHOICE_NARRATIVE",
	arrivalSnapshot.Onboarding.NarrativeKey,
	"Arrival choice maps to a localized narrative key"
);
AssertEqual(DashboardTutorialAgeGroup.Adult, arrivalSnapshot.TutorialAgeGroup, "Legacy snapshot defaults to adult guidance");
var teenSnapshot = DashboardPlayerSnapshot.FromJson(JsonNode.Parse("""{"tutorial_age_group":"teen"}""")!);
AssertEqual(DashboardTutorialAgeGroup.Teen, teenSnapshot.TutorialAgeGroup, "Snapshot parses teen guidance group");
AssertEqual(3, DashboardArrivalStory.Count, "Arrival story has three setup beats");
AssertEqual("ARRIVAL_BEAT_1_TITLE", DashboardArrivalStory.Get(0).TitleKey, "Arrival story starts with stable title key");
AssertEqual("ARRIVAL_BEAT_1_NARRATIVE", DashboardArrivalStory.Get(0).NarrativeKey, "Arrival story starts with stable narrative key");
AssertEqual("ARRIVAL_BEAT_3_TITLE", DashboardArrivalStory.Get(2).TitleKey, "Arrival story ends with stable title key");
AssertEqual("ARRIVAL_BEAT_3_NARRATIVE", DashboardArrivalStory.Get(2).NarrativeKey, "Arrival story ends with stable narrative key");
AssertEqual(
	"ARRIVAL_BEAT_2_TEEN_NARRATIVE",
	DashboardArrivalStory.Get(1, DashboardTutorialAgeGroup.Teen).NarrativeKey,
	"Teen guidance uses direct reassuring copy"
);
AssertEqual(
	"ARRIVAL_BEAT_2_ADULT_NARRATIVE",
	DashboardArrivalStory.Get(1, DashboardTutorialAgeGroup.Adult).NarrativeKey,
	"Adult guidance uses balanced copy"
);
AssertEqual(
	"ARRIVAL_BEAT_2_MATURE_NARRATIVE",
	DashboardArrivalStory.Get(1, DashboardTutorialAgeGroup.Mature).NarrativeKey,
	"Mature guidance emphasizes planning"
);
AssertEqual(DashboardTutorialAgeGroup.Adult, DashboardTutorialProfile.ParseAgeGroup(""), "Missing age group defaults to adult");
AssertEqual(DashboardTutorialAgeGroup.Teen, DashboardTutorialProfile.ParseAgeGroup("TEEN"), "Age group parsing ignores case");
AssertEqual("mature", DashboardTutorialProfile.ToApiValue(DashboardTutorialAgeGroup.Mature), "Mature age group API value");
AssertEqual("New Citizen", DashboardCharacterCreation.NormalizeUsername("  New Citizen  "), "Character name is trimmed");
AssertEqual("", DashboardCharacterCreation.ValidateUsername("Player"), "Valid character name has no error");
AssertEqual(
	DashboardCharacterCreation.InvalidUsernameKey,
	DashboardCharacterCreation.ValidateUsername("a"),
	"Short character name returns a semantic error"
);
AssertEqual(
	DashboardCharacterCreation.InvalidUsernameKey,
	DashboardCharacterCreation.ValidateUsername(new string('x', 25)),
	"Long character name returns a semantic error"
);
AssertEqual("adult", DashboardCharacterCreation.NormalizeAgeGroup("unknown"), "Unknown guidance group falls back to adult");
AssertEqual("mature", DashboardCharacterCreation.NormalizeAgeGroup("MATURE"), "Guidance group normalization ignores case");
var avatarSelection = DashboardAvatarSelection.Default;
AssertEqual("body_standard", avatarSelection.BodyPresetCode, "Avatar selection default body");
AssertEqual("face_01", avatarSelection.FacePresetCode, "Avatar selection default face");
AssertEqual("body_sturdy", avatarSelection.CycleBody(1).BodyPresetCode, "Avatar body advances");
AssertEqual("body_sturdy", avatarSelection.CycleBody(-1).BodyPresetCode, "Avatar body wraps backwards");
AssertEqual("face_20", avatarSelection.CycleFace(-1).FacePresetCode, "Avatar face wraps backwards");
AssertEqual("skin_04", avatarSelection.CycleSkin(1).SkinToneCode, "Avatar skin advances");
AssertEqual("hair_bald", avatarSelection.CycleHairStyle(-1).HairStyleCode, "Avatar hair wraps backwards");
AssertEqual("hair_black", avatarSelection.CycleHairColor(-1).HairColorCode, "Avatar hair color wraps backwards");
AssertEqual(20, DashboardAvatarSelection.FacePresetCodes.Count, "Avatar selection exposes twenty faces");
AssertEqual(3, DashboardAvatarSelection.PositionOf(
	DashboardAvatarSelection.SkinToneCodes,
	avatarSelection.SkinToneCode
), "Avatar selection resolves one-based position");
AssertEqual(
	"hair_short_01",
	avatarSelection.ToApiPayload()["hair_style_code"],
	"Avatar selection builds API payload"
);
AssertEqual("face_01", avatarSelection.ToProfile().FacePresetCode, "Avatar selection builds renderer profile");
var activeAvatar = DashboardActiveAvatarState.FromSnapshot(richSnapshot);
AssertEqual("solo-dev", activeAvatar.Username, "Active avatar uses snapshot username");
AssertEqual(20, activeAvatar.FaceNumber, "Active avatar resolves persisted face");
AssertEqual("solo-dev | face 20 | fashion 42", activeAvatar.IdentityText, "Active avatar identity text");
AssertEqual(AvatarActivity.Phone, activeAvatar.Activity.Activity, "Housing search drives phone activity");
AssertEqual(
	DashboardAvatarActivityResolver.HousingSearchReason,
	activeAvatar.Activity.ReasonCode,
	"Avatar activity keeps its environment reason"
);
AssertEqual(true, activeAvatar.ShowsFullAvatar(true), "Street focus shows full active avatar");
AssertEqual(false, activeAvatar.ShowsFullAvatar(false), "City overview keeps marker representation");
AssertEqual(false, DashboardActiveAvatarState.Empty.ShowsFullAvatar(true), "Guest identity does not render as player");
AssertEqual(
	AvatarActivity.Talk,
	DashboardAvatarActivityResolver.Resolve(new DashboardPlayerSnapshot
	{
		Onboarding = new DashboardOnboardingState { Stage = "arrival_choice", Completed = false },
	}).Activity,
	"Arrival conversation drives talk activity"
);
AssertEqual(
	AvatarActivity.Sit,
	DashboardAvatarActivityResolver.Resolve(new DashboardPlayerSnapshot
	{
		Energy = 20,
		Hostel = "Hostel A",
	}).Activity,
	"Low energy drives sit activity"
);
AssertEqual(
	AvatarActivity.Phone,
	DashboardAvatarActivityResolver.Resolve(new DashboardPlayerSnapshot
	{
		Energy = 80,
		Hostel = "Вулиця",
	}).Activity,
	"Missing housing drives phone activity"
);
AssertEqual(
	AvatarActivity.Talk,
	DashboardAvatarActivityResolver.Resolve(new DashboardPlayerSnapshot
	{
		Energy = 80,
		Hostel = "Apartment",
		OwnedBusinessId = "business-1",
		Job = "Бариста",
	}).Activity,
	"Business operations take priority over commute activity"
);
AssertEqual(
	AvatarActivity.Walk,
	DashboardAvatarActivityResolver.Resolve(new DashboardPlayerSnapshot
	{
		Energy = 80,
		Hostel = "Apartment",
		Job = "Бариста",
	}).Activity,
	"Active job drives commute activity"
);
AssertEqual(
	AvatarActivity.Idle,
	DashboardAvatarActivityResolver.Resolve(new DashboardPlayerSnapshot
	{
		Energy = 80,
		Hostel = "Apartment",
	}).Activity,
	"Stable player state uses ambient idle"
);
AssertEqual("uk", DashboardLocaleProfile.Normalize(""), "Missing locale defaults to Ukrainian");
AssertEqual("en", DashboardLocaleProfile.Normalize(" EN "), "Supported locale normalization trims and ignores case");
AssertEqual("uk", DashboardLocaleProfile.Normalize("de"), "Unsupported locale falls back to Ukrainian");
AssertEqual(DashboardArrivalVisual.WaitingHall, DashboardArrivalStory.Get(0).Visual, "First beat uses waiting hall");
AssertEqual(DashboardArrivalVisual.WaitingHall, DashboardArrivalStory.Get(1).Visual, "Second beat reuses waiting hall");
AssertEqual(DashboardArrivalVisual.TaxiRide, DashboardArrivalStory.Get(2).Visual, "Final story beat uses taxi ride");
AssertEqual(DashboardArrivalPortrait.Stranger, DashboardArrivalStory.Get(0).Portrait, "First beat shows stranger portrait");
AssertEqual(DashboardPortraitSide.Right, DashboardArrivalStory.Get(1).PortraitSide, "Stranger stays on the right");
AssertEqual(DashboardArrivalPortrait.TaxiDriver, DashboardArrivalStory.Get(2).Portrait, "Taxi beat shows driver portrait");
AssertEqual(DashboardPortraitSide.Right, DashboardArrivalStory.Get(2).PortraitSide, "Taxi driver reinforces the right-side driver");
AssertEqual(
	"res://assets/visual/core/arrival_waiting_hall_core.png",
	DashboardVisualStylePacks.ResolveArrivalAsset("core", DashboardArrivalVisual.WaitingHall),
	"Core style resolves waiting hall asset"
);
AssertEqual(
	"res://assets/visual/core/arrival_taxi_ride_core.png",
	DashboardVisualStylePacks.ResolveArrivalAsset("anime", DashboardArrivalVisual.TaxiRide),
	"Missing anime scene falls back to core asset"
);
AssertEqual(
	"res://assets/visual/core/arrival_bus_station_core_v2.png",
	DashboardVisualStylePacks.ResolveArrivalAsset("unknown", DashboardArrivalVisual.BaggageTheft),
	"Unknown style falls back to core theft scene"
);
AssertEqual(
	"res://assets/visual/core/arrival_portrait_stranger_core.png",
	DashboardVisualStylePacks.ResolveArrivalPortrait("anime", DashboardArrivalPortrait.Stranger),
	"Missing anime portrait falls back to core stranger"
);
AssertEqual(
	"",
	DashboardVisualStylePacks.ResolveArrivalPortrait("core", DashboardArrivalPortrait.None),
	"Empty portrait resolves without an asset"
);

var visualCityJson = JsonNode.Parse(
	"""
	{
		"name": "Тестове місто",
		"districts": [
			{
				"code": "bus_station",
				"name": "Автовокзал",
				"rent_level": 20,
				"job_supply": 15,
				"crime_risk": 12,
				"traffic": 45,
				"service_coverage": 70,
				"medical_coverage": 55,
				"land_value": 60,
				"desirability": 62
			},
			{
				"code": "industrial_edge",
				"name": "Промзона",
				"rent_level": 10,
				"job_supply": 35,
				"crime_risk": 22,
				"traffic": 70,
				"service_coverage": 50,
				"medical_coverage": 40,
				"land_value": 45,
				"desirability": 38
			}
		]
	}
	"""
)!;
var visualModel = DashboardCityVisualModel.FromCityStatus(visualCityJson);
AssertEqual("Тестове місто", visualModel.CityName, "Visual model city name");
AssertEqual(2, visualModel.Districts.Count, "Visual model district count");
AssertEqual("Вокзал", visualModel.Districts[0].ShortLabel, "Visual model short district label");
AssertEqual(122, visualModel.Districts[1].PressureScore, "Visual model pressure score");
AssertEqual("Тестове місто: 2 районів | робота 50 | злочинність max 22", visualModel.HeadlineText, "Visual model headline");

var emptyPortfolio = DashboardBuildingPortfolio.FromJson(JsonNode.Parse("""{"buildings": []}""")!);
AssertEqual(0, emptyPortfolio.Buildings.Count, "Empty building portfolio count");
AssertEqual("Будівлі: немає", emptyPortfolio.SummaryText, "Empty building portfolio summary");
AssertEqual(null, emptyPortfolio.OpenCandidate, "Empty building portfolio open action");
AssertEqual(null, emptyPortfolio.RepairCandidate, "Empty building portfolio repair action");

var activePortfolioJson = JsonNode.Parse(
	"""
	{
		"buildings": [
			{
				"id": "building-1",
				"name": "Вокзальний кіоск",
				"district_code": "bus_station",
				"district_name": "Автовокзал",
				"operating_status": "inactive",
				"blueprint_code": "station_kiosk",
				"blueprint_name": "Вокзальний кіоск",
				"blueprint_category": "starter_retail",
				"project_type": "commercial",
				"opening_fee": 100.0,
				"repair_fee": 25.0,
				"upkeep_daily": 8.0,
				"available_actions": ["open"]
			}
		]
	}
	"""
)!;
var activePortfolio = DashboardBuildingPortfolio.FromJson(activePortfolioJson);
AssertEqual(1, activePortfolio.Buildings.Count, "Portfolio parses building count");
AssertEqual("building-1", activePortfolio.OpenCandidate!.Id, "Portfolio open candidate id");
AssertEqual("bus_station", activePortfolio.Buildings[0].DistrictCode, "Portfolio district code");
AssertEqual("station_kiosk", activePortfolio.Buildings[0].BlueprintCode, "Portfolio blueprint code");
AssertEqual("commercial", activePortfolio.Buildings[0].ProjectType, "Portfolio project type");
AssertEqual(null, activePortfolio.RepairCandidate, "Inactive building has no repair candidate");
AssertEqual("1 будівля: Вокзальний кіоск | не відкрита, відкриття 100 ₴ | Автовокзал | upkeep 8 ₴", activePortfolio.SummaryText, "Inactive portfolio summary");

var repairPortfolioJson = JsonNode.Parse(
	"""
	{
		"buildings": [
			{
				"id": "building-2",
				"name": "Портфельний кіоск",
				"district_code": "bus_station",
				"district_name": "Автовокзал",
				"operating_status": "maintenance_due",
				"blueprint_code": "station_kiosk",
				"project_type": "commercial",
				"repair_fee": 25.0,
				"upkeep_daily": 8.0,
				"available_actions": ["repair"]
			}
		]
	}
	"""
)!;
var repairPortfolio = DashboardBuildingPortfolio.FromJson(repairPortfolioJson);
AssertEqual("building-2", repairPortfolio.RepairCandidate!.Id, "Portfolio repair candidate id");
AssertEqual(null, repairPortfolio.OpenCandidate, "Maintenance building has no open candidate");
AssertEqual("1 будівля: Портфельний кіоск | потрібен ремонт 25 ₴ | Автовокзал | upkeep 8 ₴", repairPortfolio.SummaryText, "Repair portfolio summary");
var visualWithPortfolio = visualModel.WithPortfolio(repairPortfolio);
AssertEqual(1, visualWithPortfolio.BuildingCount, "Visual model portfolio building count");
AssertEqual(1, visualWithPortfolio.ProblemBuildingCount, "Visual model problem building count");
AssertEqual(0, visualWithPortfolio.ActiveBuildingCount, "Visual model active building count");
AssertEqual("K", visualWithPortfolio.Buildings[0].ArchetypeLabel, "Visual model building archetype label");
AssertEqual("bus_station", visualWithPortfolio.Buildings[0].DistrictCode, "Visual model building district code");
AssertNear(0.5, DashboardVisualAnimation.Pulse(0.0, 1.0), 0.0001, "Visual pulse starts centered");
AssertNear(1.0, DashboardVisualAnimation.Pulse(0.25, 1.0), 0.0001, "Visual pulse reaches peak");
AssertNear(0.25, DashboardVisualAnimation.TravelFraction(0.25, 1.0), 0.0001, "Visual travel advances");
AssertNear(0.25, DashboardVisualAnimation.TravelFraction(1.25, 1.0), 0.0001, "Visual travel wraps");
AssertNear(0.0, DashboardVisualAnimation.TravelFraction(double.NaN), 0.0001, "Visual travel rejects invalid time");
AssertSequence(new[] { "core", "anime", "hyperreal", "mafia" }, DashboardVisualPalettes.Codes.ToArray(), "Visual style codes");
AssertEqual("core", DashboardVisualPalettes.Resolve(null).Code, "Visual palette defaults to core");
AssertEqual("anime", DashboardVisualPalettes.Resolve(" ANIME ").Code, "Visual palette normalizes code");
AssertEqual("hyperreal", DashboardVisualPalettes.Resolve("hyperreal").Code, "Visual palette resolves hyperreal");
AssertEqual("mafia", DashboardVisualPalettes.Resolve("mafia").Code, "Visual palette resolves mafia");
AssertEqual("core", DashboardVisualPalettes.Resolve("unknown").Code, "Visual palette rejects unknown style");
AssertEqual("core", DashboardVisualPalettes.Resolve("dark_fantasy").Code, "Removed visual style falls back to core");
AssertNear(0.25, DashboardVisualPalettes.Core.Danger.WithAlpha(0.25f).Alpha, 0.0001, "Visual token alpha override");
AssertNear(0.72, DashboardVisualPalettes.Anime.CanvasShade.Red, 0.0001, "Anime palette keeps an airy sky base");
AssertNear(0.24, DashboardVisualPalettes.Anime.Accent.Red, 0.0001, "Anime palette uses a cyan accent");
AssertNear(0.98, DashboardVisualPalettes.Anime.Traffic.Red, 0.0001, "Anime palette uses a coral activity accent");
AssertEqual(AvatarActivity.Phone, AvatarPresentationRules.ParseActivity(" PHONE "), "Avatar activity normalizes code");
AssertEqual(AvatarActivity.Idle, AvatarPresentationRules.ParseActivity("combat"), "Unsupported avatar activity falls back");
AssertEqual(AvatarActivity.Walk, AvatarPresentationRules.NextActivity(AvatarActivity.Idle), "Avatar activity sequence advances");
AssertEqual(AvatarActivity.Idle, AvatarPresentationRules.NextActivity(AvatarActivity.Talk), "Avatar activity sequence wraps");
AssertEqual(AvatarLodLevel.Cinematic, AvatarPresentationRules.ResolveLod(50.0f, true), "Cinematic camera forces full detail");
AssertEqual(AvatarLodLevel.Street, AvatarPresentationRules.ResolveLod(8.0f), "Near camera uses street avatar");
AssertEqual(AvatarLodLevel.Distance, AvatarPresentationRules.ResolveLod(18.0f), "District camera uses distance avatar");
AssertEqual(AvatarLodLevel.Marker, AvatarPresentationRules.ResolveLod(40.0f), "City camera uses marker");
AssertEqual(false, AvatarPresentationRules.UsesSkinnedAvatar(AvatarLodLevel.Distance), "Distance LOD disables skinned avatar");
var defaultAppearance = AvatarAppearanceResolver.Resolve(new DashboardAvatarProfile());
AssertEqual("body_standard", defaultAppearance.BodyPresetCode, "Avatar appearance keeps default body");
AssertEqual(1, defaultAppearance.Face.PresetIndex, "Avatar appearance resolves default face");
AssertEqual("hair_short_01", defaultAppearance.HairStyleCode, "Avatar appearance resolves default hair");
AssertSequence(new[] { "HairShort01" }, defaultAppearance.VisibleHairGroups.ToArray(), "Default hair mesh group");
AssertNear(1.0, defaultAppearance.TorsoWidthScale, 0.0001, "Default body width");
AssertNear(0.90, defaultAppearance.SkinColor.Red, 0.0001, "Default skin token");

var sturdyAppearance = AvatarAppearanceResolver.Resolve(
	new DashboardAvatarProfile
	{
		BodyPresetCode = "body_sturdy",
		FacePresetCode = "face_20",
		SkinToneCode = "skin_06",
		HairStyleCode = "hair_long_02",
		HairColorCode = "hair_auburn",
	}
);
AssertEqual("body_sturdy", sturdyAppearance.BodyPresetCode, "Avatar appearance resolves sturdy body");
AssertEqual(20, sturdyAppearance.Face.PresetIndex, "Avatar appearance resolves face 20");
AssertSequence(new[] { "HairLong02" }, sturdyAppearance.VisibleHairGroups.ToArray(), "Long hair mesh group");
AssertNear(1.14, sturdyAppearance.TorsoWidthScale, 0.0001, "Sturdy torso width");
AssertNear(0.30, sturdyAppearance.SkinColor.Red, 0.0001, "Deep skin token");
AssertNear(0.54, sturdyAppearance.HairColor.Red, 0.0001, "Auburn hair token");

var fallbackAppearance = AvatarAppearanceResolver.Resolve(
	new DashboardAvatarProfile
	{
		BodyPresetCode = "body_unknown",
		FacePresetCode = "face_99",
		SkinToneCode = "skin_unknown",
		HairStyleCode = "hair_unknown",
		HairColorCode = "hair_unknown",
	}
);
AssertEqual("body_standard", fallbackAppearance.BodyPresetCode, "Unknown body falls back");
AssertEqual(1, fallbackAppearance.Face.PresetIndex, "Unknown face falls back");
AssertEqual("skin_03", fallbackAppearance.SkinToneCode, "Unknown skin falls back");
AssertEqual("hair_short_01", fallbackAppearance.HairStyleCode, "Unknown hair falls back");

var faceShapes = Enumerable.Range(1, 20)
	.Select(index => AvatarAppearanceResolver.Resolve(
		new DashboardAvatarProfile { FacePresetCode = $"face_{index:00}" }
	).Face)
	.ToArray();
AssertEqual(20, faceShapes.Select(face =>
	$"{face.HeadWidthScale:F3}:{face.HeadHeightScale:F3}:{face.EyeSpacingScale:F3}:{face.EyeScale:F3}:{face.EyeHeightOffset:F3}:{face.MouthWidthScale:F3}"
).Distinct().Count(), "All face presets resolve unique geometry parameters");
AssertEqual(true, faceShapes.All(face =>
	face.HeadWidthScale is >= 0.90f and <= 1.10f
	&& face.HeadHeightScale is >= 0.90f and <= 1.10f
	&& face.EyeScale is >= 0.88f and <= 1.08f
	&& face.MouthWidthScale is >= 0.85f and <= 1.10f
), "Face preset parameters stay within safe bounds");
var baldAppearance = AvatarAppearanceResolver.Resolve(
	new DashboardAvatarProfile { HairStyleCode = "hair_bald" }
);
AssertEqual(0, baldAppearance.VisibleHairGroups.Count, "Bald appearance hides every hair mesh group");

var landCatalogJson = JsonNode.Parse(
	"""
	{
		"parcels": [
			{
				"id": "land-1",
				"code": "bus_station_kiosk_lot",
				"label": "Мала ділянка біля вокзалу",
				"district_name": "Автовокзал",
				"land_type": "in_city",
				"zoning_type": "commercial",
				"area_hectares": 0.20,
				"current_price": 200.0,
				"status": "city_owned",
				"owner_player_id": null
			},
			{
				"id": "land-2",
				"code": "owned_lot",
				"label": "Вже куплена ділянка",
				"district_name": "Комерційний центр",
				"land_type": "in_city",
				"zoning_type": "commercial",
				"area_hectares": 0.50,
				"current_price": 350.0,
				"status": "owned",
				"owner_player_id": "player-1"
			}
		]
	}
	"""
)!;
var blueprintCatalogJson = JsonNode.Parse(
	"""
	{
		"blueprints": [
			{
				"id": "blueprint-1",
				"code": "station_kiosk",
				"name": "Вокзальний кіоск",
				"category": "starter_retail",
				"project_type": "commercial",
				"description": "Малий торговий кіоск біля вокзалу.",
				"difficulty": "easy",
				"allowed_land_types": ["in_city"],
				"allowed_zoning_types": ["commercial"],
				"min_area_hectares": 0.20,
				"construction_cost": 300.0,
				"opening_fee": 100.0,
				"recommended_cash_reserve": 150.0,
				"daily_profit_min": 20.0,
				"daily_profit_max": 55.0,
				"upkeep_daily": 8.0,
				"risk_level": 1,
				"risks": ["Низька маржа."],
				"player_hints": ["Підходить як перший бізнес."]
			},
			{
				"id": "blueprint-2",
				"code": "coffee_shop",
				"name": "Кав'ярня району",
				"category": "food_service",
				"project_type": "commercial",
				"description": "Невелика кав'ярня.",
				"difficulty": "easy",
				"allowed_land_types": ["in_city"],
				"allowed_zoning_types": ["commercial"],
				"min_area_hectares": 0.35,
				"construction_cost": 650.0,
				"opening_fee": 120.0,
				"recommended_cash_reserve": 300.0,
				"daily_profit_min": 30.0,
				"daily_profit_max": 85.0,
				"upkeep_daily": 15.0,
				"risk_level": 2,
				"risks": [],
				"player_hints": []
			}
		]
	}
	"""
)!;
var buildCatalog = DashboardBuildCatalog.FromJson(landCatalogJson, blueprintCatalogJson);
AssertEqual(2, buildCatalog.LandOptions.Count, "Build catalog parses land options");
AssertEqual(2, buildCatalog.Blueprints.Count, "Build catalog parses blueprints");
var starterLand = buildCatalog.StarterLandFor(500)!;
AssertEqual("land-1", starterLand.Id, "Build catalog chooses affordable city land");
AssertEqual(true, starterLand.IsCityOwned, "Starter land must be city-owned");
AssertEqual(null, buildCatalog.StarterLandFor(199), "Build catalog rejects unaffordable land");
var ownedLand = buildCatalog.OwnedLandFor("player-1")!;
AssertEqual("land-2", ownedLand.Id, "Build catalog finds owned land");
AssertEqual(true, ownedLand.IsOwnedBy("player-1"), "Owned land matches player id");
var compatibleBlueprints = buildCatalog.BlueprintsFor(starterLand);
AssertEqual(1, compatibleBlueprints.Count, "Build catalog filters incompatible blueprints");
AssertEqual("station_kiosk", compatibleBlueprints[0].Code, "Build catalog keeps compatible starter blueprint");
AssertEqual("20-55 ₴/день", compatibleBlueprints[0].ProfitText, "Blueprint profit text");
AssertEqual("ризик 1/5", compatibleBlueprints[0].RiskText, "Blueprint risk text");
AssertSequence(new[] { "Низька маржа." }, compatibleBlueprints[0].Risks.ToArray(), "Blueprint risks parsed");
var starterPlan = buildCatalog.StarterPlanFor(500)!;
AssertEqual("land-1", starterPlan.Land.Id, "Starter plan land id");
AssertEqual("blueprint-1", starterPlan.Blueprint.Id, "Starter plan blueprint id");
AssertEqual(550.0, starterPlan.Blueprint.TotalRecommendedBudget, "Starter blueprint recommended budget");
AssertEqual("Перший план: Вокзальний кіоск | земля 200 ₴ | будівництво 300 ₴ | відкриття 100 ₴ | резерв 150 ₴", buildCatalog.SummaryFor(500), "Starter plan summary");
var applicationPlan = buildCatalog.StarterApplicationPlanFor("player-1")!;
AssertEqual("land-2", applicationPlan.Land.Id, "Application plan uses owned land");
AssertEqual("Заявка: Вокзальний кіоск | Вже куплена ділянка | 20-55 ₴/день | ризик 1/5", applicationPlan.ApplicationSummaryText, "Application plan summary");
AssertEqual("Погоджено: Вокзальний кіоск | можна створити будівлю", applicationPlan.ActivationSummaryText, "Activation plan summary");
AssertEqual("Будівництво: бракує коштів або сумісної ділянки", buildCatalog.SummaryFor(199), "Build catalog explains missing starter plan");

AssertEqual(
	DashboardPlayerActionEndpoint.Vacancies,
	DashboardPlayerActionEndpoints.Classify("/api/jobs/vacancies"),
	"Vacancies endpoint classification");
AssertEqual(
	DashboardPlayerActionEndpoint.JobApply,
	DashboardPlayerActionEndpoints.Classify("/api/jobs/apply"),
	"Job apply endpoint classification");
AssertEqual(
	DashboardPlayerActionEndpoint.JobApply,
	DashboardPlayerActionEndpoints.Classify("/api/jobs/apply/player-1"),
	"Job apply path endpoint classification");
AssertEqual(
	DashboardPlayerActionEndpoint.Work,
	DashboardPlayerActionEndpoints.Classify("/api/jobs/work/player-1"),
	"Work endpoint classification");
AssertEqual(
	DashboardPlayerActionEndpoint.Sleep,
	DashboardPlayerActionEndpoints.Classify("/api/hostels/sleep/player-1"),
	"Sleep endpoint classification");
AssertEqual(
	DashboardPlayerActionEndpoint.Eat,
	DashboardPlayerActionEndpoints.Classify("/api/needs/eat/player-1"),
	"Eat endpoint classification");
AssertEqual(
	DashboardPlayerActionEndpoint.BusinessMarket,
	DashboardPlayerActionEndpoints.Classify("/api/businesses/market"),
	"Business market endpoint classification");
AssertEqual(
	DashboardPlayerActionEndpoint.SportsClubs,
	DashboardPlayerActionEndpoints.Classify("/api/sports/clubs"),
	"Sports clubs endpoint classification");
AssertEqual(
	DashboardPlayerActionEndpoint.ExamInfo,
	DashboardPlayerActionEndpoints.Classify("/api/education/exam/info"),
	"Exam info endpoint classification");
AssertEqual(
	DashboardPlayerActionEndpoint.None,
	DashboardPlayerActionEndpoints.Classify("/api/player/player-1/buildings"),
	"Non-player-action endpoint classification");
AssertEqual(
	DashboardPlayerActionEndpoint.None,
	DashboardPlayerActionEndpoints.Classify("/api/jobs/vacancies/archive"),
	"Near-match endpoint classification");

var parsedResponse = DashboardApiResponseParser.Parse("""{"success":true,"data":{"id":"city-1"}}""");
AssertEqual(
	DashboardApiResponseParseStatus.Success,
	parsedResponse.Status,
	"Valid API response parse status");
AssertEqual("city-1", parsedResponse.Root?["data"]?["id"]?.ToString(), "Valid API response data");
AssertEqual(
	DashboardApiResponseParseStatus.Empty,
	DashboardApiResponseParser.Parse("").Status,
	"Empty API response parse status");
AssertEqual(
	DashboardApiResponseParseStatus.Empty,
	DashboardApiResponseParser.Parse("   ").Status,
	"Whitespace API response parse status");
AssertEqual(
	DashboardApiResponseParseStatus.Malformed,
	DashboardApiResponseParser.Parse("""{"success":true""").Status,
	"Malformed API response parse status");

Console.WriteLine("Client logic tests passed.");
