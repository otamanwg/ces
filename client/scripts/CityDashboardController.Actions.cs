using Godot;
using System;
using System.Threading.Tasks;

public partial class CityDashboardController : Control
{
    // Action Handlers - Main Game Actions
    private async void OnApplyJobButtonPressed()
    {
        if (!IsPlayerReady() || _pendingApply) return;

        _pendingApply = true;
        SetButtonEnabled(_applyJobButton, false);

        try
        {
            var response = await _apiClient.PostAsync("/api/mvp/apply-first-vacancy", new { });
            if (response.Success)
            {
                SetLabelText(StatusLabel, "✅ Job application submitted!");
                await RefreshPlayerData();
            }
            else
            {
                SetLabelText(ErrorStateLabel, $"❌ Failed to apply: {response.Message}");
            }
        }
        catch (Exception ex)
        {
            GD.PrintErr($"Job application error: {ex.Message}");
            SetLabelText(ErrorStateLabel, "❌ Network error during job application");
        }
        finally
        {
            _pendingApply = false;
            SetButtonEnabled(_applyJobButton, true);
        }
    }

    private async void OnWorkButtonPressed()
    {
        if (!IsPlayerReady() || !string.IsNullOrEmpty(_pendingWorkKey)) return;

        var workKey = Guid.NewGuid().ToString();
        _pendingWorkKey = workKey;
        SetButtonEnabled(_workButton, false);

        try
        {
            var response = await _apiClient.PostAsync("/api/mvp/work-shift", new
            {
                idempotency_key = workKey
            });

            if (response.Success)
            {
                SetLabelText(StatusLabel, "💼 Work completed! Money earned.");
                await RefreshPlayerData();
            }
            else
            {
                SetLabelText(ErrorStateLabel, $"❌ Work failed: {response.Message}");
            }
        }
        catch (Exception ex)
        {
            GD.PrintErr($"Work error: {ex.Message}");
            SetLabelText(ErrorStateLabel, "❌ Network error during work");
        }
        finally
        {
            _pendingWorkKey = "";
            SetButtonEnabled(_workButton, true);
        }
    }

    private async void OnSleepButtonPressed()
    {
        if (!IsPlayerReady() || !string.IsNullOrEmpty(_pendingSleepKey)) return;

        var sleepKey = Guid.NewGuid().ToString();
        _pendingSleepKey = sleepKey;
        SetButtonEnabled(_sleepButton, false);

        try
        {
            var response = await _apiClient.PostAsync("/api/mvp/sleep", new
            {
                idempotency_key = sleepKey
            });

            if (response.Success)
            {
                SetLabelText(StatusLabel, "😴 Good sleep! Energy restored.");
                await RefreshPlayerData();
            }
            else
            {
                SetLabelText(ErrorStateLabel, $"❌ Sleep failed: {response.Message}");
            }
        }
        catch (Exception ex)
        {
            GD.PrintErr($"Sleep error: {ex.Message}");
            SetLabelText(ErrorStateLabel, "❌ Network error during sleep");
        }
        finally
        {
            _pendingSleepKey = "";
            SetButtonEnabled(_sleepButton, true);
        }
    }

    private async void OnEatButtonPressed()
    {
        if (!IsPlayerReady() || !string.IsNullOrEmpty(_pendingEatKey)) return;

        var eatKey = Guid.NewGuid().ToString();
        _pendingEatKey = eatKey;
        SetButtonEnabled(_eatButton, false);

        try
        {
            var response = await _apiClient.PostAsync("/api/mvp/eat", new
            {
                idempotency_key = eatKey
            });

            if (response.Success)
            {
                SetLabelText(StatusLabel, "🍽️ Meal eaten! Hunger satisfied.");
                await RefreshPlayerData();
            }
            else
            {
                SetLabelText(ErrorStateLabel, $"❌ Meal failed: {response.Message}");
            }
        }
        catch (Exception ex)
        {
            GD.PrintErr($"Eat error: {ex.Message}");
            SetLabelText(ErrorStateLabel, "❌ Network error during meal");
        }
        finally
        {
            _pendingEatKey = "";
            SetButtonEnabled(_eatButton, true);
        }
    }

    // Business Actions
    private async void OnBuyBusinessButtonPressed()
    {
        if (!IsPlayerReady() || !string.IsNullOrEmpty(_pendingBusinessBuyKey)) return;

        var buyKey = Guid.NewGuid().ToString();
        _pendingBusinessBuyKey = buyKey;
        SetButtonEnabled(_buyBusinessButton, false);

        try
        {
            var response = await _apiClient.PostAsync("/api/mvp/buy-business", new
            {
                idempotency_key = buyKey
            });

            if (response.Success)
            {
                SetLabelText(StatusLabel, "🏪 Business purchased!");
                await RefreshPlayerData();
            }
            else
            {
                SetLabelText(ErrorStateLabel, $"❌ Business purchase failed: {response.Message}");
            }
        }
        catch (Exception ex)
        {
            GD.PrintErr($"Business purchase error: {ex.Message}");
            SetLabelText(ErrorStateLabel, "❌ Network error during business purchase");
        }
        finally
        {
            _pendingBusinessBuyKey = "";
            SetButtonEnabled(_buyBusinessButton, true);
        }
    }

