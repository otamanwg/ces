public sealed record DashboardButtonView(string Text, bool Disabled, string Tooltip);

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
        string busyTooltip = actionBusy ? "Дочекайтесь завершення поточної дії." : "";

        return new DashboardActionsView(
            ApplyJob: BuildButton(state, actionBusy, state.CanApplyJob, state.PendingApply ? "Шукаємо..." : "Знайти роботу", "Немає доступної вакансії для вашої освіти.", busyTooltip),
            Work: BuildButton(state, actionBusy, state.CanWork, state.PendingWork ? "Працюємо..." : "Працювати", "Спочатку знайдіть роботу або відновіть енергію.", busyTooltip),
            Sleep: BuildButton(state, actionBusy, state.CanSleep, state.PendingSleep ? "Спимо..." : "Спати", "Потрібне місце в хостелі.", busyTooltip),
            Eat: BuildButton(state, actionBusy, state.CanEat, state.PendingEat ? "Їмо..." : "Поїсти", "Потрібно більше голоду або коштів на обід.", busyTooltip),
            BuyBusiness: BuildButton(state, actionBusy, state.CanBuyBusiness, state.PendingBusinessBuy ? "Купуємо..." : state.PendingBusinessMarket ? "Шукаємо..." : "Купити бізнес", "Накопичте достатньо коштів для першого бізнесу.", busyTooltip),
            CollectDividend: BuildButton(state, actionBusy, state.CanCollectDividend && state.HasOwnedBusiness, state.PendingDividend ? "Збираємо..." : "Зібрати дивіденд", state.HasOwnedBusiness ? "У бізнесі ще замало каси для дивіденду." : "Спочатку купіть бізнес.", busyTooltip),
            JoinSports: BuildButton(state, actionBusy, state.CanJoinSports, state.PendingSportsJoin ? "Підписуємо..." : state.PendingSportsClubs ? "Шукаємо..." : "У спорт", "Спортивний контракт уже активний.", busyTooltip),
            TrainSports: BuildButton(state, actionBusy, state.CanTrainSports, state.PendingSportsTrain ? "Тренуємось..." : "Тренуватись", "Потрібен спортивний контракт, 40 ₴ і 40 енергії.", busyTooltip),
            Exam: BuildButton(state, actionBusy, state.CanTakeExam, examButtonText, "Іспит доступний для High School після накопичення коштів.", busyTooltip),
            Refresh: new DashboardButtonView(state.PendingRefresh ? "Оновлюємо..." : "Оновити", state.BootstrapPending || state.PendingRefresh, state.BootstrapPending || state.PendingRefresh ? "Оновлення вже виконується." : "Оновити стан міста і гравця.")
        );
    }

    private static DashboardButtonView BuildButton(
        DashboardActionState state,
        bool actionBusy,
        bool actionAllowed,
        string text,
        string unavailableTooltip,
        string busyTooltip)
    {
        return new DashboardButtonView(
            text,
            !state.HasPlayer || !actionAllowed || actionBusy,
            BuildTooltip(state, actionBusy, actionAllowed, "Потрібен зареєстрований гравець.", unavailableTooltip, busyTooltip)
        );
    }

    private static string BuildTooltip(
        DashboardActionState state,
        bool actionBusy,
        bool actionAllowed,
        string noPlayerTooltip,
        string unavailableTooltip,
        string busyTooltip)
    {
        if (!state.HasPlayer)
        {
            return noPlayerTooltip;
        }

        if (actionBusy)
        {
            return busyTooltip;
        }

        return actionAllowed ? "" : unavailableTooltip;
    }
}
