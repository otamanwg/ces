using System;

#nullable enable

public static class DashboardVisualAnimation
{
	public static float Pulse(double elapsedSeconds, double cyclesPerSecond = 0.60, double phase = 0.0)
	{
		if (!double.IsFinite(elapsedSeconds) || !double.IsFinite(cyclesPerSecond) || !double.IsFinite(phase))
		{
			return 0.5f;
		}

		double angle = (elapsedSeconds * cyclesPerSecond + phase) * Math.PI * 2.0;
		return (float)((Math.Sin(angle) + 1.0) * 0.5);
	}

	public static float TravelFraction(double elapsedSeconds, double speed = 0.12, double phase = 0.0)
	{
		if (!double.IsFinite(elapsedSeconds) || !double.IsFinite(speed) || !double.IsFinite(phase))
		{
			return 0.0f;
		}

		double progress = elapsedSeconds * speed + phase;
		return (float)(progress - Math.Floor(progress));
	}
}
