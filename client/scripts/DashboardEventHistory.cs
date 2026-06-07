using System.Collections.Generic;

public sealed class DashboardEventHistory
{
    private readonly int _capacity;
    private readonly Queue<string> _events = new();
    private string _lastMessage = "";

    public DashboardEventHistory(int capacity = 5)
    {
        _capacity = capacity;
    }

    public IReadOnlyCollection<string> Events => _events.ToArray();

    public bool Add(string message)
    {
        if (string.IsNullOrWhiteSpace(message) || _lastMessage == message)
        {
            return false;
        }

        _lastMessage = message;
        _events.Enqueue(message);
        while (_events.Count > _capacity)
        {
            _events.Dequeue();
        }

        return true;
    }
}
