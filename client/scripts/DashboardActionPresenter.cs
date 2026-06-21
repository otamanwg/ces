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
        var view = DashboardActionViewModel.Build(state);
        SetButtonState(_applyJobButton, view.ApplyJob, DashboardActionCategory.Work);
        SetButtonState(_workButton, view.Work, DashboardActionCategory.Work);
        SetButtonState(_sleepButton, view.Sleep, DashboardActionCategory.Survival);
        SetButtonState(_eatButton, view.Eat, DashboardActionCategory.Survival);
        SetButtonState(_buyBusinessButton, view.BuyBusiness, DashboardActionCategory.Business);
        SetButtonState(_collectDividendButton, view.CollectDividend, DashboardActionCategory.Business);
        SetButtonState(_joinSportsButton, view.JoinSports, DashboardActionCategory.Sports);
        SetButtonState(_trainSportsButton, view.TrainSports, DashboardActionCategory.Sports);
        SetButtonState(_examButton, view.Exam, DashboardActionCategory.Work);
        SetButtonState(_refreshButton, view.Refresh, DashboardActionCategory.System);
    }

    private static void SetButtonState(Button button, DashboardButtonView view, DashboardActionCategory category)
    {
        if (button != null)
        {
            button.Disabled = view.Disabled;
            button.Text = view.Text;
            button.TooltipText = view.Tooltip;
            var accent = DashboardActionCategoryStyle.Accent(category);
            // Modulate dims when disabled, full accent when available.
            button.Modulate = view.Disabled
                ? new Color(accent.Red * 0.5f, accent.Green * 0.5f, accent.Blue * 0.5f, 0.72f)
                : new Color(accent.Red, accent.Green, accent.Blue);
        }
    }
}
