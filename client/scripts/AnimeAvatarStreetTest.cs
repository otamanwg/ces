using System;
using System.Collections.Generic;
using Godot;

#nullable enable

public partial class AnimeAvatarStreetTest : Node3D
{
	private const float StateDurationSeconds = 4.0f;
	private const string StylizedShaderPath = "res://shaders/anime_stylized.gdshader";
	private const string CanonicalAvatarPath = "res://assets/visual/anime/avatar/canonical_anime_avatar.glb";

	private readonly Dictionary<AvatarActivity, Button> _activityButtons = new();
	private readonly Dictionary<AvatarLodLevel, Button> _lodButtons = new();

	private Node3D _avatarRoot = null!;
	private Node3D _bodyRig = null!;
	private Node3D _faceDetail = null!;
	private Node3D _distanceAvatar = null!;
	private Node3D _marker = null!;
	private Node3D _leftArm = null!;
	private Node3D _rightArm = null!;
	private Node3D _leftUpperLeg = null!;
	private Node3D _rightUpperLeg = null!;
	private Node3D _leftLowerLeg = null!;
	private Node3D _rightLowerLeg = null!;
	private Node3D _head = null!;
	private Node3D _phone = null!;
	private Camera3D _camera = null!;
	private Label _statusLabel = null!;
	private Shader? _stylizedShader;
	private Node3D? _canonicalAvatar;
	private Node3D? _canonicalPhone;
	private AnimationPlayer? _canonicalAnimationPlayer;
	private bool _usingCanonicalAsset;

	private AvatarActivity _activity = AvatarActivity.Idle;
	private AvatarLodLevel _lod = AvatarLodLevel.Street;
	private float _elapsed;
	private float _stateElapsed;
	private bool _autoCycle = true;

	public override void _Ready()
	{
		_stylizedShader = GD.Load<Shader>(StylizedShaderPath);
		BuildEnvironment();
		BuildStreet();
		BuildAvatar();
		LoadCanonicalAvatar();
		BuildInterface();
		ApplyCommandLinePreview();
		SetActivity(_activity);
		SetLod(_lod);
	}

	public override void _Process(double delta)
	{
		float step = (float)delta;
		_elapsed += step;
		_stateElapsed += step;
		if (_autoCycle && _stateElapsed >= StateDurationSeconds)
		{
			SetActivity(AvatarPresentationRules.NextActivity(_activity));
		}
		AnimateAvatar();
	}

	public void SetActivityCode(string code)
	{
		_autoCycle = false;
		SetActivity(AvatarPresentationRules.ParseActivity(code));
	}

	public void SetLodCode(string code)
	{
		_autoCycle = false;
		SetLod(code.Trim().ToLowerInvariant() switch
		{
			"cinematic" => AvatarLodLevel.Cinematic,
			"distance" => AvatarLodLevel.Distance,
			"marker" => AvatarLodLevel.Marker,
			_ => AvatarLodLevel.Street,
		});
	}

	private void BuildEnvironment()
	{
		var environment = new Godot.Environment
		{
			BackgroundMode = Godot.Environment.BGMode.Color,
			BackgroundColor = new Color("a9dff2"),
			AmbientLightSource = Godot.Environment.AmbientSource.Color,
			AmbientLightColor = new Color("cbeeff"),
			AmbientLightEnergy = 0.38f,
			TonemapMode = Godot.Environment.ToneMapper.Filmic,
			TonemapExposure = 0.82f,
		};
		AddChild(new WorldEnvironment { Environment = environment });

		var sunlight = new DirectionalLight3D
		{
			LightColor = new Color("fff0c2"),
			LightEnergy = 0.88f,
			ShadowEnabled = true,
			RotationDegrees = new Vector3(-52.0f, -32.0f, 0.0f),
		};
		AddChild(sunlight);

		_camera = new Camera3D
		{
			Projection = Camera3D.ProjectionType.Orthogonal,
			Current = true,
		};
		AddChild(_camera);
	}

