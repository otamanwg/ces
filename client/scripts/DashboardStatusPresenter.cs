using Godot;
using System.Collections.Generic;

public sealed class DashboardStatusPresenter
{
	private readonly Label _statusLabel;
	private readonly Label _errorStateLabel;
	private readonly Label _eventHistoryLabel;
	private readonly Queue<string> _eventHistory = new();
	private string _lastHistoryMessage = "";

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

	private void AddEventHistory(string message)
	{
		if (_lastHistoryMessage == message)
		{
			return;
		}

		_lastHistoryMessage = message;
		_eventHistory.Enqueue(message);
		while (_eventHistory.Count > 5)
		{
			_eventHistory.Dequeue();
		}

		if (_eventHistoryLabel != null)
		{
			_eventHistoryLabel.Text = "Події:\n" + string.Join("\n", _eventHistory);
		}
	}
}
