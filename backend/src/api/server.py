"""
FastAPI server for BTC Live scalping alerts.
Provides WebSocket endpoint for streaming signals to UI.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import json
from loguru import logger
from typing import List, Dict, Any

from ..config import settings
from ..database import init_db, get_session, Alert
from ..connectors import BinanceConnector, BybitConnector, OKXConnector
from ..features import OrderBook, TapeAnalyzer
from ..signals import SignalEngine

# Active WebSocket connections
active_connections: List[WebSocket] = []

# Exchange components
exchanges = {}


async def start_exchange_feeds():
    """Start WebSocket feeds for all exchanges."""
    logger.info("Starting exchange feeds...")
    
    # Initialize Binance
    binance_connector = BinanceConnector()
    binance_orderbook = OrderBook("binance", "btcusdt")
    binance_tape = TapeAnalyzer("binance", "btcusdt")
    binance_engine = SignalEngine("binance")
    binance_engine.set_orderbook(binance_orderbook)
    binance_engine.set_tape(binance_tape)
    
    # Setup callbacks
    async def binance_ob_callback(data):
        binance_orderbook.update(data["bids"], data["asks"], data["timestamp"])
    
    async def binance_trade_callback(data):
        binance_tape.add_trade(
            data["timestamp"],
            data["price"],
            data["quantity"],
            data["side"]
        )
    
    binance_connector.on_orderbook(binance_ob_callback)
    binance_connector.on_trades(binance_trade_callback)
    
    exchanges["binance"] = {
        "connector": binance_connector,
        "orderbook": binance_orderbook,
        "tape": binance_tape,
        "engine": binance_engine
    }
    
    # Initialize Bybit
    bybit_connector = BybitConnector()
    bybit_orderbook = OrderBook("bybit", "BTCUSDT")
    bybit_tape = TapeAnalyzer("bybit", "BTCUSDT")
    bybit_engine = SignalEngine("bybit")
    bybit_engine.set_orderbook(bybit_orderbook)
    bybit_engine.set_tape(bybit_tape)
    
    async def bybit_ob_callback(data):
        bybit_orderbook.update(data["bids"], data["asks"], data["timestamp"])
    
    async def bybit_trade_callback(data):
        bybit_tape.add_trade(
            data["timestamp"],
            data["price"],
            data["quantity"],
            data["side"]
        )
    
    bybit_connector.on_orderbook(bybit_ob_callback)
    bybit_connector.on_trades(bybit_trade_callback)
    
    exchanges["bybit"] = {
        "connector": bybit_connector,
        "orderbook": bybit_orderbook,
        "tape": bybit_tape,
        "engine": bybit_engine
    }
    
    # Initialize OKX
    okx_connector = OKXConnector()
    okx_orderbook = OrderBook("okx", "BTC-USDT-SWAP")
    okx_tape = TapeAnalyzer("okx", "BTC-USDT-SWAP")
    okx_engine = SignalEngine("okx")
    okx_engine.set_orderbook(okx_orderbook)
    okx_engine.set_tape(okx_tape)
    
    async def okx_ob_callback(data):
        okx_orderbook.update(data["bids"], data["asks"], data["timestamp"])
    
    async def okx_trade_callback(data):
        okx_tape.add_trade(
            data["timestamp"],
            data["price"],
            data["quantity"],
            data["side"]
        )
    
    okx_connector.on_orderbook(okx_ob_callback)
    okx_connector.on_trades(okx_trade_callback)
    
    exchanges["okx"] = {
        "connector": okx_connector,
        "orderbook": okx_orderbook,
        "tape": okx_tape,
        "engine": okx_engine
    }
    
    # Start all connectors
    tasks = [
        asyncio.create_task(binance_connector.run()),
        asyncio.create_task(bybit_connector.run()),
        asyncio.create_task(okx_connector.run())
    ]
    
    logger.info("Exchange feeds started")
    
    return tasks


async def scan_signals_loop():
    """Continuously scan for signals and broadcast to connected clients."""
    logger.info("Starting signal scanning loop...")
    
    while True:
        try:
            # Scan all exchanges for signals
            all_signals = []
            
            for exchange_name, components in exchanges.items():
                engine = components["engine"]
                signals = engine.scan_all_setups()
                all_signals.extend(signals)
            
            # Sort signals by score (highest first)
            all_signals.sort(key=lambda s: s.score, reverse=True)
            
            # Take top signals
            top_signals = all_signals[:10]
            
            # Broadcast to all connected clients
            if top_signals and active_connections:
                message = {
                    "type": "signals",
                    "data": [s.to_dict() for s in top_signals],
                    "count": len(top_signals)
                }
                
                # Send to all active connections
                disconnected = []
                for connection in active_connections:
                    try:
                        await connection.send_json(message)
                    except Exception as e:
                        logger.error(f"Error sending to client: {e}")
                        disconnected.append(connection)
                
                # Remove disconnected clients
                for conn in disconnected:
                    if conn in active_connections:
                        active_connections.remove(conn)
            
            # Wait before next scan
            await asyncio.sleep(2)  # Scan every 2 seconds
            
        except Exception as e:
            logger.error(f"Error in signal scanning loop: {e}")
            await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting BTC Live backend...")
    await init_db()
    
    # Start exchange feeds
    feed_tasks = await start_exchange_feeds()
    
    # Start signal scanning loop
    scan_task = asyncio.create_task(scan_signals_loop())
    
    yield
    
    # Shutdown
    logger.info("Shutting down BTC Live backend...")
    scan_task.cancel()
    for task in feed_tasks:
        task.cancel()


# Create FastAPI app
app = FastAPI(
    title="BTC Live Scalping Alerts",
    description="Real-time BTC scalping signal engine",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "BTC Live Scalping Alerts",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    exchange_status = {}
    for name, components in exchanges.items():
        exchange_status[name] = {
            "connected": components["connector"].running,
            "orderbook_updates": len(components["orderbook"].history),
            "trades": len(components["tape"].trades)
        }
    
    return {
        "status": "healthy",
        "exchanges": exchange_status
    }


@app.websocket("/ws/signals")
async def websocket_signals(websocket: WebSocket):
    """
    WebSocket endpoint for streaming signals to UI.
    """
    await websocket.accept()
    active_connections.append(websocket)
    
    logger.info(f"New WebSocket connection. Total: {len(active_connections)}")
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to BTC Live signal stream"
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                # Could handle commands from UI here if needed
                logger.debug(f"Received from client: {data}")
            except WebSocketDisconnect:
                break
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(active_connections)}")


@app.get("/api/exchanges")
async def get_exchanges():
    """Get list of supported exchanges."""
    return {
        "exchanges": [
            {
                "name": "binance",
                "symbol": "BTCUSDT",
                "display_name": "Binance Futures"
            },
            {
                "name": "bybit",
                "symbol": "BTCUSDT",
                "display_name": "Bybit"
            },
            {
                "name": "okx",
                "symbol": "BTC-USDT-SWAP",
                "display_name": "OKX"
            }
        ]
    }


@app.get("/api/settings")
async def get_settings():
    """Get current settings."""
    return {
        "mode": settings.MODE,
        "alert_cooldown": settings.ALERT_COOLDOWN_SECONDS,
        "max_alerts_per_minute": settings.MAX_ALERTS_PER_MINUTE,
        "reversal_min_score": settings.REVERSAL_MIN_SCORE,
        "continuation_min_score": settings.CONTINUATION_MIN_SCORE,
        "snapback_min_score": settings.VWAP_SNAPBACK_MIN_SCORE
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.server:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
