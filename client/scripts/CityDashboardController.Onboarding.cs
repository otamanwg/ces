using Godot;
using System;
using System.Threading.Tasks;

public partial class CityDashboardController : Control
{
    // Onboarding Methods
    private async void OnOnboardingPoliceButtonPressed()
    {
        if (!IsPlayerReady()) return;

        try
        {
            var response = await _apiClient.PostAsync("/api/mvp/choose-arrival-path", new
            {
                choice = "report_to_police"
            });

            if (response.Success)
            {
                SetLabelText(StatusLabel, "🚔 Police report filed");
                await RefreshOnboardingData();
            }
            else
            {
                SetLabelText(ErrorStateLabel, $"❌ Police report failed: {response.Message}");
            }
        }
        catch (Exception ex)
        {
            GD.PrintErr($"Police report error: {ex.Message}");
            SetLabelText(ErrorStateLabel, "❌ Network error during police report");
        }
    }

    private async void OnOnboardingHousingButtonPressed()
    {
        if (!IsPlayerReady()) return;

        try
        {
            var response = await _apiClient.PostAsync("/api/mvp/choose-arrival-path", new
            {
                choice = "find_housing"
            });

            if (response.Success)
            {
                SetLabelText(StatusLabel, "🏠 Housing found");
                await RefreshOnboardingData();
            }
            else
            {
                SetLabelText(ErrorStateLabel, $"❌ Housing search failed: {response.Message}");
            }
        }
        catch (Exception ex)
        {
            GD.PrintErr($"Housing search error: {ex.Message}");
            SetLabelText(ErrorStateLabel, "❌ Network error during housing search");
        }
    }

    private void OnOnboardingContinueButtonPressed()
    {
        // Continue from onboarding to main game
        SetControlVisible(_onboardingOverlay, false);
        SetLabelText(StatusLabel, "🎮 Welcome to the city!");
        AddEventToHistory("🎮 Onboarding complete");
    }

    private async void OnPoliceRecoveryButtonPressed()
    {
        if (!IsPlayerReady() || !string.IsNullOrEmpty(_pendingPoliceRecoveryKey)) return;

        var recoveryKey = Guid.NewGuid().ToString();
        _pendingPoliceRecoveryKey = recoveryKey;
        SetButtonEnabled(_policeRecoveryButton, false);

        try
        {
            var response = await _apiClient.PostAsync("/api/mvp/claim-police-recovery", new
            {
                idempotency_key = recoveryKey
            });

            if (response.Success)
            {
                SetLabelText(StatusLabel, "💰 Police recovery claimed!");
                await RefreshPlayerData();
                await RefreshOnboardingData();
            }
            else
            {
                SetLabelText(ErrorStateLabel, $"❌ Police recovery failed: {response.Message}");
            }
        }
        catch (Exception ex)
        {
            GD.PrintErr($"Police recovery error: {ex.Message}");
            SetLabelText(ErrorStateLabel, "❌ Network error during police recovery");
        }
        finally
        {
            _pendingPoliceRecoveryKey = "";
            SetButtonEnabled(_policeRecoveryButton, true);
        }
    }

    private async Task RefreshOnboardingData()
    {
        if (!IsPlayerReady()) return;

        try
        {
            var response = await _apiClient.GetAsync("/api/mvp/onboarding");
            if (response.Success)
            {
                UpdateOnboardingUI(response.Data);
            }
        }
        catch (Exception ex)
        {
            GD.PrintErr($"Onboarding data refresh error: {ex.Message}");
        }
    }

    private void UpdateOnboardingUI(object onboardingData)
    {
        if (onboardingData == null) return;

        try
        {
            var data = System.Text.Json.JsonSerializer.Deserialize<OnboardingData>(onboardingData.ToString());

            if (data == null) return;

            // Update onboarding UI elements
            SetLabelText(_onboardingTitleLabel, data.Title ?? "Arrival");
            SetLabelText(_onboardingNarrativeLabel, data.Narrative ?? "");

            // Update police status
            if (data.PoliceReportStatus != null)
            {
                SetLabelText(_onboardingPoliceStatusLabel, GetPoliceStatusText(data.PoliceReportStatus));
                SetButtonEnabled(_onboardingPoliceButton, data.AvailableChoices?.Contains("report_to_police") == true);
            }

            // Update housing button
            SetButtonEnabled(_onboardingHousingButton, data.AvailableChoices?.Contains("find_housing") == true);

            // Update continue button
            SetButtonEnabled(_onboardingContinueButton, data.Completed);

            // Update police recovery button
            if (data.PoliceRecoveryClaimable == true && data.PoliceRecoveryAmount > 0)
            {
                SetButtonEnabled(_policeRecoveryButton, true);
                _policeRecoveryButton.Text = $"Claim Recovery ({data.PoliceRecoveryAmount:F2} ₴)";
            }
            else
            {
                SetButtonEnabled(_policeRecoveryButton, false);
                _policeRecoveryButton.Text = "Police Recovery";
            }

            // Update backdrop
            if (!string.IsNullOrEmpty(data.BackdropPath))
            {
                _onboardingBackdropPath = data.BackdropPath;
                UpdateOnboardingBackdrop();
            }

            // Show/hide overlay based on completion
            SetControlVisible(_onboardingOverlay, !data.Completed);
        }
        catch (Exception ex)
        {
            GD.PrintErr($"Onboarding UI update error: {ex.Message}");
        }
    }

    private string GetPoliceStatusText(string status)
    {
        return status switch
        {
            "not_filed" => "No police report filed",
            "pending" => "Police investigation in progress",
            "closed_no_recovery" => "Police case closed - no recovery",
            "recovered" => "Police recovery completed",
            _ => "Unknown police status"
        };
    }

    private void UpdateOnboardingBackdrop()
    {
        if (!string.IsNullOrEmpty(_onboardingBackdropPath) && _onboardingBackdrop != null)
        {
            var texture = GD.Load<Texture2D>(_onboardingBackdropPath);
            if (texture != null)
            {
                _onboardingBackdrop.Texture = texture;
            }
        }
    }
}
