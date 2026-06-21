using Godot;
using System.Collections.Generic;

/// <summary>
/// Sprint 61: Shadow economy panel overlay controller.
/// Displays criminal rep, shadow businesses, shadow market.
/// Emits signals for open business, fraud accept/refuse, market buy/sell.
/// </summary>
public partial class ShadowPanelController : Control
{
    [Export] public Label TitleLabel;
    [Export] public Label DescriptionLabel;
    [Export] public VBoxContainer BusinessesContainer;
    [Export] public VBoxContainer MarketContainer;
    [Export] public Button CloseButton;
    [Export] public Button OpenBusinessButton;
    [Export] public Button FraudAcceptButton;
    [Export] public Button FraudRefuseButton;
    [Export] public Button MarketBuyButton;
    [Export] public Button MarketSellButton;
    [Export] public OptionButton ItemTypeOption;
    [Export] public SpinBox QuantityBox;
    [Export] public ProgressBar RepProgressBar;

    private DashboardShadowModel _model;

    public override void _Ready()
    {
        TitleLabel ??= GetNodeOrNull<Label>("%ShadowTitleLabel");
        DescriptionLabel ??= GetNodeOrNull<Label>("%ShadowDescriptionLabel");
        BusinessesContainer ??= GetNodeOrNull<VBoxContainer>("%ShadowBusinessesContainer");
        MarketContainer ??= GetNodeOrNull<VBoxContainer>("%ShadowMarketContainer");
        CloseButton ??= GetNodeOrNull<Button>("%ShadowCloseButton");
        OpenBusinessButton ??= GetNodeOrNull<Button>("%ShadowOpenBusinessButton");
        FraudAcceptButton ??= GetNodeOrNull<Button>("%ShadowFraudAcceptButton");
        FraudRefuseButton ??= GetNodeOrNull<Button>("%ShadowFraudRefuseButton");
        MarketBuyButton ??= GetNodeOrNull<Button>("%ShadowMarketBuyButton");
        MarketSellButton ??= GetNodeOrNull<Button>("%ShadowMarketSellButton");
        ItemTypeOption ??= GetNodeOrNull<OptionButton>("%ShadowItemTypeOption");
        QuantityBox ??= GetNodeOrNull<SpinBox>("%ShadowQuantityBox");
        RepProgressBar ??= GetNodeOrNull<ProgressBar>("%ShadowRepProgressBar");

        Visible = false;
        MouseFilter = MouseFilterEnum.Ignore;

        if (CloseButton != null)
        {
            CloseButton.Pressed += OnClosePressed;
        }

        if (OpenBusinessButton != null)
        {
            OpenBusinessButton.Pressed += OnOpenBusinessPressed;
        }

        if (FraudAcceptButton != null)
        {
            FraudAcceptButton.Pressed += OnFraudAcceptPressed;
        }

        if (FraudRefuseButton != null)
        {
            FraudRefuseButton.Pressed += OnFraudRefusePressed;
        }

        if (MarketBuyButton != null)
        {
            MarketBuyButton.Pressed += OnMarketBuyPressed;
        }

        if (MarketSellButton != null)
        {
            MarketSellButton.Pressed += OnMarketSellPressed;
        }
    }

    public void LoadModel(DashboardShadowModel model)
    {
        _model = model;
        MouseFilter = MouseFilterEnum.Stop;
        Visible = true;

        if (TitleLabel != null)
        {
            TitleLabel.Text = "Тіньова економіка";
        }

        if (DescriptionLabel != null)
        {
            DescriptionLabel.Text = model.HasMarketAccess
                ? $"Кримінальна репутація: {model.CriminalRep:F1}"
                : $"Кримінальна репутація: {model.CriminalRep:F1} (потрібно ≥ 30 для ринку)";
        }

        if (RepProgressBar != null)
        {
            RepProgressBar.MinValue = 0;
            RepProgressBar.MaxValue = 100;
            RepProgressBar.Value = model.CriminalRep;
            RepProgressBar.ShowPercentage = true;
        }

        PopulateBusinesses(model);
        PopulateMarket(model);
        UpdateActionButtons(model);
    }

    private void PopulateBusinesses(DashboardShadowModel model)
    {
        if (BusinessesContainer == null)
        {
            return;
        }

        foreach (Node child in BusinessesContainer.GetChildren())
        {
            child.QueueFree();
        }

        if (model.Businesses.Count == 0)
        {
            BusinessesContainer.AddChild(new Label { Text = "Тіньових бізнесів немає" });
            return;
        }

        foreach (var business in model.Businesses)
        {
            BusinessesContainer.AddChild(new Label
            {
                Text = $"🌑 {business.SummaryText}",
                AutowrapMode = TextServer.AutowrapMode.WordSmart,
            });
        }
    }

    private void PopulateMarket(DashboardShadowModel model)
    {
        if (MarketContainer == null)
        {
            return;
        }

        foreach (Node child in MarketContainer.GetChildren())
        {
            child.QueueFree();
        }

        if (!model.HasMarketAccess)
        {
            MarketContainer.AddChild(new Label { Text = "Доступ до тіньового ринку вимагає criminal_rep ≥ 30" });
            return;
        }

        if (model.MarketItems.Count == 0)
        {
            MarketContainer.AddChild(new Label { Text = "Товарів немає" });
            return;
        }

        foreach (var item in model.MarketItems)
        {
            MarketContainer.AddChild(new Label
            {
                Text = $"📦 {item.SummaryText}",
                AutowrapMode = TextServer.AutowrapMode.WordSmart,
            });
        }
    }

    private void UpdateActionButtons(DashboardShadowModel model)
    {
        bool hasMarketAccess = model.HasMarketAccess;
        if (OpenBusinessButton != null)
        {
            OpenBusinessButton.Disabled = !hasMarketAccess;
        }

        if (MarketBuyButton != null)
        {
            MarketBuyButton.Disabled = !hasMarketAccess;
        }

        if (MarketSellButton != null)
        {
            MarketSellButton.Disabled = !hasMarketAccess;
        }
    }

    private string GetSelectedItem()
    {
        if (ItemTypeOption == null || ItemTypeOption.Selected < 0)
        {
            return "alcohol";
        }

        return ItemTypeOption.GetSelectedMetadata().ToString() ?? "alcohol";
    }

    private int GetQuantity()
    {
        return (int)(QuantityBox?.Value ?? 1);
    }

    private void OnOpenBusinessPressed()
    {
        EmitSignal(SignalName.OpenBusinessRequested);
    }

    private void OnFraudAcceptPressed()
    {
        EmitSignal(SignalName.FraudAcceptRequested);
    }

    private void OnFraudRefusePressed()
    {
        EmitSignal(SignalName.FraudRefuseRequested);
    }

    private void OnMarketBuyPressed()
    {
        string itemType = GetSelectedItem();
        int quantity = GetQuantity();
        EmitSignal(SignalName.MarketBuyRequested, itemType, quantity);
    }

    private void OnMarketSellPressed()
    {
        string itemType = GetSelectedItem();
        int quantity = GetQuantity();
        EmitSignal(SignalName.MarketSellRequested, itemType, quantity);
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
    public delegate void OpenBusinessRequestedEventHandler();

    [Signal]
    public delegate void FraudAcceptRequestedEventHandler();

    [Signal]
    public delegate void FraudRefuseRequestedEventHandler();

    [Signal]
    public delegate void MarketBuyRequestedEventHandler(string itemType, int quantity);

    [Signal]
    public delegate void MarketSellRequestedEventHandler(string itemType, int quantity);

    [Signal]
    public delegate void ClosedEventHandler();
}