    private async void OnCollectDividendButtonPressed()
    {
        if (!IsPlayerReady() || string.IsNullOrEmpty(_ownedBusinessId) ||
            !string.IsNullOrEmpty(_pendingDividendKey)) return;

        var dividendKey = Guid.NewGuid().ToString();
        _pendingDividendKey = dividendKey;
        SetButtonEnabled(_collectDividendButton, false);

        try
        {
            var response = await _apiClient.PostAsync("/api/mvp/collect-dividend", new
            {
                business_id = _ownedBusinessId,
                idempotency_key = dividendKey
            });

            if (response.Success)
            {
                SetLabelText(StatusLabel, "💰 Dividend collected!");
                await RefreshPlayerData();
            }
            else
            {
                SetLabelText(ErrorStateLabel, $"❌ Dividend collection failed: {response.Message}");
            }
        }
        catch (Exception ex)
        {
            GD.PrintErr($"Dividend collection error: {ex.Message}");
            SetLabelText(ErrorStateLabel, "❌ Network error during dividend collection");
        }
        finally
        {
            _pendingDividendKey = "";
            SetButtonEnabled(_collectDividendButton, true);
        }
    }

    // Sports Actions
    private async void OnJoinSportsButtonPressed()
    {
        if (!IsPlayerReady() || !string.IsNullOrEmpty(_pendingSportsJoinKey)) return;

        var joinKey = Guid.NewGuid().ToString();
        _pendingSportsJoinKey = joinKey;
        SetButtonEnabled(_joinSportsButton, false);

        try
        {
            var response = await _apiClient.PostAsync("/api/mvp/join-sports-club", new
            {
                idempotency_key = joinKey
            });

            if (response.Success)
            {
                SetLabelText(StatusLabel, "⚽ Sports club joined!");
                await RefreshPlayerData();
            }
            else
            {
                SetLabelText(ErrorStateLabel, $"❌ Sports club join failed: {response.Message}");
            }
        }
        catch (Exception ex)
        {
            GD.PrintErr($"Sports club join error: {ex.Message}");
            SetLabelText(ErrorStateLabel, "❌ Network error during sports club join");
        }
        finally
        {
            _pendingSportsJoinKey = "";
            SetButtonEnabled(_joinSportsButton, true);
        }
    }

    private async void OnTrainSportsButtonPressed()
    {
        if (!IsPlayerReady() || !string.IsNullOrEmpty(_pendingSportsTrainKey)) return;

        var trainKey = Guid.NewGuid().ToString();
        _pendingSportsTrainKey = trainKey;
        SetButtonEnabled(_trainSportsButton, false);

        try
        {
            var response = await _apiClient.PostAsync("/api/mvp/train-sports", new
            {
                stat_to_train = "strength", // Default to strength training
                idempotency_key = trainKey
            });

            if (response.Success)
            {
                SetLabelText(StatusLabel, "💪 Training completed! Stats improved.");
                await RefreshPlayerData();
            }
            else
            {
                SetLabelText(ErrorStateLabel, $"❌ Sports training failed: {response.Message}");
            }
        }
        catch (Exception ex)
        {
            GD.PrintErr($"Sports training error: {ex.Message}");
            SetLabelText(ErrorStateLabel, "❌ Network error during sports training");
        }
        finally
        {
            _pendingSportsTrainKey = "";
            SetButtonEnabled(_trainSportsButton, true);
        }
    }

    // Education Actions
    private async void OnExamButtonPressed()
    {
        if (!IsPlayerReady() || !string.IsNullOrEmpty(_pendingExamKey)) return;

        var examKey = Guid.NewGuid().ToString();
        _pendingExamKey = examKey;
        SetButtonEnabled(_examButton, false);

        try
        {
            var response = await _apiClient.PostAsync("/api/mvp/exam-info", new
            {
                idempotency_key = examKey
            });

            if (response.Success)
            {
                SetLabelText(StatusLabel, "📚 Exam info loaded!");
                // Show exam panel with loaded data
                ShowExamPanel(response.Data);
            }
            else
            {
                SetLabelText(ErrorStateLabel, $"❌ Exam info failed: {response.Message}");
            }
        }
        catch (Exception ex)
        {
            GD.PrintErr($"Exam info error: {ex.Message}");
            SetLabelText(ErrorStateLabel, "❌ Network error during exam info");
        }
        finally
        {
            _pendingExamKey = "";
            SetButtonEnabled(_examButton, true);
        }
    }

