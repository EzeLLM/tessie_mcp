"""MCP server for Tesla vehicle telemetry via Tessie API."""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Add parent directory to path for imports when running as script
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.telemetry import Telemetry


# Load environment variables from .env file in project root
load_dotenv(PROJECT_ROOT / ".env")

# Initialize server
app = Server("tessie-telemetry")

# Global telemetry instance (initialized on startup)
_telemetry: Telemetry | None = None


def get_telemetry() -> Telemetry:
    """Get the global Telemetry instance.
    
    Returns:
        Telemetry instance.
    
    Raises:
        RuntimeError: If telemetry is not initialized.
    """
    if _telemetry is None:
        raise RuntimeError("Telemetry not initialized. Call init_telemetry() first.")
    return _telemetry


def init_telemetry(plate: str, interval: int | str = 5) -> None:
    """Initialize the global Telemetry instance.
    
    Args:
        plate: Vehicle license plate.
        interval: Data refresh interval in minutes, or 'realtime'.
    """
    global _telemetry
    _telemetry = Telemetry(plate=plate, interval=interval)


# =============================================================================
# TOOL DEFINITIONS
# =============================================================================

TOOLS = [
    Tool(
        name="get_in_service",
        description="Check if the vehicle is in service mode (used during maintenance/repairs)",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_battery_heater_on",
        description="Check if the battery heater is active (warms battery for optimal charging in cold weather)",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_battery_level",
        description="Get the current battery level as a percentage",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_charge_limit_soc",
        description="Get the charging limit percentage (100% means no limit set)",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_charge_port_door_open",
        description="Check if the charge port door is open or closed",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_charging_state",
        description="Get the current charging status (Charging, Complete, Disconnected, etc.)",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_minutes_to_full_charge",
        description="Get the estimated time remaining until charging is complete",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_charging_complete_at",
        description="Get the estimated date and time when charging will be complete",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_energy_remaining",
        description="Get the remaining battery energy in kilowatt-hours (kWh)",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_lifetime_energy_used",
        description="Get the total energy consumed by the vehicle over its lifetime in kWh",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_allow_cabin_overheat_protection",
        description="Check if Cabin Overheat Protection (COP) is enabled",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_outside_temp",
        description="Get the outside ambient temperature in Celsius",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_is_climate_on",
        description="Check if the climate control (HVAC) is currently active",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_supports_fan_only_cabin_overheat_protection",
        description="Check if vehicle supports fan-only Cabin Overheat Protection (uses less energy than AC)",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_seat_heater_left",
        description="Get the driver (left front) seat heater status and level",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_seat_heater_right",
        description="Get the passenger (right front) seat heater status and level",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_seat_heater_rear_left",
        description="Get the rear left seat heater status and level",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_seat_heater_rear_center",
        description="Get the rear center seat heater status and level",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_seat_heater_rear_right",
        description="Get the rear right seat heater status and level",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_side_mirror_heaters",
        description="Check if the side mirror heaters are active",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_steering_wheel_heater",
        description="Get the steering wheel heater status and level",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_wiper_blade_heater",
        description="Check if the windshield wiper blade heater is active",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_location",
        description="Get the vehicle's current GPS location and heading direction",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_power",
        description="Get the current power usage or regeneration in kilowatts",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_speed",
        description="Get the vehicle's current speed",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_shift_state",
        description="Get the current gear (Park, Reverse, Neutral, Drive)",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_active_route",
        description="Get information about the active navigation route (destination, ETA, distance, battery at arrival)",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_sentry_mode",
        description="Check if Sentry Mode is active (security camera monitoring)",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_display_name",
        description="Get the vehicle's custom display name",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_all_heater_status",
        description="Get a summary of all heater statuses (seats, steering wheel, mirrors, wipers)",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_battery_summary",
        description="Get a comprehensive battery and charging summary",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
]


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available telemetry tools.
    
    Returns:
        List of Tool definitions.
    """
    return TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a telemetry tool.
    
    Args:
        name: Tool name to execute.
        arguments: Tool arguments (unused for telemetry, but required by MCP).
    
    Returns:
        List containing TextContent with the tool result.
    
    Raises:
        ValueError: If tool name is unknown.
    """
    telemetry = get_telemetry()
    
    # Map tool names to telemetry methods
    tool_methods = {
        "get_in_service": telemetry.get_in_service,
        "get_battery_heater_on": telemetry.get_battery_heater_on,
        "get_battery_level": telemetry.get_battery_level,
        "get_charge_limit_soc": telemetry.get_charge_limit_soc,
        "get_charge_port_door_open": telemetry.get_charge_port_door_open,
        "get_charging_state": telemetry.get_charging_state,
        "get_minutes_to_full_charge": telemetry.get_minutes_to_full_charge,
        "get_charging_complete_at": telemetry.get_charging_complete_at,
        "get_energy_remaining": telemetry.get_energy_remaining,
        "get_lifetime_energy_used": telemetry.get_lifetime_energy_used,
        "get_allow_cabin_overheat_protection": telemetry.get_allow_cabin_overheat_protection,
        "get_outside_temp": telemetry.get_outside_temp,
        "get_is_climate_on": telemetry.get_is_climate_on,
        "get_supports_fan_only_cabin_overheat_protection": telemetry.get_supports_fan_only_cabin_overheat_protection,
        "get_seat_heater_left": telemetry.get_seat_heater_left,
        "get_seat_heater_right": telemetry.get_seat_heater_right,
        "get_seat_heater_rear_left": telemetry.get_seat_heater_rear_left,
        "get_seat_heater_rear_center": telemetry.get_seat_heater_rear_center,
        "get_seat_heater_rear_right": telemetry.get_seat_heater_rear_right,
        "get_side_mirror_heaters": telemetry.get_side_mirror_heaters,
        "get_steering_wheel_heater": telemetry.get_steering_wheel_heater,
        "get_wiper_blade_heater": telemetry.get_wiper_blade_heater,
        "get_location": telemetry.get_location,
        "get_power": telemetry.get_power,
        "get_speed": telemetry.get_speed,
        "get_shift_state": telemetry.get_shift_state,
        "get_active_route": telemetry.get_active_route,
        "get_sentry_mode": telemetry.get_sentry_mode,
        "get_display_name": telemetry.get_display_name,
        "get_all_heater_status": telemetry.get_all_heater_status,
        "get_battery_summary": telemetry.get_battery_summary,
    }
    
    if name not in tool_methods:
        raise ValueError(f"Unknown tool: {name}")
    
    result = tool_methods[name]()
    return [TextContent(type="text", text=result)]


async def run_server_stdio(plate: str, interval: int | str = 5) -> None:
    """Run the MCP server with STDIO transport (local).
    
    Args:
        plate: Vehicle license plate to monitor.
        interval: Data refresh interval in minutes, or 'realtime'.
    """
    init_telemetry(plate=plate, interval=interval)
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


async def run_server_sse(plate: str, interval: int | str = 5, host: str = "0.0.0.0", port: int = 8000) -> None:
    """Run the MCP server with SSE transport (remote).
    
    Args:
        plate: Vehicle license plate to monitor.
        interval: Data refresh interval in minutes, or 'realtime'.
        host: Host to bind to (0.0.0.0 for all interfaces).
        port: Port to listen on.
    """
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.responses import JSONResponse
    import uvicorn
    
    init_telemetry(plate=plate, interval=interval)
    
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
        return JSONResponse({"status": "ok", "server": "tessie-telemetry"})
    
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
        Tuple of (plate, interval).
    """
    # Load plate
    plate = os.getenv("VEHICLE_PLATE")
    if not plate:
        try:
            from config import PLATE
            plate = PLATE
        except ImportError:
            print("Error: VEHICLE_PLATE environment variable or config.PLATE required")
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
    
    return plate, interval


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
    plate, interval = get_config()
    
    if args.transport == "sse":
        asyncio.run(run_server_sse(plate, interval, args.host, args.port))
    else:
        asyncio.run(run_server_stdio(plate, interval))


if __name__ == "__main__":
    main()

