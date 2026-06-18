using Godot;
using System;
using System.Text.Json.Nodes;

public partial class CityDashboardController
{
	private void UpdateOnboardingUi()
	{
		if (_onboardingOverlay == null)
		{
			return;
		}

		_onboardingOverlay.Visible = !_onboardingState.Completed;
		if (_onboardingState.Completed)
		{
			_arrivalStoryInitialized = false;
			_arrivalStoryBeat = 0;
			return;
		}

		bool showingStory = _onboardingState.Stage == "arrival_choice"
			&& _arrivalStoryInitialized
			&& _arrivalStoryBeat < DashboardArrivalStory.Count;
		if (_onboardingState.Stage == "arrival_choice" && !_arrivalStoryInitialized)
		{
			_arrivalStoryInitialized = true;
			_arrivalStoryBeat = 0;
			showingStory = true;
		}

		var storyBeat = showingStory ? DashboardArrivalStory.Get(_arrivalStoryBeat, _tutorialAgeGroup) : null;
		UpdateOnboardingBackdrop(storyBeat?.Visual ?? DashboardArrivalVisual.BaggageTheft);
		UpdateOnboardingPortrait(
			storyBeat?.Portrait ?? DashboardArrivalPortrait.None,
			storyBeat?.PortraitSide ?? DashboardPortraitSide.Right);
		if (_onboardingTitleLabel != null)
		{
			_onboardingTitleLabel.Text = storyBeat == null
				? TranslateOrFallback(_onboardingState.TitleKey, _onboardingState.Title)
				: Tr(storyBeat.TitleKey);
		}
		if (_onboardingNarrativeLabel != null)
		{
			_onboardingNarrativeLabel.Text = storyBeat == null
				? TranslateOrFallback(_onboardingState.NarrativeKey, _onboardingState.Narrative)
				: Tr(storyBeat.NarrativeKey);
		}
		if (_onboardingPoliceStatusLabel != null)
		{
			string policeStatusText = TranslateOrFallback(_onboardingState.PoliceStatusKey, "");
			_onboardingPoliceStatusLabel.Text = policeStatusText;
			_onboardingPoliceStatusLabel.Visible = !string.IsNullOrWhiteSpace(policeStatusText);
		}
		if (_onboardingPoliceButton != null)
		{
			_onboardingPoliceButton.Visible = !showingStory && _onboardingState.CanReportToPolice;
			_onboardingPoliceButton.Disabled = _pendingOnboarding;
			_onboardingPoliceButton.Text = Tr(
				_pendingOnboarding ? "ONBOARDING_POLICE_PENDING_BUTTON" : "ONBOARDING_POLICE_BUTTON");
		}
		if (_onboardingHousingButton != null)
		{
			_onboardingHousingButton.Visible = !showingStory && _onboardingState.CanFindHousing;
			_onboardingHousingButton.Disabled = _pendingOnboarding;
			_onboardingHousingButton.Text = Tr(
				_pendingOnboarding ? "ONBOARDING_HOUSING_PENDING_BUTTON" : "ONBOARDING_HOUSING_BUTTON");
		}
		if (_onboardingContinueButton != null)
		{
			_onboardingContinueButton.Visible = showingStory;
			_onboardingContinueButton.Disabled = _pendingOnboarding;
			_onboardingContinueButton.Text = _arrivalStoryBeat + 1 < DashboardArrivalStory.Count
				? Tr("ARRIVAL_STORY_NEXT")
				: Tr("ARRIVAL_STORY_ARRIVE");
		}
	}

	private void UpdateOnboardingBackdrop(DashboardArrivalVisual visual)
	{
		if (_onboardingBackdrop == null)
		{
			return;
		}

		string assetPath = DashboardVisualStylePacks.ResolveArrivalAsset(_session?.VisualStyleCode, visual);
		if (assetPath == _onboardingBackdropPath)
		{
			return;
		}

		var texture = ResourceLoader.Load<Texture2D>(assetPath);
		if (texture == null)
		{
			GD.PushError($"Не вдалося завантажити arrival asset: {assetPath}");
			return;
		}

		_onboardingBackdrop.Texture = texture;
		_onboardingBackdropPath = assetPath;
	}