	private void BuildStreet()
	{
		CreateBox(this, "Ground", new Vector3(32.0f, 0.12f, 24.0f), new Vector3(0.0f, -0.10f, 0.0f), new Color("83c98b"));
		CreateBox(this, "Road", new Vector3(32.0f, 0.08f, 5.2f), new Vector3(0.0f, -0.01f, 2.8f), new Color("344556"));
		CreateBox(this, "NearSidewalk", new Vector3(32.0f, 0.18f, 2.2f), new Vector3(0.0f, 0.02f, -0.9f), new Color("dbe8e6"));
		CreateBox(this, "FarSidewalk", new Vector3(32.0f, 0.18f, 1.8f), new Vector3(0.0f, 0.02f, 6.1f), new Color("dbe8e6"));

		for (int index = -6; index <= 6; index++)
		{
			CreateBox(
				this,
				$"RoadDash{index}",
				new Vector3(1.05f, 0.03f, 0.12f),
				new Vector3(index * 2.4f, 0.05f, 2.8f),
				new Color("eaf8f5")
			);
		}
		for (int index = 0; index < 6; index++)
		{
			CreateBox(
				this,
				$"Crosswalk{index}",
				new Vector3(0.42f, 0.03f, 3.6f),
				new Vector3(-5.8f + index * 0.72f, 0.05f, 2.8f),
				new Color("eef8f2")
			);
		}

		CreateBuilding("ApartmentA", new Vector3(-7.5f, 2.5f, -5.2f), new Vector3(4.0f, 5.0f, 3.8f), new Color("f2b28f"), new Color("ffe7a3"));
		CreateBuilding("ApartmentB", new Vector3(-2.4f, 3.3f, -5.8f), new Vector3(4.1f, 6.6f, 4.3f), new Color("89b9dd"), new Color("ffe7a3"));
		CreateBuilding("Market", new Vector3(3.0f, 1.7f, -5.0f), new Vector3(5.0f, 3.4f, 3.4f), new Color("f5d477"), new Color("c8fff3"));
		CreateBuilding("Office", new Vector3(8.0f, 3.8f, -6.0f), new Vector3(4.3f, 7.6f, 4.8f), new Color("7bc2c6"), new Color("d9ffff"));

		CreateBench(new Vector3(2.25f, 0.0f, -0.35f));
		CreateBusStop(new Vector3(-4.5f, 0.0f, 5.75f));
		CreateTree(new Vector3(-9.6f, 0.0f, -1.2f));
		CreateTree(new Vector3(6.8f, 0.0f, -1.3f));
		CreateTree(new Vector3(10.5f, 0.0f, 6.7f));
	}

