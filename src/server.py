"""MCP server for Tesla telemetry and (upcoming) control via Tessie API."""

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


# Load environment variables from .env file in project root
load_dotenv(PROJECT_ROOT / ".env")

# Initialize server
app = Server("tessie-mcp")

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
    """Initialize telemetry and control services and build dispatch map."""
    global _telemetry, _control, _tool_dispatch
    _telemetry = Telemetry(vin=vin, interval=interval)
    _control = Control(vin=vin)
    _tool_dispatch = {
        **build_telemetry_dispatch(_telemetry),
        **build_control_dispatch(_control),
    }


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
    """Load configuration from environment or config.py."""
    # Load VIN
    vin = os.getenv("VEHICLE_VIN")
    if not vin:
        try:
            from config import VIN
            vin = VIN
        except ImportError:
            print("Error: VEHICLE_VIN environment variable or config.VIN required")
            sys.exit(1)

    # Load interval
    interval_str = os.getenv("TELEMETRY_INTERVAL", "5")
    if interval_str.lower() == "realtime":
        interval: int | str = "realtime"
    else:
        try:
            interval = int(interval_str)
        except ValueError:
            print(f"Error: Invalid TELEMETRY_INTERVAL: {interval_str}")
            sys.exit(1)

    return vin, interval


def main() -> None:
    """Main entry point for the MCP server."""
    import asyncio
    
    parser = argparse.ArgumentParser(description="Tesla Tessie MCP Server")
    parser.add_argument(
        "--transport", "-t",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport mode: stdio (local) or sse (remote HTTP)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to for SSE mode (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="Port for SSE mode (default: 8000)"
    )
    
    args = parser.parse_args()
    vin, interval = get_config()

    if args.transport == "sse":
        asyncio.run(run_server_sse(vin, interval, args.host, args.port))
    else:
        asyncio.run(run_server_stdio(vin, interval))


if __name__ == "__main__":
    main()
