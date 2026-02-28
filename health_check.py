"""
Health check HTTP server for uptime monitoring (e.g., Uptime Robot).
Allows external services to ping the bot and keep it awake.
"""
import logging
from aiohttp import web
import asyncio

logger = logging.getLogger(__name__)

HEALTH_CHECK_PORT = 8000  # Configurable via env var


async def health_handler(request):
    """
    Simple health check endpoint.
    Returns 200 OK with JSON status.
    
    Usage: GET http://your-bot-host:8000/health
    Response: {"status": "ok", "timestamp": "2026-02-28T12:34:56"}
    """
    from datetime import datetime
    return web.json_response({
        "status": "ok",
        "service": "AggresiveProfitHunterBot",
        "timestamp": datetime.utcnow().isoformat()
    })


async def start_health_server(port=HEALTH_CHECK_PORT):
    """
    Start a lightweight aiohttp health check server.
    This allows uptime monitoring bots (Uptime Robot, etc.) to keep your bot alive.
    """
    app = web.Application()
    app.router.add_get('/health', health_handler)
    app.router.add_get('/', health_handler)  # Root also responds
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"✓ Health check server started on port {port}")
    logger.info(f"  Health endpoint: http://your-host:{port}/health")
    logger.info(f"  Use this URL in Uptime Robot or similar service to keep bot awake")
    
    return runner


async def stop_health_server(runner):
    """Stop the health check server gracefully."""
    if runner:
        await runner.cleanup()
        logger.info("✓ Health check server stopped")
