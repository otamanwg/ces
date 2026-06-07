using System;
using Godot;

#nullable enable

public partial class CharacterAvatarPreview : Node3D
{
    private const string AvatarPath = "res://assets/visual/anime/avatar/canonical_anime_avatar.glb";
    private const string StylizedShaderPath = "res://shaders/anime_stylized.gdshader";

    private bool _showPlatform = true;
    private MeshInstance3D? _platform;

    [Export]
    public bool ShowPlatform
    {
        get => _showPlatform;
        set
        {
            _showPlatform = value;
            if (_platform != null)
            {
                _platform.Visible = value;
            }
        }
    }
    [Export] public bool TransparentBackground { get; set; }
    [Export] public float CameraSize { get; set; } = 3.55f;
    [Export] public float AvatarScale { get; set; } = 1.28f;

    private DashboardAvatarProfile _profile = new();
    private PackedScene? _avatarScene;
    private Node3D? _avatar;
    private AnimationPlayer? _animationPlayer;
    private MeshInstance3D? _phone;
    private Node3D? _seat;
    private Shader? _stylizedShader;
    private AvatarActivity _activity = AvatarActivity.Idle;

    public override void _Ready()
    {
        _stylizedShader = GD.Load<Shader>(StylizedShaderPath);
        _avatarScene = GD.Load<PackedScene>(AvatarPath);
        BuildStage();
        LoadAvatar();
    }

    public void SetSelection(DashboardAvatarSelection selection)
    {
        SetProfile(selection.ToProfile());
    }

    public void SetProfile(DashboardAvatarProfile profile)
    {
        if (ProfilesMatch(_profile, profile))
        {
            return;
        }
        _profile = profile;
        ReloadAppearance();
    }

    public void SetPreviewActive(bool active)
    {
        ProcessMode = active ? ProcessModeEnum.Inherit : ProcessModeEnum.Disabled;
        if (active)
        {
            PlayActivity();
        }
    }

    public void SetActivity(AvatarActivity activity)
    {
        _activity = activity;
        PlayActivity();
    }

    public void SetActivityCode(string activityCode)
    {
        SetActivity(AvatarPresentationRules.ParseActivity(activityCode));
    }

    private void BuildStage()
    {
        var environment = new Godot.Environment
        {
            BackgroundMode = Godot.Environment.BGMode.Color,
            BackgroundColor = TransparentBackground
                ? new Color(0.75f, 0.92f, 0.96f, 0.0f)
                : new Color("bfeaf4"),
            AmbientLightSource = Godot.Environment.AmbientSource.Color,
            AmbientLightColor = new Color("dff8ff"),
            AmbientLightEnergy = 0.55f,
            TonemapMode = Godot.Environment.ToneMapper.Filmic,
        };
        AddChild(new WorldEnvironment { Environment = environment });
        AddChild(new DirectionalLight3D
        {
            LightColor = new Color("fff1c8"),
            LightEnergy = 1.05f,
            ShadowEnabled = true,
            RotationDegrees = new Vector3(-48.0f, -28.0f, 0.0f),
        });

        var camera = new Camera3D
        {
            Projection = Camera3D.ProjectionType.Orthogonal,
            Size = CameraSize,
            Position = new Vector3(3.8f, 2.65f, 5.2f),
            Current = true,
        };
        AddChild(camera);
        camera.LookAt(new Vector3(0.0f, 1.18f, 0.0f), Vector3.Up);

        var platformMaterial = new StandardMaterial3D
        {
            AlbedoColor = new Color("78c7bd"),
            Roughness = 0.82f,
        };
        _platform = new MeshInstance3D
        {
            Name = "PreviewPlatform",
            Mesh = new CylinderMesh
            {
                TopRadius = 1.05f,
                BottomRadius = 1.15f,
                Height = 0.12f,
                RadialSegments = 32,
            },
            MaterialOverride = platformMaterial,
            Position = new Vector3(0.0f, -0.06f, 0.0f),
            Visible = ShowPlatform,
        };
        AddChild(_platform);
        BuildSeat();
    }

    private void BuildSeat()
    {
        var seatMaterial = new StandardMaterial3D
        {
            AlbedoColor = new Color("31545f"),
            Roughness = 0.78f,
        };
        _seat = new Node3D
        {
            Name = "ContextSeat",
            Position = new Vector3(-0.45f, 0.0f, 0.0f),
            Visible = false,
        };
        _seat.AddChild(new MeshInstance3D
        {
            Name = "SeatSurface",
            Mesh = new BoxMesh { Size = new Vector3(1.05f, 0.12f, 0.44f) },
            MaterialOverride = seatMaterial,
            Position = new Vector3(0.0f, 0.66f, -0.28f),
        });
        foreach (float x in new[] { -0.38f, 0.38f })
        {
            _seat.AddChild(new MeshInstance3D
            {
                Name = "SeatLeg",
                Mesh = new BoxMesh { Size = new Vector3(0.09f, 0.58f, 0.09f) },
                MaterialOverride = seatMaterial,
                Position = new Vector3(x, 0.31f, -0.28f),
            });
        }
        AddChild(_seat);
    }

