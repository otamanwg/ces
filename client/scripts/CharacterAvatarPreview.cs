using Godot;

#nullable enable

public partial class CharacterAvatarPreview : Node3D
{
	private const string AvatarPath = "res://assets/visual/anime/avatar/canonical_anime_avatar.glb";
	private const string StylizedShaderPath = "res://shaders/anime_stylized.gdshader";

	private DashboardAvatarProfile _profile = new();
	private PackedScene? _avatarScene;
	private Node3D? _avatar;
	private AnimationPlayer? _animationPlayer;
	private Shader? _stylizedShader;

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

	private void BuildStage()
	{
		var environment = new Godot.Environment
		{
			BackgroundMode = Godot.Environment.BGMode.Color,
			BackgroundColor = new Color("bfeaf4"),
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
			Size = 3.55f,
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
		AddChild(new MeshInstance3D
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
		});
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
		_avatar.Scale = Vector3.One * 1.28f;
		AddChild(_avatar);
		_animationPlayer = CanonicalAvatarAppearanceApplier.FindDescendant<AnimationPlayer>(_avatar);
		ReloadAppearance();
		PlayIdle();
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

		if (_avatarScene == null)
		{
			return;
		}
		_avatar = _avatarScene.Instantiate<Node3D>();
		_avatar.Name = "CharacterPreviewAvatar";
		_avatar.Scale = Vector3.One * 1.28f;
		AddChild(_avatar);
		MoveChild(_avatar, index);
		CanonicalAvatarAppearanceApplier.Apply(
			_avatar,
			AvatarAppearanceResolver.Resolve(_profile),
			_stylizedShader
		);
		_animationPlayer = CanonicalAvatarAppearanceApplier.FindDescendant<AnimationPlayer>(_avatar);
		PlayIdle();
	}

	private void PlayIdle()
	{
		if (_animationPlayer == null || !_animationPlayer.HasAnimation("idle"))
		{
			return;
		}
		var animation = _animationPlayer.GetAnimation("idle");
		if (animation != null)
		{
			animation.LoopMode = Animation.LoopModeEnum.Linear;
		}
		_animationPlayer.Play("idle", 0.12);
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
