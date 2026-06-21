using Godot;
using System.Collections.Generic;

/// <summary>
/// Sprint 61: Political panel overlay controller.
/// Displays city office status, election status, candidates.
/// Emits signals for hire office, register candidate, vote, start election.
/// </summary>
public partial class PoliticalPanelController : Control
{
    [Export] public Label TitleLabel;
    [Export] public Label DescriptionLabel;
    [Export] public VBoxContainer OfficeContainer;
    [Export] public VBoxContainer ElectionContainer;
    [Export] public VBoxContainer CandidatesContainer;
    [Export] public Button CloseButton;
    [Export] public Button HireOfficeButton;
    [Export] public Button RegisterCandidateButton;
    [Export] public Button StartElectionButton;
    [Export] public OptionButton CandidateOptionButton;

    private DashboardPoliticalModel _model;

    public override void _Ready()
    {
        TitleLabel ??= GetNodeOrNull<Label>("%PoliticalTitleLabel");
        DescriptionLabel ??= GetNodeOrNull<Label>("%PoliticalDescriptionLabel");
        OfficeContainer ??= GetNodeOrNull<VBoxContainer>("%PoliticalOfficeContainer");
        ElectionContainer ??= GetNodeOrNull<VBoxContainer>("%PoliticalElectionContainer");
        CandidatesContainer ??= GetNodeOrNull<VBoxContainer>("%PoliticalCandidatesContainer");
        CloseButton ??= GetNodeOrNull<Button>("%PoliticalCloseButton");
        HireOfficeButton ??= GetNodeOrNull<Button>("%PoliticalHireOfficeButton");
        RegisterCandidateButton ??= GetNodeOrNull<Button>("%PoliticalRegisterCandidateButton");
        StartElectionButton ??= GetNodeOrNull<Button>("%PoliticalStartElectionButton");
        CandidateOptionButton ??= GetNodeOrNull<OptionButton>("%PoliticalCandidateOption");

        Visible = false;
        MouseFilter = MouseFilterEnum.Ignore;

        if (CloseButton != null)
        {
            CloseButton.Pressed += OnClosePressed;
        }

        if (HireOfficeButton != null)
        {
            HireOfficeButton.Pressed += OnHireOfficePressed;
        }

        if (RegisterCandidateButton != null)
        {
            RegisterCandidateButton.Pressed += OnRegisterCandidatePressed;
        }

        if (StartElectionButton != null)
        {
            StartElectionButton.Pressed += OnStartElectionPressed;
        }
    }

    public void LoadModel(DashboardPoliticalModel model)
    {
        _model = model;
        MouseFilter = MouseFilterEnum.Stop;
        Visible = true;

        if (TitleLabel != null)
        {
            TitleLabel.Text = "Політика";
        }

        if (DescriptionLabel != null)
        {
            DescriptionLabel.Text = model.IsMayor
                ? $"Ви — мер міста"
                : model.MayorName != null
                    ? $"Мер: {model.MayorName}"
                    : "Мера немає";
        }

        PopulateOffice(model);
        PopulateElection(model);
        PopulateCandidates(model);
        UpdateActionButtons(model);
    }

    private void PopulateOffice(DashboardPoliticalModel model)
    {
        if (OfficeContainer == null)
        {
            return;
        }

        foreach (Node child in OfficeContainer.GetChildren())
        {
            child.QueueFree();
        }

        if (!model.HasOffice)
        {
            OfficeContainer.AddChild(new Label { Text = "Ви не працюєте в мерії" });
            return;
        }

        OfficeContainer.AddChild(new Label
        {
            Text = $"🏛 {model.Office!.SummaryText}",
            AutowrapMode = TextServer.AutowrapMode.WordSmart,
        });
        OfficeContainer.AddChild(new Label
        {
            Text = $"Стаж: з дня {model.Office!.HiredAtGameDay}",
            AutowrapMode = TextServer.AutowrapMode.WordSmart,
        });

        if (model.MayorEligible)
        {
            OfficeContainer.AddChild(new Label
            {
                Text = "✓ Відповідає вимогам мера",
                AutowrapMode = TextServer.AutowrapMode.WordSmart,
            });
        }
    }

    private void PopulateElection(DashboardPoliticalModel model)
    {
        if (ElectionContainer == null)
        {
            return;
        }

        foreach (Node child in ElectionContainer.GetChildren())
        {
            child.QueueFree();
        }

        if (!model.HasActiveElection)
        {
            ElectionContainer.AddChild(new Label { Text = "Активних виборів немає" });
            return;
        }

        var election = model.Election!;
        ElectionContainer.AddChild(new Label
        {
            Text = $"🗳 Вибори: дні {election.StartedAtGameDay}–{election.EndsAtGameDay}",
            AutowrapMode = TextServer.AutowrapMode.WordSmart,
        });
    }

    private void PopulateCandidates(DashboardPoliticalModel model)
    {
        if (CandidatesContainer == null)
        {
            return;
        }

        foreach (Node child in CandidatesContainer.GetChildren())
        {
            child.QueueFree();
        }

        CandidateOptionButton?.Clear();

        if (model.Candidates.Count == 0)
        {
            CandidatesContainer.AddChild(new Label { Text = "Кандидатів немає" });
            return;
        }

        int idx = 0;
        foreach (var candidate in model.Candidates)
        {
            CandidatesContainer.AddChild(new Label
            {
                Text = $"👤 {candidate.SummaryText}",
                AutowrapMode = TextServer.AutowrapMode.WordSmart,
            });

            if (CandidateOptionButton != null)
            {
                CandidateOptionButton.AddItem(candidate.PlayerName, idx);
                CandidateOptionButton.SetItemMetadata(idx, candidate.CandidateId);
                idx++;
            }
        }

        if (CandidateOptionButton != null && CandidateOptionButton.ItemCount > 0)
        {
            CandidateOptionButton.Select(0);
        }
    }

    private void UpdateActionButtons(DashboardPoliticalModel model)
    {
        if (HireOfficeButton != null)
        {
            HireOfficeButton.Disabled = model.HasOffice;
        }

        if (RegisterCandidateButton != null)
        {
            RegisterCandidateButton.Disabled = !model.HasActiveElection || !model.MayorEligible;
        }

        if (StartElectionButton != null)
        {
            StartElectionButton.Disabled = model.HasActiveElection;
        }
    }

    private void OnHireOfficePressed()
    {
        EmitSignal(SignalName.HireOfficeRequested);
    }

    private void OnRegisterCandidatePressed()
    {
        EmitSignal(SignalName.RegisterCandidateRequested);
    }

    private void OnStartElectionPressed()
    {
        EmitSignal(SignalName.StartElectionRequested);
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
    public delegate void HireOfficeRequestedEventHandler();

    [Signal]
    public delegate void RegisterCandidateRequestedEventHandler();

    [Signal]
    public delegate void StartElectionRequestedEventHandler();

    [Signal]
    public delegate void ClosedEventHandler();
}
