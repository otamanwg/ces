using System;
using System.Linq;

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

Console.WriteLine("Client logic tests passed.");
