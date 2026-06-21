using System;
using Godot;

#nullable enable

/// <summary>
/// Phase G7: 3D-аватар гравця з third-person камерою та WASD + миша управлінням.
/// Базові анімації: idle / walk / run. Скін застосовується через AvatarAppearanceResolver.
/// </summary>
public partial class PlayerAvatarController : CharacterBody3D
{
    [Export] public float WalkSpeed = 3.5f;
    [Export] public float RunSpeed = 7.0f;
    [Export] public float RotationSpeed = 8.0f;
    [Export] public float CameraDistance = 4.5f;
    [Export] public float CameraHeight = 2.2f;
    [Export] public float CameraLerp = 6.0f;
    [Export] public float MouseSensitivity = 0.0025f;

    private Camera3D _camera = null!;
    private Node3D _cameraPivot = null!;
    private AnimationPlayer? _animationPlayer;
    private float _cameraYaw;
    private float _cameraPitch = -0.3f;

    public override void _Ready()
    {
        // Шукаємо камеру всередині сцени
        _cameraPivot = GetNodeOrNull<Node3D>("CameraPivot") ?? CreateCameraPivot();
        _camera = _cameraPivot.GetNodeOrNull<Camera3D>("Camera3D") ?? CreateCamera(_cameraPivot);

        // Шукаємо AnimationPlayer у аватарі
        _animationPlayer = FindAnimationPlayer(this);
        if (_animationPlayer == null)
        {
            GD.PushWarning("PlayerAvatarController: AnimationPlayer не знайдено — анімації не працюватимуть.");
        }

        Input.MouseMode = Input.MouseModeEnum.Captured;
    }

    public override void _ExitTree()
    {
        if (Input.MouseMode == Input.MouseModeEnum.Captured)
        {
            Input.MouseMode = Input.MouseModeEnum.Visible;
        }
    }

    public override void _UnhandledInput(InputEvent @event)
    {
        if (@event is InputEventMouseMotion mouseMotion && Input.MouseMode == Input.MouseModeEnum.Captured)
        {
            _cameraYaw -= mouseMotion.Relative.X * MouseSensitivity;
            _cameraPitch = Mathf.Clamp(_cameraPitch - mouseMotion.Relative.Y * MouseSensitivity, -1.2f, 0.3f);
        }

        if (@event is InputEventKey key && key.Pressed && key.Keycode == Key.Escape)
        {
            Input.MouseMode = Input.MouseMode == Input.MouseModeEnum.Captured
                ? Input.MouseModeEnum.Visible
                : Input.MouseModeEnum.Captured;
        }
    }

    public override void _PhysicsProcess(double delta)
    {
        UpdateCameraPivot((float)delta);

        Vector2 inputDir = Input.GetVector("move_left", "move_right", "move_forward", "move_back");
        bool sprinting = Input.IsActionPressed("sprint");
        float speed = sprinting ? RunSpeed : WalkSpeed;

        // Напрямок руху відносно камери
        Basis cameraBasis = _cameraPivot.Basis;
        Vector3 forward = -cameraBasis.Z;
        forward.Y = 0;
        forward = forward.Normalized();
        Vector3 right = cameraBasis.X;
        right.Y = 0;
        right = right.Normalized();

        Vector3 direction = (forward * -inputDir.Y + right * inputDir.X).Normalized();

        if (direction != Vector3.Zero)
        {
            Velocity = direction * speed;
            // Поворот аватара у напрямок руху
            Quaternion targetRotation = Quaternion.FromEuler(new Vector3(0, Mathf.Atan2(-direction.X, -direction.Z), 0));
            Quaternion = Quaternion.Slerp(targetRotation, RotationSpeed * (float)delta);
        }
        else
        {
            Velocity = Velocity.MoveToward(Vector3.Zero, WalkSpeed * (float)delta);
        }

        MoveAndSlide();
        UpdateAnimation(direction, sprinting);
        SyncPositionToServer();
    }

    private void SyncPositionToServer()
    {
        var networkManager = GetNodeOrNull<NetworkManager>("/root/NetworkManager");
        networkManager?.SyncPlayerPosition(GlobalPosition.X, GlobalPosition.Y, GlobalPosition.Z, Rotation.Y);
    }

    private void UpdateCameraPivot(float delta)
    {
        _cameraPivot.GlobalPosition = _cameraPivot.GlobalPosition.Lerp(GlobalPosition, CameraLerp * delta);
        _cameraPivot.Rotation = new Vector3(_cameraPitch, _cameraYaw, 0);
    }

    private void UpdateAnimation(Vector3 direction, bool sprinting)
    {
        if (_animationPlayer == null)
        {
            return;
        }

        string targetAnim;
        if (direction == Vector3.Zero)
        {
            targetAnim = "idle";
        }
        else if (sprinting)
        {
            targetAnim = "run";
        }
        else
        {
            targetAnim = "walk";
        }

        if (_animationPlayer.HasAnimation(targetAnim) && _animationPlayer.CurrentAnimation != targetAnim)
        {
            _animationPlayer.Play(targetAnim);
        }
        else if (!_animationPlayer.HasAnimation(targetAnim) && _animationPlayer.CurrentAnimation != string.Empty)
        {
            // Якщо анімацій немає — просто зупиняємо
            _animationPlayer.Stop();
        }
    }

    private static AnimationPlayer? FindAnimationPlayer(Node root)
    {
        if (root is AnimationPlayer ap)
        {
            return ap;
        }

        foreach (Node child in root.GetChildren())
        {
            var found = FindAnimationPlayer(child);
            if (found != null)
            {
                return found;
            }
        }

        return null;
    }

    private Node3D CreateCameraPivot()
    {
        var pivot = new Node3D { Name = "CameraPivot" };
        AddChild(pivot);
        return pivot;
    }

    private Camera3D CreateCamera(Node3D pivot)
    {
        var cam = new Camera3D
        {
            Name = "Camera3D",
            Position = new Vector3(0, CameraHeight, CameraDistance),
            Current = true,
        };
        pivot.AddChild(cam);
        return cam;
    }

    /// <summary>
    /// Повертає поточну позицію для WebSocket-синхронізації.
    /// </summary>
    public Vector3 SyncPosition => GlobalPosition;

    /// <summary>
    /// Повертає поточний ротацію (yaw) для WebSocket-синхронізації.
    /// </summary>
    public float SyncRotationY => Rotation.Y;
}
