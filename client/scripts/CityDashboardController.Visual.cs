using Godot;

public partial class CityDashboardController
{
    public void OnVisualFocusButtonPressed()
    {
        if (_cityVisualOverlay == null)
        {
            return;
        }

        string nextText = _cityVisualOverlay.ToggleFocusMode();
        if (_visualFocusButton != null)
        {
            _visualFocusButton.Text = nextText;
        }
        ApplyCityFocusLayout();
        UpdateActiveAvatarPresentation();
    }

    private void ApplyCityFocusLayout()
    {
        bool streetFocus = _cityVisualOverlay?.IsStreetFocus ?? false;
        if (_leftRail != null)
        {
            _leftRail.Visible = !streetFocus;
        }
        if (_centerScroll != null)
        {
            _centerScroll.SizeFlagsHorizontal = Control.SizeFlags.ExpandFill;
            _centerScroll.SizeFlagsStretchRatio = streetFocus ? 4.6f : 2.4f;
        }
        if (_actionRail != null)
        {
            _actionRail.CustomMinimumSize = streetFocus
                ? new Vector2(180, 0)
                : new Vector2(240, 0);
            _actionRail.SizeFlagsStretchRatio = streetFocus ? 0.8f : 1.0f;
        }
        if (_cityVisualPanel != null)
        {
            _cityVisualPanel.CustomMinimumSize = streetFocus
                ? new Vector2(0, 500)
                : new Vector2(0, 360);
        }
        if (_cityCaptionLabel != null)
        {
            _cityCaptionLabel.Visible = !streetFocus;
        }
        if (_buildingPortfolioPanel != null)
        {
            _buildingPortfolioPanel.Visible = !streetFocus;
        }
        if (_buildFlowPanel != null)
        {
            _buildFlowPanel.Visible = !streetFocus;
        }
        if (_goalPanel != null)
        {
            _goalPanel.CustomMinimumSize = streetFocus
                ? new Vector2(0, 66)
                : new Vector2(0, 0);
        }
        if (_eventPanel != null)
        {
            _eventPanel.CustomMinimumSize = streetFocus
                ? new Vector2(0, 60)
                : new Vector2(0, 0);
        }
    }

    private void UpdateActiveAvatarPresentation()
    {
        bool hasIdentity = _activeAvatar.HasPlayerIdentity;
        if (_playerAvatarProfile != null)
        {
            _playerAvatarProfile.Visible = hasIdentity;
        }
        SetViewportActive(_playerAvatarViewport, hasIdentity);
        _playerAvatarPreview?.SetPreviewActive(hasIdentity);
        if (_playerAvatarIdentityLabel != null)
        {
            _playerAvatarIdentityLabel.Text =
                $"{Tr("PLAYER_AVATAR_FACE")} {_activeAvatar.FaceNumber:00} | " +
                $"{Tr("PLAYER_AVATAR_FASHION")} {_activeAvatar.Profile.FashionScore}";
        }
        if (_streetAvatarNameLabel != null)
        {
            _streetAvatarNameLabel.Text = _activeAvatar.Username;
        }
        if (hasIdentity)
        {
            _playerAvatarPreview?.SetProfile(_activeAvatar.Profile);
            _streetAvatarPreview?.SetProfile(_activeAvatar.Profile);
            _streetAvatarPreview?.SetActivity(_activeAvatar.Activity.Activity);
        }
        if (_streetAvatarContainer != null)
        {
            bool showStreetAvatar = _activeAvatar.ShowsFullAvatar(
                _cityVisualOverlay?.IsStreetFocus ?? false
            );
            _streetAvatarContainer.Visible = showStreetAvatar;
            SetViewportActive(_streetAvatarViewport, showStreetAvatar);
            _streetAvatarPreview?.SetPreviewActive(showStreetAvatar);
        }
    }

    private static void SetViewportActive(SubViewport viewport, bool active)
    {
        if (viewport != null)
        {
            viewport.RenderTargetUpdateMode = active
                ? SubViewport.UpdateMode.Always
                : SubViewport.UpdateMode.Disabled;
        }
    }
}
