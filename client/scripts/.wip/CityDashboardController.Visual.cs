using Godot;
using System;
using System.Text.Json.Nodes;
using System.Threading.Tasks;

public partial class CityDashboardController
{
    // Note: Visual layer fields are declared in main CityDashboardController.cs

    private void InitializeVisualLayer()
    {
        _cityVisualOverlay = GetNode<CityVisualOverlay>("MainContainer/VisualPanel/CityVisualOverlay");
        _visualFocusButton = GetNode<Button>("MainContainer/VisualPanel/VisualFocusButton");
        _CityNameLabel = GetNode<Label>("MainContainer/VisualPanel/CityInfoContainer/CityNameLabel");
        _TreasuryLabel = GetNode<Label>("MainContainer/VisualPanel/CityInfoContainer/TreasuryLabel");
        _InflationLabel = GetNode<Label>("MainContainer/VisualPanel/CityInfoContainer/InflationLabel");

        // Connect visual signals
        _visualFocusButton.Pressed += OnVisualFocusPressed;

        // Initialize visual state
        _visualFocusMode = VisualFocusMode.Overview;
        UpdateVisualFocusButton();
    }

    private async void OnVisualFocusPressed()
    {
        // Toggle between overview and street focus
        _visualFocusMode = _visualFocusMode == VisualFocusMode.Overview ?
            VisualFocusMode.Street : VisualFocusMode.Overview;

        UpdateVisualFocusButton();
        await RefreshCityVisual();
    }

    private void UpdateVisualFocusButton()
    {
        _visualFocusButton.Text = _visualFocusMode == VisualFocusMode.Overview ?
            "🏙️ до вулиці" : "🗺️ до огляду";
    }

    private async Task RefreshCityVisual()
    {
        try
        {
            var response = await _apiClient.GetAsync($"/api/city/status");
            if (response?.TryGetValue("success", out var success) == true && success.GetValue<bool>())
            {
                UpdateCityVisual(response);
            }
        }
        catch (Exception ex)
        {
            ErrorStateLabel.Text = $"Помилка оновлення візуалу: {ex.Message}";
        }
    }

    private void UpdateCityVisual(JsonNode response)
    {
        var cityData = response?["data"];
        if (cityData == null) return;

        // Update city info labels
        _CityNameLabel.Text = cityData?["name"]?.GetValue<string>() ?? "Місто";

        var treasury = cityData?["treasury_balance"]?.GetValue<decimal>() ?? 0;
        _TreasuryLabel.Text = $"Скарбниця: {treasury:N0} ₴";

        var inflation = cityData?["inflation_rate"]?.GetValue<decimal>() ?? 0;
        _InflationLabel.Text = $"Інфляція: {inflation:F2}%";

        // Update visual overlay
        if (_cityVisualOverlay != null)
        {
            _cityVisualOverlay.UpdateCityData(cityData, _visualFocusMode);
        }
    }

    private enum VisualFocusMode
    {
        Overview,
        Street
    }

    private VisualFocusMode _visualFocusMode;
}
