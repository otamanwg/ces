public enum DashboardPlayerActionEndpoint
{
	None,
	Vacancies,
	JobApply,
	Work,
	Sleep,
	Eat,
	BusinessMarket,
	BusinessBuy,
	BusinessDividend,
	SportsClubs,
	SportsJoin,
	SportsTrain,
	ExamInfo,
	ExamSubmit,
}

public static class DashboardPlayerActionEndpoints
{
	public static DashboardPlayerActionEndpoint Classify(string endpoint)
	{
		if (endpoint == "/api/jobs/vacancies")
		{
			return DashboardPlayerActionEndpoint.Vacancies;
		}
		if (endpoint.StartsWith("/api/jobs/apply"))
		{
			return DashboardPlayerActionEndpoint.JobApply;
		}
		if (endpoint.StartsWith("/api/jobs/work/"))
		{
			return DashboardPlayerActionEndpoint.Work;
		}
		if (endpoint.StartsWith("/api/hostels/sleep/"))
		{
			return DashboardPlayerActionEndpoint.Sleep;
		}
		if (endpoint.StartsWith("/api/needs/eat/"))
		{
			return DashboardPlayerActionEndpoint.Eat;
		}

		return endpoint switch
		{
			"/api/businesses/market" => DashboardPlayerActionEndpoint.BusinessMarket,
			"/api/businesses/buy" => DashboardPlayerActionEndpoint.BusinessBuy,
			"/api/businesses/dividend" => DashboardPlayerActionEndpoint.BusinessDividend,
			"/api/sports/clubs" => DashboardPlayerActionEndpoint.SportsClubs,
			"/api/sports/join" => DashboardPlayerActionEndpoint.SportsJoin,
			"/api/sports/train" => DashboardPlayerActionEndpoint.SportsTrain,
			"/api/education/exam/info" => DashboardPlayerActionEndpoint.ExamInfo,
			"/api/education/exam/submit" => DashboardPlayerActionEndpoint.ExamSubmit,
			_ => DashboardPlayerActionEndpoint.None,
		};
	}
}
