# Tesla Tessie MCP Server

A Model Context Protocol (MCP) server that provides Tesla vehicle telemetry data via the Tessie API. Exposes vehicle status, battery, charging, climate, and location data as tools for LLM consumption.

## Features

- **Intelligent Caching**: Configurable data refresh intervals to minimize API calls
- **Thread-Safe**: Concurrent access to cached data is safely handled
- **LLM-Optimized Output**: Human-readable formatted strings for each data point
- **Comprehensive Telemetry**: 30+ tools covering all vehicle data categories

## Installation

```bash
# Clone the repository
cd tessie_mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Required: Your Tessie API token
TESSIE_TOKEN=your_tessie_api_token_here

# Optional: Override vehicle plate (defaults to config.py)
VEHICLE_PLATE=34MIE386

# Optional: Data refresh interval in minutes (default: 5)
# Use 'realtime' to always fetch fresh data
TELEMETRY_INTERVAL=5
```

### Vehicle Configuration

The vehicle plate can also be configured in `config.py`:

```python
PLATE = '34MIE386'
```

## Usage

### 1. Create `.env` File

Copy the example and add your Tessie API token:

```bash
cp .env.example .env
```

Edit `.env`:
```env
TESSIE_TOKEN=your_tessie_api_token_here
VEHICLE_PLATE=34MIE386
TELEMETRY_INTERVAL=5
```

Get your token from: https://dash.tessie.com/settings/api

### 2. Running the MCP Server

#### Local Mode (STDIO)

```bash
source venv/bin/activate
python -m src.server
```

#### Remote Mode (HTTP/SSE)

```bash
source venv/bin/activate
python -m src.server --transport sse --port 8000
```

This starts an HTTP server with:
- SSE endpoint: `http://your-server:8000/sse`
- Health check: `http://your-server:8000/health`

### 3. Connecting to the MCP Server

#### Option A: Cursor IDE Integration

Add to your Cursor settings (`~/.cursor/mcp.json` or via Settings > MCP):

```json
{
  "mcpServers": {
    "tessie": {
      "command": "/path/to/tessie_mcp/venv/bin/python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/tessie_mcp"
    }
  }
}
```

After adding, restart Cursor. The Tesla tools will appear in your tool list.

#### Option B: Claude Desktop Integration

Add to Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "tessie": {
      "command": "/path/to/tessie_mcp/venv/bin/python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/tessie_mcp"
    }
  }
}
```

#### Option C: Direct Testing with MCP Inspector

```bash
# Install MCP inspector
npx @anthropic-ai/mcp-inspector

# In another terminal, run your server
python -m src.server
```

#### Option D: Remote Connection (HTTP/SSE)

Start the server in SSE mode on your remote machine:
```bash
python -m src.server --transport sse --host 0.0.0.0 --port 8000
```

Then connect from a client using the SSE URL:
```
http://your-server-ip:8000/sse
```

For Cursor/Claude, configure with SSE transport:
```json
{
  "mcpServers": {
    "tessie-remote": {
      "transport": "sse",
      "url": "http://your-server-ip:8000/sse"
    }
  }
}
```

#### Option E: Programmatic Usage (Python)

```python
from src.telemetry import Telemetry

# Create telemetry instance (reads from .env automatically)
telemetry = Telemetry(plate="34MIE386", interval=5)

# Get formatted data (for LLMs)
print(telemetry.get_battery_level())      # "Battery is at 41%"
print(telemetry.get_charging_state())     # "Vehicle is not connected to a charger"
print(telemetry.get_location())           # "Vehicle is at 39.869430, 32.733333 facing N (2°)"

# Get raw data (for programmatic use)
print(telemetry._get_battery_level())     # 41
print(telemetry._get_energy_remaining())  # 27.76
```

## Available Tools

### Battery & Charging

| Tool | Description |
|------|-------------|
| `get_battery_level` | Current battery percentage |
| `get_energy_remaining` | Remaining energy in kWh |
| `get_lifetime_energy_used` | Total lifetime energy consumption |
| `get_battery_heater_on` | Battery heater status (cold weather) |
| `get_charging_state` | Current charging status |
| `get_charge_limit_soc` | Charging limit percentage |
| `get_charge_port_door_open` | Charge port door status |
| `get_minutes_to_full_charge` | Time remaining to full charge |
| `get_charging_complete_at` | Estimated completion datetime |
| `get_battery_summary` | Comprehensive battery summary |

### Climate & Temperature

| Tool | Description |
|------|-------------|
| `get_is_climate_on` | HVAC system status |
| `get_outside_temp` | Ambient temperature |
| `get_allow_cabin_overheat_protection` | COP enabled status |
| `get_supports_fan_only_cabin_overheat_protection` | Fan-only COP capability |

### Heaters

| Tool | Description |
|------|-------------|
| `get_seat_heater_left` | Driver seat heater level |
| `get_seat_heater_right` | Passenger seat heater level |
| `get_seat_heater_rear_left` | Rear left seat heater level |
| `get_seat_heater_rear_center` | Rear center seat heater level |
| `get_seat_heater_rear_right` | Rear right seat heater level |
| `get_steering_wheel_heater` | Steering wheel heater status |
| `get_side_mirror_heaters` | Side mirror heaters status |
| `get_wiper_blade_heater` | Wiper blade heater status |
| `get_all_heater_status` | Summary of all heaters |

### Drive State & Location

| Tool | Description |
|------|-------------|
| `get_location` | GPS coordinates and heading |
| `get_speed` | Current vehicle speed |
| `get_power` | Power usage/regeneration |
| `get_shift_state` | Current gear (P/R/N/D) |
| `get_active_route` | Active navigation info |

### Vehicle State

| Tool | Description |
|------|-------------|
| `get_in_service` | Service mode status |
| `get_sentry_mode` | Sentry Mode status |
| `get_display_name` | Vehicle's custom name |

## Architecture

```
src/
├── __init__.py          # Package initialization
├── tessie_client.py     # Tessie API client
├── telemetry.py         # Telemetry class with caching
└── server.py            # MCP server entry point
```

### Telemetry Class

The `Telemetry` class implements a dual-method pattern for each data field:

- **Private methods** (`_get_*`): Return raw values for programmatic use
- **Public methods** (`get_*`): Return formatted strings for LLM consumption

Example:
```python
telemetry._get_battery_level()  # Returns: 41
telemetry.get_battery_level()   # Returns: "Battery is at 41%"
```

### Caching Strategy

- Data is cached with timestamps
- On each request, elapsed time is checked against the interval
- If stale, fresh data is fetched from Tessie API
- Thread-safe access using locks

## License

MIT
