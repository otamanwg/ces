using Godot;
using System.Collections.Generic;
using System.Text.Json.Nodes;

/// <summary>
/// Sprint 61: Bank panel overlay controller.
/// Displays banks, deposits, loans, and auctions.
/// Emits signals for deposit, withdraw, loan, repay, and bid actions.
/// </summary>
public partial class BankPanelController : Control
{
    [Export] public Label TitleLabel;
    [Export] public Label DescriptionLabel;
    [Export] public VBoxContainer BanksContainer;
    [Export] public VBoxContainer DepositsContainer;
    [Export] public VBoxContainer LoansContainer;
    [Export] public VBoxContainer AuctionsContainer;
    [Export] public Button CloseButton;
    [Export] public SpinBox DepositAmountBox;
    [Export] public SpinBox LoanAmountBox;
    [Export] public OptionButton BankOptionButton;
    [Export] public Button DepositButton;
    [Export] public Button LoanButton;

    private DashboardBankModel _model;
    private string _selectedBankId = "";

    public override void _Ready()
    {
        TitleLabel ??= GetNodeOrNull<Label>("%BankTitleLabel");
        DescriptionLabel ??= GetNodeOrNull<Label>("%BankDescriptionLabel");
        BanksContainer ??= GetNodeOrNull<VBoxContainer>("%BankBanksContainer");
        DepositsContainer ??= GetNodeOrNull<VBoxContainer>("%BankDepositsContainer");
        LoansContainer ??= GetNodeOrNull<VBoxContainer>("%BankLoansContainer");
        AuctionsContainer ??= GetNodeOrNull<VBoxContainer>("%BankAuctionsContainer");
        CloseButton ??= GetNodeOrNull<Button>("%BankCloseButton");
        DepositAmountBox ??= GetNodeOrNull<SpinBox>("%BankDepositAmount");
        LoanAmountBox ??= GetNodeOrNull<SpinBox>("%BankLoanAmount");
        BankOptionButton ??= GetNodeOrNull<OptionButton>("%BankBankOption");
        DepositButton ??= GetNodeOrNull<Button>("%BankDepositButton");
        LoanButton ??= GetNodeOrNull<Button>("%BankLoanButton");

        Visible = false;
        MouseFilter = MouseFilterEnum.Ignore;

        if (CloseButton != null)
        {
            CloseButton.Pressed += OnClosePressed;
        }

        if (DepositButton != null)
        {
            DepositButton.Pressed += OnDepositPressed;
        }

        if (LoanButton != null)
        {
            LoanButton.Pressed += OnLoanPressed;
        }

        if (BankOptionButton != null)
        {
            BankOptionButton.ItemSelected += OnBankSelected;
        }
    }

    public void LoadModel(DashboardBankModel model)
    {
        _model = model;
        MouseFilter = MouseFilterEnum.Stop;
        Visible = true;

        if (TitleLabel != null)
        {
            TitleLabel.Text = "Банк";
        }

        if (DescriptionLabel != null)
        {
            DescriptionLabel.Text = $"Банків: {model.Banks.Count} | Депозитів: {model.Deposits.Count} | Кредитів: {model.Loans.Count} | Аукціонів: {model.Auctions.Count}";
        }

        PopulateBanks(model);
        PopulateDeposits(model);
        PopulateLoans(model);
        PopulateAuctions(model);
        PopulateBankOptions(model);
    }

    private void PopulateBanks(DashboardBankModel model)
    {
        if (BanksContainer == null)
        {
            return;
        }

        foreach (Node child in BanksContainer.GetChildren())
        {
            child.QueueFree();
        }

        if (model.Banks.Count == 0)
        {
            BanksContainer.AddChild(new Label { Text = "Банків немає" });
            return;
        }

        foreach (var bank in model.Banks)
        {
            var label = new Label
            {
                Text = $"🏦 {bank.SummaryText}",
                AutowrapMode = TextServer.AutowrapMode.WordSmart,
            };
            BanksContainer.AddChild(label);
        }
    }

    private void PopulateDeposits(DashboardBankModel model)
    {
        if (DepositsContainer == null)
        {
            return;
        }

        foreach (Node child in DepositsContainer.GetChildren())
        {
            child.QueueFree();
        }

        if (model.Deposits.Count == 0)
        {
            DepositsContainer.AddChild(new Label { Text = "Депозитів немає" });
            return;
        }

        foreach (var deposit in model.Deposits)
        {
            var hbox = new HBoxContainer();
            var label = new Label
            {
                Text = $"💰 {deposit.SummaryText}",
                SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
                AutowrapMode = TextServer.AutowrapMode.WordSmart,
            };
            hbox.AddChild(label);

            var withdrawButton = new Button
            {
                Text = "Зняти",
                Disabled = !deposit.IsActive,
            };
            withdrawButton.Pressed += () => EmitSignal(SignalName.WithdrawRequested, deposit.Id);
            hbox.AddChild(withdrawButton);
            DepositsContainer.AddChild(hbox);
        }
    }

