using Godot;
using System.Collections.Generic;

/// <summary>
/// Sprint 61: Atelier panel overlay controller.
/// Displays shop skins and player's owned skins.
/// Emits signals for buy skin, equip skin, unequip all.
/// </summary>
public partial class AtelierPanelController : Control
{
    [Export] public Label TitleLabel;
    [Export] public Label DescriptionLabel;
    [Export] public VBoxContainer ShopContainer;
    [Export] public VBoxContainer InventoryContainer;
    [Export] public Button CloseButton;
    [Export] public Button BuyButton;
    [Export] public Button EquipButton;
    [Export] public Button UnequipAllButton;
    [Export] public OptionButton ShopSkinOption;
    [Export] public OptionButton PlayerSkinOption;

    private DashboardAtelierModel _model;

    public override void _Ready()
    {
        TitleLabel ??= GetNodeOrNull<Label>("%AtelierTitleLabel");
        DescriptionLabel ??= GetNodeOrNull<Label>("%AtelierDescriptionLabel");
        ShopContainer ??= GetNodeOrNull<VBoxContainer>("%AtelierShopContainer");
        InventoryContainer ??= GetNodeOrNull<VBoxContainer>("%AtelierInventoryContainer");
        CloseButton ??= GetNodeOrNull<Button>("%AtelierCloseButton");
        BuyButton ??= GetNodeOrNull<Button>("%AtelierBuyButton");
        EquipButton ??= GetNodeOrNull<Button>("%AtelierEquipButton");
        UnequipAllButton ??= GetNodeOrNull<Button>("%AtelierUnequipAllButton");
        ShopSkinOption ??= GetNodeOrNull<OptionButton>("%AtelierShopSkinOption");
        PlayerSkinOption ??= GetNodeOrNull<OptionButton>("%AtelierPlayerSkinOption");

        Visible = false;
        MouseFilter = MouseFilterEnum.Ignore;

        if (CloseButton != null)
        {
            CloseButton.Pressed += OnClosePressed;
        }

        if (BuyButton != null)
        {
            BuyButton.Pressed += OnBuyPressed;
        }

        if (EquipButton != null)
        {
            EquipButton.Pressed += OnEquipPressed;
        }

        if (UnequipAllButton != null)
        {
            UnequipAllButton.Pressed += OnUnequipAllPressed;
        }
    }

    public void LoadModel(DashboardAtelierModel model)
    {
        _model = model;
        MouseFilter = MouseFilterEnum.Stop;
        Visible = true;

        if (TitleLabel != null)
        {
            TitleLabel.Text = "Ательє";
        }

        if (DescriptionLabel != null)
        {
            DescriptionLabel.Text = model.HasPlayerSkins
                ? $"Скінів: {model.PlayerSkins.Count} | У магазині: {model.ShopSkins.Count}"
                : $"У магазині: {model.ShopSkins.Count} скінів";
        }

        PopulateShop(model);
        PopulateInventory(model);
        UpdateActionButtons(model);
    }

    private void PopulateShop(DashboardAtelierModel model)
    {
        if (ShopContainer == null)
        {
            return;
        }

        foreach (Node child in ShopContainer.GetChildren())
        {
            child.QueueFree();
        }

        ShopSkinOption?.Clear();

        if (model.ShopSkins.Count == 0)
        {
            ShopContainer.AddChild(new Label { Text = "Скіни у продажу відсутні" });
            return;
        }

        int idx = 0;
        foreach (var skin in model.ShopSkins)
        {
            ShopContainer.AddChild(new Label
            {
                Text = $"🎨 {skin.SummaryText}",
                AutowrapMode = TextServer.AutowrapMode.WordSmart,
            });

            if (ShopSkinOption != null)
            {
                ShopSkinOption.AddItem($"{skin.Name} ({skin.RarityLabel})", idx);
                ShopSkinOption.SetItemMetadata(idx, skin.SkinId);
                idx++;
            }
        }

        if (ShopSkinOption != null && ShopSkinOption.ItemCount > 0)
        {
            ShopSkinOption.Select(0);
        }
    }

    private void PopulateInventory(DashboardAtelierModel model)
    {
        if (InventoryContainer == null)
        {
            return;
        }

        foreach (Node child in InventoryContainer.GetChildren())
        {
            child.QueueFree();
        }

        PlayerSkinOption?.Clear();

        if (model.PlayerSkins.Count == 0)
        {
            InventoryContainer.AddChild(new Label { Text = "У вас немає скінів" });
            return;
        }

        int idx = 0;
        foreach (var skin in model.PlayerSkins)
        {
            InventoryContainer.AddChild(new Label
            {
                Text = $"👤 {skin.SummaryText}",
                AutowrapMode = TextServer.AutowrapMode.WordSmart,
            });

            if (PlayerSkinOption != null)
            {
                PlayerSkinOption.AddItem(skin.Name, idx);
                PlayerSkinOption.SetItemMetadata(idx, skin.PlayerSkinId);
                idx++;
            }
        }

        if (PlayerSkinOption != null && PlayerSkinOption.ItemCount > 0)
        {
            PlayerSkinOption.Select(0);
        }
    }

    private void UpdateActionButtons(DashboardAtelierModel model)
    {
        if (BuyButton != null)
        {
            BuyButton.Disabled = model.ShopSkins.Count == 0;
        }

        if (EquipButton != null)
        {
            EquipButton.Disabled = model.PlayerSkins.Count == 0;
        }

        if (UnequipAllButton != null)
        {
            UnequipAllButton.Disabled = !model.HasEquippedSkin;
        }
    }

    private string GetSelectedShopSkinId()
    {
        if (ShopSkinOption == null || ShopSkinOption.Selected < 0)
        {
            return "";
        }

        return ShopSkinOption.GetSelectedMetadata().ToString() ?? "";
    }

    private string GetSelectedPlayerSkinId()
    {
        if (PlayerSkinOption == null || PlayerSkinOption.Selected < 0)
        {
            return "";
        }

        return PlayerSkinOption.GetSelectedMetadata().ToString() ?? "";
    }

    private void OnBuyPressed()
    {
        string skinId = GetSelectedShopSkinId();
        EmitSignal(SignalName.BuyRequested, skinId);
    }

    private void OnEquipPressed()
    {
        string playerSkinId = GetSelectedPlayerSkinId();
        EmitSignal(SignalName.EquipRequested, playerSkinId);
    }

    private void OnUnequipAllPressed()
    {
        EmitSignal(SignalName.UnequipAllRequested);
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
    public delegate void BuyRequestedEventHandler(string skinId);

    [Signal]
    public delegate void EquipRequestedEventHandler(string playerSkinId);

    [Signal]
    public delegate void UnequipAllRequestedEventHandler();

    [Signal]
    public delegate void ClosedEventHandler();
}
