using Godot;
using System;
using System.Reflection;

public partial class ApiDispatchRuntimeSmoke : Node
{
	private static readonly BindingFlags PrivateInstance =
		BindingFlags.Instance | BindingFlags.NonPublic;

	public override void _Ready()
	{
		try
		{
			RunSmoke();
			GD.Print("API_DISPATCH_RUNTIME_SMOKE_OK");
			GetTree().Quit();
		}
		catch (Exception exception)
		{
			GD.PushError($"API dispatch runtime smoke failed: {exception}");
			GetTree().Quit(2);
		}
	}

	private static void RunSmoke()
	{
		var controller = new CityDashboardController();
		var statusLabel = new Label();
		var errorLabel = new Label();
		var historyLabel = new Label();

		try
		{
			SetField(
				controller,
				"_statusPresenter",
				new DashboardStatusPresenter(statusLabel, errorLabel, historyLabel)
			);

			SetField(controller, "_pendingWorkKey", "work-smoke");
			InvokeApiCallback(controller, "/api/jobs/work/player-smoke", """{"success":true""");
			AssertEqual("", GetField<string>(controller, "_pendingWorkKey"), "work pending key");
			AssertEqual(
				"Сервер повернув пошкоджену відповідь.",
				errorLabel.Text,
				"malformed response error"
			);

			SetField(controller, "_pendingSleepKey", "sleep-smoke");
			InvokeApiCallback(controller, "/api/hostels/sleep/player-smoke", "");
			AssertEqual("", GetField<string>(controller, "_pendingSleepKey"), "sleep pending key");
			AssertEqual("Порожня відповідь сервера.", errorLabel.Text, "empty response error");
		}
		finally
		{
			controller.Free();
			statusLabel.Free();
			errorLabel.Free();
			historyLabel.Free();
		}
	}

	private static void InvokeApiCallback(
		CityDashboardController controller,
		string endpoint,
		string body
	)
	{
		MethodInfo method = typeof(CityDashboardController).GetMethod(
			"OnApiRequestFinished",
			PrivateInstance
		) ?? throw new InvalidOperationException("OnApiRequestFinished was not found.");
		method.Invoke(controller, new object[] { endpoint, true, body });
	}

	private static void SetField<T>(CityDashboardController controller, string name, T value)
	{
		FieldInfo field = typeof(CityDashboardController).GetField(name, PrivateInstance)
			?? throw new InvalidOperationException($"{name} was not found.");
		field.SetValue(controller, value);
	}

	private static T GetField<T>(CityDashboardController controller, string name)
	{
		FieldInfo field = typeof(CityDashboardController).GetField(name, PrivateInstance)
			?? throw new InvalidOperationException($"{name} was not found.");
		return (T)field.GetValue(controller);
	}

	private static void AssertEqual<T>(T expected, T actual, string name)
	{
		if (!Equals(expected, actual))
		{
			throw new InvalidOperationException(
				$"{name}: expected '{expected}', got '{actual}'."
			);
		}
	}
}
