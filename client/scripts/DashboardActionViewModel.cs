public sealed record DashboardButtonView(string Text, bool Disabled);

public sealed record DashboardActionsView(
	DashboardButtonView ApplyJob,
	DashboardButtonView Work,
	DashboardButtonView Sleep,
	DashboardButtonView Eat,
	DashboardButtonView BuyBusiness,
	DashboardButtonView CollectDividend,
	DashboardButtonView JoinSports,
	DashboardButtonView TrainSports,
	DashboardButtonView Exam,
	DashboardButtonView Refresh);

public static class DashboardActionViewModel
{
	public static DashboardActionsView Build(DashboardActionState state)
	{
		bool actionBusy = state.BootstrapPending
			|| state.PendingApply
			|| state.PendingBusinessMarket
			|| state.PendingSportsClubs
			|| state.PendingExamInfo
			|| state.PendingRefresh
			|| state.PendingWork
			|| state.PendingSleep
			|| state.PendingEat
			|| state.PendingBusinessBuy
			|| state.PendingDividend
			|| state.PendingSportsJoin
			|| state.PendingSportsTrain
			|| state.PendingExam;

		string examButtonText = state.PendingExam
			? "Надсилаємо..."
			: state.PendingExamInfo ? "Завантаження..." : "Іспит";

		return new DashboardActionsView(
			ApplyJob: new DashboardButtonView(state.PendingApply ? "Шукаємо..." : "Знайти роботу", !state.HasPlayer || !state.CanApplyJob || actionBusy),
			Work: new DashboardButtonView(state.PendingWork ? "Працюємо..." : "Працювати", !state.HasPlayer || !state.CanWork || actionBusy),
			Sleep: new DashboardButtonView(state.PendingSleep ? "Спимо..." : "Спати", !state.HasPlayer || !state.CanSleep || actionBusy),
			Eat: new DashboardButtonView(state.PendingEat ? "Їмо..." : "Поїсти", !state.HasPlayer || !state.CanEat || actionBusy),
			BuyBusiness: new DashboardButtonView(state.PendingBusinessBuy ? "Купуємо..." : state.PendingBusinessMarket ? "Шукаємо..." : "Купити бізнес", !state.HasPlayer || !state.CanBuyBusiness || actionBusy),
			CollectDividend: new DashboardButtonView(state.PendingDividend ? "Збираємо..." : "Зібрати дивіденд", !state.HasPlayer || !state.CanCollectDividend || !state.HasOwnedBusiness || actionBusy),
			JoinSports: new DashboardButtonView(state.PendingSportsJoin ? "Підписуємо..." : state.PendingSportsClubs ? "Шукаємо..." : "У спорт", !state.HasPlayer || !state.CanJoinSports || actionBusy),
			TrainSports: new DashboardButtonView(state.PendingSportsTrain ? "Тренуємось..." : "Тренуватись", !state.HasPlayer || !state.CanTrainSports || actionBusy),
			Exam: new DashboardButtonView(examButtonText, !state.HasPlayer || !state.CanTakeExam || actionBusy),
			Refresh: new DashboardButtonView(state.PendingRefresh ? "Оновлюємо..." : "Оновити", state.BootstrapPending || state.PendingRefresh)
		);
	}
}
