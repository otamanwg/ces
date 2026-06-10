using Godot;
using System;
using System.Text.Json.Nodes;
using System.Threading.Tasks;

public partial class CityDashboardController
{
    // Note: Avatar component fields are declared in main CityDashboardController.cs

    private void InitializeAvatarComponents()
    {
        // Player avatar profile
        _playerAvatarProfile = GetNode<Control>("MainContainer/PlayerRail/PlayerAvatarProfile");
        _playerAvatarPreview = GetNode<CharacterAvatarPreview>("MainContainer/PlayerRail/PlayerAvatarProfile/AvatarPreview");
        _playerAvatarViewport = GetNode<SubViewport>("MainContainer/PlayerRail/PlayerAvatarProfile/AvatarViewport");
        _playerAvatarIdentityLabel = GetNode<Label>("MainContainer/PlayerRail/PlayerAvatarProfile/IdentityLabel");

        // Street avatar (for street focus mode)
        _streetAvatarContainer = GetNode<Control>("MainContainer/VisualPanel/StreetAvatarContainer");
        _streetAvatarPreview = GetNode<CharacterAvatarPreview>("MainContainer/VisualPanel/StreetAvatarContainer/AvatarPreview");
        _streetAvatarViewport = GetNode<SubViewport>("MainContainer/VisualPanel/StreetAvatarContainer/AvatarViewport");
        _streetAvatarNameLabel = GetNode<Label>("MainContainer/VisualPanel/StreetAvatarContainer/NameLabel");

        // Character creation viewport (shared)
        _characterAvatarViewport = GetNode<SubViewport>("MainContainer/CharacterCreationOverlay/CharacterAvatarViewport");
    }

    private void UpdateAvatarDisplay(JsonNode playerData)
    {
        var avatar = playerData?["avatar_profile"];
        if (avatar == null) return;

        var username = playerData?["username"]?.GetValue<string>() ?? "Гравець";
        var bodyCode = avatar?["body_code"]?.GetValue<string>() ?? "body_01";
        var faceCode = avatar?["face_code"]?.GetValue<string>() ?? "face_01";
        var skinCode = avatar?["skin_code"]?.GetValue<string>() ?? "skin_01";
        var hairCode = avatar?["hair_code"]?.GetValue<string>() ?? "hair_01";
        var hairColorCode = avatar?["hair_color_code"]?.GetValue<string>() ?? "black";

        // Update player avatar profile
        if (_playerAvatarPreview != null)
        {
            _playerAvatarPreview.UpdateAvatarAppearance(bodyCode, faceCode, skinCode, hairCode, hairColorCode);
            _playerAvatarIdentityLabel.Text = username;
        }

        // Update street avatar based on focus mode
        UpdateStreetAvatar(username, bodyCode, faceCode, skinCode, hairCode, hairColorCode);
    }

    private void UpdateStreetAvatar(string username, string bodyCode, string faceCode, string skinCode, string hairCode, string hairColorCode)
    {
        if (_streetAvatarContainer == null) return;

        // Show/hide based on focus mode
        _streetAvatarContainer.Visible = _visualFocusMode == VisualFocusMode.Street;

        if (_visualFocusMode == VisualFocusMode.Street && _streetAvatarPreview != null)
        {
            _streetAvatarPreview.UpdateAvatarAppearance(bodyCode, faceCode, skinCode, hairCode, hairColorCode);
            _streetAvatarNameLabel.Text = username;

            // Set appropriate activity based on player state
            var activity = DetermineAvatarActivity();
            _streetAvatarPreview.SetActivity(activity);
        }
    }

    private string DetermineAvatarActivity()
    {
        // Determine activity based on player state
        if (_session?.LastAction == "work")
            return "work";
        else if (_session?.LastAction == "sleep")
            return "idle";
        else if (_session?.LastAction == "exam")
            return "study";
        else if (_session?.PlayerNeeds?.Hunger > 70)
            return "eat";
        else
            return "idle";
    }

    private void UpdateCharacterCreationPreview(string bodyCode, string faceCode, string skinCode, string hairCode, string hairColorCode)
    {
        if (_characterAvatarPreview != null)
        {
            _characterAvatarPreview.UpdateAvatarAppearance(bodyCode, faceCode, skinCode, hairCode, hairColorCode);
        }
    }

    private void OnAvatarStylePackChanged(string stylePack)
    {
        // Update all avatar previews when style pack changes
        if (_playerAvatarPreview != null)
            _playerAvatarPreview.SetStylePack(stylePack);

        if (_streetAvatarPreview != null)
            _streetAvatarPreview.SetStylePack(stylePack);

        if (_characterAvatarPreview != null)
            _characterAvatarPreview.SetStylePack(stylePack);
    }
}
