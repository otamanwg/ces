using System;
using Godot;

#nullable enable

/// <summary>
/// Phase G7: Портал для переходу між 3D-локаціями.
/// Гравець підходить до порталу і натискає E (interact) для переходу.
/// </summary>
public partial class LocationPortal : Area3D
{
    [Export] public string TargetScenePath = string.Empty;
    [Export] public string PortalName = "Портал";
    [Export] public float InteractionRange = 1.5f;

    private Label3D? _label;
    private bool _playerInRange;

    public override void _Ready()
    {
        BodyEntered += OnBodyEntered;
        BodyExited += OnBodyExited;

        _label = new Label3D
        {
            Text = $"[E] {PortalName}",
            Modulate = new Color(1, 1, 1, 0),
            PixelSize = 0.01f,
            OutlineSize = 12,
            Position = new Vector3(0, 2.0f, 0),
        };
        AddChild(_label);
    }

    public override void _PhysicsProcess(double delta)
    {
        if (_label == null)
        {
            return;
        }

        float targetAlpha = _playerInRange ? 1.0f : 0.0f;
        Color current = _label.Modulate;
        _label.Modulate = new Color(current.R, current.G, current.B, Mathf.Lerp(current.A, targetAlpha, 8.0f * (float)delta));
    }

    public override void _UnhandledInput(InputEvent @event)
    {
        if (@event.IsActionPressed("interact") && _playerInRange && !string.IsNullOrEmpty(TargetScenePath))
        {
            GD.Print($"[LocationPortal] Перехід до: {TargetScenePath}");
            var error = GetTree().ChangeSceneToFile(TargetScenePath);
            if (error != Error.Ok)
            {
                GD.PushError($"[LocationPortal] Не вдалось завантажити сцену: {TargetScenePath} ({error})");
            }
        }
    }

    private void OnBodyEntered(Node body)
    {
        if (body is PlayerAvatarController)
        {
            _playerInRange = true;
        }
    }

    private void OnBodyExited(Node body)
    {
        if (body is PlayerAvatarController)
        {
            _playerInRange = false;
        }
    }
}
