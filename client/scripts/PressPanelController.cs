using Godot;
using System.Collections.Generic;

/// <summary>
/// Sprint 61: Press/media panel overlay controller.
/// Displays investigations (journalist view) and blackmails (target view).
/// Emits signals for investigate, publish, blackmail, respond to blackmail.
/// </summary>
public partial class PressPanelController : Control
{
    [Export] public Label TitleLabel;
    [Export] public Label DescriptionLabel;
    [Export] public VBoxContainer InvestigationsContainer;
    [Export] public VBoxContainer BlackmailsContainer;
    [Export] public Button CloseButton;
    [Export] public Button InvestigateButton;
    [Export] public Button PublishButton;
    [Export] public Button BlackmailButton;
    [Export] public OptionButton InvestigationOptionButton;
    [Export] public Button AcceptBlackmailButton;
    [Export] public Button RefuseBlackmailButton;
    [Export] public Button ReportBlackmailButton;
    [Export] public OptionButton BlackmailOptionButton;

    private DashboardPressModel _model;

    public override void _Ready()
    {
        TitleLabel ??= GetNodeOrNull<Label>("%PressTitleLabel");
        DescriptionLabel ??= GetNodeOrNull<Label>("%PressDescriptionLabel");
        InvestigationsContainer ??= GetNodeOrNull<VBoxContainer>("%PressInvestigationsContainer");
        BlackmailsContainer ??= GetNodeOrNull<VBoxContainer>("%PressBlackmailsContainer");
        CloseButton ??= GetNodeOrNull<Button>("%PressCloseButton");
        InvestigateButton ??= GetNodeOrNull<Button>("%PressInvestigateButton");
        PublishButton ??= GetNodeOrNull<Button>("%PressPublishButton");
        BlackmailButton ??= GetNodeOrNull<Button>("%PressBlackmailButton");
        InvestigationOptionButton ??= GetNodeOrNull<OptionButton>("%PressInvestigationOption");
        AcceptBlackmailButton ??= GetNodeOrNull<Button>("%PressAcceptBlackmailButton");
        RefuseBlackmailButton ??= GetNodeOrNull<Button>("%PressRefuseBlackmailButton");
        ReportBlackmailButton ??= GetNodeOrNull<Button>("%PressReportBlackmailButton");
        BlackmailOptionButton ??= GetNodeOrNull<OptionButton>("%PressBlackmailOption");

        Visible = false;
        MouseFilter = MouseFilterEnum.Ignore;

        if (CloseButton != null)
        {
            CloseButton.Pressed += OnClosePressed;
        }

        if (InvestigateButton != null)
        {
            InvestigateButton.Pressed += OnInvestigatePressed;
        }

        if (PublishButton != null)
        {
            PublishButton.Pressed += OnPublishPressed;
        }

        if (BlackmailButton != null)
        {
            BlackmailButton.Pressed += OnBlackmailPressed;
        }

        if (AcceptBlackmailButton != null)
        {
            AcceptBlackmailButton.Pressed += OnAcceptBlackmailPressed;
        }

        if (RefuseBlackmailButton != null)
        {
            RefuseBlackmailButton.Pressed += OnRefuseBlackmailPressed;
        }

        if (ReportBlackmailButton != null)
        {
            ReportBlackmailButton.Pressed += OnReportBlackmailPressed;
        }
    }

    public void LoadModel(DashboardPressModel model)
    {
        _model = model;
        MouseFilter = MouseFilterEnum.Stop;
        Visible = true;

        if (TitleLabel != null)
        {
            TitleLabel.Text = "Преса";
        }

        if (DescriptionLabel != null)
        {
            DescriptionLabel.Text = model.HasPendingBlackmails
                ? "У вас є очікуваний шантаж!"
                : model.HasInvestigations
                    ? $"Розслідувань: {model.Investigations.Count}"
                    : "Активних розслідувань немає";
        }

        PopulateInvestigations(model);
        PopulateBlackmails(model);
        UpdateActionButtons(model);
    }

    private void PopulateInvestigations(DashboardPressModel model)
    {
        if (InvestigationsContainer == null)
        {
            return;
        }

        foreach (Node child in InvestigationsContainer.GetChildren())
        {
            child.QueueFree();
        }

        InvestigationOptionButton?.Clear();

        if (model.Investigations.Count == 0)
        {
            InvestigationsContainer.AddChild(new Label { Text = "Розслідувань немає" });
            return;
        }

        int idx = 0;
        foreach (var investigation in model.Investigations)
        {
            InvestigationsContainer.AddChild(new Label
            {
                Text = $"🔍 {investigation.SummaryText}",
                AutowrapMode = TextServer.AutowrapMode.WordSmart,
            });

            if (InvestigationOptionButton != null)
            {
                string label = investigation.IsPublished
                    ? $"[опубл.] {investigation.ArticleTitle ?? "Скандал"}"
                    : $"[докази {investigation.PressEvidence:P0}] {investigation.IncidentType}";
                InvestigationOptionButton.AddItem(label, idx);
                InvestigationOptionButton.SetItemMetadata(idx, investigation.Id);
                idx++;
            }
        }

        if (InvestigationOptionButton != null && InvestigationOptionButton.ItemCount > 0)
        {
            InvestigationOptionButton.Select(0);
        }
    }