	private void BuildAvatar()
	{
		_avatarRoot = new Node3D { Name = "AvatarRoot" };
		AddChild(_avatarRoot);

		_bodyRig = new Node3D { Name = "SkinnedProxy" };
		_avatarRoot.AddChild(_bodyRig);

		var skin = new Color("f2c3a7");
		var hair = new Color("33415c");
		var jacket = new Color("35a9b8");
		var shirt = new Color("fff0d4");
		var trousers = new Color("33415c");
		var shoes = new Color("f26b6f");

		CreateBox(_bodyRig, "Hips", new Vector3(0.62f, 0.25f, 0.34f), new Vector3(0.0f, 1.58f, 0.0f), trousers);
		CreateCapsule(_bodyRig, "Torso", 0.44f, 1.18f, new Vector3(0.0f, 2.28f, 0.0f), jacket, new Vector3(0.82f, 1.0f, 0.60f));
		CreateBox(_bodyRig, "ShirtPanel", new Vector3(0.25f, 0.58f, 0.055f), new Vector3(0.0f, 2.31f, 0.29f), shirt);

		_head = new Node3D { Name = "Head", Position = new Vector3(0.0f, 3.25f, 0.0f) };
		_bodyRig.AddChild(_head);
		CreateSphere(_head, "Face", 0.31f, Vector3.Zero, skin, new Vector3(0.90f, 1.08f, 0.86f));
		CreateSphere(_head, "HairCap", 0.34f, new Vector3(0.0f, 0.14f, -0.03f), hair, new Vector3(1.00f, 0.72f, 0.96f));
		CreateCapsule(_head, "FringeLeft", 0.065f, 0.34f, new Vector3(-0.12f, 0.01f, 0.27f), hair, new Vector3(0.76f, 1.0f, 0.62f), new Vector3(0.12f, 0.0f, -0.18f));
		CreateCapsule(_head, "FringeRight", 0.065f, 0.34f, new Vector3(0.12f, 0.01f, 0.27f), hair, new Vector3(0.76f, 1.0f, 0.62f), new Vector3(0.12f, 0.0f, 0.18f));
		CreateCapsule(_head, "HairLeft", 0.09f, 0.62f, new Vector3(-0.25f, -0.12f, -0.08f), hair, new Vector3(0.82f, 1.0f, 0.70f), new Vector3(0.0f, 0.0f, -0.18f));
		CreateCapsule(_head, "HairRight", 0.09f, 0.62f, new Vector3(0.25f, -0.12f, -0.08f), hair, new Vector3(0.82f, 1.0f, 0.70f), new Vector3(0.0f, 0.0f, 0.18f));

		_faceDetail = new Node3D { Name = "FaceDetail" };
		_head.AddChild(_faceDetail);
		CreateSphere(_faceDetail, "EyeLeft", 0.048f, new Vector3(-0.10f, 0.025f, 0.267f), new Color("203247"), new Vector3(0.72f, 1.18f, 0.42f));
		CreateSphere(_faceDetail, "EyeRight", 0.048f, new Vector3(0.10f, 0.025f, 0.267f), new Color("203247"), new Vector3(0.72f, 1.18f, 0.42f));
		CreateBox(_faceDetail, "Mouth", new Vector3(0.10f, 0.022f, 0.018f), new Vector3(0.0f, -0.115f, 0.282f), new Color("d85f6a"));

		_leftArm = CreateArm("LeftArm", -0.48f, skin, jacket);
		_rightArm = CreateArm("RightArm", 0.48f, skin, jacket);
		(_leftUpperLeg, _leftLowerLeg) = CreateLeg("LeftLeg", -0.20f, trousers, skin, shoes);
		(_rightUpperLeg, _rightLowerLeg) = CreateLeg("RightLeg", 0.20f, trousers, skin, shoes);

		_phone = CreateBox(_rightArm, "Phone", new Vector3(0.18f, 0.31f, 0.055f), new Vector3(0.0f, -0.87f, 0.12f), new Color("202b3d"));
		_phone.Visible = false;

		_distanceAvatar = new Node3D { Name = "DistanceAvatar" };
		_avatarRoot.AddChild(_distanceAvatar);
		CreateCapsule(_distanceAvatar, "Body", 0.29f, 1.86f, new Vector3(0.0f, 1.65f, 0.0f), jacket, new Vector3(0.78f, 1.0f, 0.60f));
		CreateSphere(_distanceAvatar, "Head", 0.23f, new Vector3(0.0f, 2.86f, 0.0f), skin);
		CreateSphere(_distanceAvatar, "Hair", 0.25f, new Vector3(0.0f, 2.92f, -0.02f), hair, new Vector3(1.0f, 0.72f, 0.94f));

		_marker = new Node3D { Name = "PlayerMarker" };
		_avatarRoot.AddChild(_marker);
		var markerMaterial = new StandardMaterial3D
		{
			AlbedoColor = new Color("39c2d0"),
			EmissionEnabled = true,
			Emission = new Color("39c2d0"),
			EmissionEnergyMultiplier = 2.2f,
			Roughness = 0.25f,
		};
		var markerMesh = new MeshInstance3D
		{
			Name = "MarkerPin",
			Mesh = new CylinderMesh { TopRadius = 0.22f, BottomRadius = 0.38f, Height = 1.0f },
			MaterialOverride = markerMaterial,
			Position = new Vector3(0.0f, 0.70f, 0.0f),
		};
		_marker.AddChild(markerMesh);
	}

	private Node3D CreateArm(string name, float x, Color skin, Color sleeve)
	{
		var pivot = new Node3D { Name = name, Position = new Vector3(x, 2.63f, 0.0f) };
		_bodyRig.AddChild(pivot);
		CreateCapsule(pivot, "Sleeve", 0.12f, 0.48f, new Vector3(0.0f, -0.22f, 0.0f), sleeve, new Vector3(0.86f, 1.0f, 0.86f));
		CreateCapsule(pivot, "Forearm", 0.09f, 0.56f, new Vector3(0.0f, -0.68f, 0.0f), skin, new Vector3(0.86f, 1.0f, 0.86f));
		CreateSphere(pivot, "Hand", 0.105f, new Vector3(0.0f, -0.99f, 0.0f), skin, new Vector3(0.82f, 1.0f, 0.72f));
		return pivot;
	}

