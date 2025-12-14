# BTC Live - Scalping Alerts

A real-time Bitcoin scalping alert system that analyzes order book and trade data from Binance, OKX, and Bybit to generate actionable trading signals for 30s-2m scalps.

## Features

- **Multi-Exchange Support**: Binance Futures, Bybit, and OKX perpetual futures
- **Real-Time Signals**: Three types of setups:
  - **Reversal** (Sweep & Rejection): Liquidity grabs with immediate rejection
  - **Continuation** (Absorption & Break): Aggressive flows breaking key levels
  - **Snapback** (VWAP Mean Reversion): Price deviations from VWAP
- **Windows Desktop App**: C# WPF application with:
  - Ranking table for setups
  - Real-time alerts with sound notifications
  - Alert log with timestamps
  - Configurable thresholds
- **Python Backend Engine**: 
  - WebSocket connections to exchanges
  - L2 order book maintenance
  - Trade flow analysis
  - Signal scoring and ranking
  - FastAPI WebSocket server

## Architecture

```
BTCLive-Web/
├── backend/              # Python backend engine
│   ├── src/
│   │   ├── api/         # FastAPI server
│   │   ├── config/      # Configuration settings
│   │   ├── connectors/  # Exchange WebSocket connectors
│   │   ├── database/    # SQLite database models
│   │   ├── features/    # Order book & tape analysis
│   │   └── signals/     # Signal generation engine
│   ├── requirements.txt
│   └── main.py
│
├── frontend/            # C# WPF desktop application
│   └── BTCLiveUI/
│       ├── Models/      # Data models
│       ├── Services/    # WebSocket & audio services
│       ├── ViewModels/  # MVVM view models
│       ├── Views/       # UI views
│       └── Assets/      # Sounds & icons
│
└── mobile.html          # Mobile web interface (legacy)
```

## Setup Instructions

### Backend (Python)

1. **Install Python 3.12+**

2. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Run the backend**:
   ```bash
   python main.py
   ```
   
   The server will start on `http://127.0.0.1:8000`

4. **Verify it's running**:
   - Open browser: `http://127.0.0.1:8000`
   - Health check: `http://127.0.0.1:8000/health`

### Frontend (C# WPF)

1. **Install .NET 8 SDK**:
   - Download from: https://dotnet.microsoft.com/download/dotnet/8.0

2. **Build the application**:
   ```bash
   cd frontend/BTCLiveUI
   dotnet restore
   dotnet build
   ```

3. **Run the application**:
   ```bash
   dotnet run
   ```
   
   Or open `BTCLiveUI.sln` in Visual Studio and press F5.

4. **Connect to backend**:
   - Click the "Connect" button in the UI
   - The app will connect to `ws://127.0.0.1:8000/ws/signals`

## Configuration

### Backend Settings

Edit `backend/src/config/settings.py` or create a `.env` file:

```env
# Server
HOST=127.0.0.1
PORT=8000
DEBUG=True

# Signal Mode
MODE=more_action  # or "conservative"

# Thresholds
REVERSAL_MIN_SCORE=0.6
CONTINUATION_MIN_SCORE=0.65
VWAP_SNAPBACK_MIN_SCORE=0.55

# Alert Settings
ALERT_COOLDOWN_SECONDS=30
MAX_ALERTS_PER_MINUTE=10
```

### Frontend Settings

- Sound can be toggled on/off in the UI
- Custom alert sound: Place `alert.wav` in `frontend/BTCLiveUI/Assets/`

## Signal Types

### Reversal (Sweep & Rejection)
- Detects large liquidity sweeps followed by immediate price rejection
- Entry: At rejection point
- Stop: Beyond sweep level (0.2%)
- Target: Initial reversion (0.2%)
- TTL: 60 seconds

### Continuation (Absorption & Break)
- Detects heavy volume absorption and breakout
- Entry: At breakout
- Stop: Below absorption zone (0.3%)
- Target: Continuation move (0.3%)
- TTL: 90 seconds

### Snapback (VWAP Mean Reversion)
- Detects significant deviation from VWAP with reversion signals
- Entry: At current price
- Stop: Extended move (0.2%)
- Target: VWAP level
- TTL: 45 seconds

## Usage

1. **Start Backend**: Run `python backend/main.py`
2. **Start Frontend**: Run the WPF application
3. **Connect**: Click "Connect" button in UI
4. **Monitor Signals**: Watch the ranking table for new setups
5. **Alerts**: Sound plays when new high-score signals appear
6. **Review Logs**: Check alert log for historical signals

## Development

### Backend Development

- Add new exchange connectors in `backend/src/connectors/`
- Modify signal logic in `backend/src/signals/engine.py`
- Add features in `backend/src/features/`
- Database models: `backend/src/database/models.py`

### Frontend Development

- UI layout: `frontend/BTCLiveUI/MainWindow.xaml`
- Business logic: `frontend/BTCLiveUI/ViewModels/MainViewModel.cs`
- Services: `frontend/BTCLiveUI/Services/`

## Requirements

### Backend
- Python 3.12+
- FastAPI
- Websockets
- SQLAlchemy
- See `backend/requirements.txt` for full list

### Frontend
- .NET 8.0
- Windows OS
- See `frontend/BTCLiveUI/BTCLiveUI.csproj` for packages

## Troubleshooting

### Backend won't connect to exchanges
- Check internet connection
- Verify exchange WebSocket URLs are accessible
- Check logs for connection errors

### Frontend can't connect to backend
- Ensure backend is running on `127.0.0.1:8000`
- Check Windows Firewall settings
- Verify WebSocket URL in `WebSocketService.cs`

### No signals appearing
- Allow 1-2 minutes for data accumulation
- Check signal thresholds (may be too strict)
- Verify exchanges are connected in health endpoint

## License

MIT License - See LICENSE file for details

## Disclaimer

**This is a signal generator for educational purposes only. It does not execute trades.**

- Always verify signals manually
- Understand the risks of scalping
- Use appropriate position sizing
- This tool does not guarantee profits
- Past performance does not indicate future results

## Support

For issues and questions:
- GitHub Issues: [Repository Issues](https://github.com/yanoshhedo-pixel/BTCLive-Web/issues)
- Documentation: See this README and code comments

---

**Happy Scalping! 🚀**
