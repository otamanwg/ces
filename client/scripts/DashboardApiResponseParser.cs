#nullable enable

using System.Text.Json;
using System.Text.Json.Nodes;

public enum DashboardApiResponseParseStatus
{
	Success,
	Empty,
	Malformed,
}

public readonly record struct DashboardApiResponseParseResult(
	DashboardApiResponseParseStatus Status,
	JsonNode? Root
);

public static class DashboardApiResponseParser
{
	public static DashboardApiResponseParseResult Parse(string jsonBody)
	{
		if (string.IsNullOrWhiteSpace(jsonBody))
		{
			return new DashboardApiResponseParseResult(
				DashboardApiResponseParseStatus.Empty,
				null
			);
		}

		try
		{
			JsonNode? root = JsonNode.Parse(jsonBody);
			return root == null
				? new DashboardApiResponseParseResult(DashboardApiResponseParseStatus.Empty, null)
				: new DashboardApiResponseParseResult(DashboardApiResponseParseStatus.Success, root);
		}
		catch (JsonException)
		{
			return new DashboardApiResponseParseResult(
				DashboardApiResponseParseStatus.Malformed,
				null
			);
		}
	}
}