    private void PopulateLoans(DashboardBankModel model)
    {
        if (LoansContainer == null)
        {
            return;
        }

        foreach (Node child in LoansContainer.GetChildren())
        {
            child.QueueFree();
        }

        if (model.Loans.Count == 0)
        {
            LoansContainer.AddChild(new Label { Text = "Кредитів немає" });
            return;
        }

        foreach (var loan in model.Loans)
        {
            var hbox = new HBoxContainer();
            var label = new Label
            {
                Text = $"💳 {loan.SummaryText}",
                SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
                AutowrapMode = TextServer.AutowrapMode.WordSmart,
            };
            hbox.AddChild(label);

            var repayButton = new Button
            {
                Text = "Погасити",
                Disabled = loan.Status != "active",
            };
            repayButton.Pressed += () => EmitSignal(SignalName.RepayRequested, loan.Id);
            hbox.AddChild(repayButton);
            LoansContainer.AddChild(hbox);
        }
    }

    private void PopulateAuctions(DashboardBankModel model)
    {
        if (AuctionsContainer == null)
        {
            return;
        }

        foreach (Node child in AuctionsContainer.GetChildren())
        {
            child.QueueFree();
        }

        if (model.Auctions.Count == 0)
        {
            AuctionsContainer.AddChild(new Label { Text = "Аукціонів немає" });
            return;
        }

        foreach (var auction in model.Auctions)
        {
            var hbox = new HBoxContainer();
            var label = new Label
            {
                Text = $"🔨 {auction.SummaryText}",
                SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
                AutowrapMode = TextServer.AutowrapMode.WordSmart,
            };
            hbox.AddChild(label);

            var bidButton = new Button
            {
                Text = "Ставка",
                Disabled = auction.Status != "active",
            };
            bidButton.Pressed += () => EmitSignal(SignalName.BidRequested, auction.Id);
            hbox.AddChild(bidButton);
            AuctionsContainer.AddChild(hbox);
        }
    }

    private void PopulateBankOptions(DashboardBankModel model)
    {
        if (BankOptionButton == null)
        {
            return;
        }

        BankOptionButton.Clear();
        BankOptionButton.AddItem("Оберіть банк...", -1);
        foreach (var bank in model.Banks)
        {
            BankOptionButton.AddItem(bank.Name, BankOptionButton.ItemCount - 1);
        }

        BankOptionButton.Select(0);
        _selectedBankId = "";
        UpdateActionButtonState();
    }

    private void OnBankSelected(long index)
    {
        if (index <= 0 || _model == null || index > _model.Banks.Count)
        {
            _selectedBankId = "";
        }
        else
        {
            _selectedBankId = _model.Banks[(int)index - 1].Id;
        }

        UpdateActionButtonState();
    }

    private void UpdateActionButtonState()
    {
        bool hasBank = !string.IsNullOrEmpty(_selectedBankId);
        if (DepositButton != null)
        {
            DepositButton.Disabled = !hasBank;
        }

        if (LoanButton != null)
        {
            LoanButton.Disabled = !hasBank;
        }
    }

    private void OnDepositPressed()
    {
        if (string.IsNullOrEmpty(_selectedBankId))
        {
            return;
        }

        double amount = DepositAmountBox?.Value ?? 0;
        EmitSignal(SignalName.DepositRequested, _selectedBankId, amount);
    }

    private void OnLoanPressed()
    {
        if (string.IsNullOrEmpty(_selectedBankId))
        {
            return;
        }

        double amount = LoanAmountBox?.Value ?? 0;
        EmitSignal(SignalName.LoanRequested, _selectedBankId, amount);
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
    public delegate void DepositRequestedEventHandler(string bankId, double amount);

    [Signal]
    public delegate void WithdrawRequestedEventHandler(string depositId);

    [Signal]
    public delegate void LoanRequestedEventHandler(string bankId, double amount);

    [Signal]
    public delegate void RepayRequestedEventHandler(string loanId);

    [Signal]
    public delegate void BidRequestedEventHandler(string auctionId);

    [Signal]
    public delegate void ClosedEventHandler();
}
