using Godot;
using System;
using System.IO;
using System.Text.Json;

public partial class GameSession : Node
{
    public string PlayerId { get; private set; } = "";
    public string Username { get; private set; } = "";
    public string CityId { get; private set; } = "";
    public string LastJobId { get; private set; } = "";

    private const string SessionPath = "user://player_session.json";

    public override void _Ready()
    {
        LoadSession();
    }

    public void SetPlayer(string playerId, string username)
    {
        PlayerId = playerId;
        Username = username;
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

    private void SaveSession()
    {
        var data = new SessionData
        {
            PlayerId = PlayerId,
            Username = Username,
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
        public string CityId { get; set; } = "";
    }
}