    private void LoadAvatar()
    {
        if (_avatarScene == null)
        {
            GD.PushWarning($"Character avatar preview unavailable: {AvatarPath}");
            return;
        }
        _avatar = _avatarScene.Instantiate<Node3D>();
        _avatar.Name = "CharacterPreviewAvatar";
        _avatar.Scale = Vector3.One * AvatarScale;
        AddChild(_avatar);
        _animationPlayer = CanonicalAvatarAppearanceApplier.FindDescendant<AnimationPlayer>(_avatar);
        ReloadAppearance();
    }

    private void ReloadAppearance()
    {
        if (_avatar == null)
        {
            return;
        }
        var previous = _avatar;
        int index = previous.GetIndex();
        RemoveChild(previous);
        previous.Free();
        _avatar = null;
        _animationPlayer = null;
        _phone = null;

        if (_avatarScene == null)
        {
            return;
        }
        _avatar = _avatarScene.Instantiate<Node3D>();
        _avatar.Name = "CharacterPreviewAvatar";
        _avatar.Scale = Vector3.One * AvatarScale;
        AddChild(_avatar);
        MoveChild(_avatar, index);
        CanonicalAvatarAppearanceApplier.Apply(
            _avatar,
            AvatarAppearanceResolver.Resolve(_profile),
            _stylizedShader
        );
        _animationPlayer = CanonicalAvatarAppearanceApplier.FindDescendant<AnimationPlayer>(_avatar);
        AttachPhone();
        PlayActivity();
    }

    private void AttachPhone()
    {
        if (_avatar == null)
        {
            return;
        }
        var skeleton = CanonicalAvatarAppearanceApplier.FindDescendant<Skeleton3D>(_avatar);
        if (skeleton == null)
        {
            return;
        }
        var attachment = new BoneAttachment3D
        {
            Name = "PhoneAttachment",
            BoneName = "RightHand",
        };
        skeleton.AddChild(attachment);
        _phone = new MeshInstance3D
        {
            Name = "Phone",
            Mesh = new BoxMesh { Size = new Vector3(0.10f, 0.22f, 0.03f) },
            MaterialOverride = new StandardMaterial3D
            {
                AlbedoColor = new Color("182235"),
                Metallic = 0.18f,
                Roughness = 0.36f,
            },
            Position = new Vector3(0.0f, 0.09f, 0.045f),
            RotationDegrees = new Vector3(0.0f, 0.0f, 12.0f),
        };
        attachment.AddChild(_phone);
        UpdateActivityProp();
    }

    private void PlayActivity()
    {
        UpdateActivityProp();
        if (_animationPlayer == null)
        {
            return;
        }
        StringName? animationName = ResolveAnimationName(_animationPlayer, _activity);
        if (animationName == null)
        {
            return;
        }
        var animation = _animationPlayer.GetAnimation(animationName);
        if (animation != null)
        {
            animation.LoopMode = Animation.LoopModeEnum.Linear;
        }
        _animationPlayer.Play(animationName, 0.18);
    }

    private void UpdateActivityProp()
    {
        if (_phone != null)
        {
            _phone.Visible = _activity == AvatarActivity.Phone;
        }
        if (_seat != null)
        {
            _seat.Visible = _activity == AvatarActivity.Sit;
        }
    }

    private static StringName? ResolveAnimationName(
        AnimationPlayer animationPlayer,
        AvatarActivity activity
    )
    {
        string code = AvatarPresentationRules.ActivityCode(activity);
        foreach (StringName animationName in animationPlayer.GetAnimationList())
        {
            string candidate = animationName.ToString();
            if (candidate.Equals(code, StringComparison.OrdinalIgnoreCase)
                || candidate.EndsWith($"|{code}", StringComparison.OrdinalIgnoreCase)
                || candidate.EndsWith($"/{code}", StringComparison.OrdinalIgnoreCase))
            {
                return animationName;
            }
        }
        return null;
    }

    private static bool ProfilesMatch(DashboardAvatarProfile left, DashboardAvatarProfile right)
    {
        return left.BodyPresetCode == right.BodyPresetCode
            && left.FacePresetCode == right.FacePresetCode
            && left.SkinToneCode == right.SkinToneCode
            && left.HairStyleCode == right.HairStyleCode
            && left.HairColorCode == right.HairColorCode;
    }
}
