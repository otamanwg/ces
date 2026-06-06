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
    public string VisualStyleCode { get; private set; } = DashboardVisualPalettes.Core.Code;

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

    public void SetVisualStyleCode(string styleCode)
    {
        VisualStyleCode = DashboardVisualPalettes.Resolve(styleCode).Code;
        SaveSession();
    }

    public bool HasPlayer => !string.IsNullOrEmpty(PlayerId);
    public bool HasAuthenticatedPlayer => !string.IsNullOrEmpty(PlayerId) && !string.IsNullOrEmpty(AuthToken);

    public void ClearSession()
    {
        PlayerId = "";
        Username = "";
        AuthToken = "";
        LastJobId = "";
        VisualStyleCode = DashboardVisualPalettes.Core.Code;
        string sessionPath = ResolveSessionPath();
        if (File.Exists(sessionPath))
        {
            File.Delete(sessionPath);
        }
    }

    private void SaveSession()
    {
        string sessionPath = ResolveSessionPath();
        string sessionDir = Path.GetDirectoryName(sessionPath) ?? "";
        if (!string.IsNullOrEmpty(sessionDir))
        {
            Directory.CreateDirectory(sessionDir);
        }

        var data = new SessionData
        {
            PlayerId = PlayerId,
            Username = Username,
            AuthToken = AuthToken,
            CityId = CityId,
            VisualStyleCode = VisualStyleCode,
        };
        File.WriteAllText(sessionPath, JsonSerializer.Serialize(data));
    }

    private void LoadSession()
    {
        string sessionPath = ResolveSessionPath();
        if (!File.Exists(sessionPath))
        {
            return;
        }

        try
        {
            var data = JsonSerializer.Deserialize<SessionData>(File.ReadAllText(sessionPath));
            if (data == null)
            {
                return;
            }

            PlayerId = data.PlayerId ?? "";
            Username = data.Username ?? "";
            AuthToken = data.AuthToken ?? "";
            CityId = data.CityId ?? "";
            VisualStyleCode = DashboardVisualPalettes.Resolve(data.VisualStyleCode).Code;
        }
        catch (Exception e)
        {
            GD.PrintErr($"GameSession: не вдалось завантажити сесію: {e.Message}");
        }
    }

    private static string ResolveSessionPath()
    {
        return ProjectSettings.GlobalizePath(SessionPath);
    }

    private class SessionData
    {
        public string PlayerId { get; set; } = "";
        public string Username { get; set; } = "";
        public string AuthToken { get; set; } = "";
        public string CityId { get; set; } = "";
        public string VisualStyleCode { get; set; } = "";
    }
}
