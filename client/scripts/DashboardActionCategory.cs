using System;

/// <summary>
/// Categories for dashboard action buttons, used for visual grouping
/// and color coding in the gameplay HUD (Sprint 60 item #37).
/// </summary>
public enum DashboardActionCategory
{
    Survival,  // Sleep, Eat
    Work,      // ApplyJob, Work, Exam
    Business,  // BuyBusiness, CollectDividend
    Sports,    // JoinSports, TrainSports
    System,    // Refresh, PoliceRecovery
}

public static class DashboardActionCategoryStyle
{
    public static readonly DashboardVisualColor SurvivalAccent = new(0.90f, 0.60f, 0.36f);  // warm orange
    public static readonly DashboardVisualColor WorkAccent = new(0.36f, 0.56f, 0.90f);      // blue
    public static readonly DashboardVisualColor BusinessAccent = new(0.36f, 0.90f, 0.45f);  // green
    public static readonly DashboardVisualColor SportsAccent = new(0.60f, 0.36f, 0.90f);    // purple
    public static readonly DashboardVisualColor SystemAccent = new(0.54f, 0.54f, 0.58f);    // gray

    public static DashboardVisualColor Accent(DashboardActionCategory category) => category switch
    {
        DashboardActionCategory.Survival => SurvivalAccent,
        DashboardActionCategory.Work => WorkAccent,
        DashboardActionCategory.Business => BusinessAccent,
        DashboardActionCategory.Sports => SportsAccent,
        _ => SystemAccent,
    };

    public static string HeaderText(DashboardActionCategory category) => category switch
    {
        DashboardActionCategory.Survival => "Виживання",
        DashboardActionCategory.Work => "Робота",
        DashboardActionCategory.Business => "Бізнес",
        DashboardActionCategory.Sports => "Спорт",
        _ => "Система",
    };
}