	private void UpdateOnboardingPortrait(DashboardArrivalPortrait portrait, DashboardPortraitSide side)
	{
		if (_onboardingPortrait == null)
		{
			return;
		}

		if (portrait == DashboardArrivalPortrait.None)
		{
			_onboardingPortrait.Visible = false;
			return;
		}

		const float width = 260.0f;
		const float height = 325.0f;
		const float margin = 32.0f;
		const float top = 230.0f;
		float viewportWidth = GetViewportRect().Size.X;
		float left = side == DashboardPortraitSide.Left
			? margin
			: Math.Max(margin, viewportWidth - margin - width);
		_onboardingPortrait.Position = new Vector2(left, top);
		_onboardingPortrait.Size = new Vector2(width, height);
		_onboardingPortrait.Visible = true;

		string assetPath = DashboardVisualStylePacks.ResolveArrivalPortrait(_session?.VisualStyleCode, portrait);
		if (assetPath == _onboardingPortraitPath)
		{
			return;
		}

		var texture = ResourceLoader.Load<Texture2D>(assetPath);
		if (texture == null)
		{
			_onboardingPortrait.Visible = false;
			GD.PushError($"Не вдалося завантажити arrival portrait: {assetPath}");
			return;
		}

		_onboardingPortrait.Texture = texture;
		_onboardingPortraitPath = assetPath;
	}

	private void SubmitOnboardingChoice(string choice)
	{
		if (_pendingOnboarding || _session == null || !_session.HasAuthenticatedPlayer)
		{
			return;
		}

		_pendingOnboarding = true;
		UpdateOnboardingUi();
		ClearErrorState();
		string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId, choice });
		_apiClient?.PostAuthorizedIdempotent(
			"/api/player/onboarding/choose",
			_session.AuthToken,
			BuildActionKey($"onboarding-{choice}"),
			payload);
	}

	public void OnOnboardingPoliceButtonPressed()
	{
		SubmitOnboardingChoice(DashboardOnboardingState.ReportToPoliceChoice);
	}

	public void OnOnboardingHousingButtonPressed()
	{
		SubmitOnboardingChoice(DashboardOnboardingState.FindHousingChoice);
	}

	public void OnOnboardingContinueButtonPressed()
	{
		if (
			_pendingOnboarding
			|| _onboardingState.Stage != "arrival_choice"
			|| _arrivalStoryBeat >= DashboardArrivalStory.Count)
		{
			return;
		}

		_arrivalStoryBeat += 1;
		UpdateOnboardingUi();
	}

	private void UpdatePoliceRecoveryButton()
	{
		if (_policeRecoveryButton == null)
		{
			return;
		}

		bool pending = !string.IsNullOrEmpty(_pendingPoliceRecoveryKey);
		_policeRecoveryButton.Visible = _onboardingState.PoliceRecoveryClaimable || pending;
		_policeRecoveryButton.Disabled = pending;
		_policeRecoveryButton.Text = pending
			? Tr("POLICE_RECOVERY_PENDING")
			: Tr("POLICE_RECOVERY_CLAIM").Replace(
				"{amount}",
				$"{_onboardingState.PoliceRecoveryAmount:N0}");
		_policeRecoveryButton.TooltipText = pending
			? Tr("POLICE_RECOVERY_PENDING_TOOLTIP")
			: Tr("POLICE_RECOVERY_CLAIM_TOOLTIP");
	}

	private string TranslateOrFallback(string key, string fallback)
	{
		if (string.IsNullOrWhiteSpace(key))
		{
			return fallback;
		}

		string translated = Tr(key);
		return translated == key ? fallback : translated;
	}

	public void OnPoliceRecoveryButtonPressed()
	{
		if (
			!_onboardingState.PoliceRecoveryClaimable
			|| !string.IsNullOrEmpty(_pendingPoliceRecoveryKey)
			|| _session == null
			|| !_session.HasAuthenticatedPlayer)
		{
			return;
		}

		_pendingPoliceRecoveryKey = BuildActionKey("police-recovery");
		UpdatePoliceRecoveryButton();
		ClearErrorState();
		string payload = ApiClient.BuildJson(new { player_id = _session.PlayerId });
		_apiClient?.PostAuthorizedIdempotent(
			"/api/player/onboarding/police-recovery",
			_session.AuthToken,
			_pendingPoliceRecoveryKey,
			payload);
	}
}