	private (Node3D Upper, Node3D Lower) CreateLeg(string name, float x, Color trousers, Color skin, Color shoes)
	{
		var upper = new Node3D { Name = name, Position = new Vector3(x, 1.66f, 0.0f) };
		_bodyRig.AddChild(upper);
		CreateCapsule(upper, "Upper", 0.15f, 0.82f, new Vector3(0.0f, -0.39f, 0.0f), trousers, new Vector3(0.90f, 1.0f, 0.82f));

		var lower = new Node3D { Name = "Lower", Position = new Vector3(0.0f, -0.78f, 0.0f) };
		upper.AddChild(lower);
		CreateCapsule(lower, "Calf", 0.115f, 0.76f, new Vector3(0.0f, -0.36f, 0.0f), skin, new Vector3(0.88f, 1.0f, 0.82f));
		CreateBox(lower, "Shoe", new Vector3(0.28f, 0.16f, 0.46f), new Vector3(0.0f, -0.78f, 0.12f), shoes);
		return (upper, lower);
	}

	private void BuildInterface()
	{
		var canvas = new CanvasLayer { Name = "LabUi" };
		AddChild(canvas);

		var panel = new PanelContainer
		{
			Position = new Vector2(22.0f, 22.0f),
			CustomMinimumSize = new Vector2(500.0f, 0.0f),
		};
		panel.AddThemeStyleboxOverride("panel", new StyleBoxFlat
		{
			BgColor = new Color(0.05f, 0.09f, 0.15f, 0.90f),
			BorderColor = new Color("48c3cf"),
			BorderWidthLeft = 1,
			BorderWidthTop = 1,
			BorderWidthRight = 1,
			BorderWidthBottom = 1,
			CornerRadiusTopLeft = 6,
			CornerRadiusTopRight = 6,
			CornerRadiusBottomLeft = 6,
			CornerRadiusBottomRight = 6,
		});
		canvas.AddChild(panel);

		var margin = new MarginContainer();
		margin.AddThemeConstantOverride("margin_left", 16);
		margin.AddThemeConstantOverride("margin_top", 12);
		margin.AddThemeConstantOverride("margin_right", 16);
		margin.AddThemeConstantOverride("margin_bottom", 12);
		panel.AddChild(margin);

		var layout = new VBoxContainer();
		layout.AddThemeConstantOverride("separation", 8);
		margin.AddChild(layout);

		var title = new Label { Text = "AVATAR LAB" };
		title.AddThemeFontSizeOverride("font_size", 19);
		title.AddThemeColorOverride("font_color", new Color("f5fbff"));
		layout.AddChild(title);

		_statusLabel = new Label();
		_statusLabel.AddThemeColorOverride("font_color", new Color("9de7ec"));
		layout.AddChild(_statusLabel);

		var activityRow = new HBoxContainer();
		activityRow.AddThemeConstantOverride("separation", 6);
		layout.AddChild(activityRow);
		foreach (AvatarActivity activity in AvatarPresentationRules.ActivitySequence)
		{
			var button = CreateModeButton(AvatarPresentationRules.ActivityCode(activity).ToUpperInvariant());
			button.Pressed += () =>
			{
				_autoCycle = false;
				SetActivity(activity);
			};
			_activityButtons[activity] = button;
			activityRow.AddChild(button);
		}

		var lodRow = new HBoxContainer();
		lodRow.AddThemeConstantOverride("separation", 6);
		layout.AddChild(lodRow);
		foreach (AvatarLodLevel lod in Enum.GetValues<AvatarLodLevel>())
		{
			var button = CreateModeButton(lod.ToString().ToUpperInvariant());
			button.Pressed += () => SetLod(lod);
			_lodButtons[lod] = button;
			lodRow.AddChild(button);
		}
	}

	private static Button CreateModeButton(string text)
	{
		var button = new Button
		{
			Text = text,
			ToggleMode = true,
			CustomMinimumSize = new Vector2(78.0f, 34.0f),
			FocusMode = Control.FocusModeEnum.None,
		};
		return button;
	}

