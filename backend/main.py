"""Main entry point for BTC Live backend."""
from src.api.server import app
import uvicorn
from src.config import settings

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
