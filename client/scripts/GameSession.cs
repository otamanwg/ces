using Godot;
using System;
using System.IO;
using System.Text.Json;

public partial class GameSession : Node
{
    public string PlayerId { get; private set; } = "";
    public string Username { get; private set; } = "";
    public string AuthToken { get; private set; } = "";
    public string CityId { get; private set; } = "";
    public string LastJobId { get; private set; } = "";

    private const string SessionPath = "user://player_session.json";

    public override void _Ready()
    {
        LoadSession();
    }

    public void SetPlayer(string playerId, string username, string authToken = "")
    {
        PlayerId = playerId;
        Username = username;
        if (!string.IsNullOrEmpty(authToken))
        {
            AuthToken = authToken;
        }
        SaveSession();
    }

    public void SetCityId(string cityId)
    {
        CityId = cityId;
        SaveSession();
    }

    public void SetLastJobId(string jobId)
    {
        LastJobId = jobId;
    }

    public bool HasPlayer => !string.IsNullOrEmpty(PlayerId);
    public bool HasAuthenticatedPlayer => !string.IsNullOrEmpty(PlayerId) && !string.IsNullOrEmpty(AuthToken);

    public void ClearSession()
    {
        PlayerId = "";
        Username = "";
        AuthToken = "";
        LastJobId = "";
        if (File.Exists(SessionPath))
        {
            File.Delete(SessionPath);
        }
    }

    private void SaveSession()
    {
        var data = new SessionData
        {
            PlayerId = PlayerId,
            Username = Username,
            AuthToken = AuthToken,
            CityId = CityId,
        };
        File.WriteAllText(SessionPath, JsonSerializer.Serialize(data));
    }

    private void LoadSession()
    {
        if (!File.Exists(SessionPath))
        {
            return;
        }

        try
        {
            var data = JsonSerializer.Deserialize<SessionData>(File.ReadAllText(SessionPath));
            if (data == null)
            {
                return;
            }

            PlayerId = data.PlayerId ?? "";
            Username = data.Username ?? "";
            AuthToken = data.AuthToken ?? "";
            CityId = data.CityId ?? "";
        }
        catch (Exception e)
        {
            GD.PrintErr($"GameSession: не вдалось завантажити сесію: {e.Message}");
        }
    }

    private class SessionData
    {
        public string PlayerId { get; set; } = "";
        public string Username { get; set; } = "";
        public string AuthToken { get; set; } = "";
        public string CityId { get; set; } = "";
    }
}
