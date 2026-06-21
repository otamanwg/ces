using Godot;
using System.Collections.Generic;
using System.Text.Json.Nodes;

/// <summary>
/// Sprint 61: Court/Prison panel overlay controller.
/// Displays court cases, prison sentence, and prison actions.
/// Emits signals for appeal, bribe-judge, prison work/poker/socialize.
/// </summary>
public partial class CourtPanelController : Control
{
    [Export] public Label TitleLabel;
    [Export] public Label DescriptionLabel;
    [Export] public VBoxContainer CasesContainer;
    [Export] public VBoxContainer SentenceContainer;
    [Export] public Button CloseButton;
    [Export] public Button WorkButton;
    [Export] public Button PokerButton;
    [Export] public Button SocializeButton;
    [Export] public SpinBox PokerBetBox;

    private DashboardCourtModel _model;

    public override void _Ready()
    {
        TitleLabel ??= GetNodeOrNull<Label>("%CourtTitleLabel");
        DescriptionLabel ??= GetNodeOrNull<Label>("%CourtDescriptionLabel");
        CasesContainer ??= GetNodeOrNull<VBoxContainer>("%CourtCasesContainer");
        SentenceContainer ??= GetNodeOrNull<VBoxContainer>("%CourtSentenceContainer");
        CloseButton ??= GetNodeOrNull<Button>("%CourtCloseButton");
        WorkButton ??= GetNodeOrNull<Button>("%CourtWorkButton");
        PokerButton ??= GetNodeOrNull<Button>("%CourtPokerButton");
        SocializeButton ??= GetNodeOrNull<Button>("%CourtSocializeButton");
        PokerBetBox ??= GetNodeOrNull<SpinBox>("%CourtPokerBet");

        Visible = false;
        MouseFilter = MouseFilterEnum.Ignore;

        if (CloseButton != null)
        {
            CloseButton.Pressed += OnClosePressed;
        }

        if (WorkButton != null)
        {
            WorkButton.Pressed += OnWorkPressed;
        }

        if (PokerButton != null)
        {
            PokerButton.Pressed += OnPokerPressed;
        }

        if (SocializeButton != null)
        {
            SocializeButton.Pressed += OnSocializePressed;
        }
    }

    public void LoadModel(DashboardCourtModel model)
    {
        _model = model;
        MouseFilter = MouseFilterEnum.Stop;
        Visible = true;

        if (TitleLabel != null)
        {
            TitleLabel.Text = "Суд і тюрма";
        }

        if (DescriptionLabel != null)
        {
            DescriptionLabel.Text = model.IsImprisoned
                ? model.Sentence!.SummaryText
                : "Активного ув'язнення немає";
        }

        PopulateCases(model);
        PopulateSentence(model);
        UpdateActionButtons(model);
    }

    private void PopulateCases(DashboardCourtModel model)
    {
        if (CasesContainer == null)
        {
            return;
        }

        foreach (Node child in CasesContainer.GetChildren())
        {
            child.QueueFree();
        }

        if (model.Cases.Count == 0)
        {
            CasesContainer.AddChild(new Label { Text = "Судових справ немає" });
            return;
        }

        foreach (var courtCase in model.Cases)
        {
            var label = new Label
            {
                Text = $"⚖ {courtCase.SummaryText}",
                AutowrapMode = TextServer.AutowrapMode.WordSmart,
            };
            CasesContainer.AddChild(label);

            if (courtCase.IsAppealed)
            {
                var votesLabel = new Label
                {
                    Text = $"  Судді: {VoteLabel(courtCase.Judge1Vote, courtCase.Judge1Bribed)} | {VoteLabel(courtCase.Judge2Vote, courtCase.Judge2Bribed)} | {VoteLabel(courtCase.Judge3Vote, courtCase.Judge3Bribed)}",
                    AutowrapMode = TextServer.AutowrapMode.WordSmart,
                };
                CasesContainer.AddChild(votesLabel);
            }
        }
    }

    private static string VoteLabel(string vote, bool bribed)
    {
        string label = vote switch
        {
            "overturn" => "скасувати",
            "uphold" => "залишити",
            _ => "очікує",
        };
        return bribed ? $"{label} 💰" : label;
    }

    private void PopulateSentence(DashboardCourtModel model)
    {
        if (SentenceContainer == null)
        {
            return;
        }

        foreach (Node child in SentenceContainer.GetChildren())
        {
            child.QueueFree();
        }

        if (!model.IsImprisoned)
        {
            SentenceContainer.AddChild(new Label { Text = "Ви не у тюрмі" });
            return;
        }

        var sentence = model.Sentence!;
        SentenceContainer.AddChild(new Label
        {
            Text = $"🔒 {sentence.SummaryText}",
            AutowrapMode = TextServer.AutowrapMode.WordSmart,
        });

        var progressBar = new ProgressBar
        {
            MinValue = 0,
            MaxValue = 1,
            Value = sentence.ProgressPct,
            ShowPercentage = true,
            CustomMinimumSize = new Vector2(0, 24),
        };
        SentenceContainer.AddChild(progressBar);

        if (sentence.BusinessImpact != "none")
        {
            SentenceContainer.AddChild(new Label
            {
                Text = $"Бізнес: {sentence.BusinessImpact}",
                AutowrapMode = TextServer.AutowrapMode.WordSmart,
            });
        }
    }

    private void UpdateActionButtons(DashboardCourtModel model)
    {
        bool imprisoned = model.IsImprisoned;
        if (WorkButton != null)
        {
            WorkButton.Disabled = !imprisoned;
        }

        if (PokerButton != null)
        {
            PokerButton.Disabled = !imprisoned;
        }

        if (SocializeButton != null)
        {
            SocializeButton.Disabled = !imprisoned;
        }
    }

    private void OnWorkPressed()
    {
        EmitSignal(SignalName.WorkRequested);
    }

    private void OnPokerPressed()
    {
        double bet = PokerBetBox?.Value ?? 50;
        EmitSignal(SignalName.PokerRequested, bet);
    }

    private void OnSocializePressed()
    {
        EmitSignal(SignalName.SocializeRequested);
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
    public delegate void WorkRequestedEventHandler();

    [Signal]
    public delegate void PokerRequestedEventHandler(double bet);

    [Signal]
    public delegate void SocializeRequestedEventHandler();

    [Signal]
    public delegate void ClosedEventHandler();
}