    // Building Actions
    private async void OnOpenBuildingButtonPressed()
    {
        if (!IsPlayerReady() || string.IsNullOrEmpty(_portfolioOpenBuildingId) ||
            !string.IsNullOrEmpty(_pendingBuildingOpenKey)) return;

        var openKey = Guid.NewGuid().ToString();
        _pendingBuildingOpenKey = openKey;
        SetButtonEnabled(_openBuildingButton, false);

        try
        {
            var response = await _apiClient.PostAsync("/api/mvp/open-building", new
            {
                building_id = _portfolioOpenBuildingId,
                idempotency_key = openKey
            });

            if (response.Success)
            {
                SetLabelText(StatusLabel, "🏢 Building opened!");
                await RefreshPlayerData();
            }
            else
            {
                SetLabelText(ErrorStateLabel, $"❌ Building open failed: {response.Message}");
            }
        }
        catch (Exception ex)
        {
            GD.PrintErr($"Building open error: {ex.Message}");
            SetLabelText(ErrorStateLabel, "❌ Network error during building open");
        }
        finally
        {
            _pendingBuildingOpenKey = "";
            SetButtonEnabled(_openBuildingButton, true);
        }
    }

    private async void OnRepairBuildingButtonPressed()
    {
        if (!IsPlayerReady() || string.IsNullOrEmpty(_portfolioRepairBuildingId) ||
            !string.IsNullOrEmpty(_pendingBuildingRepairKey)) return;

        var repairKey = Guid.NewGuid().ToString();
        _pendingBuildingRepairKey = repairKey;
        SetButtonEnabled(_repairBuildingButton, false);

        try
        {
            var response = await _apiClient.PostAsync("/api/mvp/repair-building", new
            {
                building_id = _portfolioRepairBuildingId,
                idempotency_key = repairKey
            });

            if (response.Success)
            {
                SetLabelText(StatusLabel, "🔧 Building repaired!");
                await RefreshPlayerData();
            }
            else
            {
                SetLabelText(ErrorStateLabel, $"❌ Building repair failed: {response.Message}");
            }
        }
        catch (Exception ex)
        {
            GD.PrintErr($"Building repair error: {ex.Message}");
            SetLabelText(ErrorStateLabel, "❌ Network error during building repair");
        }
        finally
        {
            _pendingBuildingRepairKey = "";
            SetButtonEnabled(_repairBuildingButton, true);
        }
    }

    // Utility Actions
    private async void OnRefreshButtonPressed()
    {
        if (!IsPlayerReady() || _pendingRefresh) return;

        _pendingRefresh = true;
        SetButtonEnabled(_refreshButton, false);

        try
        {
            await RefreshPlayerData();
            SetLabelText(StatusLabel, "🔄 Data refreshed!");
        }
        catch (Exception ex)
        {
            GD.PrintErr($"Refresh error: {ex.Message}");
            SetLabelText(ErrorStateLabel, "❌ Network error during refresh");
        }
        finally
        {
            _pendingRefresh = false;
            SetButtonEnabled(_refreshButton, true);
        }
    }

    private void OnVisualFocusButtonPressed()
    {
        // Toggle visual focus mode or center camera
        if (_cityVisualOverlay != null)
        {
            _cityVisualOverlay.ToggleFocusMode();
        }
    }

    // Helper Methods
    private void ShowExamPanel(object examData)
    {
        if (_examPanel != null)
        {
            _examPanel.ShowExam(examData);
        }
    }

    private void ConnectActionButtons()
    {
        _applyJobButton.Pressed += OnApplyJobButtonPressed;
        _workButton.Pressed += OnWorkButtonPressed;
        _sleepButton.Pressed += OnSleepButtonPressed;
        _eatButton.Pressed += OnEatButtonPressed;
        _buyBusinessButton.Pressed += OnBuyBusinessButtonPressed;
        _collectDividendButton.Pressed += OnCollectDividendButtonPressed;
        _joinSportsButton.Pressed += OnJoinSportsButtonPressed;
        _trainSportsButton.Pressed += OnTrainSportsButtonPressed;
        _examButton.Pressed += OnExamButtonPressed;
        _refreshButton.Pressed += OnRefreshButtonPressed;
        _openBuildingButton.Pressed += OnOpenBuildingButtonPressed;
        _repairBuildingButton.Pressed += OnRepairBuildingButtonPressed;
        _visualFocusButton.Pressed += OnVisualFocusButtonPressed;
    }
}
