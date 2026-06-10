using Godot;
using System;
using System.Text.Json.Nodes;
using System.Threading.Tasks;

public partial class CityDashboardController
{
    // Note: Building-related fields are declared in main CityDashboardController.cs

    private void InitializeBuildingActions()
    {
        _buyBusinessButton = GetNode<Button>("MainContainer/PlayerRail/ActionsContainer/BuyBusinessButton");
        _collectDividendButton = GetNode<Button>("MainContainer/PlayerRail/ActionsContainer/CollectDividendButton");
        _openBuildingButton = GetNode<Button>("MainContainer/PlayerRail/ActionsContainer/OpenBuildingButton");
        _repairBuildingButton = GetNode<Button>("MainContainer/PlayerRail/ActionsContainer/RepairBuildingButton");
        _buyStarterLandButton = GetNode<Button>("MainContainer/PlayerRail/ActionsContainer/BuyStarterLandButton");
        _BuildingPortfolioLabel = GetNode<Label>("MainContainer/PlayerRail/BuildingPortfolioLabel");
        _BuildPlanLabel = GetNode<Label>("MainContainer/PlayerRail/BuildPlanLabel");

        // Connect signals
        _buyBusinessButton.Pressed += OnBuyBusinessPressed;
        _collectDividendButton.Pressed += OnCollectDividendPressed;
        _openBuildingButton.Pressed += OnOpenBuildingPressed;
        _repairBuildingButton.Pressed += OnRepairBuildingPressed;
        _buyStarterLandButton.Pressed += OnBuyStarterLandPressed;
    }

    private async void OnBuyBusinessPressed()
    {
        if (_session?.PlayerId == null) return;

        SetActionState(_buyBusinessButton, "processing");
        ErrorStateLabel.Text = "";

        try
        {
            var response = await _apiClient.PostAsync($"/api/business/purchase", new { });
            if (response?.TryGetValue("success", out var success) == true && success.GetValue<bool>())
            {
                EffectsLabel.Text = "✅ Бізнес куплено!";
                await RefreshPlayerData();
                await RefreshBuildingPortfolio();
            }
            else
            {
                var message = response?.TryGetValue("message", out var msg) == true ? msg.GetValue<string>() : "Помилка";
                ErrorStateLabel.Text = message;
            }
        }
        catch (Exception ex)
        {
            ErrorStateLabel.Text = $"Помилка: {ex.Message}";
        }
        finally
        {
            SetActionState(_buyBusinessButton, "ready");
        }
    }

    private async void OnCollectDividendPressed()
    {
        if (_session?.PlayerId == null) return;

        SetActionState(_collectDividendButton, "processing");
        ErrorStateLabel.Text = "";

        try
        {
            var response = await _apiClient.PostAsync($"/api/business/collect-dividend", new { });
            if (response?.TryGetValue("success", out var success) == true && success.GetValue<bool>())
            {
                var amount = response?.TryGetValue("dividend_amount", out var amt) == true ? amt.GetValue<decimal>() : 0;
                EffectsLabel.Text = $"✅ Дивіденди зібрано: {amount:N0} ₴";
                await RefreshPlayerData();
            }
            else
            {
                var message = response?.TryGetValue("message", out var msg) == true ? msg.GetValue<string>() : "Помилка";
                ErrorStateLabel.Text = message;
            }
        }
        catch (Exception ex)
        {
            ErrorStateLabel.Text = $"Помилка: {ex.Message}";
        }
        finally
        {
            SetActionState(_collectDividendButton, "ready");
        }
    }

