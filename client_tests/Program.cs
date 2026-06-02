using System;
using System.Linq;

static void AssertEqual<T>(T expected, T actual, string message)
{
	if (!Equals(expected, actual))
	{
		throw new InvalidOperationException($"{message}: expected {expected}, got {actual}");
	}
}

static void AssertSequence(string[] expected, string[] actual, string message)
{
	if (!expected.SequenceEqual(actual))
	{
		throw new InvalidOperationException(
			$"{message}: expected [{string.Join(", ", expected)}], got [{string.Join(", ", actual)}]"
		);
	}
}

var history = new DashboardEventHistory();

AssertEqual(false, history.Add(""), "Empty messages are ignored");
AssertEqual(false, history.Add("   "), "Whitespace messages are ignored");
AssertEqual(true, history.Add("Registered"), "First event is accepted");
AssertEqual(false, history.Add("Registered"), "Consecutive duplicate is ignored");
AssertSequence(new[] { "Registered" }, history.Events.ToArray(), "Duplicate does not change history");

history.Add("Applied job");
history.Add("Worked");
history.Add("Slept");
history.Add("Ate");
history.Add("Bought business");

AssertSequence(
	new[] { "Applied job", "Worked", "Slept", "Ate", "Bought business" },
	history.Events.ToArray(),
	"History keeps the newest five events"
);

Console.WriteLine("Client logic tests passed.");
