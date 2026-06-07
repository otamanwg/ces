using Godot;
using System.Collections.Generic;
using System.Text;
using System.Text.Json;

public partial class ApiClient : Node
{
    [Signal]
    public delegate void RequestFinishedEventHandler(string endpoint, bool success, string jsonBody);

    [Export] public string BaseUrl = "http://127.0.0.1:8000";
    private HttpRequest _http;
    private readonly Queue<PendingRequest> _queue = new();
    private bool _busy;

    private struct PendingRequest
    {
        public string Path;
        public HttpClient.Method Method;
        public string Body;
        public string[] Headers;
    }

    public override void _Ready()
    {
        _http = new HttpRequest();
        _http.UseThreads = true;
        AddChild(_http);
        _http.RequestCompleted += OnRequestCompleted;
        GD.Print("ApiClient: ready, base URL = ", BaseUrl);
    }

    public void Get(string path)
    {
        Enqueue(path, HttpClient.Method.Get, null, null);
    }

    public void GetAuthorized(string path, string playerToken)
    {
        Enqueue(path, HttpClient.Method.Get, null, BuildAuthHeaders(playerToken));
    }

    public void Post(string path, string jsonBody)
    {
        Enqueue(path, HttpClient.Method.Post, jsonBody, null);
    }

    public void Post(string path)
    {
        Enqueue(path, HttpClient.Method.Post, "{}", null);
    }

    public void PostIdempotent(string path, string idempotencyKey, string jsonBody = "{}")
    {
        Enqueue(path, HttpClient.Method.Post, jsonBody, new[] { $"Idempotency-Key: {idempotencyKey}" });
    }

    public void PostAuthorized(string path, string playerToken, string jsonBody = "{}")
    {
        Enqueue(path, HttpClient.Method.Post, jsonBody, BuildAuthHeaders(playerToken));
    }

    public void PostAuthorizedIdempotent(string path, string playerToken, string idempotencyKey, string jsonBody = "{}")
    {
        Enqueue(
            path,
            HttpClient.Method.Post,
            jsonBody,
            new[] { $"X-Player-Token: {playerToken}", $"Idempotency-Key: {idempotencyKey}" }
        );
    }

    private static string[] BuildAuthHeaders(string playerToken)
    {
        return string.IsNullOrEmpty(playerToken) ? null : new[] { $"X-Player-Token: {playerToken}" };
    }

    private void Enqueue(string path, HttpClient.Method method, string body, string[] extraHeaders)
    {
        _queue.Enqueue(new PendingRequest { Path = path, Method = method, Body = body, Headers = extraHeaders });
        GD.Print($"ApiClient: queued {method} {path}");
        TrySendNext();
    }

    private void TrySendNext()
    {
        if (_busy || _queue.Count == 0)
        {
            return;
        }

        var req = _queue.Dequeue();
        _busy = true;

        var headers = new List<string> { "Content-Type: application/json" };
        if (req.Headers != null)
        {
            headers.AddRange(req.Headers);
        }
        string url = $"{BaseUrl}{req.Path}";

        Error err = req.Body == null
            ? _http.Request(url, headers.ToArray(), req.Method)
            : _http.Request(url, headers.ToArray(), req.Method, req.Body);

        if (err != Error.Ok)
        {
            GD.PrintErr($"ApiClient: request failed to start {req.Path}: {err}");
            _busy = false;
            EmitSignal(SignalName.RequestFinished, req.Path, false, "");
            TrySendNext();
            return;
        }

        _pendingPath = req.Path;
        GD.Print($"ApiClient: sending -> {url}");
    }

    private string _pendingPath = "";

    private void OnRequestCompleted(long result, long responseCode, string[] headers, byte[] bodyBytes)
    {
        string body = bodyBytes.Length > 0 ? Encoding.UTF8.GetString(bodyBytes) : "";
        bool success = result == (long)HttpRequest.Result.Success && responseCode >= 200 && responseCode < 300;

        GD.Print($"ApiClient: done {_pendingPath} success={success} code={responseCode}");

        if (!success)
        {
            GD.PrintErr($"ApiClient: body={body}");
        }

        EmitSignal(SignalName.RequestFinished, _pendingPath, success, body);
        _busy = false;
        _pendingPath = "";
        TrySendNext();
    }

    public static string BuildJson(object payload)
    {
        return JsonSerializer.Serialize(payload);
    }
}
