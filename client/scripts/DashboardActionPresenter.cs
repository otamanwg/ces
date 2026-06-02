using Godot;

public sealed class DashboardActionPresenter
{
	private readonly Button _applyJobButton;
	private readonly Button _workButton;
	private readonly Button _sleepButton;
	private readonly Button _eatButton;
	private readonly Button _buyBusinessButton;
	private readonly Button _collectDividendButton;
	private readonly Button _joinSportsButton;
	private readonly Button _trainSportsButton;
	private readonly Button _examButton;
	private readonly Button _refreshButton;

	public DashboardActionPresenter(
		Button applyJobButton,
		Button workButton,
		Button sleepButton,
		Button eatButton,
		Button buyBusinessButton,
		Button collectDividendButton,
		Button joinSportsButton,
		Button trainSportsButton,
		Button examButton,
		Button refreshButton)
	{
		_applyJobButton = applyJobButton;
		_workButton = workButton;
		_sleepButton = sleepButton;
		_eatButton = eatButton;
		_buyBusinessButton = buyBusinessButton;
		_collectDividendButton = collectDividendButton;
		_joinSportsButton = joinSportsButton;
		_trainSportsButton = trainSportsButton;
		_examButton = examButton;
		_refreshButton = refreshButton;
	}

	public void Update(DashboardActionState state)
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

		SetButtonState(_applyJobButton, !state.HasPlayer || !state.CanApplyJob || actionBusy, state.PendingApply ? "Шукаємо..." : "Знайти роботу");
		SetButtonState(_workButton, !state.HasPlayer || !state.CanWork || actionBusy, state.PendingWork ? "Працюємо..." : "Працювати");
		SetButtonState(_sleepButton, !state.HasPlayer || !state.CanSleep || actionBusy, state.PendingSleep ? "Спимо..." : "Спати");
		SetButtonState(_eatButton, !state.HasPlayer || !state.CanEat || actionBusy, state.PendingEat ? "Їмо..." : "Поїсти");
		SetButtonState(_buyBusinessButton, !state.HasPlayer || !state.CanBuyBusiness || actionBusy, state.PendingBusinessBuy ? "Купуємо..." : state.PendingBusinessMarket ? "Шукаємо..." : "Купити бізнес");
		SetButtonState(_collectDividendButton, !state.HasPlayer || !state.CanCollectDividend || !state.HasOwnedBusiness || actionBusy, state.PendingDividend ? "Збираємо..." : "Зібрати дивіденд");
		SetButtonState(_joinSportsButton, !state.HasPlayer || !state.CanJoinSports || actionBusy, state.PendingSportsJoin ? "Підписуємо..." : state.PendingSportsClubs ? "Шукаємо..." : "У спорт");
		SetButtonState(_trainSportsButton, !state.HasPlayer || !state.CanTrainSports || actionBusy, state.PendingSportsTrain ? "Тренуємось..." : "Тренуватись");

		string examButtonText = state.PendingExam
			? "Надсилаємо..."
			: state.PendingExamInfo ? "Завантаження..." : "Іспит";
		SetButtonState(_examButton, !state.HasPlayer || !state.CanTakeExam || actionBusy, examButtonText);
		SetButtonState(_refreshButton, state.BootstrapPending || state.PendingRefresh, state.PendingRefresh ? "Оновлюємо..." : "Оновити");
	}

	private static void SetButtonState(Button button, bool disabled, string text)
	{
		if (button != null)
		{
			button.Disabled = disabled;
			button.Text = text;
		}
	}
}

public readonly record struct DashboardActionState(
	bool HasPlayer,
	bool BootstrapPending,
	bool PendingApply,
	bool PendingBusinessMarket,
	bool PendingSportsClubs,
	bool PendingExamInfo,
	bool PendingRefresh,
	bool PendingWork,
	bool PendingSleep,
	bool PendingEat,
	bool PendingBusinessBuy,
	bool PendingDividend,
	bool PendingSportsJoin,
	bool PendingSportsTrain,
	bool PendingExam,
	bool CanApplyJob,
	bool CanWork,
	bool CanSleep,
	bool CanEat,
	bool CanBuyBusiness,
	bool CanCollectDividend,
	bool CanJoinSports,
	bool CanTrainSports,
	bool CanTakeExam,
	bool HasOwnedBusiness);