	private void SetActivity(AvatarActivity activity)
	{
		_activity = activity;
		_stateElapsed = 0.0f;
		if (_canonicalPhone != null)
		{
			_canonicalPhone.Visible = activity == AvatarActivity.Phone;
		}
		PlayCanonicalAnimation(activity);
		foreach (var pair in _activityButtons)
		{
			pair.Value.ButtonPressed = pair.Key == activity;
		}
		UpdateStatus();
	}

	private void SetLod(AvatarLodLevel lod)
	{
		_lod = lod;
		bool usesFullAvatar = AvatarPresentationRules.UsesSkinnedAvatar(lod);
		_bodyRig.Visible = usesFullAvatar && !_usingCanonicalAsset;
		if (_canonicalAvatar != null)
		{
			_canonicalAvatar.Visible = usesFullAvatar;
		}
		_faceDetail.Visible = lod is AvatarLodLevel.Cinematic or AvatarLodLevel.Street;
		_distanceAvatar.Visible = lod == AvatarLodLevel.Distance;
		_marker.Visible = lod == AvatarLodLevel.Marker;

		foreach (var pair in _lodButtons)
		{
			pair.Value.ButtonPressed = pair.Key == lod;
		}

		Vector3 position;
		Vector3 target;
		switch (lod)
		{
			case AvatarLodLevel.Cinematic:
				position = new Vector3(4.7f, 3.65f, 6.2f);
				target = new Vector3(0.0f, 2.1f, 0.0f);
				_camera.Size = 4.4f;
				break;
			case AvatarLodLevel.Distance:
				position = new Vector3(14.0f, 11.5f, 15.0f);
				target = new Vector3(0.0f, 1.4f, 0.8f);
				_camera.Size = 15.0f;
				break;
			case AvatarLodLevel.Marker:
				position = new Vector3(24.0f, 21.0f, 26.0f);
				target = new Vector3(0.0f, 0.0f, 1.0f);
				_camera.Size = 27.0f;
				break;
			default:
				position = new Vector3(7.0f, 5.6f, 8.2f);
				target = new Vector3(0.0f, 1.7f, 0.8f);
				_camera.Size = 7.5f;
				break;
		}
		_camera.Position = position;
		_camera.LookAt(target, Vector3.Up);
		UpdateStatus();
	}

