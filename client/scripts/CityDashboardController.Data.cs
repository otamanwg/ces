using Godot;
using System;
using System.Threading.Tasks;
using System.Text.Json;
using City.Api;

public partial class CityDashboardController : Control
{
    // Data Management
    private ApiClient _apiClient;
    private ExamPanelController _examPanel;
    private CityVisualOverlay _cityVisualOverlay;

    // Data Refresh Methods
    private async Task RefreshPlayerData()
    {
        if (!IsPlayerReady()) return;

        try
        {
            // Get player snapshot
            var playerResponse = await _apiClient.GetAsync("/api/mvp/player");
            if (playerResponse.Success)
            {
                var playerData = JsonSerializer.Deserialize<PlayerSnapshotData>(playerResponse.Data.ToString());
                UpdatePlayerUI(playerData);
            }

            // Get city status
            var cityResponse = await _apiClient.GetAsync("/api/mvp/city-status");
            if (cityResponse.Success)
            {
                var cityData = JsonSerializer.Deserialize<CityStatusData>(cityResponse.Data.ToString());
                UpdateCityUI(cityData);
            }

            // Get building portfolio
            var portfolioResponse = await _apiClient.GetAsync("/api/mvp/building-portfolio");
            if (portfolioResponse.Success)
            {
                var portfolioData = JsonSerializer.Deserialize<BuildingPortfolioData>(portfolioResponse.Data.ToString());
                UpdateBuildingPortfolioUI(portfolioData);
            }

            // Update action states
            await UpdateActionStates();
        }
        catch (Exception ex)
        {
            GD.PrintErr($"Data refresh error: {ex.Message}");
            SetLabelText(ErrorStateLabel, "❌ Failed to refresh data");
        }
    }

    private async Task UpdateActionStates()
    {
        if (!IsPlayerReady()) return;

        try
        {
            // Get player actions
            var actionsResponse = await _apiClient.GetAsync("/api/mvp/player-actions");
            if (actionsResponse.Success)
            {
                var actionsData = JsonSerializer.Deserialize<PlayerActionsData>(actionsResponse.Data.ToString());
                UpdateActionButtons(actionsData);
            }
        }
        catch (Exception ex)
        {
            GD.PrintErr($"Action states update error: {ex.Message}");
        }
    }

    // UI Update Methods
    private void UpdatePlayerUI(PlayerSnapshotData playerData)
    {
        if (playerData == null) return;

        // Basic info
        SetLabelText(UsernameLabel, playerData.Player?.Identity?.Name ?? "Unknown");
        SetLabelText(BalanceLabel, $"💰 {playerData.Player?.Balance:F2} ₴");
        SetLabelText(EducationLabel, $"🎓 {playerData.Player?.Education ?? "High School"}");
        SetLabelText(CurrentJobLabel, $"💼 {playerData.Actions?.CurrentJob?.BusinessName ?? "Unemployed"}");
        SetLabelText(CurrentHostelLabel, $"🏠 {playerData.Actions?.CurrentHostel?.RoomNumber ?? "No housing"}");
        SetLabelText(OwnedBusinessLabel, $"🏪 {playerData.Actions?.OwnedBusiness?.Name ?? "No business"}");
        SetLabelText(SportsLabel, $"⚽ {playerData.Actions?.SportsClub?.Name ?? "No club"}");

        // Status bars
        if (playerData.Player != null)
        {
            SetTextureProgressBarValue(EnergyBar, playerData.Player.Energy);
            SetTextureProgressBarValue(MoodBar, playerData.Player.Mood);
            SetTextureProgressBarValue(HungerBar, playerData.Player.Hunger);
        }

        // Goals and progress
        if (playerData.GoalEffects != null)
        {
            SetLabelText(GoalLabel, playerData.GoalEffects.Title ?? "No active goal");
            SetProgressBarValue(GoalProgressBar, playerData.GoalEffects.Progress ?? 0f);
            SetLabelText(NextActionLabel, playerData.GoalEffects.NextAction ?? "Continue playing");
        }

        // Store business ID for dividend collection
        if (playerData.Actions?.OwnedBusiness?.Id != null)
        {
            _ownedBusinessId = playerData.Actions.OwnedBusiness.Id;
        }

        // Update player capabilities
        UpdatePlayerCapabilities(playerData.Actions);
    }

    private void UpdateCityUI(CityStatusData cityData)
    {
        if (cityData == null) return;

        SetLabelText(CityNameLabel, cityData.City?.Name ?? "Unknown City");
        SetLabelText(TreasuryLabel, $"🏛️ Treasury: {cityData.City?.TreasuryBalance:F2} ₴");
        SetLabelText(InflationLabel, $"📈 Inflation: {cityData.City?.InflationRate:F2}%");
    }

