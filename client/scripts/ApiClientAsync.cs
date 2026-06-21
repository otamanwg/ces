#nullable enable
using Godot;
using System;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using SysHttp = System.Net.Http;

/// <summary>
/// Async HTTP methods for ApiClient using System.Net.Http.HttpClient.
/// These complement the signal-based queue (for fire-and-forget actions)
/// with awaitable calls (for partial class controller refactoring).
/// </summary>
public partial class ApiClient
{
    private static readonly SysHttp.HttpClient AsyncHttp = new() { Timeout = TimeSpan.FromSeconds(10) };

    public async Task<JsonNode?> GetAsync(string path, string[]? extraHeaders = null)
    {
        using var request = new SysHttp.HttpRequestMessage(SysHttp.HttpMethod.Get, $"{BaseUrl}{path}");
        ApplyExtraHeaders(request, extraHeaders);
        try
        {
            using var response = await AsyncHttp.SendAsync(request);
            var body = await response.Content.ReadAsStringAsync();
            return response.IsSuccessStatusCode ? JsonNode.Parse(body) : null;
        }
        catch (Exception ex)
        {
            GD.PrintErr($"ApiClient.GetAsync error {path}: {ex.Message}");
            return null;
        }
    }

    public async Task<JsonNode?> PostAsync(string path, object? body = null, string[]? extraHeaders = null)
    {
        using var request = new SysHttp.HttpRequestMessage(SysHttp.HttpMethod.Post, $"{BaseUrl}{path}");
        ApplyExtraHeaders(request, extraHeaders);
        var json = body != null ? JsonSerializer.Serialize(body) : "{}";
        request.Content = new SysHttp.StringContent(json, Encoding.UTF8, "application/json");
        try
        {
            using var response = await AsyncHttp.SendAsync(request);
            var responseBody = await response.Content.ReadAsStringAsync();
            return response.IsSuccessStatusCode ? JsonNode.Parse(responseBody) : null;
        }
        catch (Exception ex)
        {
            GD.PrintErr($"ApiClient.PostAsync error {path}: {ex.Message}");
            return null;
        }
    }

    private static void ApplyExtraHeaders(SysHttp.HttpRequestMessage request, string[]? extraHeaders)
    {
        if (extraHeaders == null) return;
        foreach (var header in extraHeaders)
        {
            var sep = header.IndexOf(':');
            if (sep > 0)
                request.Headers.TryAddWithoutValidation(header[..sep].Trim(), header[(sep + 1)..].Trim());
        }
    }
}