	private void AnimateAvatar()
	{
		float wave = Mathf.Sin(_elapsed * 2.2f);
		float quickWave = Mathf.Sin(_elapsed * 7.0f);
		_avatarRoot.Position = Vector3.Zero;
		_avatarRoot.Rotation = Vector3.Zero;
		_bodyRig.Position = Vector3.Zero;
		_bodyRig.Rotation = Vector3.Zero;
		_head.Rotation = Vector3.Zero;
		_leftArm.Rotation = Vector3.Zero;
		_rightArm.Rotation = Vector3.Zero;
		_leftUpperLeg.Rotation = Vector3.Zero;
		_rightUpperLeg.Rotation = Vector3.Zero;
		_leftLowerLeg.Rotation = Vector3.Zero;
		_rightLowerLeg.Rotation = Vector3.Zero;
		_phone.Visible = false;

		switch (_activity)
		{
			case AvatarActivity.Walk:
				float stride = Mathf.Sin(_elapsed * 5.6f);
				_avatarRoot.Position = new Vector3(Mathf.Sin(_elapsed * 0.65f) * 1.2f, Mathf.Abs(stride) * 0.035f, 0.0f);
				_leftArm.Rotation = new Vector3(stride * 0.55f, 0.0f, 0.04f);
				_rightArm.Rotation = new Vector3(-stride * 0.55f, 0.0f, -0.04f);
				_leftUpperLeg.Rotation = new Vector3(-stride * 0.58f, 0.0f, 0.0f);
				_rightUpperLeg.Rotation = new Vector3(stride * 0.58f, 0.0f, 0.0f);
				_leftLowerLeg.Rotation = new Vector3(Mathf.Max(0.0f, stride) * 0.55f, 0.0f, 0.0f);
				_rightLowerLeg.Rotation = new Vector3(Mathf.Max(0.0f, -stride) * 0.55f, 0.0f, 0.0f);
				break;
			case AvatarActivity.Sit:
				float seatOffset = _usingCanonicalAsset ? -0.30f : -0.58f;
				_avatarRoot.Position = new Vector3(2.25f, seatOffset, -0.32f);
				_leftUpperLeg.Rotation = new Vector3(-1.22f, 0.0f, -0.04f);
				_rightUpperLeg.Rotation = new Vector3(-1.22f, 0.0f, 0.04f);
				_leftLowerLeg.Rotation = new Vector3(1.20f, 0.0f, 0.0f);
				_rightLowerLeg.Rotation = new Vector3(1.20f, 0.0f, 0.0f);
				_leftArm.Rotation = new Vector3(-0.18f, 0.0f, 0.10f);
				_rightArm.Rotation = new Vector3(-0.18f, 0.0f, -0.10f);
				_head.Rotation = new Vector3(0.04f, wave * 0.04f, 0.0f);
				break;
			case AvatarActivity.Phone:
				_bodyRig.Position = new Vector3(0.0f, Mathf.Abs(quickWave) * 0.018f, 0.0f);
				_rightArm.Rotation = new Vector3(-1.85f, 0.0f, -0.18f);
				_leftArm.Rotation = new Vector3(0.05f, 0.0f, 0.08f);
				_head.Rotation = new Vector3(0.10f, 0.10f, -0.03f);
				_phone.Visible = true;
				break;
			case AvatarActivity.Talk:
				_bodyRig.Position = new Vector3(0.0f, wave * 0.018f, 0.0f);
				_leftArm.Rotation = new Vector3(-0.35f + wave * 0.18f, 0.0f, 0.30f);
				_rightArm.Rotation = new Vector3(-0.52f - wave * 0.20f, 0.0f, -0.38f);
				_head.Rotation = new Vector3(0.0f, wave * 0.08f, -wave * 0.025f);
				break;
			default:
				_bodyRig.Position = new Vector3(0.0f, wave * 0.018f, 0.0f);
				_leftArm.Rotation = new Vector3(0.03f, 0.0f, 0.05f + wave * 0.025f);
				_rightArm.Rotation = new Vector3(-0.03f, 0.0f, -0.05f - wave * 0.025f);
				_head.Rotation = new Vector3(0.0f, wave * 0.025f, 0.0f);
				break;
		}

		_distanceAvatar.Position = Vector3.Zero;
		_marker.Position = Vector3.Zero;
	}

	private void UpdateStatus()
	{
		if (_statusLabel != null)
		{
			string source = _usingCanonicalAsset ? "GLB" : "PROXY";
			_statusLabel.Text =
				$"{AvatarPresentationRules.ActivityCode(_activity).ToUpperInvariant()}  /  {_lod.ToString().ToUpperInvariant()} LOD  /  {source}";
		}
	}

	private void LoadCanonicalAvatar()
	{
		var packedScene = GD.Load<PackedScene>(CanonicalAvatarPath);
		if (packedScene == null)
		{
			GD.PushWarning($"Canonical avatar unavailable: {CanonicalAvatarPath}");
			return;
		}

		_canonicalAvatar = packedScene.Instantiate<Node3D>();
		_canonicalAvatar.Name = "CanonicalAnimeAvatar";
		_canonicalAvatar.Scale = Vector3.One * 1.45f;
		_avatarRoot.AddChild(_canonicalAvatar);
		_canonicalAnimationPlayer = FindDescendant<AnimationPlayer>(_canonicalAvatar);
		var skeleton = FindDescendant<Skeleton3D>(_canonicalAvatar);
		_usingCanonicalAsset = skeleton != null;
		if (!_usingCanonicalAsset)
		{
			GD.PushWarning("Canonical avatar GLB imported without Skeleton3D; using procedural proxy.");
			_canonicalAvatar.QueueFree();
			_canonicalAvatar = null;
			_canonicalAnimationPlayer = null;
			return;
		}

		AttachCanonicalPhone(skeleton!);
		string animations = "(none)";
		if (_canonicalAnimationPlayer != null)
		{
			var summaries = new List<string>();
			foreach (StringName animationName in _canonicalAnimationPlayer.GetAnimationList())
			{
				var animation = _canonicalAnimationPlayer.GetAnimation(animationName);
				summaries.Add(
					$"{animationName}(tracks={animation?.GetTrackCount() ?? 0},length={animation?.Length ?? 0.0:0.00})"
				);
			}
			animations = string.Join(", ", summaries);
		}
		GD.Print(
			$"Canonical avatar loaded: bones={skeleton!.GetBoneCount()}, animations=[{animations}]"
		);
	}

