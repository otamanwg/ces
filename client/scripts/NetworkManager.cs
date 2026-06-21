using Godot;
using System;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

public partial class NetworkManager : Node
{
    [Signal]
    public delegate void MessageReceivedEventHandler(string jsonMessage);

    private ClientWebSocket _webSocket;
    private CancellationTokenSource _cancellationTokenSource;

    public void ConnectToCity(string cityId, string playerToken = "")
    {
        if (string.IsNullOrEmpty(cityId))
        {
            GD.PrintErr("NetworkManager: cityId порожній, WS не підключено.");
            return;
        }

        if (string.IsNullOrEmpty(playerToken))
        {
            GD.PrintErr("NetworkManager: playerToken порожній, WS не підключено.");
            return;
        }

        string serverUrl = CityWebSocketEndpoint.BuildUrl(cityId, playerToken);
        if (string.IsNullOrEmpty(serverUrl))
        {
            GD.PrintErr("NetworkManager: не вдалось сформувати WS URL.");
            return;
        }

        _ = ConnectAsync(serverUrl);
    }

    private async Task ConnectAsync(string serverUrl)
    {
        _webSocket?.Dispose();
        _cancellationTokenSource?.Cancel();

        _webSocket = new ClientWebSocket();
        _cancellationTokenSource = new CancellationTokenSource();

        try
        {
            GD.Print($"NetworkManager: підключення до {serverUrl}...");
            await _webSocket.ConnectAsync(new Uri(serverUrl), _cancellationTokenSource.Token);
            GD.Print("NetworkManager: WS підключено.");
            _ = ReceiveLoop();
        }
        catch (Exception e)
        {
            GD.PrintErr($"NetworkManager: помилка WS: {e.Message}");
        }
    }

    private async Task ReceiveLoop()
    {
        var buffer = new byte[4096];

        try
        {
            while (_webSocket.State == WebSocketState.Open && !_cancellationTokenSource.Token.IsCancellationRequested)
            {
                var result = await _webSocket.ReceiveAsync(new ArraySegment<byte>(buffer), _cancellationTokenSource.Token);

                if (result.MessageType == WebSocketMessageType.Close)
                {
                    await _webSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, "Closing", CancellationToken.None);
                    break;
                }

                string messageJson = Encoding.UTF8.GetString(buffer, 0, result.Count);
                CallDeferred(MethodName.EmitSignal, SignalName.MessageReceived, messageJson);
            }
        }
        catch (Exception e)
        {
            if (!_cancellationTokenSource.Token.IsCancellationRequested)
            {
                GD.PrintErr($"NetworkManager: помилка отримання WS: {e.Message}");
            }
        }
    }

    public async void SendJsonMessage(string jsonPayload)
    {
        if (_webSocket == null || _webSocket.State != WebSocketState.Open)
        {
            GD.PrintErr("NetworkManager: WS не підключено.");
            return;
        }

        try
        {
            var bytes = Encoding.UTF8.GetBytes(jsonPayload);
            await _webSocket.SendAsync(new ArraySegment<byte>(bytes), WebSocketMessageType.Text, true, _cancellationTokenSource.Token);
        }
        catch (Exception e)
        {
            GD.PrintErr($"NetworkManager: помилка відправки WS: {e.Message}");
        }
    }

    public override void _ExitTree()
    {
        _cancellationTokenSource?.Cancel();
        _webSocket?.Dispose();
    }

    // --- Phase G7: WebSocket позиційна синхронізація ---

    private float _positionSyncInterval = 0.15f; // 6-7 разів на секунду
    private float _positionSyncTimer;
    private string _currentLocationId = string.Empty;

    /// <summary>
    /// Встановлює поточну локацію для позиційної синхронізації.
    /// </summary>
    public void SetLocation(string locationId)
    {
        _currentLocationId = locationId ?? string.Empty;
    }

    /// <summary>
    /// Відправляє позицію гравця на сервер для синхронізації з іншими гравцями.
    /// Викликається з PlayerAvatarController._PhysicsProcess.
    /// </summary>
    public void SyncPlayerPosition(float x, float y, float z, float rotationY)
    {
        if (string.IsNullOrEmpty(_currentLocationId))
        {
            return;
        }

        _positionSyncTimer += (float)GetProcessDeltaTime();

        if (_positionSyncTimer < _positionSyncInterval)
        {
            return;
        }

        _positionSyncTimer = 0;

        string json = $"{{\"type\":\"position\",\"location\":\"{_currentLocationId}\",\"x\":{x:F2},\"y\":{y:F2},\"z\":{z:F2},\"rot_y\":{rotationY:F2}}}";
        SendJsonMessage(json);
    }
}
