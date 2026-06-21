using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;

#nullable enable

/// <summary>
/// Education catalog and enrollment state for the Sprint 61 Education panel.
/// Backed by /api/education/courses, /api/education/active, /api/education/completed.
/// </summary>
public sealed class DashboardEducationModel
{
    public IReadOnlyList<DashboardEducationCourse> Courses { get; init; } = Array.Empty<DashboardEducationCourse>();
    public IReadOnlyList<DashboardEducationEnrollment> Active { get; init; } = Array.Empty<DashboardEducationEnrollment>();
    public IReadOnlyList<DashboardEducationEnrollment> Completed { get; init; } = Array.Empty<DashboardEducationEnrollment>();

    public bool HasActiveEnrollment => Active.Count > 0;
    public bool HasCompletedCourses => Completed.Count > 0;

    public static DashboardEducationModel FromJson(JsonNode? coursesData, JsonNode? activeData, JsonNode? completedData)
    {
        return new DashboardEducationModel
        {
            Courses = ParseCourses(coursesData?["courses"]?.AsArray()),
            Active = ParseEnrollments(activeData?["active"]?.AsArray()),
            Completed = ParseEnrollments(completedData?["completed"]?.AsArray()),
        };
    }

    private static IReadOnlyList<DashboardEducationCourse> ParseCourses(JsonArray? courses)
    {
        if (courses == null || courses.Count == 0)
        {
            return Array.Empty<DashboardEducationCourse>();
        }

        var items = new List<DashboardEducationCourse>();
        foreach (var course in courses)
        {
            if (course != null)
            {
                items.Add(DashboardEducationCourse.FromJson(course));
            }
        }

        return items;
    }

    private static IReadOnlyList<DashboardEducationEnrollment> ParseEnrollments(JsonArray? enrollments)
    {
        if (enrollments == null || enrollments.Count == 0)
        {
            return Array.Empty<DashboardEducationEnrollment>();
        }

        var items = new List<DashboardEducationEnrollment>();
        foreach (var enrollment in enrollments)
        {
            if (enrollment != null)
            {
                items.Add(DashboardEducationEnrollment.FromJson(enrollment));
            }
        }

        return items;
    }
}

public sealed class DashboardEducationCourse
{
    public string Code { get; init; } = "";
    public string Name { get; init; } = "Курс";
    public int DurationDays { get; init; }
    public double Cost { get; init; }
    public int EnergyPerDay { get; init; }
    public IReadOnlyList<string> Opens { get; init; } = Array.Empty<string>();
    public IReadOnlyList<string> RequiredFor { get; init; } = Array.Empty<string>();

    public string OpensText => Opens.Count > 0 ? string.Join(", ", Opens) : "—";
    public string RequiredForText => RequiredFor.Count > 0 ? string.Join(", ", RequiredFor) : "—";
    public string SummaryText => $"{Name} | {DurationDays} днів | {Cost:N0} ₴ | {EnergyPerDay} енергії/день";

    public static DashboardEducationCourse FromJson(JsonNode data)
    {
        return new DashboardEducationCourse
        {
            Code = data["code"]?.ToString() ?? "",
            Name = data["name"]?.ToString() ?? "Курс",
            DurationDays = data["duration_days"]?.GetValue<int>() ?? 0,
            Cost = data["cost"]?.GetValue<double>() ?? 0.0,
            EnergyPerDay = data["energy_per_day"]?.GetValue<int>() ?? 0,
            Opens = ParseStringArray(data["opens"]?.AsArray()),
            RequiredFor = ParseStringArray(data["required_for"]?.AsArray()),
        };
    }

    private static IReadOnlyList<string> ParseStringArray(JsonArray? values)
    {
        if (values == null || values.Count == 0)
        {
            return Array.Empty<string>();
        }

        var parsed = new List<string>();
        foreach (var value in values)
        {
            string text = value?.ToString() ?? "";
            if (!string.IsNullOrWhiteSpace(text))
            {
                parsed.Add(text);
            }
        }

        return parsed;
    }
}

public sealed class DashboardEducationEnrollment
{
    public string Id { get; init; } = "";
    public string Course { get; init; } = "";
    public string Mode { get; init; } = "";
    public string Status { get; init; } = "";
    public bool IsFake { get; init; }

    public string ModeLabel => Mode switch
    {
        "full_time" => "Очно",
        "part_time" => "Заочно",
        _ => Mode,
    };

    public string FakeBadge => IsFake ? " ⚠ ФЕЙК" : "";

    public static DashboardEducationEnrollment FromJson(JsonNode data)
    {
        return new DashboardEducationEnrollment
        {
            Id = data["id"]?.ToString() ?? "",
            Course = data["course"]?.ToString() ?? "",
            Mode = data["mode"]?.ToString() ?? "",
            Status = data["status"]?.ToString() ?? "",
            IsFake = data["is_fake"]?.GetValue<bool>() ?? false,
        };
    }
}