	private void AttachCanonicalPhone(Skeleton3D skeleton)
	{
		var attachment = new BoneAttachment3D
		{
			Name = "PhoneAttachment",
			BoneName = "RightHand",
		};
		skeleton.AddChild(attachment);

		var phoneMaterial = new StandardMaterial3D
		{
			AlbedoColor = new Color("182235"),
			Metallic = 0.18f,
			Roughness = 0.36f,
		};
		var phone = new MeshInstance3D
		{
			Name = "Phone",
			Mesh = new BoxMesh { Size = new Vector3(0.10f, 0.22f, 0.03f) },
			MaterialOverride = phoneMaterial,
			Position = new Vector3(0.0f, 0.09f, 0.045f),
			RotationDegrees = new Vector3(0.0f, 0.0f, 12.0f),
			Visible = false,
		};
		attachment.AddChild(phone);
		_canonicalPhone = phone;
	}

	private void PlayCanonicalAnimation(AvatarActivity activity)
	{
		if (_canonicalAnimationPlayer == null)
		{
			return;
		}

		string code = AvatarPresentationRules.ActivityCode(activity);
		StringName? resolved = null;
		foreach (StringName animationName in _canonicalAnimationPlayer.GetAnimationList())
		{
			string candidate = animationName.ToString();
			if (candidate.Equals(code, StringComparison.OrdinalIgnoreCase)
				|| candidate.EndsWith($"|{code}", StringComparison.OrdinalIgnoreCase)
				|| candidate.EndsWith($"/{code}", StringComparison.OrdinalIgnoreCase))
			{
				resolved = animationName;
				break;
			}
		}
		if (resolved == null)
		{
			GD.PushWarning($"Canonical avatar animation unavailable: {code}");
			return;
		}

		var animation = _canonicalAnimationPlayer.GetAnimation(resolved);
		if (animation != null)
		{
			animation.LoopMode = Animation.LoopModeEnum.Linear;
		}
		_canonicalAnimationPlayer.Play(resolved, 0.18);
		GD.Print($"Canonical avatar animation playing: {resolved}");
	}

	private static T? FindDescendant<T>(Node root) where T : Node
	{
		if (root is T match)
		{
			return match;
		}
		foreach (Node child in root.GetChildren())
		{
			var descendant = FindDescendant<T>(child);
			if (descendant != null)
			{
				return descendant;
			}
		}
		return null;
	}

	private void ApplyCommandLinePreview()
	{
		foreach (string argument in OS.GetCmdlineUserArgs())
		{
			if (argument.StartsWith("--activity=", StringComparison.Ordinal))
			{
				SetActivityCode(argument["--activity=".Length..]);
			}
			else if (argument.StartsWith("--lod=", StringComparison.Ordinal))
			{
				SetLodCode(argument["--lod=".Length..]);
			}
		}
	}

	private void CreateBuilding(string name, Vector3 position, Vector3 size, Color wallColor, Color windowColor)
	{
		CreateBox(this, name, size, position, wallColor);
		int columns = Math.Max(2, Mathf.FloorToInt(size.X / 1.05f));
		int rows = Math.Max(2, Mathf.FloorToInt(size.Y / 1.25f));
		for (int row = 0; row < rows; row++)
		{
			for (int column = 0; column < columns; column++)
			{
				float x = position.X - size.X * 0.5f + 0.62f + column * ((size.X - 1.1f) / Math.Max(1, columns - 1));
				float y = 0.65f + row * ((size.Y - 1.2f) / Math.Max(1, rows - 1));
				CreateBox(this, $"{name}Window{row}_{column}", new Vector3(0.42f, 0.48f, 0.05f), new Vector3(x, y, position.Z + size.Z * 0.5f + 0.03f), windowColor);
			}
		}
	}

