using Godot;
using System;
using System.Threading.Tasks;

public partial class CityDashboardController
{
    // Note: Button fields are declared in main CityDashboardController.cs

    private void InitializePlayerActions()
    {
        _applyJobButton = GetNode<Button>("MainContainer/PlayerRail/ActionsContainer/ApplyJobButton");
        _workButton = GetNode<Button>("MainContainer/PlayerRail/ActionsContainer/WorkButton");
        _sleepButton = GetNode<Button>("MainContainer/PlayerRail/ActionsContainer/SleepButton");
        _eatButton = GetNode<Button>("MainContainer/PlayerRail/ActionsContainer/EatButton");
        _examButton = GetNode<Button>("MainContainer/PlayerRail/ActionsContainer/ExamButton");
        _refreshButton = GetNode<Button>("MainContainer/PlayerRail/ActionsContainer/RefreshButton");

        // Connect button signals
        _applyJobButton.Pressed += OnApplyJobPressed;
        _workButton.Pressed += OnWorkPressed;
        _sleepButton.Pressed += OnSleepPressed;
        _eatButton.Pressed += OnEatPressed;
        _examButton.Pressed += OnExamPressed;
        _refreshButton.Pressed += OnRefreshPressed;
    }

    private async void OnApplyJobPressed()
    {
        if (_session?.PlayerId == null) return;

        SetActionState(_applyJobButton, "processing");
        ErrorStateLabel.Text = "";

        try
        {
            var response = await _apiClient.PostAsync($"/api/jobs/apply", new { });
            if (response?.TryGetValue("success", out var success) == true && success.GetValue<bool>())
            {
                EffectsLabel.Text = "✅ Ви влаштувались на роботу!";
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
            SetActionState(_applyJobButton, "ready");
        }
    }

    private async void OnWorkPressed()
    {
        if (_session?.PlayerId == null) return;

        SetActionState(_workButton, "processing");
        ErrorStateLabel.Text = "";

        try
        {
            var response = await _apiClient.PostAsync($"/api/work/shift", new { });
            if (response?.TryGetValue("success", out var success) == true && success.GetValue<bool>())
            {
                EffectsLabel.Text = "✅ Зміну відпрацьовано!";
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
            SetActionState(_workButton, "ready");
        }
    }

    private async void OnSleepPressed()
    {
        if (_session?.PlayerId == null) return;

        SetActionState(_sleepButton, "processing");
        ErrorStateLabel.Text = "";

        try
        {
            var response = await _apiClient.PostAsync($"/api/sleep", new { });
            if (response?.TryGetValue("success", out var success) == true && success.GetValue<bool>())
            {
                EffectsLabel.Text = "✅ Відпочинок завершено!";
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
            SetActionState(_sleepButton, "ready");
        }
    }

    private async void OnEatPressed()
    {
        if (_session?.PlayerId == null) return;

        SetActionState(_eatButton, "processing");
        ErrorStateLabel.Text = "";

        try
        {
            var response = await _apiClient.PostAsync($"/api/eat", new { });
            if (response?.TryGetValue("success", out var success) == true && success.GetValue<bool>())
            {
                EffectsLabel.Text = "✅ Смачно!";
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
            SetActionState(_eatButton, "ready");
        }
    }

    private async void OnExamPressed()
    {
        if (_session?.PlayerId == null) return;

        SetActionState(_examButton, "processing");
        ErrorStateLabel.Text = "";

        try
        {
            var response = await _apiClient.GetAsync($"/api/exam/info");
            if (response?.TryGetValue("success", out var success) == true && success.GetValue<bool>())
            {
                _examPanel.ShowExamPanel(response);
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
            SetActionState(_examButton, "ready");
        }
    }

    private async void OnRefreshPressed()
    {
        await RefreshPlayerData();
    }

    private async Task RefreshPlayerData()
    {
        if (_session?.PlayerId == null) return;

        try
        {
            var response = await _apiClient.GetAsync($"/api/player/{_session.PlayerId}");
            if (response?.TryGetValue("success", out var success) == true && success.GetValue<bool>())
            {
                UpdatePlayerDisplay(response);
            }
        }
        catch (Exception ex)
        {
            ErrorStateLabel.Text = $"Помилка оновлення: {ex.Message}";
        }
    }

    private void SetActionState(Button button, string state)
    {
        switch (state)
        {
            case "processing":
                button.Disabled = true;
                button.Text = "...";
                break;
            case "ready":
                button.Disabled = false;
                // Restore original text based on button
                if (button == _applyJobButton) button.Text = "Знайти роботу";
                else if (button == _workButton) button.Text = "Працювати";
                else if (button == _sleepButton) button.Text = "Спати";
                else if (button == _eatButton) button.Text = "Поїсти";
                else if (button == _examButton) button.Text = "Іспит";
                else if (button == _refreshButton) button.Text = "Оновити";
                break;
        }
    }
}
