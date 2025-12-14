using System.Diagnostics;
using System.Net.WebSockets;
using System.Text;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace BTCLiveUI.Services
{
    /// <summary>
    /// WebSocket service for connecting to backend signal stream
    /// </summary>
    public class WebSocketService
    {
        private ClientWebSocket? _webSocket;
        private CancellationTokenSource? _cancellationTokenSource;
        private readonly string _serverUrl = "ws://127.0.0.1:8000/ws/signals";

        public event EventHandler<string>? MessageReceived;
        public event EventHandler<bool>? ConnectionStatusChanged;

        public bool IsConnected => _webSocket?.State == WebSocketState.Open;

        public async Task ConnectAsync()
        {
            try
            {
                _webSocket = new ClientWebSocket();
                _cancellationTokenSource = new CancellationTokenSource();

                await _webSocket.ConnectAsync(new Uri(_serverUrl), _cancellationTokenSource.Token);
                ConnectionStatusChanged?.Invoke(this, true);

                // Start receiving messages
                _ = Task.Run(ReceiveLoop);
            }
            catch (Exception ex)
            {
                ConnectionStatusChanged?.Invoke(this, false);
                throw new Exception($"Failed to connect to server: {ex.Message}", ex);
            }
        }

        private async Task ReceiveLoop()
        {
            var buffer = new byte[4096];

            try
            {
                while (_webSocket != null && _webSocket.State == WebSocketState.Open)
                {
                    var result = await _webSocket.ReceiveAsync(
                        new ArraySegment<byte>(buffer),
                        _cancellationTokenSource?.Token ?? CancellationToken.None
                    );

                    if (result.MessageType == WebSocketMessageType.Close)
                    {
                        await DisconnectAsync();
                        break;
                    }

                    var message = Encoding.UTF8.GetString(buffer, 0, result.Count);
                    MessageReceived?.Invoke(this, message);
                }
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"WebSocket receive error: {ex.Message}");
            }
            finally
            {
                ConnectionStatusChanged?.Invoke(this, false);
            }
        }

        public async Task DisconnectAsync()
        {
            if (_webSocket != null)
            {
                try
                {
                    _cancellationTokenSource?.Cancel();
                    if (_webSocket.State == WebSocketState.Open)
                    {
                        await _webSocket.CloseAsync(
                            WebSocketCloseStatus.NormalClosure,
                            "Closing",
                            CancellationToken.None
                        );
                    }
                }
                catch (Exception ex)
                {
                    Debug.WriteLine($"WebSocket disconnect error: {ex.Message}");
                }
                finally
                {
                    _webSocket?.Dispose();
                    _webSocket = null;
                    _cancellationTokenSource?.Dispose();
                    _cancellationTokenSource = null;
                    ConnectionStatusChanged?.Invoke(this, false);
                }
            }
        }

        public async Task SendAsync(string message)
        {
            if (_webSocket?.State == WebSocketState.Open)
            {
                var bytes = Encoding.UTF8.GetBytes(message);
                await _webSocket.SendAsync(
                    new ArraySegment<byte>(bytes),
                    WebSocketMessageType.Text,
                    true,
                    CancellationToken.None
                );
            }
        }
    }
}
