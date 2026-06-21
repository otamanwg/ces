using Godot;
using System.Text.Json.Nodes;

public partial class CityDashboardController
{
    private JsonNode _banksData;
    private JsonNode _depositsData;
    private JsonNode _loansData;
    private JsonNode _auctionsData;
    private bool _pendingBankCatalog;
    private string _pendingDepositKey;
    private string _pendingWithdrawKey;
    private string _pendingLoanKey;
    private string _pendingRepayKey;
    private string _pendingBidKey;

    public void OnBankButtonPressed()
    {
        if (_bankPanel == null || _session == null || !_session.HasAuthenticatedPlayer)
        {
            return;
        }

        _pendingBankCatalog = true;
        ClearErrorState();
        _apiClient?.GetAuthorized("/api/banks", _session.AuthToken);
        _apiClient?.GetAuthorized(
            $"/api/player/{_session.PlayerId}/deposits",
            _session.AuthToken);
        _apiClient?.GetAuthorized(
            $"/api/player/{_session.PlayerId}/loans",
            _session.AuthToken);
        _apiClient?.GetAuthorized("/api/auctions/active", _session.AuthToken);
    }

    public void OnBankDepositRequested(string bankId, double amount)
    {
        if (_session == null || !_session.HasAuthenticatedPlayer || string.IsNullOrEmpty(bankId) || amount <= 0)
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingDepositKey))
        {
            return;
        }

        _pendingDepositKey = BuildActionKey($"deposit-{bankId}-{amount}");
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId, amount, interest_rate = 5.0 });
        _apiClient?.PostAuthorizedIdempotent(
            $"/api/banks/{bankId}/deposit",
            _session.AuthToken,
            _pendingDepositKey,
            payload);
    }

    public void OnBankWithdrawRequested(string depositId)
    {
        if (_session == null || !_session.HasAuthenticatedPlayer || string.IsNullOrEmpty(depositId))
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingWithdrawKey))
        {
            return;
        }

        _pendingWithdrawKey = BuildActionKey($"withdraw-{depositId}");
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId });
        _apiClient?.PostAuthorizedIdempotent(
            $"/api/banks/deposits/{depositId}/withdraw",
            _session.AuthToken,
            _pendingWithdrawKey,
            payload);
    }

    public void OnBankLoanRequested(string bankId, double amount)
    {
        if (_session == null || !_session.HasAuthenticatedPlayer || string.IsNullOrEmpty(bankId) || amount <= 0)
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingLoanKey))
        {
            return;
        }

        _pendingLoanKey = BuildActionKey($"loan-{bankId}-{amount}");
        ClearErrorState();
        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId, amount, interest_rate = 12.0, term_days = 30 });
        _apiClient?.PostAuthorizedIdempotent(
            $"/api/banks/{bankId}/loan",
            _session.AuthToken,
            _pendingLoanKey,
            payload);
    }

    public void OnBankRepayRequested(string loanId)
    {
        if (_session == null || !_session.HasAuthenticatedPlayer || string.IsNullOrEmpty(loanId))
        {
            return;
        }

        if (!string.IsNullOrEmpty(_pendingRepayKey))
        {
            return;
        }

        _pendingRepayKey = BuildActionKey($"repay-{loanId}");
        ClearErrorState();
        // Repay full remaining amount — the backend caps at remaining_amount.
        string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId, amount = 999999.0 });
        _apiClient?.PostAuthorizedIdempotent(
            $"/api/banks/loans/{loanId}/repay",
            _session.AuthToken,
            _pendingRepayKey,
            payload);
    }

    public void OnBankBidRequested(string auctionId)
    {
        if (_session == null || !_session.HasAuthenticatedPlayer || string.IsNullOrEmpty(auctionId))
        {
            return;
        }

        // For now, bid at current highest + minimum increment (100).
        // A proper bid dialog can be added later.
        SetStatus("Ставки на аукціон будуть доступні в наступному оновленні.");
    }

    private void HandleBanksResponse(JsonNode data)
    {
        _banksData = data;
        TryShowBankPanel();
    }

    private void HandleDepositsResponse(JsonNode data)
    {
        _depositsData = data;
        TryShowBankPanel();
    }

    private void HandleLoansResponse(JsonNode data)
    {
        _loansData = data;
        TryShowBankPanel();
    }

    private void HandleAuctionsResponse(JsonNode data)
    {
        _auctionsData = data;
        TryShowBankPanel();
    }

    private void TryShowBankPanel()
    {
        if (_banksData == null || _depositsData == null || _loansData == null || _auctionsData == null)
        {
            return;
        }

        _pendingBankCatalog = false;
        var model = DashboardBankModel.FromJson(_banksData, _depositsData, _loansData, _auctionsData);
        _bankPanel?.LoadModel(model);
    }

    private void HandleBankActionResponse(JsonNode data)
    {
        _pendingDepositKey = "";
        _pendingWithdrawKey = "";
        _pendingLoanKey = "";
        _pendingRepayKey = "";
        _pendingBidKey = "";

        bool success = data?["success"]?.GetValue<bool>() ?? false;
        string message = data?["message"]?.ToString() ?? "Операцію завершено.";
        SetStatus(message, success);

        // Refresh bank data after any bank action.
        if (success && _session != null && _session.HasAuthenticatedPlayer)
        {
            _banksData = null;
            _depositsData = null;
            _loansData = null;
            _auctionsData = null;
            _apiClient?.GetAuthorized("/api/banks", _session.AuthToken);
            _apiClient?.GetAuthorized(
                $"/api/player/{_session.PlayerId}/deposits",
                _session.AuthToken);
            _apiClient?.GetAuthorized(
                $"/api/player/{_session.PlayerId}/loans",
                _session.AuthToken);
            _apiClient?.GetAuthorized("/api/auctions/active", _session.AuthToken);
        }
    }

    private bool TryHandleBankResponse(string endpoint, JsonNode root)
    {
        // GET /api/banks — bank list (must check before /api/banks/{id} patterns).
        if (endpoint == "/api/banks")
        {
            HandleBanksResponse(root["data"]);
            return true;
        }

        // GET /api/auctions/active
        if (endpoint == "/api/auctions/active")
        {
            HandleAuctionsResponse(root["data"]);
            return true;
        }

        // GET /api/player/{id}/deposits
        if (endpoint.StartsWith("/api/player/") && endpoint.EndsWith("/deposits"))
        {
            HandleDepositsResponse(root["data"]);
            return true;
        }

        // GET /api/player/{id}/loans
        if (endpoint.StartsWith("/api/player/") && endpoint.EndsWith("/loans"))
        {
            HandleLoansResponse(root["data"]);
            return true;
        }

        // POST /api/banks/{id}/deposit
        if (endpoint.StartsWith("/api/banks/") && endpoint.EndsWith("/deposit"))
        {
            HandleBankActionResponse(root);
            return true;
        }

        // POST /api/banks/deposits/{id}/withdraw
        if (endpoint.StartsWith("/api/banks/deposits/") && endpoint.EndsWith("/withdraw"))
        {
            HandleBankActionResponse(root);
            return true;
        }

        // POST /api/banks/{id}/loan
        if (endpoint.StartsWith("/api/banks/") && endpoint.EndsWith("/loan"))
        {
            HandleBankActionResponse(root);
            return true;
        }

        // POST /api/banks/loans/{id}/repay
        if (endpoint.StartsWith("/api/banks/loans/") && endpoint.EndsWith("/repay"))
        {
            HandleBankActionResponse(root);
            return true;
        }

        return false;
    }
}
