# Quick Start Guide

Get BTC Live up and running in 5 minutes!

## Prerequisites

- **Python 3.12+** - [Download](https://www.python.org/downloads/)
- **.NET 8 SDK** - [Download](https://dotnet.microsoft.com/download/dotnet/8.0)
- **Windows OS** (for the desktop app)
- **Internet connection** (for exchange data)

## Step 1: Start the Backend

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies (first time only)
pip install -r requirements.txt

# Start the backend server
python main.py
```

You should see:
```
INFO: Started server process
INFO: Uvicorn running on http://127.0.0.1:8000
```

Keep this terminal window open!

## Step 2: Verify Backend is Running

Open a web browser and go to:
- http://127.0.0.1:8000

You should see:
```json
{
  "name": "BTC Live Scalping Alerts",
  "version": "1.0.0",
  "status": "running"
}
```

## Step 3: Start the Frontend

### Option A: Using dotnet CLI (recommended)

```bash
# Open a new terminal
cd frontend/BTCLiveUI

# Restore dependencies (first time only)
dotnet restore

# Run the application
dotnet run
```

### Option B: Using Visual Studio

1. Open `frontend/BTCLiveUI.sln` in Visual Studio
2. Press F5 or click "Start"

## Step 4: Connect and Monitor

1. The BTC Live window will open
2. Click the **"Connect"** button in the top-right
3. Status should change to **"Connected"**
4. Wait 30-60 seconds for data to accumulate
5. Signals will start appearing in the table

## What to Expect

### Initial Connection
- Backend connects to 3 exchanges (Binance, Bybit, OKX)
- Order books and trades start streaming
- Takes ~30 seconds to build enough data

### First Signals
- Signals appear when market conditions match criteria
- Higher scores = better quality setups
- Sound plays when new signals are detected
- Alert log shows all activity

### Signal Frequency
- **"more_action" mode**: 5-15 signals per hour (more frequent, lower threshold)
- **"conservative" mode**: 2-8 signals per hour (less frequent, higher quality)

## Troubleshooting

### Backend Issues

**"Module not found" error**
```bash
pip install -r requirements.txt
```

**"Port already in use" error**
- Another application is using port 8000
- Change PORT in `backend/src/config/settings.py`

**Exchange connection errors**
- Check your internet connection
- Some networks may block WebSocket connections
- Wait a few minutes and restart

### Frontend Issues

**"Unable to connect to server"**
- Make sure backend is running on http://127.0.0.1:8000
- Check Windows Firewall isn't blocking the connection

**Application won't start**
- Ensure .NET 8 SDK is installed: `dotnet --version`
- Try `dotnet clean` then `dotnet build`

**No signals appearing**
- Wait 1-2 minutes for data accumulation
- Check backend logs for errors
- Visit http://127.0.0.1:8000/health to see exchange status

## Testing the Setup

### Manual Backend Test

```bash
# Check health endpoint
curl http://127.0.0.1:8000/health

# Should return exchange status like:
{
  "status": "healthy",
  "exchanges": {
    "binance": {"connected": true, ...},
    "bybit": {"connected": true, ...},
    "okx": {"connected": true, ...}
  }
}
```

### Frontend Test

1. Click "Connect" - should succeed
2. Status shows "Connected"
3. Check Alert Log for "Connected to server" message
4. Signals table should populate within 1-2 minutes

## Configuration Tips

### More Signals (More Action Mode)

Edit `backend/src/config/settings.py`:
```python
MODE = "more_action"
REVERSAL_MIN_SCORE = 0.5      # Lower = more signals
CONTINUATION_MIN_SCORE = 0.55
VWAP_SNAPBACK_MIN_SCORE = 0.45
ALERT_COOLDOWN_SECONDS = 20    # Shorter cooldown
```

### Fewer, Better Signals (Conservative Mode)

```python
MODE = "conservative"
REVERSAL_MIN_SCORE = 0.75      # Higher = fewer, better signals
CONTINUATION_MIN_SCORE = 0.80
VWAP_SNAPBACK_MIN_SCORE = 0.70
ALERT_COOLDOWN_SECONDS = 60    # Longer cooldown
```

After changing settings, restart the backend.

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- Customize thresholds for your trading style
- Add custom alert sound (see `frontend/BTCLiveUI/Assets/README.md`)

## Support

Having issues? Check:
1. Backend logs in terminal
2. Frontend console output
3. Exchange status at /health endpoint
4. [GitHub Issues](https://github.com/yanoshhedo-pixel/BTCLive-Web/issues)

---

**Happy Trading! 🚀**

Remember: This is a signal generator, not a trading bot. Always verify signals manually before taking any action.
