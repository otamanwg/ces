using Godot;

public sealed class DashboardStatusPresenter
{
    private readonly Label _statusLabel;
    private readonly Label _errorStateLabel;
    private readonly Label _eventHistoryLabel;
    private readonly DashboardEventHistory _eventHistory = new();

    public DashboardStatusPresenter(Label statusLabel, Label errorStateLabel, Label eventHistoryLabel)
    {
        _statusLabel = statusLabel;
        _errorStateLabel = errorStateLabel;
        _eventHistoryLabel = eventHistoryLabel;
    }

    public void SetStatus(string message, bool addToHistory = false)
    {
        if (_statusLabel != null)
        {
            _statusLabel.Text = message;
        }

        if (addToHistory && !string.IsNullOrWhiteSpace(message))
        {
            AddEventHistory(message);
        }
    }

    public void SetError(string message)
    {
        SetStatus(message, true);
        if (_errorStateLabel != null)
        {
            _errorStateLabel.Text = message;
        }
    }

    public void ClearError()
    {
        if (_errorStateLabel != null)
        {
            _errorStateLabel.Text = "";
        }
    }

    public void AddEvent(string message)
    {
        if (!string.IsNullOrWhiteSpace(message))
        {
            AddEventHistory(message);
        }
    }

    private void AddEventHistory(string message)
    {
        if (!_eventHistory.Add(message))
        {
            return;
        }

        if (_eventHistoryLabel != null)
        {
            var lines = new System.Collections.Generic.List<string>();
            int index = 0;
            foreach (string evt in _eventHistory.Events)
            {
                // Most recent event gets a bright marker, older events fade.
                float alpha = 0.95f - index * 0.15f;
                string marker = index == 0 ? "▶" : "·";
                lines.Add($"{marker} {evt}");
                index++;
            }
            _eventHistoryLabel.Text = string.Join("\n", lines);
        }
    }
}
