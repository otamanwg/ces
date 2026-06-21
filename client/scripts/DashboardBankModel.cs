using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;

#nullable enable

/// <summary>
/// Bank and auction state for the Sprint 61 Bank panel.
/// Backed by /api/banks, /api/player/{id}/deposits, /api/player/{id}/loans, /api/auctions/active.
/// </summary>
public sealed class DashboardBankModel
{
    public IReadOnlyList<DashboardBankItem> Banks { get; init; } = Array.Empty<DashboardBankItem>();
    public IReadOnlyList<DashboardDepositItem> Deposits { get; init; } = Array.Empty<DashboardDepositItem>();
    public IReadOnlyList<DashboardLoanItem> Loans { get; init; } = Array.Empty<DashboardLoanItem>();
    public IReadOnlyList<DashboardAuctionItem> Auctions { get; init; } = Array.Empty<DashboardAuctionItem>();

    public bool HasBanks => Banks.Count > 0;
    public bool HasDeposits => Deposits.Count > 0;
    public bool HasLoans => Loans.Count > 0;
    public bool HasAuctions => Auctions.Count > 0;

    public static DashboardBankModel FromJson(
        JsonNode? banksData,
        JsonNode? depositsData,
        JsonNode? loansData,
        JsonNode? auctionsData)
    {
        return new DashboardBankModel
        {
            Banks = ParseBanks(banksData?["banks"]?.AsArray()),
            Deposits = ParseDeposits(depositsData?["deposits"]?.AsArray()),
            Loans = ParseLoans(loansData?["loans"]?.AsArray()),
            Auctions = ParseAuctions(auctionsData?["auctions"]?.AsArray()),
        };
    }

    private static IReadOnlyList<DashboardBankItem> ParseBanks(JsonArray? banks)
    {
        if (banks == null || banks.Count == 0)
        {
            return Array.Empty<DashboardBankItem>();
        }

        var items = new List<DashboardBankItem>();
        foreach (var bank in banks)
        {
            if (bank != null)
            {
                items.Add(DashboardBankItem.FromJson(bank));
            }
        }

        return items;
    }

    private static IReadOnlyList<DashboardDepositItem> ParseDeposits(JsonArray? deposits)
    {
        if (deposits == null || deposits.Count == 0)
        {
            return Array.Empty<DashboardDepositItem>();
        }

        var items = new List<DashboardDepositItem>();
        foreach (var deposit in deposits)
        {
            if (deposit != null)
            {
                items.Add(DashboardDepositItem.FromJson(deposit));
            }
        }

        return items;
    }

    private static IReadOnlyList<DashboardLoanItem> ParseLoans(JsonArray? loans)
    {
        if (loans == null || loans.Count == 0)
        {
            return Array.Empty<DashboardLoanItem>();
        }

        var items = new List<DashboardLoanItem>();
        foreach (var loan in loans)
        {
            if (loan != null)
            {
                items.Add(DashboardLoanItem.FromJson(loan));
            }
        }

        return items;
    }

    private static IReadOnlyList<DashboardAuctionItem> ParseAuctions(JsonArray? auctions)
    {
        if (auctions == null || auctions.Count == 0)
        {
            return Array.Empty<DashboardAuctionItem>();
        }

        var items = new List<DashboardAuctionItem>();
        foreach (var auction in auctions)
        {
            if (auction != null)
            {
                items.Add(DashboardAuctionItem.FromJson(auction));
            }
        }

        return items;
    }
}

public sealed class DashboardBankItem
{
    public string Id { get; init; } = "";
    public string Name { get; init; } = "Банк";
    public double CashBalance { get; init; }
    public string? OwnerPlayerId { get; init; }
    public string Status { get; init; } = "";

    public string SummaryText => $"{Name} | баланс {CashBalance:N0} ₴ | {Status}";

    public static DashboardBankItem FromJson(JsonNode data)
    {
        return new DashboardBankItem
        {
            Id = data["id"]?.ToString() ?? "",
            Name = data["name"]?.ToString() ?? "Банк",
            CashBalance = data["cash_balance"]?.GetValue<double>() ?? 0.0,
            OwnerPlayerId = data["owner_player_id"]?.ToString(),
            Status = data["status"]?.ToString() ?? "",
        };
    }
}

public sealed class DashboardDepositItem
{
    public string Id { get; init; } = "";
    public string BankBusinessId { get; init; } = "";
    public double Amount { get; init; }
    public double InterestRate { get; init; }
    public int CreatedAtGameDay { get; init; }
    public bool IsActive { get; init; }

    public string SummaryText => $"{Amount:N0} ₴ | {InterestRate:N1}% річних";

    public static DashboardDepositItem FromJson(JsonNode data)
    {
        return new DashboardDepositItem
        {
            Id = data["id"]?.ToString() ?? "",
            BankBusinessId = data["bank_business_id"]?.ToString() ?? "",
            Amount = data["amount"]?.GetValue<double>() ?? 0.0,
            InterestRate = data["interest_rate"]?.GetValue<double>() ?? 0.0,
            CreatedAtGameDay = data["created_at_game_day"]?.GetValue<int>() ?? 0,
            IsActive = data["is_active"]?.GetValue<bool>() ?? false,
        };
    }
}

public sealed class DashboardLoanItem
{
    public string Id { get; init; } = "";
    public string BankBusinessId { get; init; } = "";
    public double PrincipalAmount { get; init; }
    public double RemainingAmount { get; init; }
    public double InterestRate { get; init; }
    public int TermDays { get; init; }
    public int DueGameDay { get; init; }
    public string Status { get; init; } = "";

    public string SummaryText => $"Борг {RemainingAmount:N0} ₴ | {InterestRate:N1}% | до дня {DueGameDay}";

    public static DashboardLoanItem FromJson(JsonNode data)
    {
        return new DashboardLoanItem
        {
            Id = data["id"]?.ToString() ?? "",
            BankBusinessId = data["bank_business_id"]?.ToString() ?? "",
            PrincipalAmount = data["principal_amount"]?.GetValue<double>() ?? 0.0,
            RemainingAmount = data["remaining_amount"]?.GetValue<double>() ?? 0.0,
            InterestRate = data["interest_rate"]?.GetValue<double>() ?? 0.0,
            TermDays = data["term_days"]?.GetValue<int>() ?? 0,
            DueGameDay = data["due_game_day"]?.GetValue<int>() ?? 0,
            Status = data["status"]?.ToString() ?? "",
        };
    }
}

public sealed class DashboardAuctionItem
{
    public string Id { get; init; } = "";
    public string BusinessId { get; init; } = "";
    public double StartingPrice { get; init; }
    public double HighestBid { get; init; }
    public string EndsAt { get; init; } = "";
    public string Status { get; init; } = "";

    public string SummaryText => $"Старт {StartingPrice:N0} ₴ | найвиша ставка {HighestBid:N0} ₴";

    public static DashboardAuctionItem FromJson(JsonNode data)
    {
        return new DashboardAuctionItem
        {
            Id = data["id"]?.ToString() ?? "",
            BusinessId = data["business_id"]?.ToString() ?? "",
            StartingPrice = data["starting_price"]?.GetValue<double>() ?? 0.0,
            HighestBid = data["highest_bid"]?.GetValue<double>() ?? 0.0,
            EndsAt = data["ends_at"]?.ToString() ?? "",
            Status = data["status"]?.ToString() ?? "",
        };
    }
}
