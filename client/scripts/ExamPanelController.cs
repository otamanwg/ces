using Godot;
using System.Collections.Generic;
using System.Text.Json.Nodes;

public partial class ExamPanelController : Control
{
    [Export] public Label TitleLabel;
    [Export] public Label DescriptionLabel;
    [Export] public VBoxContainer QuestionsContainer;
    [Export] public Button SubmitButton;
    [Export] public Button CloseButton;

    private readonly Dictionary<int, OptionButton> _answerControls = new();
    private JsonNode _examData;

    public override void _Ready()
    {
        TitleLabel ??= GetNodeOrNull<Label>("%ExamTitleLabel");
        DescriptionLabel ??= GetNodeOrNull<Label>("%ExamDescriptionLabel");
        QuestionsContainer ??= GetNodeOrNull<VBoxContainer>("%QuestionsContainer");
        SubmitButton ??= GetNodeOrNull<Button>("%SubmitExamButton");
        CloseButton ??= GetNodeOrNull<Button>("%CloseExamButton");

        Visible = false;
        MouseFilter = MouseFilterEnum.Ignore;

        if (SubmitButton != null)
        {
            SubmitButton.Pressed += OnSubmitPressed;
        }

        if (CloseButton != null)
        {
            CloseButton.Pressed += OnClosePressed;
        }
    }

    public void LoadExam(JsonNode examData)
    {
        _examData = examData;
        _answerControls.Clear();
        MouseFilter = MouseFilterEnum.Stop;

        if (QuestionsContainer == null)
        {
            return;
        }

        foreach (Node child in QuestionsContainer.GetChildren())
        {
            child.QueueFree();
        }

        if (TitleLabel != null)
        {
            TitleLabel.Text = examData["title"]?.ToString() ?? "Іспит";
        }

        if (DescriptionLabel != null)
        {
            double cost = examData["cost_to_take"]?.GetValue<double>() ?? 100;
            DescriptionLabel.Text =
                $"{examData["description"]}\n\nВартість: {cost:N0} ₴ | Потрібно: {examData["passing_score"]}/5";
        }

        var questions = examData["questions"]?.AsArray();
        if (questions == null)
        {
            return;
        }

        foreach (var question in questions)
        {
            int qId = question["id"]?.GetValue<int>() ?? 0;

            var block = new VBoxContainer();
            block.AddThemeConstantOverride("separation", 4);

            var qLabel = new Label
            {
                Text = $"{qId}. {question["text"]}",
                AutowrapMode = TextServer.AutowrapMode.WordSmart,
            };
            block.AddChild(qLabel);

            var optionButton = new OptionButton();
            var options = question["options"]?.AsArray();
            if (options != null)
            {
                for (int i = 0; i < options.Count; i++)
                {
                    optionButton.AddItem(options[i]?.ToString() ?? $"Варіант {i + 1}", i);
                }
            }

            block.AddChild(optionButton);
            QuestionsContainer.AddChild(block);
            _answerControls[qId] = optionButton;
        }

        Visible = true;
    }

    public Dictionary<string, int> CollectAnswers()
    {
        var answers = new Dictionary<string, int>();
        foreach (var pair in _answerControls)
        {
            answers[pair.Key.ToString()] = pair.Value.Selected;
        }

        return answers;
    }

    public void HidePanel()
    {
        Visible = false;
        MouseFilter = MouseFilterEnum.Ignore;
    }

    private void OnSubmitPressed()
    {
        EmitSignal(SignalName.SubmitRequested, JsonSerializerHelper.ToJson(CollectAnswers()));
    }

    private void OnClosePressed()
    {
        HidePanel();
        EmitSignal(SignalName.Closed);
    }

    [Signal]
    public delegate void SubmitRequestedEventHandler(string answersJson);

    [Signal]
    public delegate void ClosedEventHandler();
}

public static class JsonSerializerHelper
{
    public static string ToJson(Dictionary<string, int> answers)
    {
        return System.Text.Json.JsonSerializer.Serialize(answers);
    }
}
