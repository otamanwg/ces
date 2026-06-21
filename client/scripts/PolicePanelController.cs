using Godot;
using System.Collections.Generic;
using System.Text.Json.Nodes;

/// <summary>
/// Sprint 61: Police panel overlay controller.
/// Displays officer status, police records, corruption log.
/// Emits signals for hire, promote, patrol, arrest, confiscate, bribe actions.
/// </summary>
public partial class PolicePanelController : Control
{
    [Export] public Label TitleLabel;
    [Export] public Label DescriptionLabel;
    [Export] public VBoxContainer OfficerContainer;
    [Export] public VBoxContainer RecordsContainer;
    [Export] public VBoxContainer CorruptionLogContainer;
    [Export] public Button CloseButton;
    [Export] public Button HireButton;
    [Export] public Button PromoteButton;
    [Export] public Button PatrolButton;
    [Export] public OptionButton DistrictOptionButton;
    [Export] public Button ArrestButton;
    [Export] public Button ConfiscateButton;

    private DashboardPoliceModel _model;

    public override void _Ready()
    {
        TitleLabel ??= GetNodeOrNull<Label>("%PoliceTitleLabel");
        DescriptionLabel ??= GetNodeOrNull<Label>("%PoliceDescriptionLabel");
        OfficerContainer ??= GetNodeOrNull<VBoxContainer>("%PoliceOfficerContainer");
        RecordsContainer ??= GetNodeOrNull<VBoxContainer>("%PoliceRecordsContainer");
        CorruptionLogContainer ??= GetNodeOrNull<VBoxContainer>("%PoliceCorruptionLogContainer");
        CloseButton ??= GetNodeOrNull<Button>("%PoliceCloseButton");
        HireButton ??= GetNodeOrNull<Button>("%PoliceHireButton");
        PromoteButton ??= GetNodeOrNull<Button>("%PolicePromoteButton");
        PatrolButton ??= GetNodeOrNull<Button>("%PolicePatrolButton");
        DistrictOptionButton ??= GetNodeOrNull<OptionButton>("%PoliceDistrictOption");
        ArrestButton ??= GetNodeOrNull<Button>("%PoliceArrestButton");
        ConfiscateButton ??= GetNodeOrNull<Button>("%PoliceConfiscateButton");

        Visible = false;
        MouseFilter = MouseFilterEnum.Ignore;

        if (CloseButton != null)
        {
            CloseButton.Pressed += OnClosePressed;
        }

        if (HireButton != null)
        {
            HireButton.Pressed += OnHirePressed;
        }

        if (PromoteButton != null)
        {
            PromoteButton.Pressed += OnPromotePressed;
        }

        if (PatrolButton != null)
        {
            PatrolButton.Pressed += OnPatrolPressed;
        }
    }

    public void LoadModel(DashboardPoliceModel model)
    {
        _model = model;
        MouseFilter = MouseFilterEnum.Stop;
        Visible = true;

        if (TitleLabel != null)
        {
            TitleLabel.Text = "Поліція";
        }

        if (DescriptionLabel != null)
        {
            DescriptionLabel.Text = model.IsOfficer
                ? model.Officer!.SummaryText
                : "Ви не є поліцейським";
        }

        PopulateOfficer(model);
        PopulateRecords(model);
        PopulateCorruptionLog(model);
        UpdateActionButtons(model);
    }

    private void PopulateOfficer(DashboardPoliceModel model)
    {
        if (OfficerContainer == null)
        {
            return;
        }

        foreach (Node child in OfficerContainer.GetChildren())
        {
            child.QueueFree();
        }

        if (!model.IsOfficer)
        {
            OfficerContainer.AddChild(new Label { Text = "Ви не є поліцейським. Натисніть 'Найнятися'." });
            return;
        }

        var officer = model.Officer!;
        OfficerContainer.AddChild(new Label
        {
            Text = $"👮 Звання: {officer.RankLabel}",
            AutowrapMode = TextServer.AutowrapMode.WordSmart,
        });
        OfficerContainer.AddChild(new Label
        {
            Text = $"Розслідувань: {officer.SuccessfulInvestigations} | Хабарів: {officer.BribesTaken}",
            AutowrapMode = TextServer.AutowrapMode.WordSmart,
        });
    }

    private void PopulateRecords(DashboardPoliceModel model)
    {
        if (RecordsContainer == null)
        {
            return;
        }

        foreach (Node child in RecordsContainer.GetChildren())
        {
            child.QueueFree();
        }

        if (model.Records.Count == 0)
        {
            RecordsContainer.AddChild(new Label { Text = "Записів немає" });
            return;
        }

        foreach (var record in model.Records)
        {
            RecordsContainer.AddChild(new Label
            {
                Text = $"📋 {record.SummaryText}",
                AutowrapMode = TextServer.AutowrapMode.WordSmart,
            });
        }
    }

    private void PopulateCorruptionLog(DashboardPoliceModel model)
    {
        if (CorruptionLogContainer == null)
        {
            return;
        }

        foreach (Node child in CorruptionLogContainer.GetChildren())
        {
            child.QueueFree();
        }

        if (!model.CanViewCorruptionLog)
        {
            CorruptionLogContainer.AddChild(new Label { Text = "Доступно для детектива+" });
            return;
        }

        if (model.CorruptionLogs.Count == 0)
        {
            CorruptionLogContainer.AddChild(new Label { Text = "Корупційних записів немає" });
            return;
        }

        foreach (var log in model.CorruptionLogs)
        {
            CorruptionLogContainer.AddChild(new Label
            {
                Text = $"🔍 {log.SummaryText}",
                AutowrapMode = TextServer.AutowrapMode.WordSmart,
            });
        }
    }

    private void UpdateActionButtons(DashboardPoliceModel model)
    {
        if (HireButton != null)
        {
            HireButton.Disabled = model.IsOfficer;
        }

        if (PromoteButton != null)
        {
            PromoteButton.Disabled = !model.CanPromote;
        }

        if (PatrolButton != null)
        {
            PatrolButton.Disabled = !model.CanPatrol;
        }

        if (ArrestButton != null)
        {
            ArrestButton.Disabled = !model.CanArrest;
        }

        if (ConfiscateButton != null)
        {
            ConfiscateButton.Disabled = !model.CanConfiscate;
        }
    }

    private void OnHirePressed()
    {
        EmitSignal(SignalName.HireRequested);
    }

    private void OnPromotePressed()
    {
        EmitSignal(SignalName.PromoteRequested);
    }

    private void OnPatrolPressed()
    {
        string districtId = DistrictOptionButton?.GetSelectedId() >= 0
            ? DistrictOptionButton.GetSelectedMetadata().ToString() ?? ""
            : "";
        EmitSignal(SignalName.PatrolRequested, districtId);
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
    public delegate void HireRequestedEventHandler();

    [Signal]
    public delegate void PromoteRequestedEventHandler();

    [Signal]
    public delegate void PatrolRequestedEventHandler(string districtId);

    [Signal]
    public delegate void ClosedEventHandler();
}
