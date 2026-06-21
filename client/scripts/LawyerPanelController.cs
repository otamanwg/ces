using Godot;
using System.Collections.Generic;

/// <summary>
/// Sprint 61: Lawyer panel overlay controller.
/// Displays lawyer level, engagements (as lawyer or client).
/// Emits signals for engage lawyer, appeal case.
/// </summary>
public partial class LawyerPanelController : Control
{
    [Export] public Label TitleLabel;
    [Export] public Label DescriptionLabel;
    [Export] public VBoxContainer EngagementsContainer;
    [Export] public Button CloseButton;
    [Export] public Button EngageButton;
    [Export] public Button AppealButton;
    [Export] public Button LicenseButton;
    [Export] public SpinBox AmountBox;
    [Export] public OptionButton DealTypeOption;

    private DashboardLawyerModel _model;

    public override void _Ready()
    {
        TitleLabel ??= GetNodeOrNull<Label>("%LawyerTitleLabel");
        DescriptionLabel ??= GetNodeOrNull<Label>("%LawyerDescriptionLabel");
        EngagementsContainer ??= GetNodeOrNull<VBoxContainer>("%LawyerEngagementsContainer");
        CloseButton ??= GetNodeOrNull<Button>("%LawyerCloseButton");
        EngageButton ??= GetNodeOrNull<Button>("%LawyerEngageButton");
        AppealButton ??= GetNodeOrNull<Button>("%LawyerAppealButton");
        LicenseButton ??= GetNodeOrNull<Button>("%LawyerLicenseButton");
        AmountBox ??= GetNodeOrNull<SpinBox>("%LawyerAmountBox");
        DealTypeOption ??= GetNodeOrNull<OptionButton>("%LawyerDealTypeOption");

        Visible = false;
        MouseFilter = MouseFilterEnum.Ignore;

        if (CloseButton != null)
        {
            CloseButton.Pressed += OnClosePressed;
        }

        if (EngageButton != null)
        {
            EngageButton.Pressed += OnEngagePressed;
        }

        if (AppealButton != null)
        {
            AppealButton.Pressed += OnAppealPressed;
        }

        if (LicenseButton != null)
        {
            LicenseButton.Pressed += OnLicensePressed;
        }
    }

    public void LoadModel(DashboardLawyerModel model)
    {
        _model = model;
        MouseFilter = MouseFilterEnum.Stop;
        Visible = true;

        if (TitleLabel != null)
        {
            TitleLabel.Text = "Адвокат";
        }

        if (DescriptionLabel != null)
        {
            DescriptionLabel.Text = $"Рівень: {model.LawyerLevel} | Успішних угод: {model.SuccessfulDeals} | Бонус успіху: +{model.SuccessChanceBonus:P0}";
        }

        PopulateEngagements(model);
    }

    private void PopulateEngagements(DashboardLawyerModel model)
    {
        if (EngagementsContainer == null)
        {
            return;
        }

        foreach (Node child in EngagementsContainer.GetChildren())
        {
            child.QueueFree();
        }

        if (model.Engagements.Count == 0)
        {
            EngagementsContainer.AddChild(new Label { Text = "Доручень немає" });
            return;
        }

        foreach (var engagement in model.Engagements)
        {
            EngagementsContainer.AddChild(new Label
            {
                Text = $"⚖ {engagement.SummaryText}",
                AutowrapMode = TextServer.AutowrapMode.WordSmart,
            });
        }
    }

    private double GetAmount()
    {
        return AmountBox?.Value ?? 1000.0;
    }

    private string GetDealType()
    {
        if (DealTypeOption == null || DealTypeOption.Selected < 0)
        {
            return "general";
        }

        return DealTypeOption.GetSelectedMetadata().ToString() ?? "general";
    }

    private void OnEngagePressed()
    {
        double amount = GetAmount();
        string dealType = GetDealType();
        EmitSignal(SignalName.EngageRequested, amount, dealType);
    }

    private void OnAppealPressed()
    {
        EmitSignal(SignalName.AppealRequested);
    }

    private void OnLicensePressed()
    {
        EmitSignal(SignalName.LicenseRequested);
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
    public delegate void EngageRequestedEventHandler(double amount, string dealType);

    [Signal]
    public delegate void AppealRequestedEventHandler();

    [Signal]
    public delegate void LicenseRequestedEventHandler();

    [Signal]
    public delegate void ClosedEventHandler();
}