    private async void OnOpenBuildingPressed()
    {
        if (_session?.PlayerId == null) return;

        SetActionState(_openBuildingButton, "processing");
        ErrorStateLabel.Text = "";

        try
        {
            var response = await _apiClient.PostAsync($"/api/buildings/open", new { });
            if (response?.TryGetValue("success", out var success) == true && success.GetValue<bool>())
            {
                EffectsLabel.Text = "✅ Будівлю відкрито!";
                await RefreshPlayerData();
                await RefreshBuildingPortfolio();
            }
            else
            {
                var message = response?.TryGetValue("message", out var msg) == true ? msg.GetValue<string>() : "Помилка";
                ErrorStateLabel.Text = message;
            }
        }
        catch (Exception ex)
        {
            ErrorStateLabel.Text = $"Помилка: {ex.Message}";
        }
        finally
        {
            SetActionState(_openBuildingButton, "ready");
        }
    }

    private async void OnRepairBuildingPressed()
    {
        if (_session?.PlayerId == null) return;

        SetActionState(_repairBuildingButton, "processing");
        ErrorStateLabel.Text = "";

        try
        {
            var response = await _apiClient.PostAsync($"/api/buildings/repair", new { });
            if (response?.TryGetValue("success", out var success) == true && success.GetValue<bool>())
            {
                EffectsLabel.Text = "✅ Будівлю відремонтовано!";
                await RefreshPlayerData();
                await RefreshBuildingPortfolio();
            }
            else
            {
                var message = response?.TryGetValue("message", out var msg) == true ? msg.GetValue<string>() : "Помилка";
                ErrorStateLabel.Text = message;
            }
        }
        catch (Exception ex)
        {
            ErrorStateLabel.Text = $"Помилка: {ex.Message}";
        }
        finally
        {
            SetActionState(_repairBuildingButton, "ready");
        }
    }

    private async void OnBuyStarterLandPressed()
    {
        if (_session?.PlayerId == null) return;

        SetActionState(_buyStarterLandButton, "processing");
        ErrorStateLabel.Text = "";

        try
        {
            var response = await _apiClient.PostAsync($"/api/land/purchase-starter", new { });
            if (response?.TryGetValue("success", out var success) == true && success.GetValue<bool>())
            {
                EffectsLabel.Text = "✅ Землю куплено!";
                await RefreshPlayerData();
                await RefreshBuildingPortfolio();
            }
            else
            {
                var message = response?.TryGetValue("message", out var msg) == true ? msg.GetValue<string>() : "Помилка";
                ErrorStateLabel.Text = message;
            }
        }
        catch (Exception ex)
        {
            ErrorStateLabel.Text = $"Помилка: {ex.Message}";
        }
        finally
        {
            SetActionState(_buyStarterLandButton, "ready");
        }
    }

    private async Task RefreshBuildingPortfolio()
    {
        if (_session?.PlayerId == null) return;

        try
        {
            var response = await _apiClient.GetAsync($"/api/player/{_session.PlayerId}/buildings");
            if (response?.TryGetValue("success", out var success) == true && success.GetValue<bool>())
            {
                UpdateBuildingPortfolio(response);
            }
        }
        catch (Exception ex)
        {
            ErrorStateLabel.Text = $"Помилка оновлення портфоліо: {ex.Message}";
        }
    }

    private void UpdateBuildingPortfolio(JsonNode response)
    {
        var buildings = response?["data"]?.AsArray();
        if (buildings == null || buildings.Count == 0)
        {
            _BuildingPortfolioLabel.Text = "У вас немає будівель";
            _openBuildingButton.Visible = false;
            _repairBuildingButton.Visible = false;
            return;
        }

        var portfolioText = "Ваші будівлі:\n";
        var hasActions = false;

        foreach (var building in buildings)
        {
            var name = building?["name"]?.GetValue<string>() ?? "Невідома будівля";
            var status = building?["operating_status"]?.GetValue<string>() ?? "unknown";
            var district = building?["district_code"]?.GetValue<string>() ?? "";

            portfolioText += $"• {name} ({district}) - {status}\n";

            if (status == "inactive")
            {
                hasActions = true;
            }
            else if (status == "maintenance_due")
            {
                hasActions = true;
            }
        }

        _BuildingPortfolioLabel.Text = portfolioText;
        _openBuildingButton.Visible = hasActions;
        _repairBuildingButton.Visible = hasActions;
    }
}
