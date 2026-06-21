using Godot;
using System.Collections.Generic;
using System.Text.Json.Nodes;

/// <summary>
/// Sprint 61: Education panel overlay controller.
/// Displays course catalog, active enrollments, completed courses.
/// Emits signals for enroll and take-exam actions.
/// </summary>
public partial class EducationPanelController : Control
{
    [Export] public Label TitleLabel;
    [Export] public Label DescriptionLabel;
    [Export] public VBoxContainer CoursesContainer;
    [Export] public VBoxContainer ActiveContainer;
    [Export] public VBoxContainer CompletedContainer;
    [Export] public Button CloseButton;
    [Export] public Button EnrollButton;
    [Export] public OptionButton CourseOptionButton;
    [Export] public OptionButton ModeOptionButton;

    private DashboardEducationModel _model;
    private string _selectedCourseCode = "";

    public override void _Ready()
    {
        TitleLabel ??= GetNodeOrNull<Label>("%EducationTitleLabel");
        DescriptionLabel ??= GetNodeOrNull<Label>("%EducationDescriptionLabel");
        CoursesContainer ??= GetNodeOrNull<VBoxContainer>("%EducationCoursesContainer");
        ActiveContainer ??= GetNodeOrNull<VBoxContainer>("%EducationActiveContainer");
        CompletedContainer ??= GetNodeOrNull<VBoxContainer>("%EducationCompletedContainer");
        CloseButton ??= GetNodeOrNull<Button>("%EducationCloseButton");
        EnrollButton ??= GetNodeOrNull<Button>("%EducationEnrollButton");
        CourseOptionButton ??= GetNodeOrNull<OptionButton>("%EducationCourseOption");
        ModeOptionButton ??= GetNodeOrNull<OptionButton>("%EducationModeOption");

        Visible = false;
        MouseFilter = MouseFilterEnum.Ignore;

        if (CloseButton != null)
        {
            CloseButton.Pressed += OnClosePressed;
        }

        if (EnrollButton != null)
        {
            EnrollButton.Pressed += OnEnrollPressed;
        }

        if (CourseOptionButton != null)
        {
            CourseOptionButton.ItemSelected += OnCourseSelected;
        }
    }

    public void LoadModel(DashboardEducationModel model)
    {
        _model = model;
        MouseFilter = MouseFilterEnum.Stop;
        Visible = true;

        if (TitleLabel != null)
        {
            TitleLabel.Text = "Освіта";
        }

        if (DescriptionLabel != null)
        {
            int activeCount = model.Active.Count;
            int completedCount = model.Completed.Count;
            DescriptionLabel.Text = $"Активних: {activeCount} | Завершено: {completedCount}";
        }

        PopulateCourses(model);
        PopulateActive(model);
        PopulateCompleted(model);
        PopulateCourseOptions(model);
    }

    private void PopulateCourses(DashboardEducationModel model)
    {
        if (CoursesContainer == null)
        {
            return;
        }

        foreach (Node child in CoursesContainer.GetChildren())
        {
            child.QueueFree();
        }

        foreach (var course in model.Courses)
        {
            var label = new Label
            {
                Text = $"📖 {course.SummaryText}\n   Відкриває: {course.OpensText} | Для: {course.RequiredForText}",
                AutowrapMode = TextServer.AutowrapMode.WordSmart,
            };
            CoursesContainer.AddChild(label);
        }
    }

    private void PopulateActive(DashboardEducationModel model)
    {
        if (ActiveContainer == null)
        {
            return;
        }

        foreach (Node child in ActiveContainer.GetChildren())
        {
            child.QueueFree();
        }

        if (model.Active.Count == 0)
        {
            ActiveContainer.AddChild(new Label { Text = "Немає активних курсів" });
            return;
        }

        foreach (var enrollment in model.Active)
        {
            var label = new Label
            {
                Text = $"📚 {enrollment.Course} | {enrollment.ModeLabel}{enrollment.FakeBadge}",
                AutowrapMode = TextServer.AutowrapMode.WordSmart,
            };
            ActiveContainer.AddChild(label);
        }
    }

    private void PopulateCompleted(DashboardEducationModel model)
    {
        if (CompletedContainer == null)
        {
            return;
        }

        foreach (Node child in CompletedContainer.GetChildren())
        {
            child.QueueFree();
        }

        if (model.Completed.Count == 0)
        {
            CompletedContainer.AddChild(new Label { Text = "Немає завершених курсів" });
            return;
        }

        foreach (var enrollment in model.Completed)
        {
            var label = new Label
            {
                Text = $"✅ {enrollment.Course} | {enrollment.ModeLabel}{enrollment.FakeBadge}",
                AutowrapMode = TextServer.AutowrapMode.WordSmart,
            };
            CompletedContainer.AddChild(label);
        }
    }

    private void PopulateCourseOptions(DashboardEducationModel model)
    {
        if (CourseOptionButton == null)
        {
            return;
        }

        CourseOptionButton.Clear();
        CourseOptionButton.AddItem("Оберіть курс...", -1);
        foreach (var course in model.Courses)
        {
            CourseOptionButton.AddItem($"{course.Name} ({course.Cost:N0} ₴)", CourseOptionButton.ItemCount - 1);
        }

        CourseOptionButton.Select(0);
        _selectedCourseCode = "";
        UpdateEnrollButtonState();
    }

    private void OnCourseSelected(long index)
    {
        if (index <= 0 || _model == null || index > _model.Courses.Count)
        {
            _selectedCourseCode = "";
        }
        else
        {
            _selectedCourseCode = _model.Courses[(int)index - 1].Code;
        }

        UpdateEnrollButtonState();
    }

    private void UpdateEnrollButtonState()
    {
        if (EnrollButton != null)
        {
            EnrollButton.Disabled = string.IsNullOrEmpty(_selectedCourseCode);
        }
    }

    private void OnEnrollPressed()
    {
        if (string.IsNullOrEmpty(_selectedCourseCode))
        {
            return;
        }

        string mode = ModeOptionButton?.GetSelectedId() == 1 ? "part_time" : "full_time";
        EmitSignal(SignalName.EnrollRequested, _selectedCourseCode, mode);
    }

    private void OnClosePressed()
    {
        HidePanel();
        EmitSignal(SignalName.Closed);
    }

    public void HidePanel()
    {
        Visible = false;
        MouseFilter = MouseFilterEnum.Ignore;
    }

    [Signal]
    public delegate void EnrollRequestedEventHandler(string courseCode, string mode);

    [Signal]
    public delegate void ClosedEventHandler();
}