	private void CreateBench(Vector3 position)
	{
		CreateBox(this, "BenchSeat", new Vector3(2.1f, 0.18f, 0.60f), position + new Vector3(0.0f, 1.05f, 0.0f), new Color("e49b62"));
		CreateBox(this, "BenchBack", new Vector3(2.1f, 0.75f, 0.16f), position + new Vector3(0.0f, 1.42f, -0.28f), new Color("d98654"));
		CreateBox(this, "BenchLegLeft", new Vector3(0.16f, 1.0f, 0.16f), position + new Vector3(-0.72f, 0.50f, 0.0f), new Color("405366"));
		CreateBox(this, "BenchLegRight", new Vector3(0.16f, 1.0f, 0.16f), position + new Vector3(0.72f, 0.50f, 0.0f), new Color("405366"));
	}

	private void CreateBusStop(Vector3 position)
	{
		CreateBox(this, "BusStopRoof", new Vector3(3.4f, 0.16f, 1.6f), position + new Vector3(0.0f, 2.5f, 0.0f), new Color("44b5c4"));
		CreateBox(this, "BusStopPostLeft", new Vector3(0.14f, 2.5f, 0.14f), position + new Vector3(-1.45f, 1.25f, 0.0f), new Color("405366"));
		CreateBox(this, "BusStopPostRight", new Vector3(0.14f, 2.5f, 0.14f), position + new Vector3(1.45f, 1.25f, 0.0f), new Color("405366"));
		CreateBox(this, "BusStopBench", new Vector3(2.2f, 0.16f, 0.52f), position + new Vector3(0.0f, 0.72f, 0.0f), new Color("f2b66d"));
	}

	private void CreateTree(Vector3 position)
	{
		CreateCapsule(this, "TreeTrunk", 0.16f, 1.8f, position + new Vector3(0.0f, 0.9f, 0.0f), new Color("8d6c4e"));
		CreateSphere(this, "TreeCrownA", 0.92f, position + new Vector3(0.0f, 2.15f, 0.0f), new Color("52b77b"), new Vector3(1.0f, 0.85f, 1.0f));
		CreateSphere(this, "TreeCrownB", 0.62f, position + new Vector3(0.55f, 2.35f, 0.05f), new Color("6bc98b"));
	}

	private Node3D CreateBox(Node parent, string name, Vector3 size, Vector3 position, Color color)
	{
		var mesh = new MeshInstance3D
		{
			Name = name,
			Mesh = new BoxMesh { Size = size },
			MaterialOverride = CreateMaterial(color),
			Position = position,
		};
		parent.AddChild(mesh);
		return mesh;
	}

	private Node3D CreateCapsule(
		Node parent,
		string name,
		float radius,
		float height,
		Vector3 position,
		Color color,
		Vector3? scale = null,
		Vector3? rotation = null
	)
	{
		var mesh = new MeshInstance3D
		{
			Name = name,
			Mesh = new CapsuleMesh { Radius = radius, Height = height, RadialSegments = 16, Rings = 6 },
			MaterialOverride = CreateMaterial(color),
			Position = position,
			Scale = scale ?? Vector3.One,
			Rotation = rotation ?? Vector3.Zero,
		};
		parent.AddChild(mesh);
		return mesh;
	}

	private Node3D CreateSphere(Node parent, string name, float radius, Vector3 position, Color color, Vector3? scale = null)
	{
		var mesh = new MeshInstance3D
		{
			Name = name,
			Mesh = new SphereMesh { Radius = radius, Height = radius * 2.0f, RadialSegments = 20, Rings = 10 },
			MaterialOverride = CreateMaterial(color),
			Position = position,
			Scale = scale ?? Vector3.One,
		};
		parent.AddChild(mesh);
		return mesh;
	}

	private Material CreateMaterial(Color color)
	{
		if (_stylizedShader == null)
		{
			return new StandardMaterial3D { AlbedoColor = color, Roughness = 0.76f };
		}
		var material = new ShaderMaterial { Shader = _stylizedShader };
		material.SetShaderParameter("base_color", color);
		material.SetShaderParameter("shadow_tint", color.Darkened(0.48f));
		return material;
	}
}
