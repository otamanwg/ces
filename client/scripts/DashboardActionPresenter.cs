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
        SetButtonState(_applyJobButton, view.ApplyJob);
        SetButtonState(_workButton, view.Work);
        SetButtonState(_sleepButton, view.Sleep);
        SetButtonState(_eatButton, view.Eat);
        SetButtonState(_buyBusinessButton, view.BuyBusiness);
        SetButtonState(_collectDividendButton, view.CollectDividend);
        SetButtonState(_joinSportsButton, view.JoinSports);
        SetButtonState(_trainSportsButton, view.TrainSports);
        SetButtonState(_examButton, view.Exam);
        SetButtonState(_refreshButton, view.Refresh);
    }

    private static void SetButtonState(Button button, DashboardButtonView view)
    {
        if (button != null)
        {
            button.Disabled = view.Disabled;
            button.Text = view.Text;
            button.TooltipText = view.Tooltip;
        }
    }
}