    private void PopulateBlackmails(DashboardPressModel model)
    {
        if (BlackmailsContainer == null)
        {
            return;
        }

        foreach (Node child in BlackmailsContainer.GetChildren())
        {
            child.QueueFree();
        }

        BlackmailOptionButton?.Clear();

        if (model.Blackmails.Count == 0)
        {
            BlackmailsContainer.AddChild(new Label { Text = "Шантажів немає" });
            return;
        }

        int idx = 0;
        foreach (var blackmail in model.Blackmails)
        {
            BlackmailsContainer.AddChild(new Label
            {
                Text = $"💸 {blackmail.SummaryText}",
                AutowrapMode = TextServer.AutowrapMode.WordSmart,
            });

            if (BlackmailOptionButton != null && blackmail.Status == "pending")
            {
                BlackmailOptionButton.AddItem($"{blackmail.AmountDemanded:N0} ₴", idx);
                BlackmailOptionButton.SetItemMetadata(idx, blackmail.Id);
                idx++;
            }
        }

        if (BlackmailOptionButton != null && BlackmailOptionButton.ItemCount > 0)
        {
            BlackmailOptionButton.Select(0);
        }
    }

    private void UpdateActionButtons(DashboardPressModel model)
    {
        bool hasPublishable = false;
        foreach (var inv in model.Investigations)
        {
            if (inv.CanPublish)
            {
                hasPublishable = true;
                break;
            }
        }

        if (PublishButton != null)
        {
            PublishButton.Disabled = !hasPublishable;
        }

        if (BlackmailButton != null)
        {
            BlackmailButton.Disabled = !hasPublishable;
        }

        bool hasPending = model.HasPendingBlackmails;
        if (AcceptBlackmailButton != null)
        {
            AcceptBlackmailButton.Disabled = !hasPending;
        }

        if (RefuseBlackmailButton != null)
        {
            RefuseBlackmailButton.Disabled = !hasPending;
        }

        if (ReportBlackmailButton != null)
        {
            ReportBlackmailButton.Disabled = !hasPending;
        }
    }

    private void OnInvestigatePressed()
    {
        EmitSignal(SignalName.InvestigateRequested);
    }

    private void OnPublishPressed()
    {
        string investigationId = GetSelectedInvestigationId();
        EmitSignal(SignalName.PublishRequested, investigationId);
    }

    private void OnBlackmailPressed()
    {
        string investigationId = GetSelectedInvestigationId();
        EmitSignal(SignalName.BlackmailRequested, investigationId);
    }

    private void OnAcceptBlackmailPressed()
    {
        string blackmailId = GetSelectedBlackmailId();
        EmitSignal(SignalName.BlackmailRespondRequested, blackmailId, "accept");
    }

    private void OnRefuseBlackmailPressed()
    {
        string blackmailId = GetSelectedBlackmailId();
        EmitSignal(SignalName.BlackmailRespondRequested, blackmailId, "refuse");
    }

    private void OnReportBlackmailPressed()
    {
        string blackmailId = GetSelectedBlackmailId();
        EmitSignal(SignalName.BlackmailRespondRequested, blackmailId, "report_to_police");
    }

    private string GetSelectedInvestigationId()
    {
        if (InvestigationOptionButton == null || InvestigationOptionButton.Selected < 0)
        {
            return "";
        }

        return InvestigationOptionButton.GetSelectedMetadata().ToString() ?? "";
    }

    private string GetSelectedBlackmailId()
    {
        if (BlackmailOptionButton == null || BlackmailOptionButton.Selected < 0)
        {
            return "";
        }

        return BlackmailOptionButton.GetSelectedMetadata().ToString() ?? "";
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
    public delegate void InvestigateRequestedEventHandler();

    [Signal]
    public delegate void PublishRequestedEventHandler(string investigationId);

    [Signal]
    public delegate void BlackmailRequestedEventHandler(string investigationId);

    [Signal]
    public delegate void BlackmailRespondRequestedEventHandler(string blackmailId, string action);

    [Signal]
    public delegate void ClosedEventHandler();
}