    private void UpdateBuildingPortfolioUI(BuildingPortfolioData portfolioData)
    {
        if (portfolioData == null) return;

        if (portfolioData.Buildings != null && portfolioData.Buildings.Count > 0)
        {
            var buildingList = string.Join("\n", portfolioData.Buildings.ConvertAll(b =>
                $"🏢 {b.Name} - {b.OperatingStatus}"));
            SetLabelText(BuildingPortfolioLabel, buildingList);

            // Set first building for actions if available
            var firstBuilding = portfolioData.Buildings[0];
            if (firstBuilding.AvailableActions?.Contains("open") == true)
            {
                _portfolioOpenBuildingId = firstBuilding.Id;
            }
            if (firstBuilding.AvailableActions?.Contains("repair") == true)
            {
                _portfolioRepairBuildingId = firstBuilding.Id;
            }
        }
        else
        {
            SetLabelText(BuildingPortfolioLabel, "🏢 No buildings owned");
        }
    }

    private void UpdateActionButtons(PlayerActionsData actionsData)
    {
        if (actionsData == null) return;

        // Update button states based on available actions
        SetButtonEnabled(_applyJobButton, actionsData.CanApplyJob ?? false);
        SetButtonEnabled(_workButton, actionsData.CanWork ?? false);
        SetButtonEnabled(_sleepButton, actionsData.CanSleep ?? false);
        SetButtonEnabled(_eatButton, actionsData.CanEat ?? false);
        SetButtonEnabled(_buyBusinessButton, actionsData.CanBuyBusiness ?? false);
        SetButtonEnabled(_collectDividendButton, actionsData.CanCollectDividend ?? false);
        SetButtonEnabled(_joinSportsButton, actionsData.CanJoinSports ?? false);
        SetButtonEnabled(_trainSportsButton, actionsData.CanTrainSports ?? false);
        SetButtonEnabled(_examButton, actionsData.CanTakeExam ?? false);
        SetButtonEnabled(_openBuildingButton, !string.IsNullOrEmpty(_portfolioOpenBuildingId));
        SetButtonEnabled(_repairBuildingButton, !string.IsNullOrEmpty(_portfolioRepairBuildingId));

        // Update status messages
        if (actionsData.Effects != null && actionsData.Effects.Count > 0)
        {
            var effectsText = string.Join("\n", actionsData.Effects);
            SetLabelText(EffectsLabel, effectsText);
        }
    }

    private void UpdatePlayerCapabilities(PlayerActionsData actionsData)
    {
        if (actionsData == null) return;

        _canApplyJob = actionsData.CanApplyJob ?? false;
        _canWork = actionsData.CanWork ?? false;
        _canSleep = actionsData.CanSleep ?? false;
        _canEat = actionsData.CanEat ?? false;
        _canBuyBusiness = actionsData.CanBuyBusiness ?? false;
        _canCollectDividend = actionsData.CanCollectDividend ?? false;
        _canJoinSports = actionsData.CanJoinSports ?? false;
        _canTrainSports = actionsData.CanTrainSports ?? false;
        _canTakeExam = actionsData.CanTakeExam ?? false;

        // Update job status
        _hasJob = actionsData.CurrentJob != null;
    }

    // Event History
    private void AddEventToHistory(string eventText)
    {
        var currentHistory = EventHistoryLabel?.Text ?? "";
        var timestamp = DateTime.Now.ToString("HH:mm:ss");
        var newEntry = $"[{timestamp}] {eventText}";

        var lines = currentHistory.Split('\n');
        var newLines = new string[lines.Length + 1];
        Array.Copy(lines, newLines, lines.Length);
        newLines[^1] = newEntry;

        // Keep only last 10 events
        if (newLines.Length > 10)
        {
            var trimmedLines = new string[10];
            Array.Copy(newLines, newLines.Length - 10, trimmedLines, 0, 10);
            SetLabelText(EventHistoryLabel, string.Join("\n", trimmedLines));
        }
        else
        {
            SetLabelText(EventHistoryLabel, string.Join("\n", newLines));
        }
    }

    // Error Handling
    private void HandleApiError(string operation, string errorMessage)
    {
        GD.PrintErr($"{operation} error: {errorMessage}");
        SetLabelText(ErrorStateLabel, $"❌ {operation} failed: {errorMessage}");
        AddEventToHistory($"❌ {operation} failed");
    }

    private void HandleApiSuccess(string operation, string successMessage)
    {
        SetLabelText(StatusLabel, $"✅ {successMessage}");
        AddEventToHistory($"✅ {operation} completed");
    }

    // Data Validation
    private bool ValidatePlayerData(PlayerSnapshotData playerData)
    {
        return playerData?.Player != null &&
               !string.IsNullOrEmpty(playerData.Player.Id);
    }

    private bool ValidateCityData(CityStatusData cityData)
    {
        return cityData?.City != null &&
               !string.IsNullOrEmpty(cityData.City.Id);
    }
}
