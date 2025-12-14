using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.CompilerServices;
using System.Windows;
using System.Windows.Input;
using BTCLiveUI.Models;
using BTCLiveUI.Services;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace BTCLiveUI.ViewModels
{
    /// <summary>
    /// Main view model for the application
    /// </summary>
    public class MainViewModel : INotifyPropertyChanged
    {
        private readonly WebSocketService _webSocketService;
        private readonly AudioService _audioService;

        public ObservableCollection<Signal> Signals { get; } = new();
        public ObservableCollection<AlertLog> AlertLogs { get; } = new();

        private string _connectionStatus = "Disconnected";
        public string ConnectionStatus
        {
            get => _connectionStatus;
            set
            {
                _connectionStatus = value;
                OnPropertyChanged();
            }
        }

        private bool _isConnected = false;
        public bool IsConnected
        {
            get => _isConnected;
            set
            {
                _isConnected = value;
                OnPropertyChanged();
                OnPropertyChanged(nameof(ConnectButtonText));
            }
        }

        public string ConnectButtonText => IsConnected ? "Disconnect" : "Connect";

        private bool _soundEnabled = true;
        public bool SoundEnabled
        {
            get => _soundEnabled;
            set
            {
                _soundEnabled = value;
                _audioService.SoundEnabled = value;
                OnPropertyChanged();
            }
        }

        public ICommand ConnectCommand { get; }
        public ICommand ClearLogsCommand { get; }

        public MainViewModel(WebSocketService webSocketService, AudioService audioService)
        {
            _webSocketService = webSocketService;
            _audioService = audioService;

            // Setup commands
            ConnectCommand = new RelayCommand(async _ => await ToggleConnection());
            ClearLogsCommand = new RelayCommand(_ => AlertLogs.Clear());

            // Subscribe to events
            _webSocketService.MessageReceived += OnMessageReceived;
            _webSocketService.ConnectionStatusChanged += OnConnectionStatusChanged;
        }

        private async Task ToggleConnection()
        {
            try
            {
                if (IsConnected)
                {
                    await _webSocketService.DisconnectAsync();
                }
                else
                {
                    ConnectionStatus = "Connecting...";
                    await _webSocketService.ConnectAsync();
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Connection error: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
                ConnectionStatus = "Connection Failed";
            }
        }

        private void OnConnectionStatusChanged(object? sender, bool isConnected)
        {
            Application.Current.Dispatcher.Invoke(() =>
            {
                IsConnected = isConnected;
                ConnectionStatus = isConnected ? "Connected" : "Disconnected";
            });
        }

        private void OnMessageReceived(object? sender, string message)
        {
            try
            {
                var json = JObject.Parse(message);
                var messageType = json["type"]?.ToString();

                if (messageType == "signals")
                {
                    var signalsData = json["data"];
                    if (signalsData != null)
                    {
                        var signals = JsonConvert.DeserializeObject<List<Signal>>(signalsData.ToString());
                        if (signals != null)
                        {
                            Application.Current.Dispatcher.Invoke(() =>
                            {
                                UpdateSignals(signals);
                            });
                        }
                    }
                }
                else if (messageType == "connected")
                {
                    var msg = json["message"]?.ToString();
                    Application.Current.Dispatcher.Invoke(() =>
                    {
                        AddLog("System", "Connected to server");
                    });
                }
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Error processing message: {ex.Message}");
            }
        }

        private void UpdateSignals(List<Signal> newSignals)
        {
            // Check for new signals (not in current list)
            // Use combination of exchange, setup_type, and timestamp for uniqueness
            var existingKeys = new HashSet<string>(
                Signals.Select(s => $"{s.Exchange}_{s.SetupType}_{s.Timestamp}")
            );
            var hasNewSignals = newSignals.Any(s => 
                !existingKeys.Contains($"{s.Exchange}_{s.SetupType}_{s.Timestamp}")
            );

            // Clear and update
            Signals.Clear();
            foreach (var signal in newSignals)
            {
                Signals.Add(signal);
            }

            // Play sound for new signals
            if (hasNewSignals && Signals.Count > 0)
            {
                var topSignal = Signals[0];
                _audioService.PlayAlertSound();
                AddLog(topSignal.Exchange, $"{topSignal.SetupType} signal - Score: {topSignal.FormattedScore} - Price: {topSignal.FormattedPrice}");
            }
        }

        private void AddLog(string exchange, string message)
        {
            var log = new AlertLog
            {
                Timestamp = DateTime.Now,
                Exchange = exchange,
                Details = message,
                SetupType = "",
                Score = 0,
                Price = 0,
                Status = "Active"
            };

            AlertLogs.Insert(0, log);

            // Keep only last 100 logs
            while (AlertLogs.Count > 100)
            {
                AlertLogs.RemoveAt(AlertLogs.Count - 1);
            }
        }

        public event PropertyChangedEventHandler? PropertyChanged;

        protected void OnPropertyChanged([CallerMemberName] string? propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }

    /// <summary>
    /// Simple relay command implementation
    /// </summary>
    public class RelayCommand : ICommand
    {
        private readonly Action<object?> _execute;
        private readonly Func<object?, bool>? _canExecute;

        public RelayCommand(Action<object?> execute, Func<object?, bool>? canExecute = null)
        {
            _execute = execute;
            _canExecute = canExecute;
        }

        public bool CanExecute(object? parameter) => _canExecute?.Invoke(parameter) ?? true;

        public void Execute(object? parameter) => _execute(parameter);

        public event EventHandler? CanExecuteChanged
        {
            add => CommandManager.RequerySuggested += value;
            remove => CommandManager.RequerySuggested -= value;
        }
    }
}
