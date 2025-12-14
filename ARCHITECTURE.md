# BTC Live Architecture

## System Overview

The BTC Live system consists of two main components that communicate via WebSocket:

1. **Python Backend**: Data collection, analysis, and signal generation
2. **C# WPF Frontend**: User interface with alerts and visualization

```
┌─────────────────────────────────────────────────────────────┐
│                     Exchange APIs                            │
│  Binance Futures │ Bybit │ OKX                              │
└────────┬─────────────────┬─────────────────┬────────────────┘
         │ WebSocket       │ WebSocket       │ WebSocket
         │                 │                 │
         ▼                 ▼                 ▼
┌────────────────────────────────────────────────────────────┐
│              Python Backend (127.0.0.1:8000)               │
├────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Binance    │  │    Bybit     │  │     OKX      │     │
│  │  Connector   │  │  Connector   │  │  Connector   │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │             │
│         ▼                  ▼                  ▼             │
│  ┌──────────────────────────────────────────────────┐      │
│  │         Order Book Maintenance (L2)              │      │
│  │         Trade Flow Analysis (Tape)               │      │
│  └─────────────────────┬────────────────────────────┘      │
│                        │                                    │
│                        ▼                                    │
│  ┌──────────────────────────────────────────────────┐      │
│  │            Signal Engine                         │      │
│  │  • Reversal Detection                            │      │
│  │  • Continuation Detection                        │      │
│  │  • Snapback Detection                            │      │
│  │  • Scoring & Ranking                             │      │
│  └─────────────────────┬────────────────────────────┘      │
│                        │                                    │
│                        ▼                                    │
│  ┌──────────────────────────────────────────────────┐      │
│  │        FastAPI WebSocket Server                  │      │
│  │        /ws/signals endpoint                      │      │
│  └─────────────────────┬────────────────────────────┘      │
│                        │                                    │
│  ┌─────────────────────▼────────────────────────────┐      │
│  │          SQLite Database                         │      │
│  │          (Alert Logs & Settings)                 │      │
│  └──────────────────────────────────────────────────┘      │
└────────────────────────┬───────────────────────────────────┘
                         │ WebSocket
                         ▼
┌────────────────────────────────────────────────────────────┐
│              C# WPF Frontend (Windows)                     │
├────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────┐      │
│  │         WebSocket Client Service                 │      │
│  └─────────────────────┬────────────────────────────┘      │
│                        │                                    │
│                        ▼                                    │
│  ┌──────────────────────────────────────────────────┐      │
│  │            Main View Model                       │      │
│  │  • Signal Collection                             │      │
│  │  • Alert Log                                     │      │
│  │  • Connection Management                         │      │
│  └─────────────────────┬────────────────────────────┘      │
│                        │                                    │
│         ┌──────────────┴──────────────┐                    │
│         ▼                              ▼                    │
│  ┌─────────────┐              ┌──────────────┐            │
│  │   Audio     │              │  Main Window │            │
│  │   Service   │              │   (XAML UI)  │            │
│  │             │              │              │            │
│  │ • Alert     │              │ • Signal     │            │
│  │   Sounds    │              │   Table      │            │
│  │ • Beeps     │              │ • Alert Log  │            │
│  └─────────────┘              │ • Controls   │            │
│                               └──────────────┘            │
└────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Exchange Connectors

**Purpose**: Establish and maintain WebSocket connections to exchanges

**Responsibilities**:
- Connect to exchange WebSocket APIs
- Subscribe to order book and trade streams
- Normalize data formats across exchanges
- Handle reconnections and errors
- Emit events for data updates

**Files**:
- `backend/src/connectors/base.py` - Base connector class
- `backend/src/connectors/binance.py` - Binance Futures
- `backend/src/connectors/bybit.py` - Bybit
- `backend/src/connectors/okx.py` - OKX

### 2. Feature Extraction

**Purpose**: Maintain order book state and extract trading features

**Components**:

**OrderBook** (`backend/src/features/orderbook.py`):
- Maintains L2 order book state
- Calculates spread, mid-price
- Detects liquidity shelves
- Estimates slippage
- Computes order book imbalance

**TapeAnalyzer** (`backend/src/features/tape.py`):
- Tracks trade flow
- Calculates aggression scores
- Detects sweeps (large orders)
- Computes VWAP
- Measures price momentum

### 3. Signal Engine

**Purpose**: Generate and score trading signals

**Signal Types**:

1. **Reversal** (Sweep & Rejection):
   - Detect liquidity sweep
   - Check for immediate rejection
   - Score based on sweep size and rejection strength

2. **Continuation** (Absorption & Break):
   - Detect heavy volume absorption
   - Identify breakout
   - Score based on volume and momentum

3. **Snapback** (VWAP Mean Reversion):
   - Calculate VWAP
   - Detect significant deviation
   - Check for reversion signals

**Files**:
- `backend/src/signals/types.py` - Signal data structures
- `backend/src/signals/engine.py` - Signal generation logic

### 4. FastAPI Server

**Purpose**: Provide HTTP API and WebSocket streaming

**Endpoints**:
- `GET /` - Root info
- `GET /health` - Health check with exchange status
- `GET /api/exchanges` - List of exchanges
- `GET /api/settings` - Current configuration
- `WebSocket /ws/signals` - Real-time signal stream

**Flow**:
1. On startup: Initialize database, start exchange feeds
2. Continuous loop: Scan all exchanges for signals every 2 seconds
3. Rank signals by score
4. Broadcast top signals to all connected WebSocket clients
5. On shutdown: Clean up connections

**File**: `backend/src/api/server.py`

### 5. Database

**Purpose**: Persist alerts and settings

**Tables**:
- `alerts` - Log of all generated signals
- `settings` - User-configurable parameters

**File**: `backend/src/database/models.py`

### 6. WPF Frontend

**Purpose**: Display signals and provide user interface

**Architecture**: MVVM (Model-View-ViewModel)

**Components**:

**Models** (`frontend/BTCLiveUI/Models/`):
- `Signal.cs` - Signal data structure
- `AlertLog.cs` - Log entry

**Services** (`frontend/BTCLiveUI/Services/`):
- `WebSocketService.cs` - Backend connection
- `AudioService.cs` - Alert sounds

**ViewModels** (`frontend/BTCLiveUI/ViewModels/`):
- `MainViewModel.cs` - Business logic
  - Manages WebSocket connection
  - Updates signal collection
  - Handles alert notifications
  - Manages log entries

**Views** (`frontend/BTCLiveUI/`):
- `MainWindow.xaml` - UI layout
- Signal ranking table
- Alert log viewer
- Connection controls

## Data Flow

### Signal Generation Flow

```
1. Exchange WebSocket → Raw order book/trade data
2. Connector → Normalized data events
3. OrderBook/TapeAnalyzer → Features extracted
4. SignalEngine → Signals generated & scored
5. FastAPI Server → Signals ranked & broadcast
6. WPF Frontend → Display & alert
```

### Typical Message Flow

**Backend → Frontend**:
```json
{
  "type": "signals",
  "data": [
    {
      "exchange": "binance",
      "setup_type": "Reversal",
      "score": 0.78,
      "price": 43250.50,
      "entry_level": 43250.50,
      "invalidation_level": 43336.86,
      "target_level": 43164.14,
      "spread": 2.5,
      "spread_bps": 5.78,
      "slippage_estimate": 3.2,
      "ttl_seconds": 60,
      "mode": "more_action"
    }
  ],
  "count": 1
}
```

## Configuration

### Backend Configuration

Location: `backend/src/config/settings.py`

Key parameters:
- Signal thresholds (min scores)
- Alert cooldowns
- Order book depth
- Exchange WebSocket URLs

### Frontend Configuration

Hardcoded in:
- `WebSocketService.cs` - Backend URL
- `MainWindow.xaml` - UI styling

## Extension Points

### Adding New Exchange

1. Create connector class extending `BaseConnector`
2. Implement `connect()` and message handlers
3. Add to `server.py` startup
4. Update documentation

### Adding New Signal Type

1. Add new `SetupType` enum value
2. Implement detection method in `SignalEngine`
3. Add to `scan_all_setups()`
4. Update UI to display new type

### Adding New Features

1. Add calculation method to `OrderBook` or `TapeAnalyzer`
2. Use in signal detection logic
3. Include in signal details

## Performance Considerations

- WebSocket messages processed asynchronously
- Order book updates throttled (100ms)
- Signal scanning every 2 seconds
- Alert cooldown prevents spam (30s default)
- UI updates on main thread via Dispatcher

## Security

- Backend binds to localhost only (127.0.0.1)
- No authentication (local-only)
- No trade execution capability
- WebSocket over local network only

## Future Enhancements

- Multi-symbol support
- Historical backtesting
- Signal performance tracking
- Advanced charting
- Remote deployment support
- Mobile companion app
