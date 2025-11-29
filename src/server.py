"""MCP server for Tesla telemetry and control via Tessie API.

This module implements the Model Context Protocol (MCP) server that exposes
Tesla vehicle telemetry and control functions via the Tessie API.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Add parent directory to path for imports when running as script
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.control import CONTROL_TOOLS, Control, build_control_dispatch
from src.telemetry import TELEMETRY_TOOLS, Telemetry, build_telemetry_dispatch
from src.exceptions import ConfigurationError, TessieMCPError
from src.utils import setup_logging, validate_vin
from src.constants import MCP_SERVER_NAME, DEFAULT_SSE_HOST, DEFAULT_SSE_PORT, ENV_VEHICLE_VIN, ENV_TELEMETRY_INTERVAL


# Load environment variables from .env file in project root
load_dotenv(PROJECT_ROOT / ".env")

# Setup logging
logger = setup_logging(__name__)

# Initialize server
app = Server(MCP_SERVER_NAME)

# Global service instances (initialized on startup)
_telemetry: Telemetry | None = None
_control: Control | None = None
_tool_dispatch: dict[str, Callable[[], str]] = {}


def get_telemetry() -> Telemetry:
    """Get the global Telemetry instance."""
    if _telemetry is None:
        raise RuntimeError("Telemetry not initialized. Call init_services() first.")
    return _telemetry


def get_control() -> Control:
    """Get the global Control instance."""
    if _control is None:
        raise RuntimeError("Control not initialized. Call init_services() first.")
    return _control


def get_tool_dispatch() -> dict[str, Callable[[], str]]:
    """Get the combined tool dispatch mapping."""
    if not _tool_dispatch:
        raise RuntimeError("Tool dispatch not initialized. Call init_services() first.")
    return _tool_dispatch


def init_services(vin: str, interval: int | str = 5) -> None:
    """Initialize telemetry and control services and build dispatch map.

    Args:
        vin: Vehicle VIN to monitor/control
        interval: Telemetry refresh interval in minutes or 'realtime'

    Raises:
        ConfigurationError: If services cannot be initialized
    """
    global _telemetry, _control, _tool_dispatch

    logger.info("Initializing services for VIN ending in ...%s", vin[-4:])
    logger.info("Telemetry interval: %s", interval)

    try:
        _telemetry = Telemetry(vin=vin, interval=interval)
        _control = Control(vin=vin)
        _tool_dispatch = {
            **build_telemetry_dispatch(_telemetry),
            **build_control_dispatch(_control),
        }
        logger.info("Services initialized successfully with %d tools", len(_tool_dispatch))
    except Exception as e:
        logger.error("Failed to initialize services: %s", str(e), exc_info=True)
        raise ConfigurationError(f"Service initialization failed: {str(e)}")


# =============================================================================
# TOOL DEFINITIONS
# =============================================================================


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available telemetry and control tools."""
    return TELEMETRY_TOOLS + CONTROL_TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a telemetry or control tool."""
    dispatch = get_tool_dispatch()
    # arguments are unused today but reserved for future control params
    _ = arguments
    
    if name not in dispatch:
        raise ValueError(f"Unknown tool: {name}")
    
    result = dispatch[name]()
    return [TextContent(type="text", text=result)]


async def run_server_stdio(vin: str, interval: int | str = 5) -> None:
    """Run the MCP server with STDIO transport (local)."""
    init_services(vin=vin, interval=interval)

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


async def run_server_sse(
    vin: str,
    interval: int | str = 5,
    host: str = "0.0.0.0",
    port: int = 8000
) -> None:
    """Run the MCP server with SSE transport (remote)."""
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.responses import JSONResponse
    import uvicorn

    init_services(vin=vin, interval=interval)
    
    sse = SseServerTransport("/messages")
    
    async def handle_sse(request):
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await app.run(
                streams[0], streams[1], app.create_initialization_options()
            )
    
    async def handle_messages(request):
        await sse.handle_post_message(request.scope, request.receive, request._send)
    
    async def health(request):
        return JSONResponse({"status": "ok", "server": "tessie-mcp"})
    
    starlette_app = Starlette(
        routes=[
            Route("/health", health, methods=["GET"]),
            Route("/sse", handle_sse, methods=["GET"]),
            Route("/messages", handle_messages, methods=["POST"]),
        ],
    )
    
    print(f"🚗 Tessie MCP Server running at http://{host}:{port}")
    print(f"   SSE endpoint: http://{host}:{port}/sse")
    print(f"   Health check: http://{host}:{port}/health")
    
    config = uvicorn.Config(starlette_app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


def get_config() -> tuple[str, int | str]:
    """Load configuration from environment or config.py.

    Returns:
        Tuple of (vin, interval) where interval is either an integer or 'realtime'

    Raises:
        ConfigurationError: If required configuration is missing or invalid
    """
    logger.debug("Loading configuration")

    # Load VIN
    vin = os.getenv(ENV_VEHICLE_VIN)
    if not vin:
        try:
            from config import VIN
            vin = VIN
            logger.info("Loaded VIN from config.py")
        except ImportError:
            error_msg = (
                f"{ENV_VEHICLE_VIN} environment variable or config.VIN required. "
                "Please set VEHICLE_VIN in your .env file."
            )
            logger.error(error_msg)
            raise ConfigurationError(error_msg)

    # Validate VIN format
    if not validate_vin(vin):
        logger.warning("VIN appears to have invalid format (expected 17 characters)")

    # Load interval
    interval_str = os.getenv(ENV_TELEMETRY_INTERVAL, "5")
    if interval_str.lower() == "realtime":
        interval: int | str = "realtime"
        logger.info("Using realtime telemetry (no caching)")
    else:
        try:
            interval = int(interval_str)
            if interval <= 0:
                raise ValueError("Interval must be positive")
            logger.info("Using %d minute telemetry interval", interval)
        except ValueError as e:
            error_msg = f"Invalid {ENV_TELEMETRY_INTERVAL}: {interval_str}. Must be a positive integer or 'realtime'."
            logger.error(error_msg)
            raise ConfigurationError(error_msg)

    return vin, interval


def main() -> None:
    """Main entry point for the MCP server.

    Parses command line arguments, loads configuration, and starts the server
    in the requested transport mode (STDIO or SSE).
    """
    import asyncio

    logger.info("Starting Tessie MCP Server")

    parser = argparse.ArgumentParser(
        description="Tesla Tessie MCP Server - Exposes Tesla telemetry and control via Tessie API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with STDIO transport (local)
  python -m src.server

  # Run with SSE transport (remote HTTP)
  python -m src.server --transport sse --port 8000

Configuration:
  Set VEHICLE_VIN and TESSIE_TOKEN in .env file.
  See .env.example for template.
        """
    )
    parser.add_argument(
        "--transport", "-t",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport mode: stdio (local) or sse (remote HTTP)"
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_SSE_HOST,
        help=f"Host to bind to for SSE mode (default: {DEFAULT_SSE_HOST})"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=DEFAULT_SSE_PORT,
        help=f"Port for SSE mode (default: {DEFAULT_SSE_PORT})"
    )

    args = parser.parse_args()

    try:
        vin, interval = get_config()

        if args.transport == "sse":
            logger.info("Starting in SSE mode on %s:%d", args.host, args.port)
            asyncio.run(run_server_sse(vin, interval, args.host, args.port))
        else:
            logger.info("Starting in STDIO mode")
            asyncio.run(run_server_stdio(vin, interval))

    except ConfigurationError as e:
        logger.critical("Configuration error: %s", str(e))
        print(f"\n❌ Configuration Error: {str(e)}\n", file=sys.stderr)
        sys.exit(1)
    except TessieMCPError as e:
        logger.critical("Fatal error: %s", str(e))
        print(f"\n❌ Error: {str(e)}\n", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        print("\nServer stopped.", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        logger.critical("Unexpected error: %s", str(e), exc_info=True)
        print(f"\n❌ Unexpected Error: {str(e)}\n", file=sys.stderr)
        print("Check logs for details.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
