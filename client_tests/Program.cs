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
AssertEqual(false, noPlayerActions.Refresh.Disabled, "Refresh stays available without player");

var readyActions = DashboardActionViewModel.Build(ActionState());
AssertEqual(false, readyActions.Work.Disabled, "Work enabled when allowed");
AssertEqual("Працювати", readyActions.Work.Text, "Work default label");
AssertEqual(false, readyActions.CollectDividend.Disabled, "Dividend enabled with owned business");

var noBusinessActions = DashboardActionViewModel.Build(ActionState(hasOwnedBusiness: false));
AssertEqual(true, noBusinessActions.CollectDividend.Disabled, "Dividend disabled without owned business");

var pendingWorkActions = DashboardActionViewModel.Build(ActionState(pendingWork: true));
AssertEqual(true, pendingWorkActions.ApplyJob.Disabled, "Pending work disables other actions");
AssertEqual(true, pendingWorkActions.Sleep.Disabled, "Pending work disables sleep");
AssertEqual("Працюємо...", pendingWorkActions.Work.Text, "Pending work label");
AssertEqual(true, pendingWorkActions.Work.Disabled, "Pending work button is disabled while busy");

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

Console.WriteLine("Client logic tests passed.");
