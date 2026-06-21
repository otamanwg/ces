using Godot;
using System.Collections.Generic;

/// <summary>
/// Sprint 61: Casino panel overlay controller.
/// Displays casino businesses and poker games.
/// Emits signals for blackjack, roulette, create poker game.
/// </summary>
public partial class CasinoPanelController : Control
{
    [Export] public Label TitleLabel;
    [Export] public Label DescriptionLabel;
    [Export] public VBoxContainer CasinosContainer;
    [Export] public VBoxContainer GamesContainer;
    [Export] public Button CloseButton;
    [Export] public Button BlackjackButton;
    [Export] public Button RouletteButton;
    [Export] public Button CreatePokerButton;
    [Export] public OptionButton CasinoOptionButton;
    [Export] public OptionButton RouletteBetTypeOption;
    [Export] public SpinBox BetBox;

    private DashboardCasinoModel _model;

    public override void _Ready()
    {
        TitleLabel ??= GetNodeOrNull<Label>("%CasinoTitleLabel");
        DescriptionLabel ??= GetNodeOrNull<Label>("%CasinoDescriptionLabel");
        CasinosContainer ??= GetNodeOrNull<VBoxContainer>("%CasinoCasinosContainer");
        GamesContainer ??= GetNodeOrNull<VBoxContainer>("%CasinoGamesContainer");
        CloseButton ??= GetNodeOrNull<Button>("%CasinoCloseButton");
        BlackjackButton ??= GetNodeOrNull<Button>("%CasinoBlackjackButton");
        RouletteButton ??= GetNodeOrNull<Button>("%CasinoRouletteButton");
        CreatePokerButton ??= GetNodeOrNull<Button>("%CasinoCreatePokerButton");
        CasinoOptionButton ??= GetNodeOrNull<OptionButton>("%CasinoCasinoOption");
        RouletteBetTypeOption ??= GetNodeOrNull<OptionButton>("%CasinoRouletteBetTypeOption");
        BetBox ??= GetNodeOrNull<SpinBox>("%CasinoBetBox");

        Visible = false;
        MouseFilter = MouseFilterEnum.Ignore;

        if (CloseButton != null)
        {
            CloseButton.Pressed += OnClosePressed;
        }

        if (BlackjackButton != null)
        {
            BlackjackButton.Pressed += OnBlackjackPressed;
        }

        if (RouletteButton != null)
        {
            RouletteButton.Pressed += OnRoulettePressed;
        }

        if (CreatePokerButton != null)
        {
            CreatePokerButton.Pressed += OnCreatePokerPressed;
        }
    }

    public void LoadModel(DashboardCasinoModel model)
    {
        _model = model;
        MouseFilter = MouseFilterEnum.Stop;
        Visible = true;

        if (TitleLabel != null)
        {
            TitleLabel.Text = "Казино";
        }

        if (DescriptionLabel != null)
        {
            DescriptionLabel.Text = model.HasCasinos
                ? $"Казино: {model.Casinos.Count} | Ігор: {model.Games.Count}"
                : "У вас немає казино";
        }

        PopulateCasinos(model);
        PopulateGames(model);
        UpdateActionButtons(model);
    }

    private void PopulateCasinos(DashboardCasinoModel model)
    {
        if (CasinosContainer == null)
        {
            return;
        }

        foreach (Node child in CasinosContainer.GetChildren())
        {
            child.QueueFree();
        }

        CasinoOptionButton?.Clear();

        if (model.Casinos.Count == 0)
        {
            CasinosContainer.AddChild(new Label { Text = "Казино немає" });
            return;
        }

        int idx = 0;
        foreach (var casino in model.Casinos)
        {
            CasinosContainer.AddChild(new Label
            {
                Text = $"🎰 {casino.SummaryText}",
                AutowrapMode = TextServer.AutowrapMode.WordSmart,
            });

            if (CasinoOptionButton != null)
            {
                CasinoOptionButton.AddItem(casino.Name, idx);
                CasinoOptionButton.SetItemMetadata(idx, casino.Id);
                idx++;
            }
        }

        if (CasinoOptionButton != null && CasinoOptionButton.ItemCount > 0)
        {
            CasinoOptionButton.Select(0);
        }
    }

    private void PopulateGames(DashboardCasinoModel model)
    {
        if (GamesContainer == null)
        {
            return;
        }

        foreach (Node child in GamesContainer.GetChildren())
        {
            child.QueueFree();
        }

        if (model.Games.Count == 0)
        {
            GamesContainer.AddChild(new Label { Text = "Активних ігор немає" });
            return;
        }

        foreach (var game in model.Games)
        {
            GamesContainer.AddChild(new Label
            {
                Text = $"🃏 {game.SummaryText}",
                AutowrapMode = TextServer.AutowrapMode.WordSmart,
            });
        }
    }

    private void UpdateActionButtons(DashboardCasinoModel model)
    {
        bool hasCasino = model.HasCasinos;
        if (BlackjackButton != null)
        {
            BlackjackButton.Disabled = !hasCasino;
        }

        if (RouletteButton != null)
        {
            RouletteButton.Disabled = !hasCasino;
        }

        if (CreatePokerButton != null)
        {
            CreatePokerButton.Disabled = !hasCasino;
        }
    }

    private string GetSelectedCasinoId()
    {
        if (CasinoOptionButton == null || CasinoOptionButton.Selected < 0)
        {
            return "";
        }

        return CasinoOptionButton.GetSelectedMetadata().ToString() ?? "";
    }

    private double GetBetAmount()
    {
        return BetBox?.Value ?? 100.0;
    }

    private string GetRouletteBetType()
    {
        if (RouletteBetTypeOption == null || RouletteBetTypeOption.Selected < 0)
        {
            return "red";
        }

        return RouletteBetTypeOption.GetSelectedMetadata().ToString() ?? "red";
    }

    private void OnBlackjackPressed()
    {
        string casinoId = GetSelectedCasinoId();
        double bet = GetBetAmount();
        EmitSignal(SignalName.BlackjackRequested, casinoId, bet);
    }

    private void OnRoulettePressed()
    {
        string casinoId = GetSelectedCasinoId();
        double bet = GetBetAmount();
        string betType = GetRouletteBetType();
        EmitSignal(SignalName.RouletteRequested, casinoId, bet, betType);
    }

    private void OnCreatePokerPressed()
    {
        string casinoId = GetSelectedCasinoId();
        EmitSignal(SignalName.CreatePokerRequested, casinoId);
    }

    private void OnClosePressed()
    {
        HidePanel();
        EmitSignal(SignalName.Closed);
    }

    public void HidePanel()
    {
        Visible = false;
        MouseFilter = MouseFilterEnum.Ignore;
    }

    [Signal]
    public delegate void BlackjackRequestedEventHandler(string casinoId, double bet);

    [Signal]
    public delegate void RouletteRequestedEventHandler(string casinoId, double bet, string betType);

    [Signal]
    public delegate void CreatePokerRequestedEventHandler(string casinoId);

    [Signal]
    public delegate void ClosedEventHandler();
}
